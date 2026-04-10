import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from database import init_db, get_db
from database import (
    add_event,
    get_session,
    get_all_sessions,
    get_session_events,
    get_metrics,
    count_sessions,
    get_live_feed,
)
from models import EventType, Session as SessionModel

# Initialize database
init_db()

# Pydantic schemas


class EventRequest(BaseModel):
    session_id: str
    event_type: EventType
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_output: Optional[dict] = None
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[dict] = None


class EventResponse(BaseModel):
    id: int
    session_id: str
    event_type: EventType
    timestamp: datetime
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_output: Optional[dict] = None
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[dict] = Field(default=None, alias="custom_data")

    class Config:
        from_attributes = True
        populate_by_name = True


class SessionResponse(BaseModel):
    id: str
    created_at: datetime
    ended_at: Optional[datetime] = None
    metadata: Optional[dict] = Field(default=None, alias="custom_data")
    event_count: int = 0
    tool_use_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0

    class Config:
        from_attributes = True
        populate_by_name = True


class SessionDetailResponse(SessionResponse):
    events: List[EventResponse] = []


class MetricsResponse(BaseModel):
    time_range_hours: int
    timestamp: str
    total_events: int
    events_by_type: Dict[str, int]
    tool_usage: Dict[str, int]
    error_count: int
    average_event_duration_ms: Optional[float] = None
    total_sessions: int


class LiveFeedEvent(BaseModel):
    sessionId: str
    type: str  # 'session_start', 'session_end', 'tool_start', 'tool_end'
    timestamp: int
    data: Dict[str, Optional[str]] = {}


class LiveFeedResponse(BaseModel):
    events: List[LiveFeedEvent]
    activeSessionCount: int


class ToolData(BaseModel):
    id: str
    name: str
    status: str
    startTime: int
    endTime: int
    duration: int
    error: Optional[str] = None
    inputTokens: Optional[int] = None
    outputTokens: Optional[int] = None


class SessionDetailForFrontend(BaseModel):
    id: str
    userId: str
    userEmail: str
    status: str
    startTime: int
    endTime: Optional[int] = None
    duration: Optional[int] = None
    tools: List[ToolData] = []
    inputTokens: int
    outputTokens: int
    totalCost: float
    errorMessage: Optional[str] = None


class SessionDetailResponseForFrontend(BaseModel):
    session: SessionDetailForFrontend


class MetricsResponseForFrontend(BaseModel):
    totalSessions: int
    activeSessions: int
    completedSessions: int
    failedSessions: int
    averageSessionDuration: float
    totalTokensUsed: int
    totalCost: float
    toolMetrics: List[Dict] = []
    errorBreakdown: List[Dict] = []
    sessionsByHour: List[Dict] = []


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = []
            self.active_connections[session_id].append(websocket)

    async def disconnect(self, session_id: str, websocket: WebSocket):
        async with self.lock:
            if session_id in self.active_connections:
                try:
                    self.active_connections[session_id].remove(websocket)
                    if not self.active_connections[session_id]:
                        del self.active_connections[session_id]
                except ValueError:
                    pass

    async def broadcast_event(self, session_id: str, event: dict):
        async with self.lock:
            connections = self.active_connections.get(session_id, [])

        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(event)
            except Exception:
                disconnected.append(connection)

        if disconnected:
            async with self.lock:
                for conn in disconnected:
                    if session_id in self.active_connections:
                        try:
                            self.active_connections[session_id].remove(conn)
                        except ValueError:
                            pass


manager = ConnectionManager()

# FastAPI app
app = FastAPI(
    title="Telemetry API",
    description="Event telemetry and session tracking",
    version="1.0.0",
)

# Add CORS middleware for sandbox compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Endpoints


