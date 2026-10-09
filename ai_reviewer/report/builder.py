import logging

from .marked_article import MarkedArticle

logger = logging.getLogger(__name__)

type Claim = dict[str, object]
type Grouped = dict[str, dict[int, dict[str, list[Claim]]]]


class ReportBuilder:
    """Groups property claims by chapter, paragraph and property."""

    def build(
        self, article: MarkedArticle, claims: dict[str, list[object]]
    ) -> list[dict[str, object]]:
        """
        Build the ``report.json`` content; skip claims with an invalid place.

        :param article: marked-up article, chapters in document order
        :param claims: raw claim array by property name

        :return: chapters with claims in document order; ``[]`` for no claims
        """
        grouped: Grouped = {chapter: {} for chapter in article.chapters()}
        for property_name, items in claims.items():
            for item in items:
                self._add(grouped, property_name, item, article)
        return self._render(grouped)

    def _add(
        self,
        grouped: Grouped,
        property_name: str,
        item: object,
        article: MarkedArticle,
    ) -> None:
        """
        Add one claim under its place, or log why it is skipped.

        :param grouped: claims grouped so far; updated in place
        :param property_name: property the claim belongs to
        :param item: raw claim from the property file
        :param article: marked-up article
        """
        place = self._place_of(item, article)
        if isinstance(place, str):
            logger.warning("%s: skip claim: %s", property_name, place)
            return
        chapter, paragraph = place
        claim = {key: value for key, value in item.items() if key != "place"}
        by_property = grouped[chapter].setdefault(paragraph, {})
        by_property.setdefault(property_name, []).append(claim)

    @staticmethod
    def _place_of(
        item: object, article: MarkedArticle
    ) -> tuple[str, int] | str:
        """
        Check the place of a claim against the article.

        :param item: raw claim from the property file
        :param article: marked-up article

        :return: chapter and paragraph, or why the claim is skipped
        """
        if not isinstance(item, dict):
            return "claim is not an object"
        place = item.get("place")
        if not isinstance(place, dict):
            return "no place"
        chapter = place.get("chapter")
        if not isinstance(chapter, str) or not article.has_chapter(chapter):
            return f"unknown chapter {chapter!r}"
        paragraph = place.get("paragraph")
        # bool and float pass `in` checks: True in {1}, 3.0 in {3}.
        if type(paragraph) is not int or not article.has_paragraph(
            chapter, paragraph
        ):
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
