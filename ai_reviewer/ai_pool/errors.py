class DuplicateAgentError(ValueError):
    """An agent with this name is already registered."""


class OutputDirMismatchError(ValueError):
    """The output dir differs from the one of the agents added before."""


class PoolStartError(Exception):
    """The run cannot start."""


class NoAgentsError(PoolStartError):
    """No agents are registered."""


class MissingApiKeyError(PoolStartError):
    """``CURSOR_API_KEY`` is not set."""


class RunDirError(PoolStartError):
    """The run dir cannot be created or filled."""


class BridgeLaunchError(PoolStartError):
    """The Cursor bridge cannot be launched."""


class PropertyDocsError(Exception):
    """A property docs file cannot be read."""
