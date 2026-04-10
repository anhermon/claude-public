import os
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker, Session
from models import Base, Event, EventType, Session as SessionModel

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./telemetry.db")

# Create engine with SQLite-specific settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Query operations

def create_or_get_session(db: Session, session_id: str, custom_data: Optional[dict] = None) -> SessionModel:
    """Create a new session or return existing one."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        session = SessionModel(id=session_id, custom_data=custom_data)
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def add_event(
    db: Session,
    session_id: str,
    event_type: EventType,
    tool_name: Optional[str] = None,
    tool_input: Optional[dict] = None,
    tool_output: Optional[dict] = None,
    duration_ms: Optional[float] = None,
    error_message: Optional[str] = None,
    custom_data: Optional[dict] = None,
) -> Event:
    """Add an event to the database and update session stats."""
    session = create_or_get_session(db, session_id)

    event = Event(
        session_id=session_id,
        event_type=event_type,
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
        duration_ms=duration_ms,
        error_message=error_message,
        custom_data=custom_data,
    )
    db.add(event)

    # Update session stats
    session.event_count = (session.event_count or 0) + 1
    if event_type in [EventType.PreToolUse, EventType.PostToolUse]:
        session.tool_use_count = (session.tool_use_count or 0) + 1
    if error_message:
        session.error_count = (session.error_count or 0) + 1
    if duration_ms:
        session.total_duration_ms = (session.total_duration_ms or 0) + duration_ms

    # Mark session as ended if Stop or SessionEnd event
    if event_type in [EventType.SessionEnd, EventType.Stop]:
        session.ended_at = event.timestamp

    db.commit()
    db.refresh(event)
    return event


def get_session(db: Session, session_id: str) -> Optional[SessionModel]:
    """Get a session by ID."""
    return db.query(SessionModel).filter(SessionModel.id == session_id).first()


def get_all_sessions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
) -> List[SessionModel]:
    """Get all sessions with optional filtering."""
    query = db.query(SessionModel)

    if status == "active":
        query = query.filter(SessionModel.ended_at.is_(None))
    elif status == "completed":
        query = query.filter(SessionModel.ended_at.isnot(None))

    return query.order_by(desc(SessionModel.created_at)).offset(skip).limit(limit).all()


def count_sessions(
    db: Session,
    status: Optional[str] = None,
) -> int:
    """Count all sessions with optional filtering."""
    query = db.query(SessionModel)

    if status == "active":
        query = query.filter(SessionModel.ended_at.is_(None))
    elif status == "completed":
        query = query.filter(SessionModel.ended_at.isnot(None))

    return query.count()


def get_session_events(db: Session, session_id: str) -> List[Event]:
    """Get all events for a session."""
    return (
        db.query(Event)
        .filter(Event.session_id == session_id)
        .order_by(Event.timestamp)
        .all()
    )


def get_metrics(
    db: Session,
    session_id: Optional[str] = None,
    time_range_hours: int = 24,
) -> dict:
    """Calculate telemetry metrics."""
    cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)

    base_query = db.query(Event).filter(Event.timestamp >= cutoff_time)

    if session_id:
        base_query = base_query.filter(Event.session_id == session_id)

    total_events = base_query.count()
    events_by_type = db.query(
        Event.event_type,
        func.count(Event.id).label('count')
    ).filter(Event.timestamp >= cutoff_time).group_by(Event.event_type).all()

    tool_events = base_query.filter(
        Event.event_type.in_([EventType.PreToolUse, EventType.PostToolUse])
    ).all()

    tool_usage = {}
    for event in tool_events:
        if event.tool_name:
            if event.tool_name not in tool_usage:
                tool_usage[event.tool_name] = 0
            tool_usage[event.tool_name] += 1

    errors = base_query.filter(Event.error_message.isnot(None)).count()

    avg_duration = None
    durations = base_query.filter(Event.duration_ms.isnot(None)).all()
    if durations:
        avg_duration = sum(e.duration_ms for e in durations) / len(durations)

    sessions_count = db.query(SessionModel).filter(
        SessionModel.created_at >= cutoff_time
    ).count()

    return {
        "time_range_hours": time_range_hours,
        "timestamp": datetime.utcnow().isoformat(),
        "total_events": total_events,
        "events_by_type": {str(t[0].value): t[1] for t in events_by_type},
        "tool_usage": tool_usage,
        "error_count": errors,
        "average_event_duration_ms": avg_duration,
        "total_sessions": sessions_count,
    }


def get_live_feed(db: Session, limit: int = 50) -> tuple[List[dict], int]:
    """Get recent events and count of active sessions for live feed."""
    # Get recent events (last 50, ordered by most recent first)
    recent_events = (
        db.query(Event)
        .order_by(desc(Event.timestamp))
        .limit(limit)
        .all()
    )

    # Convert events to live feed format
    live_events = []
    for event in reversed(recent_events):  # Reverse to chronological order
        event_type = event.event_type.value

        # Map backend event types to frontend types
        if event_type == "SessionStart":
            feed_type = "session_start"
            data = {
                "userEmail": event.custom_data.get("userEmail") if event.custom_data else None,
                "sessionId": event.session_id
            }
        elif event_type == "SessionEnd":
            feed_type = "session_end"
            data = {
                "duration": event.duration_ms,
                "sessionId": event.session_id
            }
        elif event_type == "PreToolUse":
            feed_type = "tool_start"
            data = {
                "toolName": event.tool_name,
                "sessionId": event.session_id
            }
        elif event_type == "PostToolUse":
            feed_type = "tool_end"
            data = {
                "toolName": event.tool_name,
                "status": "completed" if not event.error_message else "failed",
                "sessionId": event.session_id
            }
        else:
            continue

        live_events.append({
            "sessionId": event.session_id,
            "type": feed_type,
            "timestamp": int(event.timestamp.timestamp() * 1000),  # Convert to milliseconds
            "data": data
        })

    # Count active sessions (sessions without ended_at)
    active_count = db.query(SessionModel).filter(SessionModel.ended_at.is_(None)).count()

    return live_events, active_count
