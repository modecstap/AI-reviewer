import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from cursor_sdk import (
    AgentOptions,
    CursorAgentError,
    CursorClient,
    LocalAgentOptions,
    ModelSelection,
)

from .. import BridgeLaunchError, MissingApiKeyError
from .session import CursorAgentSession


class CursorAgentLauncher:
    """Starts local Cursor agents of a run through the Cursor bridge."""

    def __init__(self, model: ModelSelection) -> None:
        """
        Set up the launcher.

        :param model: Cursor model every agent runs on
        """
        self._model = model

    def check(self) -> None:
        """
        Check that the Cursor API key is set; called before the run dir exists.

        :raises MissingApiKeyError: when ``CURSOR_API_KEY`` is unset or blank
        """
        self._api_key()

    @contextmanager
    def connect(self, run_dir: Path) -> Iterator[CursorAgentSession]:
        """
        Launch the Cursor bridge with the run dir as the agents' workspace.

        :param run_dir: run dir the agents work in

        :raises MissingApiKeyError: when ``CURSOR_API_KEY`` is unset or blank
        :raises BridgeLaunchError: when the Cursor bridge cannot start

        :return: session of the run; the bridge closes on exit
        """
        options = AgentOptions(
            model=self._model,
            api_key=self._api_key(),
            local=LocalAgentOptions(cwd=str(run_dir)),
        )
        try:
            bridge = CursorClient.launch_bridge(workspace=str(run_dir))
        except (CursorAgentError, OSError) as error:
            raise BridgeLaunchError(
                f"cannot launch Cursor bridge: {error}"
            ) from error
        with bridge as client:
            yield CursorAgentSession(client, options)

    @staticmethod
    def _api_key() -> str:
        """
        Read the Cursor API key from the environment.

        :raises MissingApiKeyError: when ``CURSOR_API_KEY`` is unset or blank

        :return: the API key
        """
        api_key = os.environ.get("CURSOR_API_KEY", "")
        if not api_key.strip():
            raise MissingApiKeyError("CURSOR_API_KEY is not set")
        return api_key
