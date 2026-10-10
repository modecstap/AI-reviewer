from .entities import Claim, ClaimType, PrintedChapter
from .labels import ReportLabels


class ClaimTypeGrid:
    """Claim counts per property and claim-type number of the printed report."""

    def __init__(
        self, chapters: list[PrintedChapter], labels: ReportLabels
    ) -> None:
        """
        Count the claims of the report.

        :param chapters: chapters of the report
        :param labels: fixed labels in the report language
        """
        self._labels = labels
        self._totals: dict[str, int] = {}
        self._counts: dict[tuple[str, str], int] = {}
        self._names: dict[tuple[str, str], str] = {}
        for chapter in chapters:
            for paragraph in chapter.paragraphs:
                for name, claims in paragraph.claims.items():
                    self._add_claims(name, claims)

    def _add_claims(self, property_name: str, claims: list[Claim]) -> None:
        """
        Count the claims of one property in one paragraph.

        :param property_name: property name as in ``report.json``
        :param claims: claims of the property
        """
        self._totals[property_name] = (
            self._totals.get(property_name, 0) + len(claims)
        )
        for claim in claims:
            numbers = {claim_type.number for claim_type in claim.types}
            for number in numbers - {None}:
                key = (property_name, number)
                self._counts[key] = self._counts.get(key, 0) + 1
            for claim_type in claim.types:
                if claim_type.number is not None and claim_type.name:
                    key = (property_name, claim_type.number)
                    self._names.setdefault(key, claim_type.name)

    def claim_total(self) -> int:
        """
        Count all claim objects of the report.

        :return: the number of claims
        """
        return sum(self._totals.values())

    def properties(self) -> list[str]:
        """
        List the grid rows: dictionary and report properties.

        :return: property names sorted by the printed name
        """
        names = set(self._labels.type_names) | set(self._totals)
        return sorted(names, key=self._labels.property_name)

    def numbers(self) -> list[str]:
        """
        List the grid columns: dictionary and report type numbers.

        :return: numbers in numeric order, non-numeric ones after them
        """
        numbers = {
            number
            for names in self._labels.type_names.values()
            for number in names
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

    def has_type(self, property_name: str, number: str) -> bool:
        """
        Check that a property has a claim type with this number.

        :param property_name: property name as in ``report.json``
        :param number: type number

        :return: whether the dictionary or the report has the type
        """
        known = self._labels.type_names.get(property_name, {})
        return number in known or (property_name, number) in self._counts

    def count(self, property_name: str, number: str) -> int:
        """
        Count the claims of a property with a type number.

        :param property_name: property name as in ``report.json``
        :param number: type number

        :return: the number of claims
        """
        return self._counts.get((property_name, number), 0)

    def property_total(self, property_name: str) -> int:
        """
        Count the claim objects of a property.

        :param property_name: property name as in ``report.json``

        :return: the number of claims
        """
        return self._totals.get(property_name, 0)

    def type_name(self, property_name: str, number: str) -> str | None:
        """
        Name a claim type: dictionary name first, else the report name.

        :param property_name: property name as in ``report.json``
        :param number: type number

        :return: the type name, or ``None`` when unknown
        """
        name = self._names.get((property_name, number))
        return self._labels.type_name(property_name, ClaimType(number, name))
