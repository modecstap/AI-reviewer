import logging
from pathlib import Path

from ai_reviewer.article import ArticleText, MarkedArticle
from ai_reviewer.claims import Claim, ClaimsFormatError, ClaimsParser
from ai_reviewer.report import ReportChapter, ReportFormatError, ReportJson

from .errors import RunDirReadError
from .files import ARTICLE_FILE, REPORT_FILE

logger = logging.getLogger(__name__)


class RunDirReader:
    """Reads the article, the property claims and the report of a run dir."""

    def __init__(
        self,
        article_text: ArticleText | None = None,
        claims_parser: ClaimsParser | None = None,
        report_json: ReportJson | None = None,
    ) -> None:
        """
        Set up the reader.

        :param article_text: article text format; default one when omitted
        :param claims_parser: property file parser; default one when omitted
        :param report_json: ``report.json`` format; default one when omitted
        """
        self._article_text = article_text or ArticleText()
        self._claims_parser = claims_parser or ClaimsParser()
        self._report_json = report_json or ReportJson()

    def read_article(self, run_dir: Path) -> MarkedArticle:
        """
        Read ``article.txt`` of the run dir.

        :param run_dir: run dir ``<output_dir>/<N>/``

        :raises RunDirReadError: when the run dir or ``article.txt`` cannot
            be read

        :return: the article with paragraph texts, chapters in document order
        """
        if not run_dir.is_dir():
            raise RunDirReadError(f"run dir not found: {run_dir}")
        text = self._read(run_dir / ARTICLE_FILE)
        return self._article_text.read(text)

    def read_claims(self, run_dir: Path) -> dict[str, list[Claim]]:
        """
        Read the claims of every property file; skip broken files.

        A broken file only loses its own claims, not the whole report.

        :param run_dir: run dir ``<output_dir>/<N>/``

        :raises RunDirReadError: when the run dir cannot be listed

        :return: claims by property id, files sorted by path
        """
        claims: dict[str, list[Claim]] = {}
        for path in self._property_files(run_dir):
            try:
                text = path.read_text(encoding="utf-8")
                claims[path.stem] = self._claims_parser.parse(text, path.stem)
            except (OSError, UnicodeDecodeError, ClaimsFormatError) as error:
                logger.warning("skip property file %s: %s", path.name, error)
        return claims

    def read_report(self, run_dir: Path) -> list[ReportChapter]:
        """
        Read ``report.json`` of the run dir with texts from ``article.txt``.

        :param run_dir: run dir ``<output_dir>/<N>/``

        :raises RunDirReadError: when the run dir, ``article.txt`` or
            ``report.json`` cannot be read
        :raises ReportFormatError: when ``report.json`` is invalid or names a
            paragraph missing from ``article.txt``

        :return: chapters in ``report.json`` order
        """
        article = self.read_article(run_dir)
        path = run_dir / REPORT_FILE
        text = self._read(path)
        try:
            return self._report_json.read(text, article)
        except ReportFormatError as error:
            raise ReportFormatError(f"{path}: {error}") from error

    @staticmethod
    def _property_files(run_dir: Path) -> list[Path]:
        """
        List the property files of the run dir, ``report.json`` excluded.

        :param run_dir: run dir to list

        :raises RunDirReadError: when the run dir cannot be listed

        :return: property files sorted by path
        """
        # Exact suffix match: glob("*.json") is case-insensitive on Windows.
        try:
            return sorted(
                path
                for path in run_dir.iterdir()
                if path.is_file()
                and path.suffix == ".json"
                and path.name != REPORT_FILE
            )
        except OSError as error:
            raise RunDirReadError(f"cannot list {run_dir}: {error}") from error

    @staticmethod
    def _read(path: Path) -> str:
        """
        Read a run dir text file.

        :param path: file to read

        :raises RunDirReadError: when the file cannot be read as UTF-8

        :return: the file text
        """
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise RunDirReadError(f"cannot read {path}: {error}") from error
