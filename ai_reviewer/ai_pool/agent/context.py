from dataclasses import dataclass
from pathlib import Path

from .session import AgentSession


@dataclass(frozen=True)
class AgentRunContext:
    """Article, output file and session of one agent in one run."""

    article: Path
    output: Path
    session: AgentSession
