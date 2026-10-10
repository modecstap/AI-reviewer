"""The article as chapters and paragraphs, and its marked-up text format."""

from .chapter import Chapter
from .marked_article import MarkedArticle
from .text import ArticleText

__all__ = ["ArticleText", "Chapter", "MarkedArticle"]
