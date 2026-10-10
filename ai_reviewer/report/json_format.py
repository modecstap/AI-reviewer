import json

from ai_reviewer.article import MarkedArticle
from ai_reviewer.claims import Claim, Place

from .entities import ReportChapter, ReportParagraph
from .errors import ReportFormatError


class ReportJson:
    """
    Writes and reads the ``report.json`` format.

    The root is an array of ``{"chapter": <id>, "claims": [...]}`` entries.
    Each claims entry is ``{"paragraph": <N>, <property id>: [<claim>, ...]}``
    where a claim is the source claim object without ``place``.
    """

    def write(self, chapters: list[ReportChapter]) -> str:
        """
        Render the report as ``report.json`` text.

        :param chapters: chapters of the report

        :return: indented JSON with non-ASCII kept, ending with a newline
        """
        report = [
            {"chapter": chapter.name, "claims": [
                {"paragraph": paragraph.number, **{
                    property_id: [claim.fields for claim in claims]
                    for property_id, claims in paragraph.claims.items()
                }}
                for paragraph in chapter.paragraphs
            ]}
            for chapter in chapters
        ]
        return json.dumps(report, ensure_ascii=False, indent=2) + "\n"

    def read(self, text: str, article: MarkedArticle) -> list[ReportChapter]:
        """
        Parse ``report.json`` text with paragraph texts from the article.

        :param text: ``report.json`` content
        :param article: marked-up article with paragraph texts

        :raises ReportFormatError: when the text is invalid JSON, has an
            unexpected shape, or names a paragraph missing from the article

        :return: chapters in ``report.json`` order
        """
        try:
            report = json.loads(text)
        except ValueError as error:
            raise ReportFormatError(f"invalid JSON: {error}") from error
        if not isinstance(report, list):
            raise ReportFormatError("root is not an array")
        return [self._chapter_of(entry, article) for entry in report]

    def _chapter_of(
        self, entry: object, article: MarkedArticle
    ) -> ReportChapter:
        """
        Convert one chapter entry.

        :param entry: raw chapter entry
        :param article: marked-up article with paragraph texts

        :raises ReportFormatError: when the entry has an unexpected shape

        :return: the chapter with its paragraphs in entry order
        """
        name = entry.get("chapter") if isinstance(entry, dict) else None
        items = entry.get("claims") if isinstance(entry, dict) else None
        if not isinstance(name, str) or not isinstance(items, list):
            raise ReportFormatError(
                "chapter entry needs a string 'chapter' and an array 'claims'"
            )
        return ReportChapter(
            name, [self._paragraph_of(name, item, article) for item in items]
        )

    def _paragraph_of(
        self, chapter: str, entry: object, article: MarkedArticle
    ) -> ReportParagraph:
        """
        Convert one paragraph entry of a chapter.

        :param chapter: chapter id
        :param entry: raw paragraph entry
        :param article: marked-up article with paragraph texts

        :raises ReportFormatError: when the entry has an unexpected shape or
            its paragraph is missing from the article

        :return: the paragraph with its claims by property in entry order
        """
        location = f"chapter {chapter!r}"
        number = entry.get("paragraph") if isinstance(entry, dict) else None
        if type(number) is not int:
            raise ReportFormatError(f"{location}: no integer 'paragraph'")
        text = article.paragraph_text(chapter, number)
        if text is None:
            raise ReportFormatError(
                f"{location}: paragraph {number} is missing from the article"
            )
        place = Place(chapter, number)
        claims = {
            property_id: self._claims_of(place, property_id, items)
            for property_id, items in entry.items()
            if property_id != "paragraph"
        }
        return ReportParagraph(number, text, claims)

    @staticmethod
    def _claims_of(
        place: Place, property_id: str, items: object
    ) -> list[Claim]:
        """
        Convert the claim array of one property.

        :param place: paragraph the claims belong to
        :param property_id: property of the claims, for the error message
        :param items: raw claim array

        :raises ReportFormatError: when it is not an array of objects

        :return: claims in array order
        """
        if not isinstance(items, list) or not all(
            isinstance(item, dict) for item in items
        ):
            raise ReportFormatError(
                f"chapter {place.chapter!r} paragraph {place.paragraph} "
                f"property {property_id!r}: claims are not an array of objects"
            )
        return [Claim(place, item) for item in items]
