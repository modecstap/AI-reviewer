import json
import shutil
import tempfile
from pathlib import Path

from ai_reviewer.splitter.entities.chapter import Chapter, CHAPTERS_FILE
from ai_reviewer.splitter.errors import OutputWriteError
from ai_reviewer.splitter.writers.errors import OutputPathIsFileError


class ChapterWriter:
    """Replaces an output folder with chapter folders and `CHAPTERS_FILE`."""

    STAGING_PREFIX = ".splitter-"

    def write(self, chapters: list[Chapter], output_dir: str | Path) -> None:
        """
        Replace `output_dir` with the chapters.

        Chapters go to a sibling staging folder first, so a failure
        leaves the previous content of `output_dir` in place.

        :param chapters: chapters with unique folder names
        :param output_dir: output folder; deleted and recreated

        :raises OutputPathIsFileError:
        :raises OutputWriteError:
        """
        output = Path(output_dir).resolve()
        if output.exists() and not output.is_dir():
            raise OutputPathIsFileError(f"output path is a file: {output}")
        staging = self._stage(chapters, output)
        try:
            self._swap(staging, output)
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def _stage(self, chapters: list[Chapter], output: Path) -> Path:
        """
        Write the chapters into a new staging folder next to `output`.

        :param chapters: chapters to write
        :param output: final output folder

        :raises OutputWriteError:

        :return: staging folder
        """
        staging = self._create_staging(output)
        try:
            self._write_tree(chapters, staging)
        except OSError as error:
            shutil.rmtree(staging, ignore_errors=True)
            raise OutputWriteError(
                f"cannot write chapters to {staging}: {error}"
            ) from error
        return staging

    def _create_staging(self, output: Path) -> Path:
        """
        Create an empty staging folder next to `output`.

        :param output: final output folder

        :raises OutputWriteError:

        :return: staging folder
        """
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            folder = tempfile.mkdtemp(
                prefix=self.STAGING_PREFIX, dir=output.parent
            )
        except OSError as error:
            raise OutputWriteError(
                f"cannot create staging folder next to {output}: {error}"
            ) from error
        return Path(folder)

    @staticmethod
    def _write_tree(chapters: list[Chapter], root: Path) -> None:
        """
        Write chapter folders with numbered paragraph files and the index.

        :param chapters: chapters to write
        :param root: existing empty folder
        """
        for chapter in chapters:
            folder = root / chapter.name
            folder.mkdir()
            for number, text in enumerate(chapter.paragraphs, start=1):
                path = folder / f"{number}.txt"
                path.write_text(text, encoding="utf-8", newline="")
        index = [
            {"chapter": chapter.name, "title": chapter.title}
            for chapter in chapters
        ]
        content = json.dumps(index, ensure_ascii=False, indent=2)
        (root / CHAPTERS_FILE).write_text(content, encoding="utf-8")

    def _swap(self, staging: Path, output: Path) -> None:
        """
        Move the staging folder to `output`, restoring the old one on failure.

        :param staging: fully written staging folder
        :param output: final output folder

        :raises OutputWriteError:
        """
        backup = staging.with_name(staging.name + ".old")
        try:
            if output.exists():
                output.rename(backup)
            staging.rename(output)
        except OSError as error:
            self._restore(backup, output)
            raise OutputWriteError(
                f"cannot replace output folder {output}: {error}"
            ) from error
        # The new output is complete; a stale backup must not fail the write.
        shutil.rmtree(backup, ignore_errors=True)

    @staticmethod
    def _restore(backup: Path, output: Path) -> None:
        """
        Put the previous output back after a failed swap.

        :param backup: where the previous output was moved
        :param output: final output folder

        :raises OutputWriteError: when the previous output cannot be moved back
        """
        if not backup.exists() or output.exists():
            return
        try:
            backup.rename(output)
        except OSError as error:
            raise OutputWriteError(
                f"output folder {output} lost; "
                f"previous content kept at {backup}: {error}"
            ) from error
