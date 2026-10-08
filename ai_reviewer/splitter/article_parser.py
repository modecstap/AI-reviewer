import zipfile
from dataclasses import replace
from pathlib import Path

import docx
from docx.document import Document as WordDocument
from docx.opc.exceptions import PackageNotFoundError
from docx.text.paragraph import Paragraph
from lxml.etree import _Element as XmlElement

from .block import Block
from .chapter import NO_HEADING, Chapter
from .chapter_namer import ChapterNamer
from .docx_xml import DocxXml
from .errors import ArticleNotFoundError, ArticleReadError, InvalidArticleError
from .heading_detector import HeadingDetector


class ArticleParser:
    """Reads an article .docx and splits its body into chapters."""

    INVALID_PACKAGE_ERRORS = (
        PackageNotFoundError, ValueError, KeyError, zipfile.BadZipFile
    )

    def __init__(
        self,
        detector: HeadingDetector | None = None,
        namer: ChapterNamer | None = None,
    ) -> None:
        """
        Set up the parser.

        :param detector: heading detector; default one when omitted
        :param namer: folder namer; default one when omitted
        """
        self._detector = detector or HeadingDetector()
        self._namer = namer or ChapterNamer()

    def parse(self, docx_path: str | Path) -> list[Chapter]:
        """
        Read the article and return its chapters; touches no files.

        :param docx_path: path to the article .docx

        :raises ArticleNotFoundError:
        :raises InvalidArticleError:
        :raises ArticleReadError:

        :return: chapters in document order with unique folder names
        """
        document = self._open(Path(docx_path))
        chapters = self._group(self._blocks(document))
        names = self._namer.unique_names([each.name for each in chapters])
        return [
            replace(chapter, name=name)
            for chapter, name in zip(chapters, names)
        ]

    @classmethod
    def _open(cls, path: Path) -> WordDocument:
        """
        Load the .docx package.

        :param path: path to the article .docx

        :raises ArticleNotFoundError:
        :raises InvalidArticleError:
        :raises ArticleReadError: on an I/O failure while reading

        :return: loaded document
        """
        if not path.is_file():
            raise ArticleNotFoundError(f"article file not found: {path}")
        try:
            return docx.Document(str(path))
        except cls.INVALID_PACKAGE_ERRORS as error:
            message = f"article is not a valid .docx file: {path}"
            raise InvalidArticleError(message) from error
        except OSError as error:
            message = f"cannot read article {path}: {error}"
            raise ArticleReadError(message) from error

    def _blocks(self, document: WordDocument) -> list[Block]:
        """
        Collect the non-empty top-level paragraphs and tables of the body.

        :param document: loaded document

        :return: blocks in document order
        """
        blocks = []
        for element in DocxXml.children(document.element.body):
            block = self._block(element, document)
            if block is not None:
                blocks.append(block)
        return blocks

    def _block(
        self, element: XmlElement, document: WordDocument
    ) -> Block | None:
        """
        Turn a top-level body element into a block.

        :param element: child of `w:body`
        :param document: document owning the element

        :return: block, or None for empty or non-content elements
        """
        if element.tag == DocxXml.PARAGRAPH:
            return self._paragraph_block(element, document)
        if element.tag == DocxXml.TABLE:
            text = DocxXml.table_text(element)
            return Block(text) if text.strip() else None
        return None

    def _paragraph_block(
        self, element: XmlElement, document: WordDocument
    ) -> Block | None:
        """
        Turn a paragraph into a block with both heading verdicts.

        :param element: `w:p` element
        :param document: document owning the element

        :return: block, or None for a blank paragraph
        """
        text = DocxXml.paragraph_text(element).strip()
        if not text:
            return None
        paragraph = Paragraph(element, document.part)
        title = self._normalize(text)
        return Block(
            text=text,
            is_style_heading=self._detector.is_style_heading(paragraph),
            is_heuristic_heading=self._detector.is_heuristic_heading(
                paragraph, title
            ),
        )

    def _group(self, blocks: list[Block]) -> list[Chapter]:
        """
        Group blocks into chapters, each heading opening a new one.

        Heuristics apply only when no paragraph has a heading style,
        because styled documents mark their real headings explicitly.

        :param blocks: blocks in document order

        :return: chapters, names not yet unique
        """
        by_style = any(block.is_style_heading for block in blocks)
        chapters: list[Chapter] = []
        for block in blocks:
            if (block.is_style_heading if by_style
                    else block.is_heuristic_heading):
                chapters.append(self._chapter(self._normalize(block.text)))
                continue
            if not chapters:
                chapters.append(Chapter(name=NO_HEADING, title=None))
            chapters[-1].paragraphs.append(block.text)
        return chapters

    def _chapter(self, title: str) -> Chapter:
        """
        Create an empty chapter for a heading.

        :param title: whitespace-normalized heading text

        :return: chapter without paragraphs
        """
        return Chapter(name=self._namer.folder_name(title), title=title)

    @staticmethod
    def _normalize(text: str) -> str:
        """
        Collapse every whitespace run into a single space.

        :param text: text to normalize

        :return: normalized text
        """
        return " ".join(text.split())
