from pathlib import Path

from ai_reviewer.splitter import CHAPTER_MARKER, PARAGRAPH_MARKER

from .errors import RunDirReadError


class OutlineReader:
    """Reads the chapters and paragraph numbers of a marked-up article."""

    def read(self, article: Path) -> dict[str, set[int]]:
        """
        Read the outline of ``article.txt``.

        :param article: marked-up article text file

        :raises RunDirReadError: when the article cannot be read

        :return: paragraph numbers by chapter name, chapters in document order
        """
        try:
            text = article.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise RunDirReadError(f"cannot read {article}: {error}") from error
        return self._outline_of(text)

    @staticmethod
    def _outline_of(text: str) -> dict[str, set[int]]:
        """
        Collect chapters and paragraph numbers from the marker lines.

        :param text: marked-up article text

        :return: paragraph numbers by chapter name, chapters in document order
        """
        outline: dict[str, set[int]] = {}
        chapter: str | None = None
        # ArticleWriter joins with "\n"; splitlines() also splits on \x0b etc.
        for line in text.split("\n"):
            if line.startswith(CHAPTER_MARKER):
                chapter = line.removeprefix(CHAPTER_MARKER)
                outline[chapter] = set()
            elif line.startswith(PARAGRAPH_MARKER) and chapter is not None:
                number = line.removeprefix(PARAGRAPH_MARKER)
                if number.isascii() and number.isdigit():
                    outline[chapter].add(int(number))
        return outline
