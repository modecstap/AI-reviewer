from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgentDefinition:
    """Files and name of one registered review agent."""

    io_structure: Path
    docs: Path
    name: str
