import logging

from ai_reviewer.article import MarkedArticle
from ai_reviewer.claims import Claim, Place

from .entities import ReportChapter, ReportParagraph

logger = logging.getLogger(__name__)

type Grouped = dict[str, dict[int, dict[str, list[Claim]]]]


class ReportBuilder:
    """Groups property claims by chapter, paragraph and property."""

    def build(
        self, article: MarkedArticle, claims: dict[str, list[Claim]]
    ) -> list[ReportChapter]:
        """
        Build the report; skip claims whose place is not in the article.

        :param article: marked-up article, chapters in document order
        :param claims: claims by property id

        :return: chapters with claims in document order; ``[]`` for no claims
        """
        grouped: Grouped = {chapter: {} for chapter in article.chapters()}
        for property_id, items in claims.items():
            for claim in items:
                reason = self._skip_reason(claim.place, article)
                if reason is not None:
                    logger.warning("%s: skip claim: %s", property_id, reason)
                    continue
                place = claim.place
                by_property = grouped[place.chapter].setdefault(
                    place.paragraph, {}
                )
                by_property.setdefault(property_id, []).append(claim)
        return self._chapters(grouped, article)

    @staticmethod
    def _skip_reason(place: Place, article: MarkedArticle) -> str | None:
        """
        Check the place of a claim against the article.

        :param place: place of the claim
        :param article: marked-up article

        :return: why the claim is skipped, or None when the place exists
        """
        chapter, paragraph = place.chapter, place.paragraph
        if not article.has_chapter(chapter):
            return f"unknown chapter {chapter!r}"
        if not article.has_paragraph(chapter, paragraph):
            return f"unknown paragraph {paragraph!r} in chapter {chapter!r}"
        return None

    @staticmethod
    def _chapters(
        grouped: Grouped, article: MarkedArticle
    ) -> list[ReportChapter]:
        """
        Turn grouped claims into chapters; drop chapters without claims.

        :param grouped: claims by chapter, paragraph and property
        :param article: marked-up article with paragraph texts

        :return: chapters in document order, paragraphs ascending,
            property ids sorted
        """
        return [
            ReportChapter(chapter, [
                ReportParagraph(
                    number,
                    article.paragraph_text(chapter, number),
                    dict(sorted(by_property.items())),
                )
                for number, by_property in sorted(paragraphs.items())
            ])
            for chapter, paragraphs in grouped.items()
            if paragraphs
        ]
