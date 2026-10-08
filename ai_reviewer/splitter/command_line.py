import argparse
import sys

from .article_splitter import ArticleSplitter
from .errors import SplitError


class SplitterCommandLine:
    """Command-line entry point: `python -m ai_reviewer.splitter`."""

    def __init__(self, splitter: ArticleSplitter | None = None) -> None:
        """
        Set up the command line.

        :param splitter: article splitter; default one when omitted
        """
        self._splitter = splitter or ArticleSplitter()

    def run(self, arguments: list[str] | None = None) -> int:
        """
        Split the article named on the command line.

        :param arguments: command-line arguments; `sys.argv[1:]` when None

        :return: exit code: 0 on success, 1 on a split failure
        """
        options = self._argument_parser().parse_args(arguments)
        try:
            self._splitter.split(options.article, options.out_dir)
        except SplitError as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        return 0

    @staticmethod
    def _argument_parser() -> argparse.ArgumentParser:
        """
        Describe the command-line arguments.

        :return: argument parser
        """
        parser = argparse.ArgumentParser(
            prog="python -m ai_reviewer.splitter",
            description="Split an article .docx into chapter folders "
                        "with numbered paragraph files.",
        )
        parser.add_argument("article", help="path to the article .docx")
        parser.add_argument(
            "out_dir", help="output folder; deleted and recreated"
        )
        return parser
