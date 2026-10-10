from dataclasses import dataclass


@dataclass(frozen=True)
class Place:
    """Where a claim points: a chapter id and a paragraph number."""

    chapter: str
    paragraph: int


@dataclass(frozen=True)
class ClaimType:
    """Type of a claim; each part is ``None`` when absent."""

    number: str | None
    name: str | None


@dataclass(frozen=True)
class Claim:
    """
    One claim of a property.

    ``fields`` is the source claim object without ``place``, in source key
    order; it is written to ``report.json`` as is.
    """

    place: Place
    fields: dict[str, object]

    @property
    def quote(self) -> str | None:
        """
        Quote from the article.

        :return: the quote, or None when it is absent or not a string
        """
        return self._text_of(self.fields.get("quote"))

    @property
    def problem(self) -> str | None:
        """
        Description of the problem.

        :return: the problem, or None when it is absent or not a string
        """
        return self._text_of(self.fields.get("problem"))

    @property
    def types(self) -> list[ClaimType]:
        """
        Types of the claim; drop entries that are not objects.

        :return: claim types in source order; empty when absent
        """
        types = self.fields.get("types")
        if not isinstance(types, list):
            return []
        return [
            self._type_of(entry) for entry in types if isinstance(entry, dict)
        ]

    @classmethod
    def _type_of(cls, item: dict[str, object]) -> ClaimType:
        """
        Convert one claim type; drop parts that are missing or of a wrong type.

        :param item: raw claim type object

        :return: the claim type
        """
        number = item.get("number")
        valid = isinstance(number, int | str) and not isinstance(number, bool)
        return ClaimType(
            number=str(number) if valid else None,
            name=cls._text_of(item.get("name")),
        )

    @staticmethod
    def _text_of(value: object) -> str | None:
        """
        Keep a value only when it is a string.

        :param value: raw JSON value

        :return: the string, or None for any other value
        """
        return value if isinstance(value, str) else None
