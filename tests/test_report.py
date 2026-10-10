import json
import logging

import pytest

from ai_reviewer.article import ArticleText, Chapter
from ai_reviewer.report import ReportBuilder
from ai_reviewer.run_dir import RunDirReadError, RunDirReader, RunDirWriteError, RunDirWriter
from ai_reviewer.splitter import NO_HEADING


def write_report(run_dir):
    reader = RunDirReader()
    chapters = ReportBuilder().build(reader.read_article(run_dir), reader.read_claims(run_dir))
    return RunDirWriter().write_report(run_dir, chapters)


def make_run_dir(tmp_path, chapters, **properties):
    run_dir = tmp_path / "1"
    run_dir.mkdir()
    article = ArticleText().write([Chapter(name, ["p"] * count) for name, count in chapters])
    (run_dir / "article.txt").write_text(article, encoding="utf-8", newline="")
    for name, content in properties.items():
        text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
        (run_dir / f"{name}.json").write_text(text, encoding="utf-8")
    return run_dir


def claim(chapter, paragraph, quote, **extra):
    return {"place": {"chapter": chapter, "paragraph": paragraph}, "quote": quote, **extra}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_groups_and_orders(tmp_path):
    run_dir = make_run_dir(
        tmp_path,
        [(NO_HEADING, 2), ("Введение", 3), ("Пусто", 0), ("Итоги", 1)],
        structure=[claim("Итоги", 1, "s1"), claim("Введение", 3, "s2")],
        caution=[claim("Введение", 3, "c1"), claim("Введение", 3, "c2"), claim("Введение", 1, "c3", confidence=0.5)],
        literacy=[],
    )

    path = write_report(run_dir)

    report = read(path)
    assert path == run_dir / "report.json"
    assert report == [
        {"chapter": "Введение", "claims": [
            {"paragraph": 1, "caution": [{"quote": "c3", "confidence": 0.5}]},
            {"paragraph": 3, "caution": [{"quote": "c1"}, {"quote": "c2"}], "structure": [{"quote": "s2"}]},
        ]},
        {"chapter": "Итоги", "claims": [{"paragraph": 1, "structure": [{"quote": "s1"}]}]},
    ]
    assert list(report[0]["claims"][1]) == ["paragraph", "caution", "structure"]
    assert "Введение".encode("utf-8") in path.read_bytes()
    assert b"\\u" not in path.read_bytes()


def test_invalid_claims_are_skipped_with_warning(tmp_path, caplog):
    invalid = [
        {"quote": "no place"},
        {"place": "x", "quote": "place not object"},
        claim("Нет", 1, "unknown chapter"),
        claim("A", 9, "unknown paragraph"),
        claim("A", True, "bool paragraph"),
        claim("A", "1", "str paragraph"),
        "not an object",
    ]
    run_dir = make_run_dir(
        tmp_path, [("A", 1)], caution=[claim("A", 1, "ok"), *invalid], broken="{not json", object={}
    )

    with caplog.at_level(logging.WARNING):
        report = read(write_report(run_dir))

    assert report == [{"chapter": "A", "claims": [{"paragraph": 1, "caution": [{"quote": "ok"}]}]}]
    assert len([r for r in caplog.records if r.levelno == logging.WARNING]) == 7 + 2
    assert "caution" in caplog.text and "broken.json" in caplog.text and "object.json" in caplog.text


def test_no_claims_and_rerun(tmp_path, caplog):
    run_dir = make_run_dir(tmp_path, [("A", 1)])

    assert read(write_report(run_dir)) == []
    with caplog.at_level(logging.WARNING):
        assert read(write_report(run_dir)) == []
    assert not caplog.records

    (run_dir / "caution.json").write_text(json.dumps([claim("A", 1, "q")]), encoding="utf-8")
    assert read(write_report(run_dir)) == [{"chapter": "A", "claims": [{"paragraph": 1, "caution": [{"quote": "q"}]}]}]


@pytest.mark.parametrize("case, error_type", [
    ("no run dir", RunDirReadError),
    ("no article", RunDirReadError),
    ("report is dir", RunDirWriteError),
])
def test_errors(tmp_path, case, error_type):
    run_dir = make_run_dir(tmp_path, [("A", 1)])
    if case == "no run dir":
        run_dir = tmp_path / "missing"
    elif case == "no article":
        (run_dir / "article.txt").unlink()
    else:
        (run_dir / "report.json").mkdir()

    with pytest.raises(error_type):
        write_report(run_dir)

    assert not (run_dir / "report.json.tmp").exists()
