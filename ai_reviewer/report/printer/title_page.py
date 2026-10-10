from collections.abc import Callable
from datetime import date
from html import escape

from .entities import PrintedChapter
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
        self, chapters: list[PrintedChapter], labels: ReportLabels
    ) -> str:
        """
        Render the title page with the creation date and claim counts.

        :param chapters: chapters of the report
        :param labels: fixed labels in the report language

        :return: the ``<section class="title">`` HTML
        """
        counts = self._counts(chapters)
        created = escape(labels.date(self._today()))
        return (
            '<section class="title">\n'
            '<p class="company">VSRT</p>\n'
            '<h1 class="product">AI-Reviewer</h1>\n'
            f'<p class="created"><span class="label">'
            f"{escape(labels.created)}</span> {created}</p>\n"
            '<section class="summary">\n'
            f'<p class="total"><span class="label">'
            f"{escape(labels.total_claims)}</span> "
            f"<strong>{sum(counts.values())}</strong></p>\n"
            f"{self._property_list(counts, labels)}"
            "</section>\n"
            "</section>\n"
        )

    @staticmethod
    def _counts(chapters: list[PrintedChapter]) -> dict[str, int]:
        """
        Count claim objects per property over all paragraphs.

        :param chapters: chapters of the report

        :return: claim counts by property name, without zeros
        """
        counts: dict[str, int] = {}
        for chapter in chapters:
            for paragraph in chapter.paragraphs:
                for name, claims in paragraph.claims.items():
                    counts[name] = counts.get(name, 0) + len(claims)
        return {name: count for name, count in counts.items() if count}

    @staticmethod
    def _property_list(counts: dict[str, int], labels: ReportLabels) -> str:
        """
        Render the claim counts per property, sorted by the printed name.

        :param counts: claim counts by property name
        :param labels: fixed labels in the report language

        :return: the list HTML, or an empty string without counts
        """
        if not counts:
            return ""
        names = {name: labels.property_name(name) for name in counts}
        items = "".join(
            f'<li><span class="property">{escape(names[name])}</span> '
            f'<span class="count">{counts[name]}</span></li>\n'
            for name in sorted(counts, key=names.__getitem__)
        )
        return f"<ul>\n{items}</ul>\n"
