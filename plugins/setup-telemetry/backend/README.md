# Telemetry API

A production-ready FastAPI telemetry server for tracking events, sessions, and metrics with real-time WebSocket updates.

## Features

- **Event Tracking**: Store and retrieve telemetry events (SessionStart, PreToolUse, PostToolUse, SessionEnd, Stop)
- **Session Management**: Track sessions with automatic statistics (event count, tool use, errors, duration)
- **Metrics API**: Aggregate metrics over configurable time ranges
- **Real-time Updates**: WebSocket endpoint for live event streaming
- **SQLite Storage**: Zero-configuration, file-based database
- **Production-Ready**: Graceful error handling, CORS support, health checks

## Quick Start

### Installation

```bash
cd /Users/angelhermon/.paperclip/instances/telemetry-backend
pip install -r requirements.txt
```

### Run the Server

```bash
python app.py
```

The server will start on `http://0.0.0.0:5000`

Alternatively, with uvicorn directly:

```bash
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

### Database

- Automatically created on first run as `telemetry.db` (SQLite)
- Schema auto-initializes via SQLAlchemy
- To reset: delete `telemetry.db` and restart the server

## API Endpoints

### POST /events

Create a new telemetry event.

**Request Body:**
```json
{
  "session_id": "session-123",
  "event_type": "SessionStart",
  "tool_name": "calculator",
  "tool_input": {"operation": "add", "values": [1, 2]},
  "tool_output": {"result": 3},
  "duration_ms": 45.2,
  "error_message": null,
  "metadata": {"user": "alice", "environment": "dev"}
}
```

**Event Types:**
- `SessionStart` - Session begins
- `PreToolUse` - Before tool execution
- `PostToolUse` - After tool execution
- `SessionEnd` - Session ends normally
- `Stop` - Session stopped

**Response:** `201 Created`
```json
{
  "id": 1,
  "session_id": "session-123",
  "event_type": "SessionStart",
  "timestamp": "2024-01-15T10:30:45.123456",
  "tool_name": null,
  "tool_input": null,
  "tool_output": null,
  "duration_ms": null,
  "error_message": null,
  "metadata": {"user": "alice", "environment": "dev"}
}
```

### GET /sessions

List all sessions with optional filtering.

**Query Parameters:**
- `skip` (int, default: 0) - Number of sessions to skip
- `limit` (int, default: 100, max: 1000) - Number of sessions to return
- `status` (string, optional) - Filter by "active" or "completed"

**Example:**
```
GET /sessions?status=active&limit=10
```

**Response:** `200 OK`
```json
[
  {
    "id": "session-123",
    "created_at": "2024-01-15T10:30:45.123456",
    "ended_at": null,
    "metadata": {"user": "alice"},
    "event_count": 5,
    "tool_use_count": 2,
    "error_count": 0,
    "total_duration_ms": 234.5
  }
]
```

### GET /sessions/{session_id}

Get detailed information about a specific session, including all events.

**Example:**
```
GET /sessions/session-123
```

**Response:** `200 OK`
```json
{
  "id": "session-123",
  "created_at": "2024-01-15T10:30:45.123456",
  "ended_at": "2024-01-15T10:35:20.654321",
  "metadata": {"user": "alice"},
  "event_count": 5,
  "tool_use_count": 2,
  "error_count": 0,
  "total_duration_ms": 234.5,
  "events": [
    {
      "id": 1,
      "session_id": "session-123",
      "event_type": "SessionStart",
      "timestamp": "2024-01-15T10:30:45.123456",
      "tool_name": null,
      "tool_input": null,
      "tool_output": null,
      "duration_ms": null,
      "error_message": null,
      "metadata": null
    }
  ]
}
```

### GET /metrics

Get aggregated telemetry metrics.

**Query Parameters:**
- `session_id` (string, optional) - Filter metrics for a specific session
- `time_range_hours` (int, default: 24, max: 720) - Time range in hours

**Example:**
```
GET /metrics?time_range_hours=24
GET /metrics?session_id=session-123&time_range_hours=1
```

**Response:** `200 OK`
```json
{
  "time_range_hours": 24,
  "timestamp": "2024-01-15T11:45:30.123456",
  "total_events": 42,
  "events_by_type": {
    "SessionStart": 5,
    "PreToolUse": 10,
    "PostToolUse": 10,
    "SessionEnd": 5,
    "Stop": 12
  },
  "tool_usage": {
    "calculator": 8,
    "weather": 2
  },
  "error_count": 3,
  "average_event_duration_ms": 52.3,
  "total_sessions": 5
}
```

### WebSocket /ws/sessions/{session_id}

Real-time event streaming for a session.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:5000/ws/sessions/session-123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New event:', data);
};

// Keep alive
setInterval(() => ws.send('ping'), 30000);
```

**Message Format:**
```json
{
  "type": "event",
  "event": {
    "id": 1,
    "session_id": "session-123",
    "event_type": "PostToolUse",
    "timestamp": "2024-01-15T10:31:10.123456",
    "tool_name": "calculator",
    "tool_input": {"operation": "add", "values": [1, 2]},
    "tool_output": {"result": 3},
    "duration_ms": 45.2,
    "error_message": null,
    "metadata": null
  }
}
```

