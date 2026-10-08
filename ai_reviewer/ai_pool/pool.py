import json
import logging
import os
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from functools import partial
from pathlib import Path

from cursor_sdk import (
    Agent,
    AgentOptions,
    CursorAgentError,
    CursorClient,
    LocalAgentOptions,
)

from .entities import AgentDefinition, AgentStatus, PoolResult
from .errors import (
    BridgeLaunchError,
    DuplicateAgentError,
    MissingApiKeyError,
    NoAgentsError,
    OutputDirMismatchError,
    RunDirError,
)
from .prompt import PROMPT

logger = logging.getLogger(__name__)


class AIPool:
    """Pool of review agents, one per property, run together on one article."""

    def __init__(self, model: str = "composer-2.5") -> None:
        """
        Set up an empty pool.

        :param model: Cursor model id every agent runs on
        """
        self._model = model
        self._agents: list[AgentDefinition] = []
        self._output_dir: Path | None = None

    def add_agent(
        self, IO: str, docs: str, name: str, output_dir: str
    ) -> None:
        """
        Register the review agent of one property.

        :param IO: path to ``IO-structure.md`` with the output format
        :param docs: property dir with ``instruction.md`` and ``reference.md``
        :param name: property id; the agent writes ``{name}.json``
        :param output_dir: dir of numbered run dirs, shared by all agents

        :raises DuplicateAgentError: when ``name`` is already registered
        :raises OutputDirMismatchError: when ``output_dir`` differs from the
            output dir of the agents added before
        """
        if any(agent.name == name for agent in self._agents):
            raise DuplicateAgentError(f"agent {name!r} is already registered")
        new_output_dir = Path(output_dir)
        if self._output_dir is None:
            self._output_dir = new_output_dir
        elif new_output_dir.resolve() != self._output_dir.resolve():
            raise OutputDirMismatchError(
                f"output_dir {output_dir!r} differs from "
                f"{str(self._output_dir)!r}"
            )
        self._agents.append(AgentDefinition(Path(IO), Path(docs), name))

    def execute(self, text: str) -> PoolResult:
        """
        Run every registered agent on the article in a new run dir.

        A failed agent does not stop the others; its status says why it failed.

        :param text: marked-up article text the agents review

        :raises NoAgentsError: when no agents are registered
        :raises MissingApiKeyError: when ``CURSOR_API_KEY`` is not set
        :raises RunDirError: when the run dir cannot be prepared
        :raises BridgeLaunchError: when the Cursor bridge cannot start

        :return: run dir and the status of every agent by name
        """
        if not self._agents:
            raise NoAgentsError("no agents registered")
        api_key = self._api_key()
        run_dir = self._next_run_dir()
        self._create_run_dir(run_dir, text)
        try:
            statuses = self._run_agents(run_dir, api_key)
        except Exception:
            self._remove_run_dir(run_dir)
            raise
        return PoolResult(run_dir, statuses)

    @staticmethod
    def _api_key() -> str:
        """
        Read the Cursor API key from the environment.

        :raises MissingApiKeyError: when ``CURSOR_API_KEY`` is unset or blank

        :return: the API key
        """
        api_key = os.environ.get("CURSOR_API_KEY", "")
        if not api_key.strip():
            raise MissingApiKeyError("CURSOR_API_KEY is not set")
        return api_key

    def _next_run_dir(self) -> Path:
        """
        Pick the run dir after the highest numbered one in the output dir.

        :raises RunDirError: when the output dir cannot be listed

        :return: ``{output_dir}/{max N + 1}``; ``1`` for the first run
        """
        output_dir = self._output_dir.resolve()
        if not output_dir.is_dir():
            return output_dir / "1"
        try:
            names = [
                path.name for path in output_dir.iterdir() if path.is_dir()
            ]
        except OSError as error:
            raise RunDirError(f"cannot list {output_dir}: {error}") from error
        numbers = [
            int(name) for name in names if name.isascii() and name.isdigit()
        ]
        return output_dir / str(max(numbers, default=0) + 1)

    def _create_run_dir(self, run_dir: Path, text: str) -> None:
        """
        Create the run dir with ``article.txt``; remove it if writing fails.

        :param run_dir: run dir to create; must not exist
        :param text: article text to write into ``article.txt``

        :raises RunDirError: when the dir or ``article.txt`` cannot be written
        """
        try:
            run_dir.mkdir(parents=True)
        except OSError as error:
            raise RunDirError(f"cannot create {run_dir}: {error}") from error
        article = run_dir / "article.txt"
        try:
            article.write_text(text, encoding="utf-8", newline="")
        except OSError as error:
            self._remove_run_dir(run_dir)
            raise RunDirError(f"cannot write {article}: {error}") from error

    @staticmethod
    def _remove_run_dir(run_dir: Path) -> None:
        """
        Remove the run dir of a failed run; only log if removal fails.

        The caller re-raises the original error, which must not be replaced.

        :param run_dir: run dir to remove
        """
        try:
            shutil.rmtree(run_dir)
        except OSError as error:
            logger.warning("cannot remove run dir %s: %s", run_dir, error)

    def _run_agents(
        self, run_dir: Path, api_key: str
    ) -> dict[str, AgentStatus]:
        """
        Run all agents in parallel through one Cursor bridge.

        :param run_dir: run dir the agents work in
        :param api_key: Cursor API key

        :raises BridgeLaunchError: when the Cursor bridge cannot start

        :return: status of every agent by name, in registration order
        """
        with ExitStack() as stack:
            client = self._launch_bridge(stack, run_dir)
            run_agent = partial(
                self._run_agent,
                run_dir=run_dir,
                api_key=api_key,
                client=client,
            )
            workers = len(self._agents)
            with ThreadPoolExecutor(max_workers=workers) as executor:
                statuses = list(executor.map(run_agent, self._agents))
        names = [agent.name for agent in self._agents]
        return dict(zip(names, statuses))

    @staticmethod
    def _launch_bridge(stack: ExitStack, run_dir: Path) -> CursorClient:
        """
        Launch the Cursor bridge for the run dir; ``stack`` closes it.

        :param stack: exit stack that owns the bridge
        :param run_dir: workspace of the bridge

        :raises BridgeLaunchError: when the Cursor bridge cannot start

        :return: client connected to the bridge
        """
        try:
            return stack.enter_context(
                CursorClient.launch_bridge(workspace=str(run_dir))
            )
        except (CursorAgentError, OSError) as error:
            raise BridgeLaunchError(
                f"cannot launch Cursor bridge: {error}"
            ) from error

    def _run_agent(
        self,
        agent: AgentDefinition,
        run_dir: Path,
        api_key: str,
        client: CursorClient,
    ) -> AgentStatus:
        """
        Run one agent and check its output; remove the output on failure.

        :param agent: agent to run
        :param run_dir: run dir the agent works in
        :param api_key: Cursor API key
        :param client: client connected to the Cursor bridge

        :return: ok status, or failed status with the reason
        """
        output = run_dir / f"{agent.name}.json"
        reason = self._prompt_agent(agent, run_dir, api_key, client)
        if reason is None:
            reason = self._check_output(output)
        if reason is None:
            return AgentStatus(ok=True)
        logger.warning("agent %s failed: %s", agent.name, reason)
        self._remove_output(agent.name, output)
        return AgentStatus(ok=False, reason=reason)

    def _prompt_agent(
        self,
        agent: AgentDefinition,
        run_dir: Path,
        api_key: str,
        client: CursorClient,
    ) -> str | None:
        """
        Send the review prompt to a new Cursor agent and wait for its run.

        :param agent: agent to prompt
        :param run_dir: run dir the agent works in
        :param api_key: Cursor API key
        :param client: client connected to the Cursor bridge

        :return: why the run failed, or ``None`` when it finished
        """
        try:
            prompt = self._build_prompt(agent, run_dir)
        except (OSError, UnicodeDecodeError) as error:
            return f"cannot read property docs: {error}"
        options = self._agent_options(run_dir, api_key)
        agent_id = options.agent_id
        logger.info("agent %s starting, agent_id=%s", agent.name, agent_id)
        try:
            result = Agent.prompt(prompt, options, client=client)
        except CursorAgentError as error:
            logger.warning(
                "agent %s (agent_id=%s) raised %s, request_id=%s",
                agent.name, agent_id, error, error.request_id,
            )
            return f"prompt failed: {type(error).__name__}: {error}"
        logger.info(
            "agent %s done, agent_id=%s, run_id=%s, status=%s",
            agent.name, agent_id, result.id, result.status,
        )
        if result.status != "finished":
            return f"run status: {result.status}"
        return None

    def _agent_options(self, run_dir: Path, api_key: str) -> AgentOptions:
        """
        Build the options of a new local agent with a fresh agent id.

        :param run_dir: run dir the agent works in
        :param api_key: Cursor API key

        :return: options for ``Agent.prompt``
        """
        return AgentOptions(
            model=self._model,
            api_key=api_key,
            agent_id=f"agent-{uuid.uuid4()}",
            local=LocalAgentOptions(cwd=str(run_dir)),
        )

    @staticmethod
    def _build_prompt(agent: AgentDefinition, run_dir: Path) -> str:
        """
        Fill the review prompt with the agent's property docs.

        :param agent: agent whose docs go into the prompt
        :param run_dir: run dir the agent works in

        :raises OSError: when a docs file cannot be read
        :raises UnicodeDecodeError: when a docs file is not UTF-8

        :return: prompt text
        """
        return PROMPT.format(
            name=agent.name,
            run_dir=run_dir.as_posix(),
            io=agent.io_structure.read_text(encoding="utf-8"),
            instruction=(agent.docs / "instruction.md").read_text(
                encoding="utf-8"
            ),
            reference=(agent.docs / "reference.md").read_text(
                encoding="utf-8"
            ),
        )

    @staticmethod
    def _check_output(output: Path) -> str | None:
        """
        Check that the agent wrote a JSON array.

        :param output: agent output file

        :return: why the output is a failure, or ``None`` when it is valid
        """
        if not output.is_file():
            return f"{output.name} not written"
        try:
            data = json.loads(output.read_text(encoding="utf-8"))
        except OSError as error:
            return f"cannot read {output.name}: {error}"
        except ValueError as error:
            return f"invalid JSON: {error}"
        if not isinstance(data, list):
            return "JSON root is not an array"
        return None

    @staticmethod
    def _remove_output(agent_name: str, output: Path) -> None:
        """
        Remove the output of a failed agent; only log if removal fails.

        One failed removal must not stop the other agents.

        :param agent_name: name of the failed agent
        :param output: agent output file
        """
        try:
            output.unlink(missing_ok=True)
        except OSError as error:
            logger.warning(
                "agent %s: cannot remove %s: %s", agent_name, output, error
            )
