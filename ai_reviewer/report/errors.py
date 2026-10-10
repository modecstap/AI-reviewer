class ReportError(Exception):
    """The report cannot be built or printed."""


class ReportFormatError(ReportError):
    """
    ``report.json`` has an unexpected shape, or names a paragraph missing
    from the article.
    """
