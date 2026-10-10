from ai_reviewer.claims import Claim, ClaimType

from ... import ReportChapter
from ..labels import ReportLabels


class ClaimTypeGrid:
    """Claim counts per property and claim-type number of the printed report."""

    def __init__(
        self, chapters: list[ReportChapter], labels: ReportLabels
    ) -> None:
        """
        Count the claims of the report.

        :param chapters: chapters of the report
        :param labels: labels in the report language with the catalog names
        """
        self._labels = labels
        self._totals: dict[str, int] = {}
        self._counts: dict[tuple[str, str], int] = {}
        self._names: dict[tuple[str, str], str] = {}
        for chapter in chapters:
            for paragraph in chapter.paragraphs:
                for property_id, claims in paragraph.claims.items():
                    self._add_claims(property_id, claims)

    def _add_claims(self, property_id: str, claims: list[Claim]) -> None:
        """
        Count the claims of one property in one paragraph.

        :param property_id: property id as in ``report.json``
        :param claims: claims of the property
        """
        self._totals[property_id] = (
            self._totals.get(property_id, 0) + len(claims)
        )
        for claim in claims:
            types = claim.types
            numbers = {claim_type.number for claim_type in types}
            for number in numbers - {None}:
                key = (property_id, number)
                self._counts[key] = self._counts.get(key, 0) + 1
            for claim_type in types:
                if claim_type.number is not None and claim_type.name:
                    key = (property_id, claim_type.number)
                    self._names.setdefault(key, claim_type.name)

    def claim_total(self) -> int:
        """
        Count all claim objects of the report.

        :return: the number of claims
        """
        return sum(self._totals.values())

    def properties(self) -> list[str]:
        """
        List the grid rows: catalog and report properties.

        :return: property ids sorted by the printed name
        """
        names = self._labels.names
        property_ids = set(names.property_ids()) | set(self._totals)
        return sorted(property_ids, key=self._labels.property_name)

    def numbers(self) -> list[str]:
        """
        List the grid columns: catalog and report type numbers.

        :return: numbers in numeric order, non-numeric ones after them
        """
        names = self._labels.names
        numbers = {
            number
            for property_id in names.property_ids()
            for number in names.numbers(property_id)
        } | {number for _, number in self._counts}
        return sorted(numbers, key=self._number_key)

    @staticmethod
    def _number_key(number: str) -> tuple[int, int, str]:
        """
        Build the sort key of a type number.

        :param number: type number

        :return: numeric numbers first by value, others after by text
        """
        try:
            return (0, int(number), number)
        except ValueError:
            return (1, 0, number)

    def has_type(self, property_id: str, number: str) -> bool:
        """
        Check that a property has a claim type with this number.

        :param property_id: property id as in ``report.json``
        :param number: type number

        :return: whether the catalog or the report has the type
        """
        known = self._labels.names.numbers(property_id)
        return number in known or (property_id, number) in self._counts

    def count(self, property_id: str, number: str) -> int:
        """
        Count the claims of a property with a type number.

        :param property_id: property id as in ``report.json``
        :param number: type number

        :return: the number of claims
        """
        return self._counts.get((property_id, number), 0)

    def property_total(self, property_id: str) -> int:
        """
        Count the claim objects of a property.

        :param property_id: property id as in ``report.json``

        :return: the number of claims
        """
        return self._totals.get(property_id, 0)

    def claim_type(self, property_id: str, number: str) -> ClaimType:
        """
        Build a claim type of the grid with its first name in the report.

        :param property_id: property id as in ``report.json``
        :param number: type number

        :return: the claim type; its name is ``None`` when the report has none
        """
        return ClaimType(number, self._names.get((property_id, number)))
