import dataclasses
import datetime
from dataclasses import dataclass, field

from ai_reviewer.claims import ClaimType
from ai_reviewer.properties import PropertyNames


@dataclass(frozen=True)
class ReportLabels:
    """Labels of the printed report in one language."""

    language: str
    created: str
    total_claims: str
    statistics: str
    total: str
    chapter: str
    paragraph: str
    problem: str
    types: str
    quote: str
    months: tuple[str, ...]
    date_pattern: str
    names: PropertyNames = field(default_factory=PropertyNames)

    def with_names(self, names: PropertyNames) -> "ReportLabels":
        """
        Copy the labels with property and claim type names.

        :param names: property and claim type names in this language

        :return: the labels with ``names`` replaced
        """
        return dataclasses.replace(self, names=names)

    def property_name(self, property_id: str) -> str:
        """
        Translate a property name.

        :param property_id: property id as in ``report.json``

        :return: the translated name, or ``property_id`` without a translation
        """
        return self.names.property_name(property_id)

    def type_name(
        self, property_id: str, claim_type: ClaimType
    ) -> str | None:
        """
        Translate the name of a claim type by its number.

        :param property_id: property id as in ``report.json``
        :param claim_type: claim type to translate

        :return: the translated name, or the original name without a
            translation
        """
        translated = None
        if claim_type.number is not None:
            translated = self.names.type_name(property_id, claim_type.number)
        return claim_type.name if translated is None else translated

    def type_caption(self, property_id: str, claim_type: ClaimType) -> str:
        """
        Caption a claim type as ``<number>. <name>``.

        :param property_id: property id as in ``report.json``
        :param claim_type: claim type to caption

        :return: the present parts joined; ``""`` when both are absent
        """
        return ". ".join(filter(None, (
            claim_type.number, self.type_name(property_id, claim_type)
        )))

    def date(self, day: datetime.date) -> str:
        """
        Format a date in this language.

        :param day: date to format

        :return: the date by ``date_pattern``
        """
        return self.date_pattern.format(
            day=day.day,
            month=day.month,
            month_name=self.months[day.month - 1],
            year=day.year,
        )
