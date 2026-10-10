from pathlib import Path

from ai_reviewer.report import ReportChapter, ReportJson

from .atomic_file import AtomicFile
from .files import CSS_FILE, HTML_FILE, PDF_FILE, REPORT_FILE
from .printed_report import PrintedReport


class RunDirWriter:
    """Writes ``report.json`` and the printed report into a run dir."""

    def __init__(
        self,
        atomic_file: AtomicFile | None = None,
        report_json: ReportJson | None = None,
    ) -> None:
        """
        Set up the writer.

        :param atomic_file: atomic file writer; default one when omitted
        :param report_json: ``report.json`` format; default one when omitted
        """
        self._atomic_file = atomic_file or AtomicFile()
        self._report_json = report_json or ReportJson()

    def write_report(self, run_dir: Path, chapters: list[ReportChapter]) -> Path:
        """
        Write ``report.json`` of the run dir; replace the previous one.

        :param run_dir: run dir ``<output_dir>/<N>/``
        :param chapters: chapters of the report

        :raises RunDirWriteError: when ``report.json`` cannot be written

        :return: path of the written ``report.json``
        """
        path = run_dir / REPORT_FILE
        self._atomic_file.write(path, self._report_json.write(chapters))
        return path

    def write_printed(self, run_dir: Path, printed: PrintedReport) -> None:
        """
        Write the printed report files; replace the previous ones.

        :param run_dir: run dir ``<output_dir>/<N>/``
        :param printed: printed report

        :raises RunDirWriteError: when a file cannot be written
        """
        self._atomic_file.write(run_dir / HTML_FILE, printed.html)
        self._atomic_file.write(run_dir / CSS_FILE, printed.css)
        self._atomic_file.write(run_dir / PDF_FILE, printed.pdf)
