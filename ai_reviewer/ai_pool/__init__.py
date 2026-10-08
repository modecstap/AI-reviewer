"""Run one Cursor SDK agent per academic-writing property in parallel.

Each ``AIPool.execute`` writes into a new run dir ``{output_dir}/{N}/``:
``article.txt`` plus ``{name}.json`` of every agent that succeeded.
"""

from .agent_output_validator import AgentOutputValidator
from .agent_registry import AgentRegistry
from .agent_runner import AgentRunner
from .cursor_agent_factory import CursorAgentFactory
from .cursor_bridge import CursorBridge
from .entities import AgentStatus, PoolResult
from .errors import (
    BridgeLaunchError,
    DuplicateAgentError,
    MissingApiKeyError,
    NoAgentsError,
    OutputDirMismatchError,
    PoolStartError,
    PropertyDocsError,
    RunDirError,
)
from .pool import AIPool
from .prompt_builder import PromptBuilder
from .run_directory_manager import RunDirectoryManager

__all__ = [
    "AIPool",
    "AgentOutputValidator",
    "AgentRegistry",
    "AgentRunner",
    "AgentStatus",
    "BridgeLaunchError",
    "CursorAgentFactory",
    "CursorBridge",
    "DuplicateAgentError",
    "MissingApiKeyError",
    "NoAgentsError",
    "OutputDirMismatchError",
    "PoolResult",
    "PoolStartError",
    "PromptBuilder",
    "PropertyDocsError",
    "RunDirError",
    "RunDirectoryManager",
]
