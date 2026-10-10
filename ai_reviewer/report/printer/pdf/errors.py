from ... import ReportError


class PdfRenderError(ReportError):
    """WeasyPrint is unavailable or cannot render the PDF."""
