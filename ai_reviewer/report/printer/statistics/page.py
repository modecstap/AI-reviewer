from html import escape

from ... import ReportChapter
from ..labels import ReportLabels
from .type_grid import ClaimTypeGrid


class StatisticsPageRenderer:
    """Renders the claim statistics page of the printed report as HTML."""

    def render(
        self, chapters: list[ReportChapter], labels: ReportLabels
    ) -> str:
        """
        Render the claim total, the property by type table and the legend.

        :param chapters: chapters of the report
        :param labels: labels in the report language with the catalog names

        :return: the ``<section class="statistics">`` HTML
        """
        grid = ClaimTypeGrid(chapters, labels)
        return (
            '<section class="statistics">\n'
            f"<h2>{escape(labels.statistics)}</h2>\n"
            f'<p class="total-claims"><span class="label">'
            f"{escape(labels.total_claims)}</span> "
            f"<strong>{grid.claim_total()}</strong></p>\n"
            f"{self._table(grid, labels)}"
            f"{self._legend(grid, labels)}"
            "</section>\n"
        )

    def _table(self, grid: ClaimTypeGrid, labels: ReportLabels) -> str:
        """
        Render the table of claim counts per property and type number.

        :param grid: claim counts of the report
        :param labels: fixed labels in the report language

        :return: the table HTML
        """
        header = "".join(
            f"<th>{escape(number)}</th>" for number in grid.numbers()
        )
        rows = "".join(
            self._row(grid, name, labels) for name in grid.properties()
        )
        return (
            '<table class="types-table">\n'
            f"<thead><tr><th></th>{header}"
            f"<th>{escape(labels.total)}</th></tr></thead>\n"
            f"<tbody>\n{rows}</tbody></table>\n"
        )

    def _row(
        self, grid: ClaimTypeGrid, property_id: str, labels: ReportLabels
    ) -> str:
        """
        Render the table row of one property.

        :param grid: claim counts of the report
        :param property_id: property id as in ``report.json``
        :param labels: fixed labels in the report language

        :return: the row HTML
        """
        cells = "".join(
            self._cell(grid, property_id, number)
            for number in grid.numbers()
        )
        total = grid.property_total(property_id)
        total_class = "total" if total else "total zero"
        return (
            '<tr><th scope="row">'
            f"{escape(labels.property_name(property_id))}</th>{cells}"
            f'<td class="{total_class}">{total}</td></tr>\n'
        )

    @staticmethod
    def _cell(grid: ClaimTypeGrid, property_id: str, number: str) -> str:
        """
        Render the cell of one property and type number.

        :param grid: claim counts of the report
        :param property_id: property id as in ``report.json``
        :param number: type number

        :return: an empty grey cell for a type the property lacks, else the
            claim count
        """
        if not grid.has_type(property_id, number):
            return '<td class="absent"></td>'
        count = grid.count(property_id, number)
        if not count:
            return '<td class="zero">0</td>'
        return f"<td>{count}</td>"

    def _legend(self, grid: ClaimTypeGrid, labels: ReportLabels) -> str:
        """
        Render the type names of every property with types.

        :param grid: claim counts of the report
        :param labels: fixed labels in the report language

        :return: the legend HTML
        """
        groups = "".join(
            self._legend_property(grid, name, labels)
            for name in grid.properties()
        )
        return f'<div class="legend">{groups}</div>\n'

    @staticmethod
    def _legend_property(
        grid: ClaimTypeGrid, property_id: str, labels: ReportLabels
    ) -> str:
        """
        Render the type names of one property.

        :param grid: claim counts of the report
        :param property_id: property id as in ``report.json``
        :param labels: fixed labels in the report language

        :return: the group HTML, or an empty string without types
        """
        items = "".join(
            "<li>"
            + escape(labels.type_caption(
                property_id, grid.claim_type(property_id, number)
            ))
            + "</li>"
            for number in grid.numbers()
            if grid.has_type(property_id, number)
        )
        if not items:
            return ""
        return (
            '<div class="legend-property"><p class="property">'
            f"{escape(labels.property_name(property_id))}</p>"
            f"<ul>{items}</ul></div>\n"
        )
