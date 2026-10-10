"""Render the printed report as a PDF with paragraph page breaks."""

from .errors import PdfRenderError
from .page_breaks import ParagraphPageBreaks
from .renderer import PdfRenderer

__all__ = ["ParagraphPageBreaks", "PdfRenderError", "PdfRenderer"]
