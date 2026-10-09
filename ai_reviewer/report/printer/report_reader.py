import json
from pathlib import Path

from ai_reviewer.ai_pool import ARTICLE_FILE

from ..errors import RunDirReadError
from ..marked_article import MarkedArticle, MarkedArticleReader
from ..writer import REPORT_FILE
from .entities import Claim, ClaimType, PrintedChapter, PrintedParagraph
from .errors import ReportFormatError


class ReportReader:
    """Reads ``report.json`` of a run dir with texts from ``article.txt``."""

    def __init__(
        self, article_reader: MarkedArticleReader | None = None
    ) -> None:
        """
        Set up the reader.

        :param article_reader: marked-up article reader; default one when
            omitted
        """
        self._article_reader = article_reader or MarkedArticleReader()

    def read(self, run_dir: Path) -> list[PrintedChapter]:
        """
        Read the report of the run dir into printer entities.

        :param run_dir: run dir ``problems/<N>/`` with ``report.json`` and
            ``article.txt``

        :raises RunDirReadError: when the run dir, ``report.json`` or
            ``article.txt`` cannot be read
        :raises ReportFormatError: when ``report.json`` is invalid JSON, has
            an unexpected shape, or names a paragraph missing from
            ``article.txt``

        :return: chapters in ``report.json`` order
        """
        if not run_dir.is_dir():
            raise RunDirReadError(f"run dir not found: {run_dir}")
        report = self._load_json(run_dir / REPORT_FILE)
        article = self._article_reader.read(run_dir / ARTICLE_FILE)
        if not isinstance(report, list):
            raise ReportFormatError(f"{REPORT_FILE}: root is not an array")
        return [self._chapter_of(entry, article) for entry in report]

    @staticmethod
    def _load_json(path: Path) -> object:
        """
        Read and parse ``report.json``.

        :param path: ``report.json`` path

        :raises RunDirReadError: when the file cannot be read
        :raises ReportFormatError: when the file is invalid JSON

        :return: parsed JSON value
        """
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise RunDirReadError(f"cannot read {path}: {error}") from error
        try:
            return json.loads(text)
        except ValueError as error:
            raise ReportFormatError(
                f"{REPORT_FILE}: invalid JSON: {error}"
            ) from error

    def _chapter_of(
        self, entry: object, article: MarkedArticle
    ) -> PrintedChapter:
        """
        Convert one chapter entry of ``report.json``.

        :param entry: raw chapter entry
        :param article: marked-up article with paragraph texts

        :raises ReportFormatError: when the entry has an unexpected shape

        :return: the chapter with its paragraphs in entry order
        """
        name = entry.get("chapter") if isinstance(entry, dict) else None
        items = entry.get("claims") if isinstance(entry, dict) else None
        if not isinstance(name, str) or not isinstance(items, list):
            raise ReportFormatError(
                f"{REPORT_FILE}: chapter entry needs a string 'chapter' "
                "and an array 'claims'"
            )
        return PrintedChapter(
            name, [self._paragraph_of(name, item, article) for item in items]
        )

    def _paragraph_of(
        self, chapter: str, entry: object, article: MarkedArticle
    ) -> PrintedParagraph:
        """
        Convert one paragraph entry of a chapter.

        :param chapter: chapter name
        :param entry: raw paragraph entry
        :param article: marked-up article with paragraph texts

        :raises ReportFormatError: when the entry has an unexpected shape or
            its paragraph is missing from ``article.txt``

        :return: the paragraph with its claims by property in entry order
        """
        place = f"{REPORT_FILE}: chapter {chapter!r}"
        number = entry.get("paragraph") if isinstance(entry, dict) else None
        if type(number) is not int:
            raise ReportFormatError(f"{place}: no integer 'paragraph'")
        text = article.paragraph_text(chapter, number)
        if text is None:
            raise ReportFormatError(
                f"{place}: paragraph {number} is missing from {ARTICLE_FILE}"
            )
        place = f"{place} paragraph {number}"
        claims = {
            name: self._claims_of(f"{place} property {name!r}", items)
            for name, items in entry.items()
            if name != "paragraph"
        }
        return PrintedParagraph(number, text, claims)

    def _claims_of(self, place: str, items: object) -> list[Claim]:
        """
        Convert the claim array of one property.

        :param place: where the array is, for the error message
        :param items: raw claim array

        :raises ReportFormatError: when it is not an array of objects

        :return: claims in array order
        """
        if not isinstance(items, list) or not all(
            isinstance(item, dict) for item in items
        ):
            raise ReportFormatError(
                f"{place}: claims are not an array of objects"
            )
        return [self._claim_of(item) for item in items]

    def _claim_of(self, item: dict[str, object]) -> Claim:
        """
        Convert one claim; drop fields that are missing or of a wrong type.

        :param item: raw claim object

        :return: the claim
        """
        types = item.get("types")
        types = types if isinstance(types, list) else []
        corrections = item.get("corrections")
        corrections = corrections if isinstance(corrections, list) else []
        return Claim(
            quote=self._text_of(item.get("quote")),
            problem=self._text_of(item.get("problem")),
            types=[
                self._type_of(entry)
                for entry in types
                if isinstance(entry, dict)
            ],
            corrections=[
                entry for entry in corrections if isinstance(entry, str)
            ],
        )

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
