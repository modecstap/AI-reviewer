from html import escape

from .entities import Claim, ClaimType, PrintedChapter, PrintedParagraph
from .labels import ReportLabels
from .page_breaks import ParagraphPageBreaks


class ClaimPagesRenderer:
    """Renders the chapters of the printed report with their claims as HTML."""

    def render(
        self, chapters: list[PrintedChapter], labels: ReportLabels
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
        self, chapter: PrintedChapter, position: int, labels: ReportLabels
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
        self, paragraph: PrintedParagraph, block_id: str, text_end_id: str,
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
            self._claim(escape(name), ordinal, claim, labels)
            for name, items in paragraph.claims.items()
            for ordinal, claim in enumerate(items, start=1)
        )
        return (
            f'<div class="paragraph" id="{block_id}">\n'
            '<div class="paragraph-text"><p class="paragraph-caption">'
            f"{escape(labels.paragraph)} {paragraph.number}</p>"
            f'<p class="text">{escape(paragraph.text)}'
            f'<span id="{text_end_id}"></span></p></div>\n'
            f'<div class="claims">\n{claims}</div>\n'
            "</div>\n"
        )

    def _claim(
        self, property_html: str, ordinal: int, claim: Claim,
        labels: ReportLabels,
    ) -> str:
        """
        Render one claim with its heading and non-empty blocks.

        :param property_html: escaped property name
        :param ordinal: number of the claim within its property, from 1
        :param claim: claim to render
        :param labels: fixed labels in the report language

        :return: the claim article HTML
        """
        blocks = [
            f'<h4><span class="property">{property_html}</span> '
            f'<span class="ordinal">{ordinal}</span></h4>\n'
        ]
        if claim.problem is not None:
            problem = escape(claim.problem)
            blocks.append(self._labelled(
                labels.problem, f'<p class="problem">{problem}</p>'
            ))
        blocks.append(self._types(claim.types, labels))
        if claim.quote is not None:
            quote = escape(claim.quote)
            blocks.append(self._labelled(
                labels.quote, f'<blockquote class="quote">{quote}</blockquote>'
            ))
        blocks.append(self._corrections(claim.corrections, labels))
        return f'<article class="claim">\n{"".join(blocks)}</article>\n'

    def _types(self, types: list[ClaimType], labels: ReportLabels) -> str:
        """
        Render the types block of a claim.

        :param types: claim types
        :param labels: fixed labels in the report language

        :return: the labelled list HTML, or an empty string when no type has
            a number or a name
        """
        texts = [
            ". ".join(filter(None, (claim_type.number, claim_type.name)))
            for claim_type in types
        ]
        items = "".join(f"<li>{escape(text)}</li>" for text in texts if text)
        if not items:
            return ""
        return self._labelled(labels.types, f'<ul class="types">{items}</ul>')

    def _corrections(
        self, corrections: list[str], labels: ReportLabels
    ) -> str:
        """
        Render the corrections block of a claim.

        :param corrections: suggested corrections
        :param labels: fixed labels in the report language

        :return: the labelled list HTML, or an empty string without corrections
        """
        if not corrections:
            return ""
        items = "".join(
            f"<li>{escape(correction)}</li>" for correction in corrections
        )
        return self._labelled(
            labels.corrections, f'<ul class="corrections">{items}</ul>'
        )

    @staticmethod
    def _labelled(label: str, content: str) -> str:
        """
        Put a caption label before a block.

        :param label: fixed label text
        :param content: block HTML, already escaped

        :return: the label and the block HTML
        """
        return f'<p class="label">{escape(label)}</p>{content}\n'
