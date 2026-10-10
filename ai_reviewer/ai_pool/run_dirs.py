from pathlib import Path
from typing import Protocol


class RunDirLayout(Protocol):
    """Creates, removes and names the files of numbered run dirs."""

    def create(self, output_dir: Path, article: str) -> Path:
        """
        Create the next numbered run dir with the article file.

        A partly created run dir is removed before raising.

        :param output_dir: dir of numbered run dirs
        :param article: marked-up article text the agents review

        :raises OSError: when the run dir or the article file cannot be
            written

        :return: the new run dir ``<output_dir>/<N>/``
        """
        ...

    def remove(self, run_dir: Path) -> None:
        """
        Remove the run dir of a failed run; never raise, only log.

        :param run_dir: run dir to remove
        """
        ...

    def article_file(self, run_dir: Path) -> Path:
        """
        Name the article file of a run dir.

        :param run_dir: run dir

        :return: path of the article file
        """
        ...

    def property_file(self, run_dir: Path, property_id: str) -> Path:
        """
        Name the file an agent writes its claims to.

        :param run_dir: run dir
        :param property_id: property the agent reviews

        :return: path of the property file
        """
        ...
