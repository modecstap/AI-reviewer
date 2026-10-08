"""Run one Cursor SDK agent per academic-writing property in parallel.

Each ``AIPool.execute`` writes into a new run dir ``{output_dir}/{N}/``:
``article.txt`` plus ``{name}.json`` of every agent that succeeded.
"""

from .entities import AgentStatus, PoolResult
from .errors import (
    BridgeLaunchError,
    DuplicateAgentError,
    MissingApiKeyError,
    NoAgentsError,
    OutputDirMismatchError,
    PoolStartError,
    RunDirError,
)
from .pool import AIPool

__all__ = [
    "AIPool",
    "AgentStatus",
    "BridgeLaunchError",
    "DuplicateAgentError",
    "MissingApiKeyError",
    "NoAgentsError",
    "OutputDirMismatchError",
    "PoolResult",
    "PoolStartError",
    "RunDirError",
]
