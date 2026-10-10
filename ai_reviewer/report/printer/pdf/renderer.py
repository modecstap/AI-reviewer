from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from .errors import PdfRenderError
from .page_breaks import ParagraphPageBreaks

if TYPE_CHECKING:
    from weasyprint import Document

PANGO_HINT = (
    "on Windows install MSYS2, run "
    "'pacman -S mingw-w64-ucrt-x86_64-pango' in the UCRT64 shell and set "
    r"WEASYPRINT_DLL_DIRECTORIES=C:\msys64\ucrt64\bin"
)


class PdfRenderer:
    """Renders the printed report as a PDF with WeasyPrint."""

    def __init__(
        self, stylesheet: Path, page_breaks: ParagraphPageBreaks | None = None
    ) -> None:
        """
        Set up the renderer.

        :param stylesheet: path of the report stylesheet; relative URLs of
            the HTML and CSS resolve against it
        :param page_breaks: paragraph page break chooser; default one when
            omitted
        """
        self._base_url = str(stylesheet)
        self._page_breaks = page_breaks or ParagraphPageBreaks()

    def render(self, html: str, css: str) -> bytes:
        """
        Render the HTML fragment styled by the stylesheet as a PDF.

        A paragraph block whose caption and text do not fit in the rest of
        the page starts on a new page.

        :param html: HTML fragment of the report
        :param css: stylesheet of the report; ``url(fonts/...)`` resolves
            against the stylesheet path

        :raises PdfRenderError: when WeasyPrint or Pango cannot be loaded, or
            the PDF cannot be rendered

        :return: PDF document bytes
        """
        document = self.document(html, css)
        try:
            return document.write_pdf()
        except OSError as error:
            raise PdfRenderError(f"cannot render the PDF: {error}") from error

    def document(self, html: str, css: str) -> "Document":
        """
        Lay out the HTML fragment with the paragraph page breaks it needs.

        :param html: HTML fragment of the report
        :param css: stylesheet of the report; ``url(fonts/...)`` resolves
            against the stylesheet path

        :raises PdfRenderError: when WeasyPrint or Pango cannot be loaded, or
            the document cannot be laid out

        :return: the laid-out WeasyPrint document
        """
        try:
            # WeasyPrint loads the native Pango libraries at import time.
            from weasyprint import CSS, HTML
            from weasyprint.text.fonts import FontConfiguration
        except (ImportError, OSError) as error:
            raise PdfRenderError(
                f"cannot load WeasyPrint to render the PDF: {error}; "
                f"{PANGO_HINT}"
            ) from error
        font_config = FontConfiguration()
        try:
            main = CSS(
                string=css, base_url=self._base_url, font_config=font_config
            )
            source = HTML(string=html, base_url=self._base_url)
            return self._lay_out(lambda breaks: source.render(
                stylesheets=[main, CSS(string=breaks, font_config=font_config)],
                font_config=font_config,
            ))
        except OSError as error:
            raise PdfRenderError(f"cannot render the PDF: {error}") from error

    def _lay_out(self, render: Callable[[str], "Document"]) -> "Document":
        """
        Render again with more page breaks until no paragraph block must move.

        :param render: renders the document with the given extra CSS

        :return: the document where no more paragraph block must move
        """
        moved: set[str] = set()
        while True:
            document = render(self._page_breaks.stylesheet(moved))
            moves = self._page_breaks.next_moves(
                [page.anchors for page in document.pages], moved
            )
            if not moves:
                return document
            moved |= moves
