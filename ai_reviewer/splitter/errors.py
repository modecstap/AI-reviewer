class RefineError(Exception):
    """Base of every expected splitter failure."""


class ArticleReadError(RefineError):
    """The article cannot be read."""

class OutputWriteError(RefineError):
    """The chapters cannot be written to the output folder."""
