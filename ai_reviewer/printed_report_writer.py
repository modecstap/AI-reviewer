import logging
import os
from pathlib import Path

from ai_reviewer.report import (
    RUSSIAN_LABELS,
    ReportError,
    ReportLabels,
    ReportPrinter,
)

logger = logging.getLogger(__name__)

HTML_FILE = "report.html"
CSS_FILE = "report.css"
PDF_FILE = "report.pdf"


class PrintedReportWriteError(ReportError):
    """The printed report cannot be saved."""


class PrintedReportWriter:
    """Saves the printed report of a run dir as HTML, CSS and PDF files."""

    def __init__(self, printer: ReportPrinter | None = None) -> None:
        """
        Set up the writer.

        :param printer: report printer; default one when omitted
        """
        self._printer = printer or ReportPrinter()

    def write(
        self, run_dir: Path, labels: ReportLabels = RUSSIAN_LABELS
    ) -> None:
        """
        Print the report of the run dir; replace the previous files.

        :param run_dir: run dir ``problems/<N>/`` with ``report.json`` and
            ``article.txt``
        :param labels: fixed labels in the report language

        :raises RunDirReadError: when the run dir, ``report.json`` or
            ``article.txt`` cannot be read
        :raises ReportFormatError: when ``report.json`` is invalid or does not
            match ``article.txt``
        :raises StylesheetReadError: when the bundled stylesheet cannot be read
        :raises PdfRenderError: when the PDF cannot be rendered
        :raises PrintedReportWriteError: when a file cannot be written
        """
        html = self._printer.html(run_dir, labels)
        css = self._printer.css()
        pdf = self._printer.pdf(html, css)
        self._save(run_dir / HTML_FILE, html)
        self._save(run_dir / CSS_FILE, css)
        self._save(run_dir / PDF_FILE, pdf)

    @staticmethod
    def _save(path: Path, content: str | bytes) -> None:
        """
        Write one file atomically through a temporary file.

        :param path: target file path
        :param content: text, written as UTF-8, or raw bytes

        :raises PrintedReportWriteError: when the file cannot be written
        """
        temporary = path.with_name(path.name + ".tmp")
        try:
            if isinstance(content, bytes):
                temporary.write_bytes(content)
            else:
                temporary.write_text(content, encoding="utf-8", newline="")
            os.replace(temporary, path)
        except OSError as error:
            try:
                temporary.unlink(missing_ok=True)
            except OSError as cleanup_error:
                logger.warning("cannot remove %s: %s", temporary, cleanup_error)
            raise PrintedReportWriteError(
                f"cannot write {path}: {error}"
            ) from error
