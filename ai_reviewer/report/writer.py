import json
import logging
import os
from pathlib import Path

from ai_reviewer.ai_pool import ARTICLE_FILE

from .builder import ReportBuilder
from .errors import ReportWriteError, RunDirReadError
from .outline import OutlineReader
from .property_claims import PropertyClaimsReader

logger = logging.getLogger(__name__)

REPORT_FILE = "report.json"


class ReportWriter:
    """Builds ``report.json`` of a run dir from its property files."""

    def __init__(
        self,
        outline_reader: OutlineReader | None = None,
        claims_reader: PropertyClaimsReader | None = None,
        builder: ReportBuilder | None = None,
    ) -> None:
        """
        Set up the writer.

        :param outline_reader: article outline reader; default one when omitted
        :param claims_reader: property files reader; default one when omitted
        :param builder: report builder; default one when omitted
        """
        self._outline_reader = outline_reader or OutlineReader()
        self._claims_reader = claims_reader or PropertyClaimsReader()
        self._builder = builder or ReportBuilder()

    def write(self, run_dir: Path) -> Path:
        """
        Build ``report.json`` of the run dir; replace the previous one.

        :param run_dir: run dir ``problems/<N>/`` with ``article.txt``

        :raises RunDirReadError: when the run dir or ``article.txt`` cannot
            be read
        :raises ReportWriteError: when ``report.json`` cannot be written

        :return: path of the written ``report.json``
        """
        if not run_dir.is_dir():
            raise RunDirReadError(f"run dir not found: {run_dir}")
        outline = self._outline_reader.read(run_dir / ARTICLE_FILE)
        claims = self._claims_reader.read(self._property_files(run_dir))
        report = self._builder.build(outline, claims)
        path = run_dir / REPORT_FILE
        self._save(path, report)
        return path

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
    def _save(path: Path, report: list[dict[str, object]]) -> None:
        """
        Write the report atomically through a temporary file.

        :param path: ``report.json`` path
        :param report: report content

        :raises ReportWriteError: when the report cannot be written
        """
        text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        temporary = path.with_name(path.name + ".tmp")
        try:
            temporary.write_text(text, encoding="utf-8", newline="")
            os.replace(temporary, path)
        except OSError as error:
            try:
                temporary.unlink(missing_ok=True)
            except OSError as cleanup_error:
                logger.warning("cannot remove %s: %s", temporary, cleanup_error)
            raise ReportWriteError(f"cannot write {path}: {error}") from error
