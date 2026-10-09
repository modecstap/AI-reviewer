from pathlib import Path

from ai_reviewer.splitter import CHAPTER_MARKER, PARAGRAPH_MARKER

from .errors import RunDirReadError


class MarkedArticle:
    """Paragraph texts of a marked-up article by chapter and number."""

    def __init__(self, paragraphs: dict[str, dict[int, str]]) -> None:
        """
        Set up the article.

        :param paragraphs: paragraph text by number by chapter name,
            chapters in document order
        """
        self._paragraphs = paragraphs

    def chapters(self) -> list[str]:
        """
        List the chapter names.

        :return: chapter names in document order
        """
        return list(self._paragraphs)

    def has_chapter(self, chapter: str) -> bool:
        """
        Check whether the article has the chapter.

        :param chapter: chapter name

        :return: True when the chapter exists
        """
        return chapter in self._paragraphs

    def has_paragraph(self, chapter: str, number: int) -> bool:
        """
        Check whether the chapter has the paragraph.

        :param chapter: chapter name
        :param number: paragraph number within the chapter

        :return: True when the chapter and the paragraph exist
        """
        return number in self._paragraphs.get(chapter, {})

    def paragraph_text(self, chapter: str, number: int) -> str | None:
        """
        Get the text of a paragraph.

        :param chapter: chapter name
        :param number: paragraph number within the chapter

        :return: verbatim paragraph text, or None when absent
        """
        return self._paragraphs.get(chapter, {}).get(number)


class MarkedArticleReader:
    """
    Reads the chapters and paragraphs of ``article.txt``.

    ``ArticleWriter`` writes each chapter as a ``!! chapter: <name>`` line
    followed by blocks ``!! paragraph: <N>\\n<text>`` separated by ``\\n\\n``.
    Chapters are joined by ``\\n\\n`` and the file ends with ``\\n``. Paragraph
    text is verbatim and may contain ``\\n``.
    """

    def read(self, article: Path) -> MarkedArticle:
        """
        Read ``article.txt``.

        :param article: marked-up article text file

        :raises RunDirReadError: when the article cannot be read

        :return: the article with paragraph texts, chapters in document order
        """
        try:
            text = article.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise RunDirReadError(f"cannot read {article}: {error}") from error
        return self._article_of(text)

    @classmethod
    def _article_of(cls, text: str) -> MarkedArticle:
        """
        Collect chapters and paragraph texts between the marker lines.

        :param text: marked-up article text

        :return: the article, chapters in document order
        """
        chapters: dict[str, dict[int, list[str]]] = {}
        chapter: dict[int, list[str]] | None = None
        paragraph: list[str] | None = None
        # ArticleWriter joins with "\n"; splitlines() also splits on \x0b etc.
        for line in text.split("\n"):
            number = cls._paragraph_number(line)
            if line.startswith(CHAPTER_MARKER):
                chapter = chapters[line.removeprefix(CHAPTER_MARKER)] = {}
                paragraph = None
            elif number is not None and chapter is not None:
                paragraph = chapter[number] = []
            elif paragraph is not None:
                paragraph.append(line)
        return MarkedArticle(
            {name: cls._texts_of(lines) for name, lines in chapters.items()}
        )

    @staticmethod
    def _paragraph_number(line: str) -> int | None:
        """
        Parse a paragraph marker line.

        :param line: article line

        :return: paragraph number, or None when the line is no valid marker
        """
        if not line.startswith(PARAGRAPH_MARKER):
            return None
        number = line.removeprefix(PARAGRAPH_MARKER)
        return int(number) if number.isascii() and number.isdigit() else None

    @staticmethod
    def _texts_of(lines: dict[int, list[str]]) -> dict[int, str]:
        """
        Join the lines of each paragraph into its verbatim text.

        :param lines: lines after each paragraph marker by paragraph number

        :return: paragraph text by number, without the separator newline
        """
        return {
            number: "\n".join(paragraph).removesuffix("\n")
            for number, paragraph in lines.items()
        }
