from collections.abc import Callable
from datetime import date
from html import escape

from .. import ReportChapter
from .labels import ReportLabels


class TitlePageRenderer:
    """Renders the title page of the printed report as HTML."""

    def __init__(self, today: Callable[[], date] | None = None) -> None:
        """
        Set up the renderer.

        :param today: source of the creation date; ``date.today`` when omitted
        """
        self._today = today or date.today

    def render(
        self, chapters: list[ReportChapter], labels: ReportLabels
    ) -> str:
        """
        Render the title page with the creation date.

        :param chapters: chapters of the report
        :param labels: fixed labels in the report language

        :return: the ``<section class="title">`` HTML
        """
        created = escape(labels.date(self._today()))
        return (
            '<section class="title">\n'
            '<p class="company">VSRT</p>\n'
            '<h1 class="product">AI-Reviewer</h1>\n'
            f'<p class="created"><span class="label">'
            f"{escape(labels.created)}</span> {created}</p>\n"
            "</section>\n"
        )
