from .chapter import Chapter
from .marked_article import MarkedArticle

CHAPTER_MARKER = "!! chapter: "
PARAGRAPH_MARKER = "!! paragraph: "


class ArticleText:
    """
    Writes and reads the marked-up article text review agents receive.

    Each chapter is a ``!! chapter: <name>`` line followed by blocks
    ``!! paragraph: <N>\\n<text>`` separated by ``\\n\\n``. Chapters are joined
    by ``\\n\\n`` and the text ends with ``\\n``. Paragraph text is verbatim and
    may contain ``\\n``.
    """

    def write(self, chapters: list[Chapter]) -> str:
        """
        Render the chapters as `!! chapter:` / `!! paragraph:` marked text.

        :param chapters: chapters in document order

        :return: the article text ending with one newline; "" for no chapters
        """
        if not chapters:
            return ""
        return "\n\n".join(self._chapter_text(c) for c in chapters) + "\n"

    def read(self, text: str) -> MarkedArticle:
        """
        Collect chapters and paragraph texts between the marker lines.

        :param text: marked-up article text

        :return: the article, chapters in document order
        """
        chapters: dict[str, dict[int, list[str]]] = {}
        chapter: dict[int, list[str]] | None = None
        paragraph: list[str] | None = None
        # write joins with "\n"; splitlines() also splits on \x0b etc.
        for line in text.split("\n"):
            number = self._paragraph_number(line)
            if line.startswith(CHAPTER_MARKER):
                chapter = chapters[line.removeprefix(CHAPTER_MARKER)] = {}
                paragraph = None
            elif number is not None and chapter is not None:
                paragraph = chapter[number] = []
            elif paragraph is not None:
                paragraph.append(line)
        return MarkedArticle(
            {name: self._texts_of(lines) for name, lines in chapters.items()}
        )

    @staticmethod
    def _chapter_text(chapter: Chapter) -> str:
        """
        Render one chapter with its numbered paragraphs, text kept verbatim.

        :param chapter: chapter to render

        :return: the chapter block without trailing newline
        """
        paragraphs = "\n\n".join(
            f"{PARAGRAPH_MARKER}{number}\n{text}"
            for number, text in enumerate(chapter.paragraphs, start=1)
        )
        return "\n".join(
            filter(None, [f"{CHAPTER_MARKER}{chapter.name}", paragraphs])
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
