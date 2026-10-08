class SplitError(Exception):
    """Base of every expected splitter failure."""


class ArticleReadError(SplitError):
    """The article cannot be read."""

class OutputWriteError(SplitError):
    """The chapters cannot be written to the output folder."""
