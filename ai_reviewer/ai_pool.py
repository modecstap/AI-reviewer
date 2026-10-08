"""Run one Cursor SDK agent per academic-writing property in parallel.

Each ``execute`` writes into a new run dir ``{output_dir}/{N}/``: ``article.txt``
plus ``{name}.json`` of every agent that succeeded.
"""

import json
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path

from cursor_sdk import Agent, AgentOptions, CursorClient, LocalAgentOptions

logger = logging.getLogger(__name__)

_PROMPT = """Ты рецензент научной статьи по свойству академичности «{name}».
Прочитай размеченный текст статьи из файла {run_dir}/article.txt.
Оцени его по инструкции и справочнику ниже.
Запиши результат только в файл {run_dir}/{name}.json строго по формату из раздела IO-structure.md.
Не создавай и не изменяй другие файлы.

# Файл IO-structure.md
{io}

# Файл instruction.md
{instruction}

# Файл reference.md
{reference}
"""


class PoolStartError(Exception):
    """The run cannot start."""


@dataclass(frozen=True)
class AgentStatus:
    ok: bool
    reason: str | None = None


@dataclass(frozen=True)
class PoolResult:
    run_dir: Path
    statuses: dict[str, AgentStatus]


@dataclass(frozen=True)
class _AgentSpec:
    io: Path
    docs: Path
    name: str


class AIPool:
    """Pool of review agents, one per property, run together on one article."""

    def __init__(self, model: str = "composer-2.5") -> None:
        """
        Set up an empty pool.

        :param model: Cursor model id every agent runs on
        """
        self._model = model
        self._agents: list[_AgentSpec] = []
        self._output_dir: Path | None = None

    def add_agent(self, IO: str, docs: str, name: str, output_dir: str) -> None:
        if any(spec.name == name for spec in self._agents):
            raise ValueError(f"agent {name!r} is already registered")
        if self._output_dir is None:
            self._output_dir = Path(output_dir)
        elif Path(output_dir).resolve() != self._output_dir.resolve():
            raise ValueError(f"output_dir {output_dir!r} differs from {str(self._output_dir)!r}")
        self._agents.append(_AgentSpec(Path(IO), Path(docs), name))

    def execute(self, text: str) -> PoolResult:
        if not self._agents:
            raise PoolStartError("no agents registered")
        api_key = os.environ.get("CURSOR_API_KEY")
        if api_key is None or api_key.strip() == "":
            raise PoolStartError("CURSOR_API_KEY is not set")
        try:
            run_dir = self._next_run_dir()
            run_dir.mkdir(parents=True)
            (run_dir / "article.txt").write_text(text, encoding="utf-8", newline="")
        except OSError as err:
            raise PoolStartError(f"cannot prepare run dir: {err}") from err

        with ExitStack() as stack:
            try:
                client = stack.enter_context(CursorClient.launch_bridge(workspace=str(run_dir)))
            except Exception as err:
                raise PoolStartError(f"cannot launch Cursor bridge: {err}") from err
            with ThreadPoolExecutor(max_workers=len(self._agents)) as executor:
                statuses = list(
                    executor.map(lambda spec: self._run_agent(spec, run_dir, api_key, client), self._agents)
                )
        return PoolResult(run_dir, {spec.name: status for spec, status in zip(self._agents, statuses)})

    def _next_run_dir(self) -> Path:
        output_dir = self._output_dir.resolve()
        numbers = [0]
        if output_dir.is_dir():
            numbers += [
                int(p.name) for p in output_dir.iterdir() if p.is_dir() and p.name.isascii() and p.name.isdigit()
            ]
        return output_dir / str(max(numbers) + 1)

    def _run_agent(self, spec: _AgentSpec, run_dir: Path, api_key: str, client: CursorClient) -> AgentStatus:
        agent_id = f"agent-{uuid.uuid4()}"
        output = run_dir / f"{spec.name}.json"
        try:
            reason = self._prompt_agent(spec, run_dir, api_key, client, agent_id) or _check_output(output)
        except Exception as err:
            reason = f"{type(err).__name__}: {err}"
        if reason is None:
            return AgentStatus(ok=True)
        logger.warning("agent %s failed: %s", spec.name, reason)
        try:
            output.unlink(missing_ok=True)
        except OSError as err:
            logger.warning("agent %s: cannot remove %s: %s", spec.name, output, err)
        return AgentStatus(ok=False, reason=reason)

    def _prompt_agent(
        self, spec: _AgentSpec, run_dir: Path, api_key: str, client: CursorClient, agent_id: str
    ) -> str | None:
        prompt = _build_prompt(spec, run_dir)
        options = AgentOptions(
            model=self._model, api_key=api_key, agent_id=agent_id, local=LocalAgentOptions(cwd=str(run_dir))
        )
        logger.info("agent %s starting, agent_id=%s", spec.name, agent_id)
        try:
            result = Agent.prompt(prompt, options, client=client)
        except Exception as err:
            logger.warning(
                "agent %s (agent_id=%s) raised %s, request_id=%s",
                spec.name, agent_id, err, getattr(err, "request_id", None),
            )
            raise
        logger.info("agent %s done, agent_id=%s, run_id=%s, status=%s", spec.name, agent_id, result.id, result.status)
        if result.status != "finished":
            return f"run status: {result.status}"
        return None


def _build_prompt(spec: _AgentSpec, run_dir: Path) -> str:
    return _PROMPT.format(
        name=spec.name,
        run_dir=run_dir.as_posix(),
        io=spec.io.read_text(encoding="utf-8"),
        instruction=(spec.docs / "instruction.md").read_text(encoding="utf-8"),
        reference=(spec.docs / "reference.md").read_text(encoding="utf-8"),
    )


def _check_output(path: Path) -> str | None:
    """Return why the agent output is a failure, or ``None`` when it is valid."""
    if not path.is_file():
        return f"{path.name} not written"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as err:
        return f"invalid JSON: {err}"
    if not isinstance(data, list):
        return "JSON root is not an array"
    return None
