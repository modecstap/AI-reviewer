from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

from cursor_sdk import ModelSelection

from .agent import (
    AgentDefinition,
    AgentRegistry,
    AgentRunContext,
    AgentRunner,
    AgentStatus,
)
from .cursor import CursorAgentFactory, CursorBridge
from .errors import NoAgentsError
from .result import PoolResult
from .run_dirs import RunDirs


class AIPool:
    """Pool of review agents, one per property, run together on one article."""

    def __init__(
        self,
        model: ModelSelection,
        registry: AgentRegistry | None = None,
        run_dirs: RunDirs | None = None,
        factory: CursorAgentFactory | None = None,
        bridge: CursorBridge | None = None,
        runner: AgentRunner | None = None,
    ) -> None:
        """
        Set up an empty pool.

        :param model: Cursor model id every agent runs on; ignored when
            ``factory`` is given
        :param registry: agent registry; default one when omitted
        :param run_dirs: run dirs; default one when omitted
        :param factory: agent options factory; default one when omitted
        :param bridge: Cursor bridge; default one when omitted
        :param runner: agent runner; default one with ``factory`` when omitted
        """
        self._registry = registry or AgentRegistry()
        self._run_dirs = run_dirs or RunDirs()
        self._factory = factory or CursorAgentFactory(model)
        self._bridge = bridge or CursorBridge()
        self._runner = runner or AgentRunner(self._factory)

    def add_agent(
        self, definition: AgentDefinition, output_dir: Path
    ) -> None:
        """
        Register the review agent of one property.

        :param definition: agent definition to register
        :param output_dir: dir of numbered run dirs, shared by all agents

        :raises DuplicateAgentError: when ``name`` is already registered
        :raises OutputDirMismatchError: when ``output_dir`` differs from the
            output dir of the agents added before
        """
        self._registry.add(definition, output_dir)

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
        agents = self._registry.agents
        if not agents:
            raise NoAgentsError("no agents registered")
        api_key = self._factory.api_key()
        run_dir = self._run_dirs.next_run_dir(self._registry.output_dir)
        self._run_dirs.create(run_dir, text)
        try:
            statuses = self._run_agents(agents, run_dir, api_key)
        except Exception:
            self._run_dirs.remove(run_dir)
            raise
        return PoolResult(run_dir, statuses)

    def _run_agents(
        self,
        agents: tuple[AgentDefinition, ...],
        run_dir: Path,
        api_key: str,
    ) -> dict[str, AgentStatus]:
        """
        Run all agents in parallel through one Cursor bridge.

        :param agents: agents to run
        :param run_dir: run dir the agents work in
        :param api_key: Cursor API key

        :raises BridgeLaunchError: when the Cursor bridge cannot start

        :return: status of every agent by name, in registration order
        """
        with self._bridge.connect(run_dir) as client:
            context = AgentRunContext(run_dir, api_key, client)
            run_agent = partial(self._runner.run, context=context)
            workers = len(agents)
            with ThreadPoolExecutor(max_workers=workers) as executor:
                statuses = list(executor.map(run_agent, agents))
        names = [agent.name for agent in agents]
        return dict(zip(names, statuses))
