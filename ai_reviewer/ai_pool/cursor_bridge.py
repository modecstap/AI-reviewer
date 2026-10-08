from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path

from cursor_sdk import CursorAgentError, CursorClient

from .errors import BridgeLaunchError


class CursorBridge:
    """Launches the Cursor bridge of a run and closes it afterwards."""

    @contextmanager
    def connect(self, run_dir: Path) -> Iterator[CursorClient]:
        """
        Launch the Cursor bridge for the run dir.

        :param run_dir: workspace of the bridge

        :raises BridgeLaunchError: when the Cursor bridge cannot start

        :return: client connected to the bridge; the bridge closes on exit
        """
        with ExitStack() as stack:
            try:
                client = stack.enter_context(
                    CursorClient.launch_bridge(workspace=str(run_dir))
                )
            except (CursorAgentError, OSError) as error:
                raise BridgeLaunchError(
                    f"cannot launch Cursor bridge: {error}"
                ) from error
            yield client
