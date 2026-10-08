from pathlib import Path

from ai_reviewer.splitter.parsers.article_parser import ArticleParser
from ai_reviewer.splitter.writers.chapter_writer import ChapterWriter


class ArticleSplitter:
    """Parses an article and writes its chapters to an output folder."""

    def __init__(
        self,
        parser: ArticleParser | None = None,
        writer: ChapterWriter | None = None,
    ) -> None:
        """
        Set up the splitter.

        :param parser: article parser; default one when omitted
        :param writer: chapter writer; default one when omitted
        """
        self._parser = parser or ArticleParser()
        self._writer = writer or ChapterWriter()

    def split(self, docx_path: str | Path, output_dir: str | Path) -> None:
        """
        Parse the article, then replace `output_dir` with its chapters.

        `output_dir` is untouched when the article cannot be read.

        :param docx_path: path to the article .docx
        :param output_dir: output folder; deleted and recreated

        :raises ArticleReadError:
        :raises OutputWriteError:
        """
        chapters = self._parser.parse(docx_path)
        self._writer.write(chapters, output_dir)
