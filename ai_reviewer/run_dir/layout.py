import logging
import shutil
from pathlib import Path

from .errors import RunDirWriteError
from .files import ARTICLE_FILE, PROPERTY_FILE

logger = logging.getLogger(__name__)


class RunDirs:
    """Creates, removes and names the files of numbered run dirs."""

    def create(self, output_dir: Path, article: str) -> Path:
        """
        Create the run dir after the highest numbered one, with the article.

        The run dir is removed when the article cannot be written.

        :param output_dir: dir of numbered run dirs; created when missing
        :param article: marked-up article text for ``article.txt``

        :raises RunDirWriteError: when the output dir cannot be listed, or
            the run dir or ``article.txt`` cannot be written

        :return: the new run dir ``<output_dir>/<N>/``
        """
        run_dir = self._next_run_dir(output_dir)
        try:
            run_dir.mkdir(parents=True)
        except OSError as error:
            raise RunDirWriteError(f"cannot create {run_dir}: {error}") from error
        path = self.article_file(run_dir)
        try:
            path.write_text(article, encoding="utf-8", newline="")
        except OSError as error:
            self.remove(run_dir)
            raise RunDirWriteError(f"cannot write {path}: {error}") from error
        return run_dir

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

    def article_file(self, run_dir: Path) -> Path:
        """
        Name the article file of a run dir.

        :param run_dir: run dir

        :return: path of ``article.txt``
        """
        return run_dir / ARTICLE_FILE

    def property_file(self, run_dir: Path, property_id: str) -> Path:
        """
        Name the claims file of a property in a run dir.

        :param run_dir: run dir
        :param property_id: property id

        :return: path of ``<property_id>.json``
        """
        return run_dir / PROPERTY_FILE.format(property_id=property_id)

    @staticmethod
    def _next_run_dir(output_dir: Path) -> Path:
        """
        Pick the run dir after the highest numbered one in the output dir.

        :param output_dir: dir of numbered run dirs

        :raises RunDirWriteError: when the output dir cannot be listed

        :return: ``<output_dir>/<max N + 1>``; ``1`` for the first run
        """
        output_dir = output_dir.resolve()
        if not output_dir.is_dir():
            return output_dir / "1"
        try:
            names = [
                path.name for path in output_dir.iterdir() if path.is_dir()
            ]
        except OSError as error:
            raise RunDirWriteError(f"cannot list {output_dir}: {error}") from error
        numbers = [
            int(name) for name in names if name.isascii() and name.isdigit()
        ]
        return output_dir / str(max(numbers, default=0) + 1)
