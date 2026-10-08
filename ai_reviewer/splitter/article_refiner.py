from pathlib import Path

from ai_reviewer.splitter.parsers.article_parser import ArticleParser
from ai_reviewer.splitter.writers.article_writer import ArticleWriter


class ArticleRefiner:
    """Parses an article and refines it."""

    def __init__(
        self,
        parser: ArticleParser | None = None,
        writer: ArticleWriter | None = None,
    ) -> None:
        """
        Set up the splitter.

        :param parser: article parser; default one when omitted
        :param writer: chapter writer; default one when omitted
        """
        self._parser = parser or ArticleParser()
        self._writer = writer or ArticleWriter()

    def refine(self, docx_path: str | Path) -> str:
        chapters = self._parser.parse(docx_path)
        return self._writer.write(chapters)
