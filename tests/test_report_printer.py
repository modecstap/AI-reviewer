import json
import re
from datetime import date
from html import escape
from pathlib import Path

import pytest

from ai_reviewer.article import ArticleText, Chapter
from ai_reviewer.claims import Claim, Place
from ai_reviewer.properties import PropertyCatalog
from ai_reviewer.report import ReportChapter, ReportFormatError, ReportParagraph
from ai_reviewer.report.printer import ENGLISH_LABELS, RUSSIAN_LABELS, ReportPrinter
from ai_reviewer.report.printer.claim_pages import ClaimPagesRenderer
from ai_reviewer.report.printer.pdf import ParagraphPageBreaks, PdfRenderer
from ai_reviewer.report.printer.printer import STYLESHEET
from ai_reviewer.report.printer.statistics import StatisticsPageRenderer
from ai_reviewer.report.printer.title_page import TitlePageRenderer
from ai_reviewer.run_dir import PrintedReport, RunDirReadError, RunDirReader, RunDirWriter
from ai_reviewer.splitter import NO_HEADING

ROOT = Path(__file__).resolve().parent.parent
CATALOG = PropertyCatalog(ROOT / "properties")
RU = RUSSIAN_LABELS.with_names(CATALOG.names("ru"))
EN = ENGLISH_LABELS.with_names(CATALOG.names("en"))

printer = ReportPrinter(title_page=TitlePageRenderer(today=lambda: date(2026, 10, 9)))

FULL = {"quote": "c1 quote", "problem": "c1 problem", "types": [{"number": 1, "name": "Hedging"}], "extra": ["fix c1"]}
SAMPLE_REPORT = [{"chapter": "Введение", "claims": [
    {"paragraph": 1},
    {"paragraph": 3,
     "caution": [FULL, {"quote": "c2 quote", "problem": "c2 problem"}],
     "structure": [{"quote": "s1 <i>", "problem": "s1 & problem", "types": [{"name": "Order"}]}]},
]}]


def claim(**fields):
    return Claim(Place("A", 1), fields)


