class SplitError(Exception):
    """Base of every expected splitter failure."""


class ArticleReadError(SplitError):
    """The article cannot be read."""


class ArticleNotFoundError(ArticleReadError):
    """The article path does not point to an existing file."""


class InvalidArticleError(ArticleReadError):
    """The article file exists but is not a valid .docx package."""


class OutputWriteError(SplitError):
    """The chapters cannot be written to the output folder."""


class OutputPathIsFileError(OutputWriteError):
    """The output path is occupied by a file instead of a folder."""
