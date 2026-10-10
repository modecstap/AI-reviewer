from contextlib import AbstractContextManager
from pathlib import Path
from typing import Protocol

from .agent import AgentSession


class AgentLauncher(Protocol):
    """Starts the agent backend of a run."""

    def check(self) -> None:
        """
        Check that the backend can start; called before the run dir exists.

        :raises MissingApiKeyError: when the backend API key is not set
        """
        ...

    def connect(self, run_dir: Path) -> AbstractContextManager[AgentSession]:
        """
        Start the backend with the run dir as the agents' workspace.

        :param run_dir: run dir the agents work in

        :raises BridgeLaunchError: when the backend cannot start

        :return: session of the run; the backend stops on exit
        """
        ...