### GET /health

Health check endpoint.

**Response:** `200 OK`
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T11:45:30.123456"
}
```

## Usage Examples

### Python Client

```python
import requests
import json

BASE_URL = "http://localhost:5000"

# Create a session event
response = requests.post(f"{BASE_URL}/events", json={
    "session_id": "session-123",
    "event_type": "SessionStart",
    "metadata": {"user": "alice"}
})
print(response.json())

# Log a tool use
requests.post(f"{BASE_URL}/events", json={
    "session_id": "session-123",
    "event_type": "PreToolUse",
    "tool_name": "calculator",
    "tool_input": {"operation": "add", "values": [1, 2]}
})

requests.post(f"{BASE_URL}/events", json={
    "session_id": "session-123",
    "event_type": "PostToolUse",
    "tool_name": "calculator",
    "tool_output": {"result": 3},
    "duration_ms": 45.2
})

# Get session details
response = requests.get(f"{BASE_URL}/sessions/session-123")
print(response.json())

# Get metrics
response = requests.get(f"{BASE_URL}/metrics?time_range_hours=24")
print(response.json())

# List active sessions
response = requests.get(f"{BASE_URL}/sessions?status=active")
print(response.json())
```

### cURL Examples

```bash
# Create event
curl -X POST http://localhost:5000/events \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-123",
    "event_type": "SessionStart"
  }'

# Get session
curl http://localhost:5000/sessions/session-123

# Get metrics
curl http://localhost:5000/metrics

# Get active sessions
curl "http://localhost:5000/sessions?status=active"

# Health check
curl http://localhost:5000/health
```

## Architecture

### Database Schema

**events** table:
- `id` (PK) - Auto-incrementing event ID
- `session_id` (FK) - Reference to session
- `event_type` - One of: SessionStart, PreToolUse, PostToolUse, SessionEnd, Stop
- `timestamp` - Event creation time (indexed)
- `tool_name` - Tool identifier (for tool events)
- `tool_input` - Tool input parameters (JSON)
- `tool_output` - Tool output/result (JSON)
- `duration_ms` - Event duration in milliseconds
- `error_message` - Error text (if any)
- `metadata` - Custom metadata (JSON)
- Index: `(session_id, timestamp)`

**sessions** table:
- `id` (PK) - Session identifier
- `created_at` - Session start time (indexed)
- `ended_at` - Session end time (nullable, indexed)
- `metadata` - Custom metadata (JSON)
- `event_count` - Total events in session
- `tool_use_count` - Tool execution count
- `error_count` - Error event count
- `total_duration_ms` - Aggregate duration

### WebSocket Flow

1. Client connects to `/ws/sessions/{session_id}`
2. Connection manager tracks active connections per session
3. When `/events` endpoint receives a POST:
   - Event is stored in database
   - Event is broadcasted to all WebSocket clients of that session
   - Failed connections are cleaned up automatically

## Configuration

### Environment Variables

- `DATABASE_URL` - Database connection string (default: `sqlite:///./telemetry.db`)

### Customization

To change the port or host, modify the `if __name__ == "__main__"` block in `app.py`:

```python
uvicorn.run(app, host="127.0.0.1", port=8000)
```

Or use uvicorn CLI:
```bash
uvicorn app:app --host 127.0.0.1 --port 8000
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `201 Created` - Event created successfully
- `200 OK` - Successful GET request
- `400 Bad Request` - Invalid event data
- `404 Not Found` - Session or resource not found
- `500 Internal Server Error` - Server error

Error responses include a detail message:
```json
{
  "detail": "Session not found"
}
```

## Testing

### Manual Testing

1. Start the server:
   ```bash
   python app.py
   ```

2. Create a session:
   ```bash
   curl -X POST http://localhost:5000/events \
     -H "Content-Type: application/json" \
     -d '{"session_id": "test-1", "event_type": "SessionStart"}'
   ```

3. Add events:
   ```bash
   curl -X POST http://localhost:5000/events \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "test-1",
       "event_type": "PreToolUse",
       "tool_name": "calc",
       "tool_input": {"x": 1, "y": 2}
     }'
   ```

4. Query session:
   ```bash
   curl http://localhost:5000/sessions/test-1
   ```

5. Get metrics:
   ```bash
   curl http://localhost:5000/metrics
   ```

## Production Deployment

For production use:

1. Use a production ASGI server (e.g., Gunicorn with Uvicorn workers):
   ```bash
   pip install gunicorn
   gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000
   ```

2. Consider using PostgreSQL or MySQL instead of SQLite for multi-process scenarios
3. Enable HTTPS/TLS
4. Add authentication/authorization as needed
5. Configure appropriate logging
6. Set up monitoring and alerting
7. Use environment variables for configuration
8. Keep database backups

## Development

### File Structure

```
telemetry-backend/
├── app.py              # FastAPI application and endpoints
├── models.py           # SQLAlchemy ORM models
├── database.py         # Database initialization and queries
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Code Overview

- **app.py**: FastAPI server with all endpoints and WebSocket handler
- **models.py**: SQLAlchemy declarative models for Event and Session
- **database.py**: Database engine setup, session management, and query operations
- **database.py** also includes the ConnectionManager class for WebSocket broadcasts

## License

MIT
