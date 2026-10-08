import argparse
import sys

from .article_refiner import ArticleRefiner
from .errors import RefineError


class SplitterCommandLine:
    """Command-line entry point: `python -m ai_reviewer.splitter`."""

    def __init__(self, refiner: ArticleRefiner | None = None) -> None:
        """
        Set up the command line.

        :param refiner: article refiner; default one when omitted
        """
        self._refiner = refiner or ArticleRefiner()

    def run(self, arguments: list[str] | None = None) -> int:
        """
        Refine the article named on the command line.

        :param arguments: command-line arguments; `sys.argv[1:]` when None

        :return: exit code: 0 on success, 1 on a refine failure
        """
        options = self._argument_parser().parse_args(arguments)
        try:
            article_text = self._splitter.refine(options.article)
            print(article_text)
        except RefineError as error:
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
