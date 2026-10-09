from ..errors import ReportError


class ReportPrintError(ReportError):
    """The report of a run dir cannot be printed."""


class ReportFormatError(ReportPrintError):
    """
    ``report.json`` has an unexpected shape, or names a paragraph missing
    from ``article.txt``.
    """


class StylesheetReadError(ReportPrintError):
    """The bundled ``report.css`` cannot be read."""


class PdfRenderError(ReportPrintError):
    """WeasyPrint is unavailable or cannot render the PDF."""
