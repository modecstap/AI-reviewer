from pathlib import Path

from .errors import PdfRenderError

BASE_URL = str(Path(__file__).with_name("report.css"))
PANGO_HINT = (
    "on Windows install MSYS2, run "
    "'pacman -S mingw-w64-ucrt-x86_64-pango' in the UCRT64 shell and set "
    r"WEASYPRINT_DLL_DIRECTORIES=C:\msys64\ucrt64\bin"
)


class PdfRenderer:
    """Renders the printed report as a PDF with WeasyPrint."""

    def render(self, html: str, css: str) -> bytes:
        """
        Render the HTML fragment styled by the stylesheet as a PDF.

        :param html: HTML fragment of the report
        :param css: stylesheet of the report; ``url(fonts/...)`` resolves
            against the package directory

        :raises PdfRenderError: when WeasyPrint or Pango cannot be loaded, or
            the PDF cannot be rendered

        :return: PDF document bytes
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
            stylesheet = CSS(
                string=css, base_url=BASE_URL, font_config=font_config
            )
            return HTML(string=html, base_url=BASE_URL).write_pdf(
                stylesheets=[stylesheet], font_config=font_config
            )
        except OSError as error:
            raise PdfRenderError(f"cannot render the PDF: {error}") from error
