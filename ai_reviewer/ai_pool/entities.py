from dataclasses import dataclass
from pathlib import Path

from cursor_sdk import CursorClient


@dataclass(frozen=True)
class AgentStatus:
    """Outcome of one agent; ``reason`` explains a failure."""

    ok: bool
    reason: str | None = None


@dataclass(frozen=True)
class PoolResult:
    """Run dir of one ``execute`` and the status of every agent by name."""

    run_dir: Path
    statuses: dict[str, AgentStatus]


@dataclass(frozen=True)
class AgentDefinition:
    """Files and name of one registered review agent."""

    io_structure: Path
    docs: Path
    name: str


@dataclass(frozen=True)
class AgentRunContext:
    """Run dir, API key and bridge client shared by the agents of one run."""

    run_dir: Path
    api_key: str
    client: CursorClient
