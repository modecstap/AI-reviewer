import contextlib
import threading
from types import SimpleNamespace

import pytest
from cursor_sdk import CursorAgentError

from ai_reviewer.ai_pool import (
    AIPool,
    AgentRunError,
    BridgeLaunchError,
    DuplicateAgentError,
    MissingApiKeyError,
    PoolStartError,
)
from ai_reviewer.ai_pool.cursor import CursorAgentLauncher
from ai_reviewer.ai_pool.cursor import launcher as launcher_module
from ai_reviewer.ai_pool.cursor import session as session_module
from ai_reviewer.properties import AgentDefinition
from ai_reviewer.run_dir import RunDirs

TEXT = "Первый абзац.\nВторой абзац.\n"


def make_property(tmp_path, name, reference=True):
    props = tmp_path / "props"
    (props / name).mkdir(parents=True)
    (props / "IO-structure.md").write_text("IO-MARKER", encoding="utf-8")
    (props / name / "instruction.md").write_text(f"INSTR-{name}", encoding="utf-8")
    if reference:
        (props / name / "reference.md").write_text(f"REF-{name}", encoding="utf-8")
    return AgentDefinition(name, props / "IO-structure.md", props / name / "instruction.md", props / name / "reference.md")


class FakeSession:
    def __init__(self, launcher, run_dir):
        self.launcher, self.run_dir = launcher, run_dir

    def prompt(self, property_id, prompt):
        self.launcher.calls.append(SimpleNamespace(id=property_id, prompt=prompt, run_dir=self.run_dir))
        self.launcher.behaviors[property_id](self.run_dir, property_id)


class FakeLauncher:
    def __init__(self, behaviors=None, missing_key=False, bridge_fails=False):
        self.behaviors, self.calls = behaviors or {}, []
        self.missing_key, self.bridge_fails = missing_key, bridge_fails

    def check(self):
        if self.missing_key:
            raise MissingApiKeyError("CURSOR_API_KEY is not set")

    @contextlib.contextmanager
    def connect(self, run_dir):
        if self.bridge_fails:
            raise BridgeLaunchError("no bridge")
        yield FakeSession(self, run_dir)


def make_pool(tmp_path, launcher, missing_reference=()):
    pool = AIPool(launcher, RunDirs())
    for name in launcher.behaviors:
        pool.add_agent(make_property(tmp_path, name, reference=name not in missing_reference))
    return pool


def write(content):
    return lambda run_dir, name: (run_dir / f"{name}.json").write_text(content, encoding="utf-8")


def silent(run_dir, name):
    pass


def fails(run_dir, name):
    raise AgentRunError("run status: error")


def test_happy_path_runs_agents_in_parallel(tmp_path):
    names = ["alpha", "beta", "gamma"]
    barrier = threading.Barrier(3, timeout=5)

    def behave(run_dir, name):
        barrier.wait()
        write("[]")(run_dir, name)

    launcher = FakeLauncher({name: behave for name in names})
    result = make_pool(tmp_path, launcher).execute(TEXT, tmp_path / "out")

    run_dir = result.run_dir
    assert run_dir == (tmp_path / "out" / "1").resolve()
    assert list(result.statuses) == names
    assert all(status.ok for status in result.statuses.values())
    assert (run_dir / "article.txt").read_bytes() == TEXT.encode("utf-8")
    assert sorted(p.name for p in run_dir.iterdir()) == ["alpha.json", "article.txt", "beta.json", "gamma.json"]
    for call in launcher.calls:
        assert call.run_dir == run_dir
        markers = ["IO-MARKER", f"INSTR-{call.id}", f"REF-{call.id}", f"file {run_dir.as_posix()}/article.txt.", f"file {run_dir.as_posix()}/{call.id}.json,"]
        for marker in markers:
            assert marker in call.prompt


