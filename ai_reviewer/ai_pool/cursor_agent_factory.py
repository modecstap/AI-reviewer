import os
import uuid
from pathlib import Path

from cursor_sdk import AgentOptions, LocalAgentOptions

from .errors import MissingApiKeyError


class CursorAgentFactory:
    """Reads the Cursor API key and builds the options of new agents."""

    def __init__(self, model: str) -> None:
        """
        Set up the factory.

        :param model: Cursor model id every agent runs on
        """
        self._model = model

    def api_key(self) -> str:
        """
        Read the Cursor API key from the environment.

        :raises MissingApiKeyError: when ``CURSOR_API_KEY`` is unset or blank

        :return: the API key
        """
        api_key = os.environ.get("CURSOR_API_KEY", "")
        if not api_key.strip():
            raise MissingApiKeyError("CURSOR_API_KEY is not set")
        return api_key

    def options(self, run_dir: Path, api_key: str) -> AgentOptions:
        """
        Build the options of a new local agent with a fresh agent id.

        :param run_dir: run dir the agent works in
        :param api_key: Cursor API key

        :return: options for ``Agent.prompt``
        """
        return AgentOptions(
            model=self._model,
            api_key=api_key,
            agent_id=f"agent-{uuid.uuid4()}",
            local=LocalAgentOptions(cwd=str(run_dir)),
        )