def make_run_dir(tmp_path, chapters, report):
    run_dir = tmp_path / "1"
    run_dir.mkdir()
    article = ArticleText().write([Chapter(name, paragraphs) for name, paragraphs in chapters])
    (run_dir / "article.txt").write_text(article, encoding="utf-8", newline="")
    (run_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    return run_dir


def sample_report(tmp_path):
    chapters = [(NO_HEADING, ["n"]), ("Введение", ["p1 <b> & x\nline2", "p2", "p3"]), ("Пусто", ["e"])]
    return RunDirReader().read_report(make_run_dir(tmp_path, chapters, SAMPLE_REPORT))


def test_content_order_and_escaping(tmp_path):
    html = printer.html(sample_report(tmp_path), RU)
    title_end, chapter_start = html.index('class="statistics"'), html.index('class="chapter"')
    title, statistics, chapters = html[:title_end], html[title_end:chapter_start], html[chapter_start:]

    assert html.index('class="title"') < title_end < chapter_start
    assert "&lt;b&gt; &amp; x\nline2" in html and "<b>" not in html
    assert "s1 &lt;i&gt;" in html and "s1 &amp; problem" in html
    assert all(absent not in chapters for absent in ["p2", "Пусто", NO_HEADING])
    assert html.index("c1 quote") < html.index("c2 quote") < html.index("s1 &lt;i&gt;")
    assert re.findall(r'class="ordinal">(\d+)<', html) == ["1", "2", "1"]
    assert all(part in title for part in ["VSRT", "AI-Reviewer", "09.10.2026"])
    assert "<strong>" not in title and "Всего претензий" not in title
    assert "Всего претензий" in statistics and "<strong>3</strong>" in statistics
    assert "caution" not in html and "structure" not in html and "Претензии по свойствам" not in html
    assert "Проблема" in html
    assert "<li>1. Гипотеза подана как установленный факт</li>" in chapters and "<li>Order</li>" in chapters
    assert html.count("Типы") == 2 and "Корректировки" not in html and "fix c1" not in html


def test_english_labels_keep_data(tmp_path):
    html = printer.html(sample_report(tmp_path), EN)

    assert 'lang="en"' in html and "October 9, 2026" in html and "Problem" in html
    assert "Проблема" not in html and "Claims by property" not in html
    assert "Введение" in html and "&lt;b&gt;" in html and "c1 problem" in html
    assert '<span class="property">caution</span>' in html and "<li>1. Hedging</li>" in html
    assert "Statistics" in html and ">Total<" in html


def render_paragraph(text, claims, labels=RU):
    return ClaimPagesRenderer().render([ReportChapter("A", [ReportParagraph(1, text, claims)])], labels)


@pytest.mark.parametrize("labels, expected", [
    (RU, ["<li>2. Нарушение управления</li>", "<li>99. Odd</li>", "<li>Bare</li>",
          'class="property">Грамотность<', 'class="property">unknown<']),
    (EN, ["<li>2. Incorrect government</li>", 'class="property">literacy<']),
])
def test_names_fallback(labels, expected):
    types = [{"number": 2, "name": "Incorrect government"}, {"number": "99", "name": "Odd"}, {"name": "Bare"}]
    claims = {"literacy": [claim(types=types)], "unknown": [claim()]}

    html = render_paragraph("t", claims, labels)

    assert all(part in html for part in expected)


def test_quote_highlights():
    text = "a <b> & c d e"
    claims = {
        "caution": [claim(quote="<b> &"), claim(quote="b"), claim(quote="zzz")],
        "literacy": [claim(quote="& c"), claim(quote="e"), claim(problem="p")],
    }

    html = render_paragraph(text, claims)
    paragraph_text = re.search(r'<p class="text">(.*?)</p>', html).group(1)

    assert 'a <mark>&lt;b&gt; &amp; c</mark> d <mark>e</mark><span id="paragraph-1-1-text-end"></span>' in html
    assert html.count("<mark>") == 2 and re.sub(r"<[^>]+>", "", paragraph_text) == escape(text)
    assert '<blockquote class="quote">&lt;b&gt; &amp;</blockquote>' in html


def test_empty_report(tmp_path):
    html = printer.html(RunDirReader().read_report(make_run_dir(tmp_path, [("A", ["a"])], [])), RU)

    assert "<strong>0</strong>" in html
    assert 'class="chapter"' not in html and "Претензии по свойствам" not in html
    assert html.count('class="zero"') == 60 and html.count('class="total zero"') == 7
    assert html.count('class="absent"') == 38


def test_statistics_grid():
    caution = [claim(types=[{"number": "1"}, {"number": "2"}]), claim(types=[{"number": "1"}, {"name": "Bare"}]), claim()]
    odd = [claim(types=[{"number": "15", "name": "Fifteen <b>"}, {"number": "x"}])]
    chapters = [ReportChapter("A", [ReportParagraph(1, "t", {"caution": caution[:2]})]),
                ReportChapter("B", [ReportParagraph(2, "t", {"caution": caution[2:], "Odd<x>": odd})])]

    html = StatisticsPageRenderer().render(chapters, RU)

    def cells(name):
        row = re.search(rf'scope="row">{name}</th>(.*?)</tr>', html).group(1)
        return re.findall(r"<td[^>]*>\d*</td>", row)

    caution_cells, odd_cells = cells("Осторожность выводов"), cells("Odd&lt;x&gt;")
    header = re.search(r"<thead>(.*?)</thead>", html).group(1)
    assert re.findall(r"<th>(\w*)</th>", header) == ["", *map(str, range(1, 16)), "x", "Всего"]
    assert "<strong>4</strong>" in html and "Bare" not in html
    assert caution_cells[:3] == ["<td>2</td>", "<td>1</td>", '<td class="zero">0</td>']
    assert caution_cells[14:] == ['<td class="absent"></td>'] * 2 + ['<td class="total">3</td>']
    assert odd_cells[0] == '<td class="absent"></td>'
    assert odd_cells[14:] == ["<td>1</td>", "<td>1</td>", '<td class="total">1</td>']
    assert "<li>15. Fifteen &lt;b&gt;</li>" in html and "<li>x</li>" in html


def test_statistics_page_layout():
    names = CATALOG.names("ru")
    claims = {id: [claim(types=[{"number": number} for number in names.numbers(id)])] * 100
              for id in names.property_ids()}
    chapters = [ReportChapter("A", [ReportParagraph(1, "t", claims)])]
    html = ('<div class="ai-reviewer-report">' + TitlePageRenderer().render(chapters, RU)
            + StatisticsPageRenderer().render(chapters, RU) + "</div>")

    pages = PdfRenderer(STYLESHEET).document(html, printer.css()).pages
    texts = [box.text for box in pages[-1]._page_box.descendants() if hasattr(box, "text")]

    assert len(pages) == 2 and texts.count("Статистика") == 2 and "14. Неясная отсылка" in texts


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

    with pytest.raises(error_type):
        RunDirReader().read_report(run_dir)


def test_css():
    css = printer.css()

    assert "#fbc847" in css and "#393939" in css and "string(heading)" in css and "•" not in css
    fonts = re.findall(r"url\((fonts/[^)]+)\)", css)
    assert fonts and all((STYLESHEET.parent / font).is_file() for font in fonts)


def test_pdf(tmp_path):
    html = printer.html(sample_report(tmp_path), RU)

    assert printer.pdf(html, printer.css()).startswith(b"%PDF-")


def make_chapter(name, sizes):
    return ReportChapter(name, [ReportParagraph(
        n, "\n".join(f"line {n}.{i}" for i in range(lines)),
        {"caution": [claim(quote=f"line {n}.0", problem=f"problem {n}.{i} " * 6) for i in range(claims)]},
    ) for n, (lines, claims) in enumerate(sizes, start=1)])


def test_paragraph_page_breaks():
    chapters = [make_chapter("A", [(10, 1), (20, 1), (30, 1), (3, 15), (80, 1)]), make_chapter("B", [(80, 1)])]
    html = '<div class="ai-reviewer-report">' + ClaimPagesRenderer().render(chapters, RU) + "</div>"
    anchors = {}
    for index, page in enumerate(PdfRenderer(STYLESHEET).document(html, printer.css()).pages):
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


def test_writer_saves_and_overwrites(tmp_path):
    for mark in ["old", "new"]:
        RunDirWriter().write_printed(tmp_path, PrintedReport(f"<p>{mark} ж</p>", f"/* {mark} */", f"%PDF-{mark}".encode()))

    assert (tmp_path / "report.html").read_text(encoding="utf-8") == "<p>new ж</p>"
    assert (tmp_path / "report.css").read_text(encoding="utf-8") == "/* new */"
    assert (tmp_path / "report.pdf").read_bytes() == b"%PDF-new"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["report.css", "report.html", "report.pdf"]
