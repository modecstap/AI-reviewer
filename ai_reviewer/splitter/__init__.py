"""Split an article .docx into the `refine/` folder of the per-article layout.

Each chapter becomes a folder holding its paragraphs as `1.txt`, `2.txt`, ...;
`chapters.json` lists the chapters in document order.

CLI: python -m ai_reviewer.splitter <article.docx> <output dir>
"""

from .errors import ArticleReadError, OutputWriteError, SplitError
from .parsers.article_parser import ArticleParser
from .article_splitter import ArticleSplitter
from .entities.chapter import CHAPTERS_FILE, NO_HEADING, Chapter
from ai_reviewer.splitter.writers.chapter_writer import ChapterWriter
from .command_line import SplitterCommandLine


__all__ = [
    "CHAPTERS_FILE",
    "NO_HEADING",
    "ArticleParser",
    "ArticleReadError",
    "ArticleSplitter",
    "Chapter",
    "ChapterWriter",
    "OutputWriteError",
    "SplitError",
    "SplitterCommandLine",
]
