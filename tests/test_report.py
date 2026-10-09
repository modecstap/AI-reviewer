import json
import logging

import pytest

from ai_reviewer.report import ReportError, ReportWriteError, ReportWriter, RunDirReadError
from ai_reviewer.splitter import NO_HEADING, ArticleWriter, Chapter

write_report = ReportWriter().write


def make_run_dir(tmp_path, chapters, **properties):
    run_dir = tmp_path / "1"
    run_dir.mkdir()
    article = ArticleWriter().write([Chapter(name, name, ["p"] * count) for name, count in chapters])
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
        Structure=[claim("Итоги", 1, "s1"), claim("Введение", 3, "s2")],
        Caution=[claim("Введение", 3, "c1"), claim("Введение", 3, "c2"), claim("Введение", 1, "c3", confidence=0.5)],
        Literacy=[],
    )

    path = write_report(run_dir)

    report = read(path)
    assert path == run_dir / "report.json"
    assert report == [
        {"chapter": "Введение", "claims": [
            {"paragraph": 1, "Caution": [{"quote": "c3", "confidence": 0.5}]},
            {"paragraph": 3, "Caution": [{"quote": "c1"}, {"quote": "c2"}], "Structure": [{"quote": "s2"}]},
        ]},
        {"chapter": "Итоги", "claims": [{"paragraph": 1, "Structure": [{"quote": "s1"}]}]},
    ]
    assert list(report[0]["claims"][1]) == ["paragraph", "Caution", "Structure"]
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
        tmp_path, [("A", 1)], Caution=[claim("A", 1, "ok"), *invalid], Broken="{not json", Object={}
    )

    with caplog.at_level(logging.WARNING):
        report = read(write_report(run_dir))

    assert report == [{"chapter": "A", "claims": [{"paragraph": 1, "Caution": [{"quote": "ok"}]}]}]
    assert len([r for r in caplog.records if r.levelno == logging.WARNING]) == 7 + 2
    assert "Caution" in caplog.text and "Broken.json" in caplog.text and "Object.json" in caplog.text


def test_no_claims_and_rerun(tmp_path, caplog):
    run_dir = make_run_dir(tmp_path, [("A", 1)])

    assert read(write_report(run_dir)) == []
    with caplog.at_level(logging.WARNING):
        assert read(write_report(run_dir)) == []
    assert not caplog.records

    (run_dir / "Caution.json").write_text(json.dumps([claim("A", 1, "q")]), encoding="utf-8")
    assert read(write_report(run_dir)) == [{"chapter": "A", "claims": [{"paragraph": 1, "Caution": [{"quote": "q"}]}]}]


@pytest.mark.parametrize("case, error_type", [
    ("no run dir", RunDirReadError),
    ("no article", RunDirReadError),
    ("report is dir", ReportWriteError),
])
def test_errors(tmp_path, case, error_type):
    run_dir = make_run_dir(tmp_path, [("A", 1)])
    if case == "no run dir":
        run_dir = tmp_path / "missing"
    elif case == "no article":
        (run_dir / "article.txt").unlink()
    else:
        (run_dir / "report.json").mkdir()

    with pytest.raises(error_type) as caught:
        write_report(run_dir)

    assert isinstance(caught.value, ReportError)
    assert not (run_dir / "report.json.tmp").exists()
