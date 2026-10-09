from ai_reviewer.splitter.entities.chapter import Chapter

CHAPTER_MARKER = "!! chapter: "
PARAGRAPH_MARKER = "!! paragraph: "


class ArticleWriter:
    """Renders chapters as the single text review agents receive."""

    def write(self, chapters: list[Chapter]) -> str:
        """
        Render the chapters as `!! chapter:` / `!! paragraph:` marked text.

        :param chapters: chapters in document order, as from ArticleParser.parse

        :return: the article text ending with one newline; "" for no chapters
        """
        if not chapters:
            return ""
        return "\n\n".join(self._chapter_text(c) for c in chapters) + "\n"

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