def test_failed_agents_do_not_stop_others(tmp_path):
    launcher = FakeLauncher({
        "errored": fails,
        "silent": silent,
        "broken": write("{not json"),
        "object": write("{}"),
        "noref": write("[]"),
        "good": write("[]"),
    })

    result = make_pool(tmp_path, launcher, missing_reference=["noref"]).execute(TEXT, tmp_path / "out")

    assert result.statuses["good"].ok is True
    assert (result.run_dir / "good.json").is_file()
    for name, status in result.statuses.items():
        if name != "good":
            assert status.ok is False and status.reason, name
            assert not (result.run_dir / f"{name}.json").exists(), name
    reasons = {name: status.reason for name, status in result.statuses.items()}
    assert reasons["errored"] == "run status: error"
    assert reasons["silent"] == "silent.json not written"
    assert reasons["broken"].startswith("invalid JSON: ")
    assert reasons["object"] == "JSON root is not an array"
    assert reasons["noref"].startswith("cannot read property docs: ")


def test_run_dirs_are_numbered_after_max(tmp_path):
    out = tmp_path / "out"
    for d in ["1", "7", "x"]:
        (out / d).mkdir(parents=True)
    (out / "7" / "keep.txt").write_text("old", encoding="utf-8")
    (out / "3.txt").write_text("", encoding="utf-8")
    pool = make_pool(tmp_path, FakeLauncher({"alpha": write("[]")}))

    assert pool.execute(TEXT, out).run_dir.name == "8"
    assert pool.execute(TEXT, out).run_dir.name == "9"
    assert (out / "7" / "keep.txt").read_text(encoding="utf-8") == "old"


@pytest.mark.parametrize("case", ["no agents", "no key", "output is file", "bridge fails"])
def test_execute_start_errors(tmp_path, case):
    if case == "output is file":
        (tmp_path / "out").write_text("", encoding="utf-8")
    behaviors = {} if case == "no agents" else {"alpha": write("[]")}
    launcher = FakeLauncher(behaviors, missing_key=case == "no key", bridge_fails=case == "bridge fails")
    pool = make_pool(tmp_path, launcher)

    with pytest.raises(PoolStartError):
        pool.execute(TEXT, tmp_path / "out")
    if case == "bridge fails":
        assert not (tmp_path / "out" / "1").exists()


def test_cursor_launcher_adapter(tmp_path, monkeypatch):
    calls, outcomes = [], iter(["finished", "error", CursorAgentError("boom", request_id="r1")])

    def prompt(prompt, options, client):
        calls.append(options)
        outcome = next(outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(id="r", status=outcome)

    bridge = SimpleNamespace(launch_bridge=lambda workspace: contextlib.nullcontext("client"))
    monkeypatch.setattr(launcher_module, "CursorClient", bridge)
    monkeypatch.setattr(session_module, "Agent", SimpleNamespace(prompt=prompt))
    monkeypatch.setenv("CURSOR_API_KEY", "key")
    launcher = CursorAgentLauncher("model")

    with launcher.connect(tmp_path) as session:
        session.prompt("alpha", "p")
        with pytest.raises(AgentRunError, match="^run status: error$"):
            session.prompt("alpha", "p")
        with pytest.raises(AgentRunError, match="^prompt failed: CursorAgentError"):
            session.prompt("alpha", "p")
    options = calls[0]
    assert (options.model, options.api_key, options.local.cwd) == ("model", "key", str(tmp_path))
    assert options.agent_id.startswith("agent-") and options.agent_id != calls[1].agent_id
    monkeypatch.setenv("CURSOR_API_KEY", " ")
    with pytest.raises(MissingApiKeyError):
        launcher.check()


def test_add_agent_rejects_duplicate_id(tmp_path):
    pool = make_pool(tmp_path, FakeLauncher({"alpha": write("[]")}))
    agent = AgentDefinition("alpha", tmp_path / "io", tmp_path / "instruction", tmp_path / "reference")

    with pytest.raises(DuplicateAgentError):
        pool.add_agent(agent)
