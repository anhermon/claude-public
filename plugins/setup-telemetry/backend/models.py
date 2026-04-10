from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Index, Enum as SQLEnum, Text
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class EventType(str, enum.Enum):
    SessionStart = "SessionStart"
    PreToolUse = "PreToolUse"
    PostToolUse = "PostToolUse"
    SessionEnd = "SessionEnd"
    Stop = "Stop"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    # Tool use specific fields
    tool_name = Column(String, nullable=True, index=True)
    tool_input = Column(JSON, nullable=True)
    tool_output = Column(JSON, nullable=True)

    # Performance metrics
    duration_ms = Column(Float, nullable=True)
    error_message = Column(String, nullable=True)

    # Custom data (renamed from metadata to avoid SQLAlchemy reserved name)
    custom_data = Column(JSON, nullable=True)

    __table_args__ = (
        Index('idx_session_timestamp', 'session_id', 'timestamp'),
    )


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    ended_at = Column(DateTime, nullable=True, index=True)

    # Custom data (renamed from metadata to avoid SQLAlchemy reserved name)
    custom_data = Column(JSON, nullable=True)

    # Summary stats
    event_count = Column(Integer, default=0)
    tool_use_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    total_duration_ms = Column(Float, default=0)

    __table_args__ = (
        Index('idx_created_at', 'created_at'),
    )
