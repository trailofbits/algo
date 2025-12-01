"""In-memory session management for deployments."""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class DeploymentStatus(Enum):
    """Status of a deployment session."""

    PENDING = "pending"
    VALIDATING = "validating"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Session:
    """A deployment session."""

    id: str
    provider: str
    credentials: dict[str, Any]
    config: dict[str, Any]
    status: DeploymentStatus = DeploymentStatus.PENDING
    output_lines: list[str] = field(default_factory=list)
    config_path: str | None = None
    error: str | None = None
    exit_code: int | None = None
    created_at: datetime = field(default_factory=datetime.now)
    process: asyncio.subprocess.Process | None = None

    def is_expired(self) -> bool:
        """Check if this session has expired (1 hour TTL)."""
        return datetime.now() - self.created_at > timedelta(hours=1)

    def add_output(self, line: str) -> None:
        """Add a line to the output buffer."""
        self.output_lines.append(line)

    def clear_credentials(self) -> None:
        """Clear credentials from memory after deployment starts."""
        self.credentials = {}


class SessionStore:
    """Thread-safe in-memory session store."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()

    async def create(
        self,
        provider: str,
        credentials: dict[str, Any],
        config: dict[str, Any],
    ) -> Session:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id,
            provider=provider,
            credentials=credentials,
            config=config,
        )

        async with self._lock:
            self._sessions[session_id] = session
            # Cleanup expired sessions
            await self._cleanup_expired()

        return session

    async def get(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session and session.is_expired():
                del self._sessions[session_id]
                return None
            return session

    async def update(self, session: Session) -> None:
        """Update a session."""
        async with self._lock:
            if session.id in self._sessions:
                self._sessions[session.id] = session

    async def delete(self, session_id: str) -> None:
        """Delete a session."""
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]

    async def _cleanup_expired(self) -> None:
        """Remove expired sessions (called during create)."""
        expired = [sid for sid, session in self._sessions.items() if session.is_expired()]
        for sid in expired:
            del self._sessions[sid]


# Global session store instance
sessions = SessionStore()
