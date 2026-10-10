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
