from html import escape
from pathlib import Path

from .. import ReportChapter
from .claim_pages import ClaimPagesRenderer
from .errors import StylesheetReadError
from .labels import ReportLabels
from .pdf import PdfRenderer
from .statistics import StatisticsPageRenderer
from .title_page import TitlePageRenderer

STYLESHEET = Path(__file__).with_name("report.css")


class ReportPrinter:
    """Prints the report as HTML, CSS and PDF; reads and writes no files."""

    def __init__(
        self,
        title_page: TitlePageRenderer | None = None,
        statistics_page: StatisticsPageRenderer | None = None,
        claim_pages: ClaimPagesRenderer | None = None,
        pdf_renderer: PdfRenderer | None = None,
    ) -> None:
        """
        Set up the printer.

        :param title_page: title page renderer; default one when omitted
        :param statistics_page: statistics page renderer; default one when
            omitted
        :param claim_pages: claim pages renderer; default one when omitted
        :param pdf_renderer: PDF renderer; default one with the bundled
            stylesheet when omitted
        """
        self._title_page = title_page or TitlePageRenderer()
        self._statistics_page = statistics_page or StatisticsPageRenderer()
        self._claim_pages = claim_pages or ClaimPagesRenderer()
        self._pdf_renderer = pdf_renderer or PdfRenderer(STYLESHEET)

    def html(self, chapters: list[ReportChapter], labels: ReportLabels) -> str:
        """
        Render the report as an HTML fragment.

        :param chapters: chapters of the report
        :param labels: labels in the report language with the catalog names

        :return: the ``<div class="ai-reviewer-report">`` fragment
        """
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
