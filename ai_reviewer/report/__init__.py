"""Build ``report.json`` of one run dir ``problems/<N>/``.

Claims of every property file are grouped by chapter, paragraph and property.
The report is printed as an HTML fragment, a CSS stylesheet and a PDF.
"""

from .errors import ReportError, ReportWriteError, RunDirReadError
from .writer import REPORT_FILE, ReportWriter
from .printer import (
    ENGLISH_LABELS,
    RUSSIAN_LABELS,
    PdfRenderError,
    ReportFormatError,
    ReportLabels,
    ReportPrinter,
    ReportPrintError,
    StylesheetReadError,
)

__all__ = [
    "ENGLISH_LABELS",
    "PdfRenderError",
    "REPORT_FILE",
    "RUSSIAN_LABELS",
    "ReportError",
    "ReportFormatError",
    "ReportLabels",
    "ReportPrintError",
    "ReportPrinter",
    "ReportWriteError",
    "ReportWriter",
    "RunDirReadError",
    "StylesheetReadError",
]
