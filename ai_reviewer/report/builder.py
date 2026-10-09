import logging

logger = logging.getLogger(__name__)

type Claim = dict[str, object]
type Grouped = dict[str, dict[int, dict[str, list[Claim]]]]


class ReportBuilder:
    """Groups property claims by chapter, paragraph and property."""

    def build(
        self, outline: dict[str, set[int]], claims: dict[str, list[object]]
    ) -> list[dict[str, object]]:
        """
        Build the ``report.json`` content; skip claims with an invalid place.

        :param outline: paragraph numbers by chapter name, in document order
        :param claims: raw claim array by property name

        :return: chapters with claims in document order; ``[]`` for no claims
        """
        grouped: Grouped = {chapter: {} for chapter in outline}
        for property_name, items in claims.items():
            for item in items:
                self._add(grouped, property_name, item, outline)
        return self._render(grouped)

    def _add(
        self,
        grouped: Grouped,
        property_name: str,
        item: object,
        outline: dict[str, set[int]],
    ) -> None:
        """
        Add one claim under its place, or log why it is skipped.

        :param grouped: claims grouped so far; updated in place
        :param property_name: property the claim belongs to
        :param item: raw claim from the property file
        :param outline: paragraph numbers by chapter name
        """
        place = self._place_of(item, outline)
        if isinstance(place, str):
            logger.warning("%s: skip claim: %s", property_name, place)
            return
        chapter, paragraph = place
        claim = {key: value for key, value in item.items() if key != "place"}
        by_property = grouped[chapter].setdefault(paragraph, {})
        by_property.setdefault(property_name, []).append(claim)

    @staticmethod
    def _place_of(
        item: object, outline: dict[str, set[int]]
    ) -> tuple[str, int] | str:
        """
        Check the place of a claim against the article outline.

        :param item: raw claim from the property file
        :param outline: paragraph numbers by chapter name

        :return: chapter and paragraph, or why the claim is skipped
        """
        if not isinstance(item, dict):
            return "claim is not an object"
        place = item.get("place")
        if not isinstance(place, dict):
            return "no place"
        chapter = place.get("chapter")
        if not isinstance(chapter, str) or chapter not in outline:
            return f"unknown chapter {chapter!r}"
        paragraph = place.get("paragraph")
        # bool and float pass `in` checks: True in {1}, 3.0 in {3}.
        if type(paragraph) is not int or paragraph not in outline[chapter]:
            return f"unknown paragraph {paragraph!r} in chapter {chapter!r}"
        return chapter, paragraph

    @staticmethod
    def _render(grouped: Grouped) -> list[dict[str, object]]:
        """
        Render grouped claims; drop chapters without claims, sort the rest.

        :param grouped: claims by chapter, paragraph and property

        :return: chapters in document order, paragraphs ascending,
            property keys sorted by name
        """
        return [
            {
                "chapter": chapter,
                "claims": [
                    {"paragraph": number, **dict(sorted(by_property.items()))}
                    for number, by_property in sorted(paragraphs.items())
                ],
            }
            for chapter, paragraphs in grouped.items()
            if paragraphs
        ]
