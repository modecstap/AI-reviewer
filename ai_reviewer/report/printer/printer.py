from html import escape
from pathlib import Path

from .claim_pages import ClaimPagesRenderer
from .errors import StylesheetReadError
from .labels import RUSSIAN_LABELS, ReportLabels
from .pdf import PdfRenderer
from .report_reader import ReportReader
from .statistics_page import StatisticsPageRenderer
from .title_page import TitlePageRenderer

STYLESHEET = Path(__file__).with_name("report.css")


class ReportPrinter:
    """Prints the report of a run dir as HTML, CSS and PDF; writes no files."""

    def __init__(
        self,
        reader: ReportReader | None = None,
        title_page: TitlePageRenderer | None = None,
        statistics_page: StatisticsPageRenderer | None = None,
        claim_pages: ClaimPagesRenderer | None = None,
        pdf_renderer: PdfRenderer | None = None,
    ) -> None:
        """
        Set up the printer.

        :param reader: run dir report reader; default one when omitted
        :param title_page: title page renderer; default one when omitted
        :param statistics_page: statistics page renderer; default one when
            omitted
        :param claim_pages: claim pages renderer; default one when omitted
        :param pdf_renderer: PDF renderer; default one when omitted
        """
        self._reader = reader or ReportReader()
        self._title_page = title_page or TitlePageRenderer()
        self._statistics_page = statistics_page or StatisticsPageRenderer()
        self._claim_pages = claim_pages or ClaimPagesRenderer()
        self._pdf_renderer = pdf_renderer or PdfRenderer()

    def html(
        self, run_dir: Path, labels: ReportLabels = RUSSIAN_LABELS
    ) -> str:
        """
        Render the report of the run dir as an HTML fragment.

        :param run_dir: run dir ``problems/<N>/`` with ``report.json`` and
            ``article.txt``
        :param labels: fixed labels in the report language

        :raises RunDirReadError: when the run dir, ``report.json`` or
            ``article.txt`` cannot be read
        :raises ReportFormatError: when ``report.json`` is invalid or does not
            match ``article.txt``

        :return: the ``<div class="ai-reviewer-report">`` fragment
        """
        chapters = self._reader.read(run_dir)
        language = escape(labels.language, quote=True)
        return (
            f'<div class="ai-reviewer-report" lang="{language}">\n'
            f"{self._title_page.render(chapters, labels)}"
            f"{self._statistics_page.render(chapters, labels)}"
            f"{self._claim_pages.render(chapters, labels)}"
            "</div>\n"
        )

    @staticmethod
    def css() -> str:
        """
        Read the stylesheet of the report.

        :raises StylesheetReadError: when the bundled ``report.css`` cannot
            be read

        :return: the CSS text; fonts are referenced as ``fonts/...``
            relative to it
        """
        try:
            return STYLESHEET.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise StylesheetReadError(
                f"cannot read {STYLESHEET}: {error}"
            ) from error

    def pdf(self, html: str, css: str) -> bytes:
        """
        Render the PDF from the given HTML and CSS plus computed paragraph
        page breaks.

        :param html: HTML fragment from ``html``
        :param css: stylesheet from ``css``

        :raises PdfRenderError: when WeasyPrint cannot render the PDF

        :return: PDF document bytes
        """
        return self._pdf_renderer.render(html, css)
