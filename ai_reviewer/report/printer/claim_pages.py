from html import escape

from ai_reviewer.claims import Claim, ClaimType

from .. import ReportChapter, ReportParagraph
from .labels import ReportLabels
from .pdf import ParagraphPageBreaks


class ClaimPagesRenderer:
    """Renders the chapters of the printed report with their claims as HTML."""

    def render(
        self, chapters: list[ReportChapter], labels: ReportLabels
    ) -> str:
        """
        Render one section per chapter, in the given order.

        :param chapters: chapters of the report
        :param labels: fixed labels in the report language

        :return: the ``<section class="chapter">`` HTML of every chapter
        """
        return "".join(
            self._chapter(chapter, position, labels)
            for position, chapter in enumerate(chapters, start=1)
        )

    def _chapter(
        self, chapter: ReportChapter, position: int, labels: ReportLabels
    ) -> str:
        """
        Render one chapter with its paragraphs.

        :param chapter: chapter to render
        :param position: position of the chapter in the report, from 1
        :param labels: fixed labels in the report language

        :return: the chapter section HTML
        """
        paragraphs = "".join(
            self._paragraph(
                paragraph,
                ParagraphPageBreaks.block_id(position, index),
                ParagraphPageBreaks.text_end_id(position, index),
                labels,
            )
            for index, paragraph in enumerate(chapter.paragraphs, start=1)
        )
        return (
            '<section class="chapter">\n'
            f'<p class="chapter-caption">{escape(labels.chapter)}</p>\n'
            f"<h2>{escape(chapter.name)}</h2>\n"
            f"{paragraphs}"
            "</section>\n"
        )

    def _paragraph(
        self, paragraph: ReportParagraph, block_id: str, text_end_id: str,
        labels: ReportLabels,
    ) -> str:
        """
        Render one paragraph: its text on the left, its claims on the right.

        :param paragraph: paragraph to render
        :param block_id: id of the paragraph block
        :param text_end_id: id of the empty marker at the end of the text
        :param labels: fixed labels in the report language

        :return: the paragraph block HTML
        """
        claims = "".join(
            self._claim(name, ordinal, claim, labels)
            for name, items in paragraph.claims.items()
            for ordinal, claim in enumerate(items, start=1)
        )
        return (
            f'<div class="paragraph" id="{block_id}">\n'
            '<div class="paragraph-text"><p class="paragraph-caption">'
            f"{escape(labels.paragraph)} {paragraph.number}</p>"
            f'<p class="text">{self._highlighted_text(paragraph)}'
            f'<span id="{text_end_id}"></span></p></div>\n'
            f'<div class="claims">\n{claims}</div>\n'
            "</div>\n"
        )

    def _highlighted_text(self, paragraph: ReportParagraph) -> str:
        """
        Escape the paragraph text and mark the quotes of its claims.

        :param paragraph: paragraph to render

        :return: the escaped text with ``<mark>`` around every found quote
        """
        text = paragraph.text
        parts: list[str] = []
        position = 0
        for start, end in self._quote_ranges(paragraph):
            parts.append(escape(text[position:start]))
            parts.append(f"<mark>{escape(text[start:end])}</mark>")
            position = end
        parts.append(escape(text[position:]))
        return "".join(parts)

    @staticmethod
    def _quote_ranges(paragraph: ReportParagraph) -> list[tuple[int, int]]:
        """
        Find the first occurrence of every claim quote in the paragraph text.

        :param paragraph: paragraph whose claim quotes to find

        :return: disjoint ``(start, end)`` ranges in ascending order; quotes
            not found in the text are skipped, overlapping ranges are merged
        """
        found: list[tuple[int, int]] = []
        for claims in paragraph.claims.values():
            for claim in claims:
                quote = claim.quote or ""
                start = paragraph.text.find(quote) if quote else -1
                if start >= 0:
                    found.append((start, start + len(quote)))
        ranges: list[tuple[int, int]] = []
        for start, end in sorted(found):
            if ranges and start <= ranges[-1][1]:
                ranges[-1] = (ranges[-1][0], max(ranges[-1][1], end))
            else:
                ranges.append((start, end))
        return ranges

    def _claim(
        self, property_id: str, ordinal: int, claim: Claim,
        labels: ReportLabels,
    ) -> str:
        """
        Render one claim with its heading and non-empty blocks.

        :param property_id: property id as in ``report.json``
        :param ordinal: number of the claim within its property, from 1
        :param claim: claim to render
        :param labels: fixed labels in the report language

        :return: the claim article HTML
        """
        heading = escape(labels.property_name(property_id))
        blocks = [
            f'<h4><span class="property">{heading}</span> '
            f'<span class="ordinal">{ordinal}</span></h4>\n'
        ]
        if claim.problem is not None:
            problem = escape(claim.problem)
            blocks.append(self._labelled(
                labels.problem, f'<p class="problem">{problem}</p>'
            ))
        blocks.append(self._types(property_id, claim.types, labels))
        if claim.quote is not None:
            quote = escape(claim.quote)
            blocks.append(self._labelled(
                labels.quote, f'<blockquote class="quote">{quote}</blockquote>'
            ))
        return f'<article class="claim">\n{"".join(blocks)}</article>\n'

    def _types(
        self, property_id: str, types: list[ClaimType],
        labels: ReportLabels,
    ) -> str:
        """
        Render the types block of a claim.

        :param property_id: property id as in ``report.json``
        :param types: claim types
        :param labels: fixed labels in the report language

        :return: the labelled list HTML, or an empty string when no type has
            a number or a name
        """
        texts = [
            labels.type_caption(property_id, claim_type)
            for claim_type in types
        ]
        items = "".join(f"<li>{escape(text)}</li>" for text in texts if text)
        if not items:
            return ""
        return self._labelled(labels.types, f'<ul class="types">{items}</ul>')

    @staticmethod
    def _labelled(label: str, content: str) -> str:
        """
        Put a caption label before a block.

        :param label: fixed label text
        :param content: block HTML, already escaped

        :return: the label and the block HTML
        """
        return f'<p class="label">{escape(label)}</p>{content}\n'
