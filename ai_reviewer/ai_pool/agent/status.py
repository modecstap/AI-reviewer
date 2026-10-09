from dataclasses import dataclass


@dataclass(frozen=True)
class AgentStatus:
    """Outcome of one agent; ``reason`` explains a failure."""

    ok: bool
    reason: str | None = None
