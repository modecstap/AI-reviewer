import json
import re
from datetime import date
from html import escape

import pytest

from ai_reviewer.printed_report_writer import PrintedReportWriter
from ai_reviewer.report import (
    ENGLISH_LABELS,
    ReportError,
    ReportFormatError,
    ReportPrinter,
    RunDirReadError,
)
from ai_reviewer.report.printer.claim_pages import ClaimPagesRenderer
from ai_reviewer.report.printer.entities import Claim, ClaimType, PrintedChapter, PrintedParagraph
from ai_reviewer.report.printer.labels import RUSSIAN_LABELS
from ai_reviewer.report.printer.page_breaks import ParagraphPageBreaks
from ai_reviewer.report.printer.pdf import PdfRenderer
from ai_reviewer.report.printer.printer import STYLESHEET
from ai_reviewer.report.printer.title_page import TitlePageRenderer
from ai_reviewer.splitter import NO_HEADING, ArticleWriter, Chapter

printer = ReportPrinter(title_page=TitlePageRenderer(today=lambda: date(2026, 10, 9)))

FULL = {"quote": "c1 quote", "problem": "c1 problem", "types": [{"number": 1, "name": "Hedging"}], "extra": ["fix c1"]}
SAMPLE_REPORT = [{"chapter": "Введение", "claims": [
    {"paragraph": 1},
    {"paragraph": 3,
     "Caution": [FULL, {"quote": "c2 quote", "problem": "c2 problem"}],
     "Structure": [{"quote": "s1 <i>", "problem": "s1 & problem", "types": [{"name": "Order"}]}]},
]}]


