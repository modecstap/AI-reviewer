from dataclasses import dataclass


@dataclass(frozen=True)
class PrintedReport:
    """The printed report: HTML fragment, its stylesheet and the PDF."""

    html: str
    css: str
    pdf: bytes
