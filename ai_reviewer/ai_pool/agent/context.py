from dataclasses import dataclass
from pathlib import Path

from cursor_sdk import CursorClient


@dataclass(frozen=True)
class AgentRunContext:
    """Run dir, API key and bridge client shared by the agents of one run."""

    run_dir: Path
    api_key: str
    client: CursorClient
