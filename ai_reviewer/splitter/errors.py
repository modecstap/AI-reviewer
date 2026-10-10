class ArticleReadError(Exception):
    """The article cannot be read."""


class ArticleNotFoundError(ArticleReadError):
    """The article path does not point to an existing file."""


class InvalidArticleError(ArticleReadError):
    """The article file exists but is not a valid .docx package."""
