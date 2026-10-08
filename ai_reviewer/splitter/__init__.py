"""Split an article .docx into the `refine/` folder of the per-article layout.

Each chapter becomes a folder holding its paragraphs as `1.txt`, `2.txt`, ...;
`chapters.json` lists the chapters in document order.
`ArticleTextWriter` renders the chapters as the single text review agents receive.

CLI: python -m ai_reviewer.splitter <article.docx> <output dir>
"""

from .errors import ArticleReadError, OutputWriteError, RefineError
from .parsers.article_parser import ArticleParser
from .article_refiner import ArticleRefiner
from .entities.chapter import CHAPTERS_FILE, NO_HEADING, Chapter
from ai_reviewer.splitter.writers.article_writer import ArticleWriter
from .command_line import SplitterCommandLine


__all__ = [
    "CHAPTERS_FILE",
    "NO_HEADING",
    "ArticleParser",
    "ArticleReadError",
    "ArticleRefiner",
    "ArticleWriter",
    "Chapter",
    "OutputWriteError",
    "RefineError",
    "SplitterCommandLine",
]
