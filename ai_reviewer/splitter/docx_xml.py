import re
from collections.abc import Iterator

from docx.oxml.ns import qn
from lxml.etree import _Element as XmlElement


class DocxXml:
    """Queries over the raw WordprocessingML tree of a document body."""

    MATH = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
    COMPATIBILITY = (
        "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
    )
    PARAGRAPH, TABLE, ROW, CELL = (
        qn(f"w:{tag}") for tag in ("p", "tbl", "tr", "tc")
    )
    RUN, TEXT = qn("w:r"), qn("w:t")
    CONTENT_CONTROL, CONTENT_CONTROL_BODY = qn("w:sdt"), qn("w:sdtContent")
    PARAGRAPH_PROPERTIES = qn("w:pPr")
    # Never descended into while collecting paragraph text or runs.
    SKIPPED = frozenset({
        PARAGRAPH_PROPERTIES, qn("w:rPr"), qn("w:sdtPr"), qn("w:del"),
        qn("w:moveFrom"), qn("w:txbxContent"),
        MATH + "oMath", MATH + "oMathPara", COMPATIBILITY + "Fallback",
    })
    SPECIAL_CHARACTERS = {
        qn("w:tab"): "\t", qn("w:br"): "\n", qn("w:cr"): "\n",
        qn("w:noBreakHyphen"): "-",
    }

    @classmethod
    def children(cls, element: XmlElement) -> Iterator[XmlElement]:
        """
        Yield child elements, unwrapping content controls (`w:sdt`).

        :param element: parent element

        :return: child elements in document order
        """
        for child in element:
            if child.tag != cls.CONTENT_CONTROL:
                yield child
                continue
            body = child.find(cls.CONTENT_CONTROL_BODY)
            if body is not None:
                yield from cls.children(body)

    @classmethod
    def descendants(cls, element: XmlElement) -> Iterator[XmlElement]:
        """
        Yield descendants in document order, skipping `SKIPPED` subtrees.

        :param element: root element, not yielded itself

        :return: descendant elements in document order
        """
        for child in element:
            if not isinstance(child.tag, str) or child.tag in cls.SKIPPED:
                continue
            yield child
            yield from cls.descendants(child)

    @classmethod
    def paragraph_text(cls, paragraph: XmlElement) -> str:
        """
        Collect the visible text of a paragraph, tabs and breaks included.

        :param paragraph: `w:p` element

        :return: raw paragraph text
        """
        parts = []
        for element in cls.descendants(paragraph):
            if element.tag == cls.TEXT:
                parts.append(element.text or "")
            elif element.tag in cls.SPECIAL_CHARACTERS:
                parts.append(cls.SPECIAL_CHARACTERS[element.tag])
        return "".join(parts)

    @classmethod
    def table_text(cls, table: XmlElement) -> str:
        """
        Render a table as text: cells joined by tabs, rows by newlines.

        :param table: `w:tbl` element

        :return: table text
        """
        rows = (
            "\t".join(" ".join(cls._cell_paragraphs(cell)) for cell in row)
            for row in cls._rows(table)
        )
        return "\n".join(rows)

    @classmethod
    def text_runs(cls, paragraph: XmlElement) -> list[XmlElement]:
        """
        Find the runs of a paragraph that hold non-blank text.

        :param paragraph: `w:p` element

        :return: `w:r` elements in document order
        """
        return [
            element for element in cls.descendants(paragraph)
            if element.tag == cls.RUN and cls._run_text(element).strip()
        ]

    @classmethod
    def _run_text(cls, run: XmlElement) -> str:
        """
        Collect the text of a run.

        :param run: `w:r` element

        :return: run text
        """
        return "".join(text.text or "" for text in run.iterchildren(cls.TEXT))

    @classmethod
    def _rows(cls, table: XmlElement) -> Iterator[list[XmlElement]]:
        """
        Yield the cells of each table row.

        :param table: `w:tbl` element

        :return: `w:tc` elements of each row
        """
        for row in cls.children(table):
            if row.tag == cls.ROW:
                yield [
                    cell for cell in cls.children(row) if cell.tag == cls.CELL
                ]

    @classmethod
    def _cell_paragraphs(cls, container: XmlElement) -> Iterator[str]:
        """
        Yield the non-empty single-line paragraphs of a cell, nested included.

        :param container: `w:tc` element

        :return: paragraph texts with tabs and breaks replaced by spaces
        """
        for element in cls.children(container):
            if element.tag == cls.PARAGRAPH:
                text = re.sub(r"[\t\n]", " ", cls.paragraph_text(element))
                if text.strip():
                    yield text.strip()
            elif element.tag == cls.TABLE:
                for row in cls._rows(element):
                    for cell in row:
                        yield from cls._cell_paragraphs(cell)
