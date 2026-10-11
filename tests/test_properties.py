from pathlib import Path

import pytest

from ai_reviewer.properties import PropertyCatalog, PropertyCatalogError

ROOT = Path(__file__).resolve().parent.parent
CATALOG = PropertyCatalog(ROOT / "properties")
TYPE_COUNTS = {"caution": 9, "conciseness": 7, "consistency": 6, "correctness": 14, "impersonality": 8, "literacy": 8, "structure": 8}
IDS = list(TYPE_COUNTS)


def make_property(root, name, files=("instruction.md", "reference.md")):
    (root / name).mkdir(parents=True)
    for file in files:
        (root / name / file).write_text("## Violation types\n### 1. X\n### 2. Y\n## Markers\n### 3. Z\n", encoding="utf-8")


def test_repository_catalog():
    assert [agent.id for agent in CATALOG.agents()] == IDS
    names = CATALOG.names("ru")
    assert names.property_ids() == IDS
    assert all(names.numbers(id) == tuple(str(n) for n in range(1, count + 1)) for id, count in TYPE_COUNTS.items())
    assert names.property_name("caution") == "Осторожность выводов"
    assert names.type_name("literacy", "2") == "Нарушение управления"
    assert all(set(names.type_translations[id]) == set(names.numbers(id)) for id in IDS)
    english = CATALOG.names("en")
    assert english.property_name("caution") == "caution"
    assert english.type_name("literacy", "2") is None


def test_new_property_and_broken_translation(tmp_path):
    make_property(tmp_path, "new")
    make_property(tmp_path, "half", files=("instruction.md",))
    make_property(tmp_path, "translation")
    agent = PropertyCatalog(tmp_path).agents()[0]
    assert [a.id for a in PropertyCatalog(tmp_path).agents()] == ["new"]
    assert (agent.io_structure, agent.reference) == (tmp_path / "IO-structure.md", tmp_path / "new" / "reference.md")
    assert PropertyCatalog(tmp_path).names("ru").numbers("new") == ("1", "2")
    for broken in ("{not json", "[]", '{"new": {"name": 1, "types": {}}}', '{"new": {"name": "N", "types": {"1": 2}}}'):
        (tmp_path / "translation" / "ru.json").write_text(broken, encoding="utf-8")
        with pytest.raises(PropertyCatalogError):
            PropertyCatalog(tmp_path).names("ru")
    with pytest.raises(PropertyCatalogError):
        PropertyCatalog(tmp_path / "missing").agents()
