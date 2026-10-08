import re
from collections.abc import Iterator

from docx.oxml.ns import qn
from docx.styles.style import CharacterStyle
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from lxml.etree import _Element as XmlElement

from .docx_xml import DocxXml


class HeadingDetector:
    """Decides whether a paragraph is a chapter heading."""

    STYLE_NAME = re.compile(r"heading [1-9]|title|заголовок [1-9]|название")
    SECTION_NUMBER = re.compile(r"\d+\.(\d+\.?)*\s")
    MAX_HEURISTIC_LENGTH = 200
    MAX_OUTLINE_LEVEL = 8

    def is_style_heading(self, paragraph: Paragraph) -> bool:
        """
        Check whether the paragraph style or outline level marks a heading.

        :param paragraph: paragraph to check

        :return: True for a heading
        """
        style = paragraph.style
        name = (style.name or "").lower() if style is not None else ""
        if self.STYLE_NAME.fullmatch(name):
            return True
        level = self._outline_level(paragraph, style)
        return level is not None and 0 <= level <= self.MAX_OUTLINE_LEVEL

    def is_heuristic_heading(self, paragraph: Paragraph, title: str) -> bool:
        """
        Guess a heading from its look when the document uses no heading styles.

        :param paragraph: paragraph to check
        :param title: whitespace-normalized non-empty paragraph text

        :return: True for a short line that is upper-case, numbered or bold
        """
        too_long = len(title) > self.MAX_HEURISTIC_LENGTH
        if too_long or title[-1] in ".:;,":
            return False
        if title.upper() == title and title.lower() != title:
            return True
        if self.SECTION_NUMBER.match(title):
            return True
        runs = [
            Run(element, paragraph)
            for element in DocxXml.text_runs(paragraph._p)
        ]
        return bool(runs) and all(self._is_bold(run, paragraph) for run in runs)

    def _outline_level(
        self, paragraph: Paragraph, style: CharacterStyle | None
    ) -> int | None:
        """
        Find the outline level set on the paragraph or inherited from its style.

        :param paragraph: paragraph to check
        :param style: paragraph style

        :return: outline level, or None when unset or malformed
        """
        tag = DocxXml.PARAGRAPH_PROPERTIES
        candidates = (
            paragraph._p.find(tag),
            *(each.element.find(tag) for each in self._style_chain(style)),
        )
        for properties in candidates:
            if properties is None:
                continue
            level = properties.find(qn("w:outlineLvl"))
            if level is not None:
                return self._parse_level(level)
        return None

    @staticmethod
    def _parse_level(level: XmlElement) -> int | None:
        """
        Read the value of a `w:outlineLvl` element.

        :param level: `w:outlineLvl` element

        :return: outline level, or None when malformed
        """
        try:
            return int(level.get(qn("w:val")))
        # A malformed level in one paragraph must not abort the whole split.
        except (TypeError, ValueError):
            return None

    def _is_bold(self, run: Run, paragraph: Paragraph) -> bool:
        """
        Resolve run boldness through direct, run style and paragraph style.

        :param run: run to check
        :param paragraph: paragraph holding the run

        :return: True when the run renders bold
        """
        if run.bold is not None:
            return run.bold
        styles = (
            *self._style_chain(run.style),
            *self._style_chain(paragraph.style),
        )
        for style in styles:
            if style.font.bold is not None:
                return style.font.bold
        return False

    @staticmethod
    def _style_chain(style: CharacterStyle | None) -> Iterator[CharacterStyle]:
        """
        Yield the style and its base styles, stopping at a cycle.

        :param style: starting style

        :return: styles from the most to the least specific
        """
        seen = set()
        while style is not None and style.style_id not in seen:
            seen.add(style.style_id)
            yield style
            style = style.base_style
