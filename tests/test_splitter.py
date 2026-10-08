import json
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from ai_reviewer.splitter import NO_HEADING, ArticleParser, ArticleRefiner, ArticleWriter, Chapter

parse_article = ArticleParser().parse
refine_article = ArticleRefiner().refine
article_text = ArticleWriter().write

ROOT = Path(__file__).resolve().parent.parent
ARTICLE = ROOT / "tests" / "data" / "test_article.docx"
TITLE = "Пространственно-сакральный аспект топографии курганных могильников на примере Подмосковья"


def save(doc, tmp_path, name="a.docx"):
    path = tmp_path / name
    doc.save(path)
    return path


def chapters_of(path):
    return [(ch.name, ch.paragraphs) for ch in parse_article(path)]


def read(path):
    return path.read_text(encoding="utf-8")

def test_styles_beat_heuristics(tmp_path):
    doc = Document()
    doc.add_heading("Введение", 1)
    doc.add_paragraph().add_run("Жирная строка").bold = True
    doc.add_paragraph("Текст.")

    assert chapters_of(save(doc, tmp_path)) == [("Введение", ["Жирная строка", "Текст."])]


def test_no_headings(tmp_path):
    doc = Document()
    for text in ["Первый абзац.", "", "Второй абзац.", "   ", "Третий."]:
        doc.add_paragraph(text)

    assert chapters_of(save(doc, tmp_path)) == [(NO_HEADING, ["Первый абзац.", "Второй абзац.", "Третий."])]


def test_folder_names(tmp_path):
    doc = Document()
    for title in ['A/B:C*?"<>|D', "д" * 150, "Итоги", "итоги", "Итоги"]:
        doc.add_heading(title, 1)

    names = [name for name, _ in chapters_of(save(doc, tmp_path))]

    assert names == ["A_B_C______D", "д" * 100, "Итоги", "итоги (2)", "Итоги (3)"]


def test_table_and_list(tmp_path):
    doc = Document()
    doc.add_paragraph("До.")
    table = doc.add_table(rows=2, cols=2)
    for cell, text in zip(table._cells, "abcd"):
        cell.text = text
    doc.add_paragraph("После.")
    doc.add_paragraph("один;", style="List Number")
    doc.add_paragraph("два.", style="List Bullet")

    assert chapters_of(save(doc, tmp_path)) == [
        (NO_HEADING, ["До.", "a\tb\nc\td", "После.", "один;", "два."])
    ]


def test_exclusions_and_tracked_changes(tmp_path):
    doc = Document()
    doc.sections[0].header.paragraphs[0].text = "HDR"
    doc.sections[0].footer.paragraphs[0].text = "FTR"
    doc.add_paragraph("Формула ")._p.append(parse_xml(
        '<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">'
        "<m:r><m:t>EQ</m:t></m:r></m:oMath>"
    ))
    edited = doc.add_paragraph("Правка ")._p
    edited.append(parse_xml(f'<w:ins {nsdecls("w")} w:id="1" w:author="a"><w:r><w:t>INS</w:t></w:r></w:ins>'))
    edited.append(parse_xml(
        f'<w:del {nsdecls("w")} w:id="2" w:author="a"><w:r><w:delText>DEL</w:delText></w:r></w:del>'
    ))

    assert chapters_of(save(doc, tmp_path)) == [(NO_HEADING, ["Формула", "Правка INS"])]


def test_article_text_format():
    chapters = [Chapter("A", "A", ["p1", "p2"]), Chapter("B", "B", ["q1"])]

    assert article_text(chapters) == (
        "!! chapter: A\n!! paragraph: 1\np1\n\n!! paragraph: 2\np2\n\n!! chapter: B\n!! paragraph: 1\nq1\n"
    )


def test_article_text_name_verbatim_and_empty_chapter():
    chapters = [
        Chapter(NO_HEADING, None, ["Г.\xa0А.\xa0Шебанин"]),
        Chapter("A_B", "A/B", ["a\nb\tc"]),
        Chapter("Пусто", "Пусто"),
        Chapter("C", "C", ["d"]),
    ]

    assert article_text(chapters) == (
        f"!! chapter: {NO_HEADING}\n!! paragraph: 1\nГ.\xa0А.\xa0Шебанин\n\n"
        "!! chapter: A_B\n!! paragraph: 1\na\nb\tc\n\n"
        "!! chapter: Пусто\n\n"
        "!! chapter: C\n!! paragraph: 1\nd\n"
    )


def test_article_text_edges():
    assert article_text([]) == ""
    assert article_text([Chapter("A", "A", ["p"]), Chapter("B", "B")]).endswith("p\n\n!! chapter: B\n")
