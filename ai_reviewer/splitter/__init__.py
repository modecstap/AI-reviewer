"""Split an article .docx into the `refine/` folder of the per-article layout.

Each chapter becomes a folder holding its paragraphs as `1.txt`, `2.txt`, ...;
`chapters.json` lists the chapters in document order.

CLI: python -m ai_reviewer.splitter <article.docx> <output dir>
"""

from .article_parser import ArticleParser
from .article_splitter import ArticleSplitter
from .chapter import CHAPTERS_FILE, NO_HEADING, Chapter
from .chapter_writer import ChapterWriter
from .command_line import SplitterCommandLine
from .errors import (
    ArticleNotFoundError,
    ArticleReadError,
    InvalidArticleError,
    OutputPathIsFileError,
    OutputWriteError,
    SplitError,
)

__all__ = [
    "CHAPTERS_FILE",
    "NO_HEADING",
    "ArticleNotFoundError",
    "ArticleParser",
    "ArticleReadError",
    "ArticleSplitter",
    "Chapter",
    "ChapterWriter",
    "InvalidArticleError",
    "OutputPathIsFileError",
    "OutputWriteError",
    "SplitError",
    "SplitterCommandLine",
]
