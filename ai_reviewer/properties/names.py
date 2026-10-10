from dataclasses import dataclass, field


@dataclass(frozen=True)
class PropertyNames:
    """Names of the properties and their claim types in one language."""

    type_numbers: dict[str, tuple[str, ...]] = field(default_factory=dict)
    property_translations: dict[str, str] = field(default_factory=dict)
    type_translations: dict[str, dict[str, str]] = field(default_factory=dict)

    def property_ids(self) -> list[str]:
        """
        List the properties of the catalog.

        :return: property ids in catalog order
        """
        return list(self.type_numbers)

    def numbers(self, property_id: str) -> tuple[str, ...]:
        """
        List the claim type numbers of a property.

        :param property_id: property id

        :return: type numbers in ``reference.md`` order; empty for an unknown
            property
        """
        return self.type_numbers.get(property_id, ())

    def property_name(self, property_id: str) -> str:
        """
        Translate a property name.

        :param property_id: property id

        :return: the translated name, or ``property_id`` without a translation
        """
        return self.property_translations.get(property_id, property_id)

    def type_name(self, property_id: str, number: str) -> str | None:
        """
        Translate the name of a claim type.

        :param property_id: property id
        :param number: claim type number

        :return: the translated name, or None without a translation
        """
        return self.type_translations.get(property_id, {}).get(number)
