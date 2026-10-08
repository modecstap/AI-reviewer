import contextlib
import logging
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from cursor_sdk import CursorAgentError

from ai_reviewer.ai_pool import AIPool, PoolStartError
from ai_reviewer.ai_pool import pool as ai_pool

TEXT = "Первый абзац.\nВторой абзац.\n"


def make_property(tmp_path, name, reference=True):
    props = tmp_path / "props"
    (props / name).mkdir(parents=True)
    (props / "IO-structure.md").write_text("IO-MARKER", encoding="utf-8")
    (props / name / "instruction.md").write_text(f"INSTR-{name}", encoding="utf-8")
    if reference:
        (props / name / "reference.md").write_text(f"REF-{name}", encoding="utf-8")
    return str(props / "IO-structure.md"), str(props / name)


def make_pool(tmp_path, names, missing_reference=(), **kwargs):
    pool = AIPool(**kwargs)
    for name in names:
        io, docs = make_property(tmp_path, name, reference=name not in missing_reference)
        pool.add_agent(io, docs, name, str(tmp_path / "out"))
    return pool


def write(content, status="finished"):
    def behave(cwd, name):
        (cwd / f"{name}.json").write_text(content, encoding="utf-8")
        return status
    return behave


def returns(status):
    return lambda cwd, name: status


def raises(err):
    def behave(cwd, name):
        raise err
    return behave


@pytest.fixture(autouse=True)
def sdk(monkeypatch):
    behaviors, calls = {}, []

    def prompt(message, options, client=None):
        name = next(n for n in behaviors if f"{n}.json" in message)
        calls.append(SimpleNamespace(name=name, message=message, options=options, client=client))
        return SimpleNamespace(id=f"run-{name}", status=behaviors[name](Path(options.local.cwd), name))

    monkeypatch.setenv("CURSOR_API_KEY", "test-key")
    monkeypatch.setattr(ai_pool, "CursorClient", SimpleNamespace(launch_bridge=lambda **kw: contextlib.nullcontext("client")))
    monkeypatch.setattr(ai_pool, "Agent", SimpleNamespace(prompt=prompt))
    return SimpleNamespace(behaviors=behaviors, calls=calls)


def test_happy_path_runs_agents_in_parallel(tmp_path, sdk, caplog):
    caplog.set_level(logging.INFO, logger="ai_reviewer.ai_pool")
    names = ["alpha", "beta", "gamma"]
    barrier = threading.Barrier(3, timeout=5)

    def behave(cwd, name):
        barrier.wait()
        return write("[]")(cwd, name)

    sdk.behaviors.update({name: behave for name in names})

    result = make_pool(tmp_path, names).execute(TEXT)

    run_dir = result.run_dir
    assert run_dir == (tmp_path / "out" / "1").resolve()
    assert list(result.statuses) == names
    assert all(status.ok for status in result.statuses.values())
    assert (run_dir / "article.txt").read_bytes() == TEXT.encode("utf-8")
    assert sorted(p.name for p in run_dir.iterdir()) == ["alpha.json", "article.txt", "beta.json", "gamma.json"]

    agent_ids = {call.options.agent_id for call in sdk.calls}
    assert len(agent_ids) == 3 and all(i.startswith("agent-") for i in agent_ids)
    for call in sdk.calls:
        options = call.options
        assert options.model == "composer-2.5" and options.api_key == "test-key"
        assert options.local.cwd == str(run_dir) and options.local.setting_sources is None
        assert options.cloud is None and call.client == "client"
        for marker in ["IO-MARKER", f"INSTR-{call.name}", f"REF-{call.name}", "article.txt", f"{call.name}.json"]:
            assert marker in call.message
        assert options.agent_id in caplog.text
        assert f"run_id=run-{call.name}, status=finished" in caplog.text

    sdk.calls.clear()
    sdk.behaviors["delta"] = write("[]")
    make_pool(tmp_path / "other", ["delta"], model="x").execute(TEXT)
    assert sdk.calls[0].options.model == "x"


def test_failed_agents_do_not_stop_others(tmp_path, sdk):
    sdk.behaviors.update({
        "raises": raises(CursorAgentError("boom", request_id="r1")),
        "errored": returns("error"),
        "cancelled": returns("cancelled"),
        "silent": returns("finished"),
        "broken": write("{not json"),
        "object": write("{}"),
        "noref": write("[]"),
        "good": write("[]"),
    })

    result = make_pool(tmp_path, list(sdk.behaviors), missing_reference=["noref"]).execute(TEXT)

    assert result.statuses["good"].ok is True
    assert (result.run_dir / "good.json").is_file()
    for name, status in result.statuses.items():
        if name != "good":
            assert status.ok is False and status.reason, name
            assert not (result.run_dir / f"{name}.json").exists(), name
    assert result.statuses["errored"].reason == "run status: error"
    assert result.statuses["object"].reason == "JSON root is not an array"


def test_run_dirs_are_numbered_after_max(tmp_path, sdk):
    out = tmp_path / "out"
    for d in ["1", "7", "x"]:
        (out / d).mkdir(parents=True)
    (out / "7" / "keep.txt").write_text("old", encoding="utf-8")
    (out / "3.txt").write_text("", encoding="utf-8")
    sdk.behaviors["alpha"] = write("[]")
    pool = make_pool(tmp_path, ["alpha"])

    assert pool.execute(TEXT).run_dir.name == "8"
    assert pool.execute(TEXT).run_dir.name == "9"
    assert (out / "7" / "keep.txt").read_text(encoding="utf-8") == "old"


def fail_bridge(**kwargs):
    raise CursorAgentError("no bridge")


@pytest.mark.parametrize("case", ["no agents", "no key", "blank key", "output is file", "bridge fails"])
def test_execute_start_errors(tmp_path, monkeypatch, case):
    if case == "no key":
        monkeypatch.delenv("CURSOR_API_KEY")
    if case == "blank key":
        monkeypatch.setenv("CURSOR_API_KEY", "  ")
    if case == "output is file":
        (tmp_path / "out").write_text("", encoding="utf-8")
    if case == "bridge fails":
        monkeypatch.setattr(ai_pool, "CursorClient", SimpleNamespace(launch_bridge=fail_bridge))
    pool = AIPool() if case == "no agents" else make_pool(tmp_path, ["alpha"])

    with pytest.raises(PoolStartError):
        pool.execute(TEXT)
    if case == "bridge fails":
        assert not (tmp_path / "out" / "1").exists()


def test_add_agent_rejects_duplicate_name_and_other_output_dir(tmp_path):
    pool = make_pool(tmp_path, ["alpha"])
    io, docs = str(tmp_path / "props" / "IO-structure.md"), str(tmp_path / "props" / "alpha")

    with pytest.raises(ValueError):
        pool.add_agent(io, docs, "alpha", str(tmp_path / "out"))
    with pytest.raises(ValueError):
        pool.add_agent(io, docs, "beta", str(tmp_path / "elsewhere"))
