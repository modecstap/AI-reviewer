from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgentDefinition:
    """Id and prompt files of the review agent of one property."""

    id: str
    io_structure: Path
    instruction: Path
    reference: Path
