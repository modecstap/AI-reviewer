import json
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from ai_reviewer.splitter import NO_HEADING, ArticleParser, ArticleSplitter

parse_article = ArticleParser().parse
split_article = ArticleSplitter().split

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


def test_article_end_to_end(tmp_path):
    out = tmp_path / "refine"
    split_article(ARTICLE, out)

    assert sorted(p.name for p in out.iterdir()) == sorted([NO_HEADING, TITLE, "chapters.json"])
    assert [p.name for p in (out / NO_HEADING).iterdir()] == ["1.txt"]
    assert read(out / NO_HEADING / "1.txt") == "Г.\xa0А.\xa0Шебанин"

    body = out / TITLE
    assert sorted(p.name for p in body.iterdir()) == sorted(f"{i}.txt" for i in range(1, 89))
    assert read(body / "1.txt").startswith("Курганные могильники Подмосковья, как одна из самых массовых")
    assert read(body / "75.txt").startswith("1. Возвышенный участок")
    assert read(body / "79.txt").startswith("5. Берега и верховья небольших оврагов:")
    assert read(body / "88.txt").startswith("Подводя итоги, можно говорить о том, что каждая")

    raw = (out / "chapters.json").read_bytes()
    assert json.loads(raw) == [{"chapter": NO_HEADING, "title": None}, {"chapter": TITLE, "title": TITLE}]
    assert NO_HEADING.encode() in raw and b"\\u" not in raw

    assert not any("Автор благодарит" in read(f) for f in out.rglob("*.txt"))


def test_rerun_wipes_output(tmp_path):
    out = tmp_path / "refine"
    split_article(ARTICLE, out)
    (out / "stray.txt").write_text("x")
    (out / "junk").mkdir()

    doc = Document()
    doc.add_paragraph("Один абзац.")
    split_article(save(doc, tmp_path), out)

    assert sorted(p.name for p in out.iterdir()) == sorted([NO_HEADING, "chapters.json"])
    assert read(out / NO_HEADING / "1.txt") == "Один абзац."


def test_cli(tmp_path):
    out = tmp_path / "refine"
    cmd = [sys.executable, "-m", "ai_reviewer.splitter"]
    ok = subprocess.run([*cmd, str(ARTICLE), str(out)], cwd=ROOT, capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    assert (out / "chapters.json").is_file()

    bad = subprocess.run([*cmd, str(tmp_path / "missing.docx"), str(out)], cwd=ROOT, capture_output=True, text=True)
    assert bad.returncode != 0
    assert bad.stderr.strip()
    assert (out / "chapters.json").is_file()


def test_styles_beat_heuristics(tmp_path):
    doc = Document()
    doc.add_heading("Введение", 1)
    doc.add_paragraph().add_run("Жирная строка").bold = True
    doc.add_paragraph("Текст.")

    assert chapters_of(save(doc, tmp_path)) == [("Введение", ["Жирная строка", "Текст."])]


def test_flat_levels_and_empty_chapter(tmp_path):
    doc = Document()
    doc.add_heading("2. Метод", 1)
    doc.add_heading("2.1 Выборка", 2)
    doc.add_paragraph("Текст.")
    out = tmp_path / "refine"

    path = save(doc, tmp_path)
    split_article(path, out)

    assert chapters_of(path) == [("2. Метод", []), ("2.1 Выборка", ["Текст."])]
    assert (out / "2. Метод").is_dir() and not any((out / "2. Метод").iterdir())
    assert [c["chapter"] for c in json.loads(read(out / "chapters.json"))] == ["2. Метод", "2.1 Выборка"]


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
