from dataclasses import dataclass
from pathlib import Path


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
