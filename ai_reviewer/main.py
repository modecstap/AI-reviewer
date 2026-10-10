import argparse
import sys
from pathlib import Path

from cursor_sdk import ModelParameterValue, ModelSelection

from ai_reviewer.ai_pool import AIPool, PoolStartError
from ai_reviewer.ai_pool.cursor import CursorAgentLauncher
from ai_reviewer.article import ArticleText
from ai_reviewer.properties import PropertyCatalog, PropertyCatalogError
from ai_reviewer.report import ReportBuilder, ReportError
from ai_reviewer.report.printer import (
    RUSSIAN_LABELS,
    ReportLabels,
    ReportPrinter,
)
from ai_reviewer.run_dir import (
    PrintedReport,
    RunDirReadError,
    RunDirReader,
    RunDirs,
    RunDirWriteError,
    RunDirWriter,
)
from ai_reviewer.splitter import ArticleParser, ArticleReadError

MODEL = ModelSelection(
    id="composer-2.5",
    params=(ModelParameterValue(id="fast", value="false"),),
)
PROPERTIES_DIR = Path("properties")


class ReviewCommandLine:
    """Command-line entry point: ``python -m ai_reviewer.main``."""

    def run(self, arguments: list[str] | None = None) -> int:
        """
        Review the article named on the command line in a new run dir.

        :param arguments: command-line arguments; ``sys.argv[1:]`` when None

        :return: exit code: 0 on success, 1 on an expected failure
        """
        options = self._argument_parser().parse_args(arguments)
        try:
            run_dir = self._review(
                Path(options.article), Path(options.output_dir)
            )
        except (
            ArticleReadError,
            PropertyCatalogError,
            PoolStartError,
            ReportError,
            RunDirReadError,
            RunDirWriteError,
        ) as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        print(run_dir)
        return 0

    def _review(self, article: Path, output_dir: Path) -> Path:
        """
        Run the agents of every catalog property and print their report.

        :param article: path to the article ``.docx``
        :param output_dir: dir of numbered run dirs

        :raises ArticleReadError: when the article cannot be read
        :raises PropertyCatalogError: when the property catalog or its
            translation cannot be read
        :raises PoolStartError: when the agents cannot start
        :raises ReportError: when the report cannot be built or printed
        :raises RunDirReadError: when a run dir file cannot be read
        :raises RunDirWriteError: when a run dir file cannot be written

        :return: the new run dir
        """
        catalog = PropertyCatalog(PROPERTIES_DIR)
        # Read the translation before the agents run: a broken one fails fast.
        labels = RUSSIAN_LABELS.with_names(
            catalog.names(RUSSIAN_LABELS.language)
        )
        text = ArticleText().write(ArticleParser().parse(article))
        run_dir = self._run_agents(catalog, text, output_dir)
        self._write_report(run_dir)
        self._print_report(run_dir, labels)
        return run_dir

    @staticmethod
    def _run_agents(
        catalog: PropertyCatalog, text: str, output_dir: Path
    ) -> Path:
        """
        Run the agent of every catalog property on the article.

        :param catalog: property catalog
        :param text: marked-up article text
        :param output_dir: dir of numbered run dirs

        :raises PropertyCatalogError: when the catalog cannot be read
        :raises PoolStartError: when the agents cannot start

        :return: the new run dir
        """
        pool = AIPool(CursorAgentLauncher(MODEL), RunDirs())
        for definition in catalog.agents():
            pool.add_agent(definition)
        return pool.execute(text, output_dir).run_dir

    @staticmethod
    def _write_report(run_dir: Path) -> None:
        """
        Build ``report.json`` from the property files of the run dir.

        :param run_dir: run dir ``<output_dir>/<N>/``

        :raises RunDirReadError: when the run dir cannot be read
        :raises RunDirWriteError: when ``report.json`` cannot be written
        """
        reader = RunDirReader()
        chapters = ReportBuilder().build(
            reader.read_article(run_dir), reader.read_claims(run_dir)
        )
        RunDirWriter().write_report(run_dir, chapters)

    @staticmethod
    def _print_report(run_dir: Path, labels: ReportLabels) -> None:
        """
        Print ``report.json`` of the run dir as HTML, CSS and PDF files.

        :param run_dir: run dir ``<output_dir>/<N>/``
        :param labels: labels of the report language with catalog names

        :raises RunDirReadError: when the run dir files cannot be read
        :raises ReportError: when the report is invalid or cannot be printed
        :raises RunDirWriteError: when a printed file cannot be written
        """
        chapters = RunDirReader().read_report(run_dir)
        printer = ReportPrinter()
        html = printer.html(chapters, labels)
        css = printer.css()
        printed = PrintedReport(html, css, printer.pdf(html, css))
        RunDirWriter().write_printed(run_dir, printed)

    @staticmethod
    def _argument_parser() -> argparse.ArgumentParser:
        """
        Describe the command-line arguments.

        :return: argument parser
        """
        parser = argparse.ArgumentParser(
            prog="python -m ai_reviewer.main",
            description="Review an article .docx against every property "
                        "of ./properties in a new run dir.",
        )
        parser.add_argument("article", help="path to the article .docx")
        parser.add_argument(
            "output_dir", help="dir of numbered run dirs <output_dir>/<N>/"
        )
        return parser


if __name__ == "__main__":
    sys.exit(ReviewCommandLine().run())
