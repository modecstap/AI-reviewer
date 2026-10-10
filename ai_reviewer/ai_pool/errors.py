class DuplicateAgentError(ValueError):
    """An agent with this property id is already registered."""


class PoolStartError(Exception):
    """The run cannot start."""


class NoAgentsError(PoolStartError):
    """No agents are registered."""


class MissingApiKeyError(PoolStartError):
    """The API key of the agent backend is not set."""


class RunDirError(PoolStartError):
    """The run dir cannot be created or filled."""


class BridgeLaunchError(PoolStartError):
    """The agent backend cannot be launched."""