@app.post("/events", response_model=EventResponse, status_code=201)
async def create_event(
    event: EventRequest,
    db: Session = Depends(get_db),
):
    """Create a new telemetry event."""
    try:
        db_event = add_event(
            db,
            session_id=event.session_id,
            event_type=event.event_type,
            tool_name=event.tool_name,
            tool_input=event.tool_input,
            tool_output=event.tool_output,
            duration_ms=event.duration_ms,
            error_message=event.error_message,
            custom_data=event.metadata,
        )

        # Broadcast event to WebSocket clients
        event_data = {
            "type": "event",
            "event": {
                "id": db_event.id,
                "session_id": db_event.session_id,
                "event_type": db_event.event_type.value,
                "timestamp": db_event.timestamp.isoformat(),
                "tool_name": db_event.tool_name,
                "tool_input": db_event.tool_input,
                "tool_output": db_event.tool_output,
                "duration_ms": db_event.duration_ms,
                "error_message": db_event.error_message,
                "metadata": db_event.custom_data,
            },
        }
        await manager.broadcast_event(event.session_id, event_data)

        return EventResponse.model_validate(db_event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SessionListResponseForFrontend(BaseModel):
    sessions: List[Dict] = []
    total: int
    page: int
    pageSize: int
    totalPages: int


@app.get("/sessions", response_model=SessionListResponseForFrontend)
@app.get("/api/sessions", response_model=SessionListResponseForFrontend)
async def list_sessions(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(active|completed)$"),
    db: Session = Depends(get_db),
):
    """List all sessions with optional filtering and pagination."""
    # Calculate skip and limit
    skip = (page - 1) * pageSize

    # Get total count
    total = count_sessions(db, status=status)

    # Get paginated sessions
    db_sessions = get_all_sessions(db, skip=skip, limit=pageSize, status=status)

    # Convert to frontend format
    sessions_data = []
    for session in db_sessions:
        # Determine status
        session_status = "active"
        if session.ended_at:
            session_status = "completed"

        # Get user info
        user_email = "unknown@example.com"
        user_id = "unknown"
        if session.custom_data:
            user_email = session.custom_data.get("userEmail", user_email)
            user_id = session.custom_data.get("userId", user_id)

        sessions_data.append({
            "id": session.id,
            "userId": user_id,
            "userEmail": user_email,
            "status": session_status,
            "startTime": int(session.created_at.timestamp() * 1000),
            "endTime": int(session.ended_at.timestamp() * 1000) if session.ended_at else None,
            "duration": int(session.total_duration_ms) if session.total_duration_ms else None,
            "tools": [],  # Empty for list view
            "inputTokens": 0,
            "outputTokens": 0,
            "totalCost": 0.0,
        })

    # Calculate total pages
    total_pages = (total + pageSize - 1) // pageSize

    return SessionListResponseForFrontend(
        sessions=sessions_data,
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages
    )


@app.get("/sessions/count", response_model=Dict[str, int])
async def count_sessions_endpoint(
    status: Optional[str] = Query(None, pattern="^(active|completed)$"),
    db: Session = Depends(get_db),
):
    """Count all sessions with optional filtering."""
    total = count_sessions(db, status=status)
    return {"count": total}


@app.get("/sessions/{session_id}", response_model=SessionDetailResponseForFrontend)
@app.get("/api/sessions/{session_id}", response_model=SessionDetailResponseForFrontend)
async def get_session_detail(
    session_id: str = None,
    db: Session = Depends(get_db),
):
    """Get detailed information about a specific session, including all events."""
    # Skip if session_id is "count" - let the count endpoint handle it
    if session_id == "count":
        raise HTTPException(status_code=404, detail="Not found")

    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    events = get_session_events(db, session_id)

    # Transform events to tools format
    tools = []
    for event in events:
        if event.event_type.value == "PreToolUse":
            tool = {
                "id": f"{event.id}",
                "name": event.tool_name or "Unknown",
                "status": "running",
                "startTime": int(event.timestamp.timestamp() * 1000),
                "endTime": int(event.timestamp.timestamp() * 1000),
                "duration": int(event.duration_ms or 0),
            }
            tools.append(tool)
        elif event.event_type.value == "PostToolUse":
            # Update the last matching tool with end time and status
            if tools:
                for tool in reversed(tools):
                    if tool["name"] == (event.tool_name or "Unknown"):
                        tool["status"] = "failed" if event.error_message else "completed"
                        tool["endTime"] = int(event.timestamp.timestamp() * 1000)
                        tool["duration"] = int(event.duration_ms or 0)
                        if event.error_message:
                            tool["error"] = event.error_message
                        break

    # Calculate token usage from events
    input_tokens = 0
    output_tokens = 0
    total_cost = 0.0

    for event in events:
        if event.custom_data:
            input_tokens += event.custom_data.get("inputTokens", 0)
            output_tokens += event.custom_data.get("outputTokens", 0)
            total_cost += event.custom_data.get("cost", 0.0)

    # Determine session status
    status = "active"
    if session.ended_at:
        status = "completed"

    # Get user info from session custom data
    user_email = "unknown@example.com"
    user_id = "unknown"
    if session.custom_data:
        user_email = session.custom_data.get("userEmail", user_email)
        user_id = session.custom_data.get("userId", user_id)

    session_detail = SessionDetailForFrontend(
        id=session.id,
        userId=user_id,
        userEmail=user_email,
        status=status,
        startTime=int(session.created_at.timestamp() * 1000),
        endTime=int(session.ended_at.timestamp() * 1000) if session.ended_at else None,
        duration=int(session.total_duration_ms) if session.total_duration_ms else None,
        tools=tools,
        inputTokens=input_tokens,
        outputTokens=output_tokens,
        totalCost=total_cost,
        errorMessage=None,
    )

    return SessionDetailResponseForFrontend(session=session_detail)


@app.get("/live", response_model=LiveFeedResponse)
@app.get("/api/live", response_model=LiveFeedResponse)
async def get_live_feed_endpoint(
    db: Session = Depends(get_db),
):
    """Get live feed of recent events and active session count."""
    events, active_count = get_live_feed(db, limit=50)
    return LiveFeedResponse(
        events=[LiveFeedEvent(**event) for event in events],
        activeSessionCount=active_count
    )


@app.get("/metrics", response_model=MetricsResponseForFrontend)
@app.get("/api/metrics", response_model=MetricsResponseForFrontend)
async def get_telemetry_metrics(
    fromDate: Optional[int] = Query(None),
    toDate: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Get aggregated telemetry metrics."""
    # Calculate time range from fromDate and toDate (milliseconds since epoch)
    time_range_hours = 24
    if fromDate and toDate:
        time_range_hours = max(1, int((toDate - fromDate) / (1000 * 60 * 60)))

    metrics = get_metrics(db, session_id=None, time_range_hours=time_range_hours)

    # Get session counts by status
    from datetime import timedelta as td
    cutoff_time = datetime.utcnow() - td(hours=time_range_hours)

    total_sessions = db.query(SessionModel).filter(
        SessionModel.created_at >= cutoff_time
    ).count()
    active_sessions = db.query(SessionModel).filter(
        SessionModel.created_at >= cutoff_time,
        SessionModel.ended_at.is_(None)
    ).count()
    completed_sessions = db.query(SessionModel).filter(
        SessionModel.created_at >= cutoff_time,
        SessionModel.ended_at.isnot(None)
    ).count()
    failed_sessions = 0  # Would need error tracking to implement

    # Calculate average session duration
    sessions = db.query(SessionModel).filter(
        SessionModel.created_at >= cutoff_time,
        SessionModel.ended_at.isnot(None)
    ).all()
    avg_duration = 0
    if sessions:
        total_duration = sum(s.total_duration_ms for s in sessions if s.total_duration_ms)
        avg_duration = int(total_duration / len(sessions)) if sessions else 0

    # Tool metrics
    tool_metrics = []
    for tool_name, count in metrics.get("tool_usage", {}).items():
        tool_metrics.append({
            "name": tool_name,
            "count": count,
            "averageDuration": 0,
            "failureRate": 0,
            "averageCost": 0
        })

    # Error breakdown
    error_breakdown = []
    for error_type, count in metrics.get("events_by_type", {}).items():
        if "error" in error_type.lower() or error_type in ["PreToolUse", "PostToolUse"]:
            error_breakdown.append({
                "errorType": error_type,
                "count": count,
                "percentage": round((count / metrics.get("total_events", 1)) * 100, 2)
            })

    # Sessions by hour (placeholder)
    sessions_by_hour = []

    return MetricsResponseForFrontend(
        totalSessions=total_sessions,
        activeSessions=active_sessions,
        completedSessions=completed_sessions,
        failedSessions=failed_sessions,
        averageSessionDuration=avg_duration,
        totalTokensUsed=0,
        totalCost=0.0,
        toolMetrics=tool_metrics,
        errorBreakdown=error_breakdown,
        sessionsByHour=sessions_by_hour
    )


@app.websocket("/ws/sessions/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time session updates."""
    await manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(session_id, websocket)
    except Exception:
        await manager.disconnect(session_id, websocket)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    import os

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5001))
    log_level = os.getenv("LOG_LEVEL", "info")

    print(f"Starting Telemetry API on {host}:{port}")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        access_log=True,
    )
