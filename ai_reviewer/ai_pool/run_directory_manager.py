import logging
import shutil
from pathlib import Path

from .errors import RunDirError

logger = logging.getLogger(__name__)


class RunDirectoryManager:
    """Picks, creates and removes the numbered run dirs of an output dir."""

    def next_run_dir(self, output_dir: Path) -> Path:
        """
        Pick the run dir after the highest numbered one in the output dir.

        :param output_dir: dir of numbered run dirs

        :raises RunDirError: when the output dir cannot be listed

        :return: ``{output_dir}/{max N + 1}``; ``1`` for the first run
        """
        output_dir = output_dir.resolve()
        if not output_dir.is_dir():
            return output_dir / "1"
        try:
            names = [
                path.name for path in output_dir.iterdir() if path.is_dir()
            ]
        except OSError as error:
            raise RunDirError(f"cannot list {output_dir}: {error}") from error
        numbers = [
            int(name) for name in names if name.isascii() and name.isdigit()
        ]
        return output_dir / str(max(numbers, default=0) + 1)

    def create(self, run_dir: Path, text: str) -> None:
        """
        Create the run dir with ``article.txt``; remove it if writing fails.

        :param run_dir: run dir to create; must not exist
        :param text: article text to write into ``article.txt``

        :raises RunDirError: when the dir or ``article.txt`` cannot be written
        """
        try:
            run_dir.mkdir(parents=True)
        except OSError as error:
            raise RunDirError(f"cannot create {run_dir}: {error}") from error
        article = run_dir / "article.txt"
        try:
            article.write_text(text, encoding="utf-8", newline="")
        except OSError as error:
            self.remove(run_dir)
            raise RunDirError(f"cannot write {article}: {error}") from error

    def remove(self, run_dir: Path) -> None:
        """
        Remove the run dir of a failed run; only log if removal fails.

        The caller re-raises the original error, which must not be replaced.

        :param run_dir: run dir to remove
        """
        try:
            shutil.rmtree(run_dir)
        except OSError as error:
            logger.warning("cannot remove run dir %s: %s", run_dir, error)