def make_run_dir(tmp_path, chapters, report):
    run_dir = tmp_path / "1"
    run_dir.mkdir()
    article = ArticleWriter().write([Chapter(name, name, paragraphs) for name, paragraphs in chapters])
    (run_dir / "article.txt").write_text(article, encoding="utf-8", newline="")
    (run_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    return run_dir


def make_sample_run_dir(tmp_path):
    chapters = [(NO_HEADING, ["n"]), ("Введение", ["p1 <b> & x\nline2", "p2", "p3"]), ("Пусто", ["e"])]
    return make_run_dir(tmp_path, chapters, SAMPLE_REPORT)


def test_content_order_and_escaping(tmp_path):
    html = printer.html(make_sample_run_dir(tmp_path))

    assert "&lt;b&gt; &amp; x\nline2" in html and "<b>" not in html
    assert "s1 &lt;i&gt;" in html and "s1 &amp; problem" in html
    assert all(absent not in html for absent in ["p2", "Пусто", NO_HEADING])
    assert html.index("c1 quote") < html.index("c2 quote") < html.index("s1 &lt;i&gt;")
    assert re.findall(r'class="ordinal">(\d+)<', html) == ["1", "2", "1"]
    assert '<span class="property">Осторожность выводов</span> <span class="count">2</span>' in html
    assert '<span class="property">Структура</span> <span class="count">1</span>' in html
    assert "Caution" not in html and "Structure" not in html and "Претензии по свойствам" not in html
    assert "<strong>3</strong>" in html
    assert "09.10.2026" in html and "Проблема" in html
    assert "<li>1. Гипотеза подана как установленный факт</li>" in html and "<li>Order</li>" in html
    assert html.count("Типы") == 2 and "Корректировки" not in html and "fix c1" not in html


def test_english_labels_keep_data(tmp_path):
    html = printer.html(make_sample_run_dir(tmp_path), ENGLISH_LABELS)

    assert 'lang="en"' in html and "October 9, 2026" in html and "Problem" in html
    assert "Проблема" not in html and "Claims by property" not in html
    assert "Введение" in html and "&lt;b&gt;" in html and "c1 problem" in html
    assert '<span class="property">Caution</span>' in html and "<li>1. Hedging</li>" in html


def render_paragraph(text, claims, labels=RUSSIAN_LABELS):
    return ClaimPagesRenderer().render([PrintedChapter("A", [PrintedParagraph(1, text, claims)])], labels)


@pytest.mark.parametrize("labels, expected", [
    (RUSSIAN_LABELS, ["<li>2. Нарушение управления</li>", "<li>99. Odd</li>", "<li>Bare</li>",
                      'class="property">Грамотность<', 'class="property">Unknown<']),
    (ENGLISH_LABELS, ["<li>2. Incorrect government</li>", 'class="property">Literacy<']),
])
def test_names_fallback(labels, expected):
    types = [ClaimType("2", "Incorrect government"), ClaimType("99", "Odd"), ClaimType(None, "Bare")]
    claims = {"Literacy": [Claim(None, None, types)], "Unknown": [Claim(None, None)]}

    html = render_paragraph("t", claims, labels)

    assert all(part in html for part in expected)


def test_quote_highlights():
    text = "a <b> & c d e"
    claims = {
        "Caution": [Claim("<b> &", None), Claim("b", None), Claim("zzz", None)],
        "Literacy": [Claim("& c", None), Claim("e", None), Claim(None, "p")],
    }

    html = render_paragraph(text, claims)
    paragraph_text = re.search(r'<p class="text">(.*?)</p>', html).group(1)

    assert 'a <mark>&lt;b&gt; &amp; c</mark> d <mark>e</mark><span id="paragraph-1-1-text-end"></span>' in html
    assert html.count("<mark>") == 2 and re.sub(r"<[^>]+>", "", paragraph_text) == escape(text)
    assert '<blockquote class="quote">&lt;b&gt; &amp;</blockquote>' in html


def test_empty_report(tmp_path):
    html = printer.html(make_run_dir(tmp_path, [("A", ["a"])], []))

    assert "<strong>0</strong>" in html
    assert 'class="chapter"' not in html and "Претензии по свойствам" not in html


@pytest.mark.parametrize("case, error_type", [
    ("no report", RunDirReadError),
    ("report is object", ReportFormatError),
    ("paragraph missing", ReportFormatError),
])
def test_errors(tmp_path, case, error_type):
    run_dir = make_run_dir(tmp_path, [("A", ["a"])], [{"chapter": "A", "claims": [{"paragraph": 1}]}])
    if case == "no report":
        (run_dir / "report.json").unlink()
    elif case == "report is object":
        (run_dir / "report.json").write_text("{}", encoding="utf-8")
    else:
        (run_dir / "report.json").write_text(json.dumps([{"chapter": "A", "claims": [{"paragraph": 2}]}]), encoding="utf-8")

    with pytest.raises(error_type) as caught:
        printer.html(run_dir)

    assert isinstance(caught.value, ReportError)


def test_css():
    css = printer.css()

    assert "#fbc847" in css and "#393939" in css and "string(heading)" in css and "•" not in css
    fonts = re.findall(r"url\((fonts/[^)]+)\)", css)
    assert fonts and all((STYLESHEET.parent / font).is_file() for font in fonts)


def test_pdf(tmp_path):
    html = printer.html(make_sample_run_dir(tmp_path))

    assert printer.pdf(html, printer.css()).startswith(b"%PDF-")


def make_chapter(name, sizes):
    return PrintedChapter(name, [PrintedParagraph(
        n, "\n".join(f"line {n}.{i}" for i in range(lines)),
        {"Caution": [Claim(quote=f"line {n}.0", problem=f"problem {n}.{i} " * 6) for i in range(claims)]},
    ) for n, (lines, claims) in enumerate(sizes, start=1)])


def test_paragraph_page_breaks():
    chapters = [make_chapter("A", [(10, 1), (20, 1), (30, 1), (3, 15), (80, 1)]), make_chapter("B", [(80, 1)])]
    html = '<div class="ai-reviewer-report">' + ClaimPagesRenderer().render(chapters, RUSSIAN_LABELS) + "</div>"
    anchors = {}
    for index, page in enumerate(PdfRenderer().document(html, printer.css()).pages):
        for name, box in page.anchors.items():
            anchors.setdefault(name, (index, box[1]))

    def start(chapter, position):
        return anchors[ParagraphPageBreaks.block_id(chapter, position)]

    def end_page(chapter, position):
        return anchors[ParagraphPageBreaks.text_end_id(chapter, position)][0]

    assert start(1, 3)[0] == end_page(1, 2) + 1 == end_page(1, 3)
    assert start(1, 4)[0] == end_page(1, 3)
    assert start(1, 5)[1] == start(1, 3)[1] and end_page(1, 5) > start(1, 5)[0]
    assert start(2, 1)[1] > start(1, 3)[1] and end_page(2, 1) > start(2, 1)[0]


class StubPrinter:
    def __init__(self, mark):
        self.mark = mark

    def html(self, run_dir, labels):
        return f"<p>{self.mark} ж</p>"

    def css(self):
        return f"/* {self.mark} */"

    def pdf(self, html, css):
        return f"%PDF-{self.mark}".encode()


def test_writer_saves_and_overwrites(tmp_path):
    for mark in ["old", "new"]:
        PrintedReportWriter(printer=StubPrinter(mark)).write(tmp_path)

    assert (tmp_path / "report.html").read_text(encoding="utf-8") == "<p>new ж</p>"
    assert (tmp_path / "report.css").read_text(encoding="utf-8") == "/* new */"
    assert (tmp_path / "report.pdf").read_bytes() == b"%PDF-new"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["report.css", "report.html", "report.pdf"]
