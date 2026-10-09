from dataclasses import dataclass
from pathlib import Path

from .agent import AgentStatus


@dataclass(frozen=True)
class PoolResult:
    """Run dir of one ``execute`` and the status of every agent by name."""

    run_dir: Path
    statuses: dict[str, AgentStatus]
