"""Run one Cursor SDK agent per academic-writing property in parallel.

Each ``AIPool.execute`` writes into a new run dir ``{output_dir}/{N}/``:
``article.txt`` plus ``{name}.json`` of every agent that succeeded.
"""

from .agent import AgentStatus, AgentDefinition
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
from .result import PoolResult

__all__ = [
    "AIPool",
    "AgentStatus",
    "AgentDefinition",
    "BridgeLaunchError",
    "DuplicateAgentError",
    "MissingApiKeyError",
    "NoAgentsError",
    "OutputDirMismatchError",
    "PoolResult",
    "PoolStartError",
    "RunDirError",
]
