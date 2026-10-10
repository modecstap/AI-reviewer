from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ai_reviewer.properties import AgentDefinition

from .agent import AgentRunContext, AgentRunner, AgentSession, AgentStatus
from .errors import NoAgentsError, RunDirError
from .launcher import AgentLauncher
from .registry import AgentRegistry
from .result import PoolResult
from .run_dirs import RunDirLayout


class AIPool:
    """Pool of review agents, one per property, run together on one article."""

    def __init__(
        self,
        launcher: AgentLauncher,
        run_dirs: RunDirLayout,
        registry: AgentRegistry | None = None,
        runner: AgentRunner | None = None,
    ) -> None:
        """
        Set up an empty pool.

        :param launcher: launcher of the agent backend
        :param run_dirs: layout of the numbered run dirs
        :param registry: agent registry; default one when omitted
        :param runner: agent runner; default one when omitted
        """
        self._launcher = launcher
        self._run_dirs = run_dirs
        self._registry = registry or AgentRegistry()
        self._runner = runner or AgentRunner()

    def add_agent(self, definition: AgentDefinition) -> None:
        """
        Register the review agent of one property.

        :param definition: agent definition to register

        :raises DuplicateAgentError: when ``definition.id`` is already
            registered
        """
        self._registry.add(definition)

    def execute(self, text: str, output_dir: Path) -> PoolResult:
        """
        Run every registered agent on the article in a new run dir.

        A failed agent does not stop the others; its status says why it failed.

        :param text: marked-up article text the agents review
        :param output_dir: dir of numbered run dirs

        :raises NoAgentsError: when no agents are registered
        :raises MissingApiKeyError: when the backend API key is not set
        :raises RunDirError: when the run dir cannot be prepared
        :raises BridgeLaunchError: when the agent backend cannot start

        :return: run dir and the status of every agent by property id
        """
        agents = self._registry.agents
        if not agents:
            raise NoAgentsError("no agents registered")
        self._launcher.check()
        run_dir = self._create_run_dir(output_dir, text)
        try:
            statuses = self._run_agents(agents, run_dir)
        except Exception:
            self._run_dirs.remove(run_dir)
            raise
        return PoolResult(run_dir, statuses)

    def _create_run_dir(self, output_dir: Path, text: str) -> Path:
        """
        Create the next run dir with the article.

        :param output_dir: dir of numbered run dirs
        :param text: marked-up article text

        :raises RunDirError: when the run dir cannot be created or filled

        :return: the new run dir
        """
        try:
            return self._run_dirs.create(output_dir, text)
        except OSError as error:
            raise RunDirError(
                f"cannot create a run dir in {output_dir}: {error}"
            ) from error

    def _run_agents(
        self, agents: tuple[AgentDefinition, ...], run_dir: Path
    ) -> dict[str, AgentStatus]:
        """
        Run all agents in parallel through one backend session.

        :param agents: agents to run
        :param run_dir: run dir the agents work in

        :raises BridgeLaunchError: when the agent backend cannot start

        :return: status of every agent by property id, in registration order
        """
        with self._launcher.connect(run_dir) as session:
            contexts = self._contexts(agents, run_dir, session)
            with ThreadPoolExecutor(max_workers=len(agents)) as executor:
                statuses = list(
                    executor.map(self._runner.run, agents, contexts)
                )
        ids = [agent.id for agent in agents]
        return dict(zip(ids, statuses))

    def _contexts(
        self,
        agents: tuple[AgentDefinition, ...],
        run_dir: Path,
        session: AgentSession,
    ) -> list[AgentRunContext]:
        """
        Build the run context of every agent.

        :param agents: agents to run
        :param run_dir: run dir the agents work in
        :param session: backend session shared by the agents

        :return: contexts in the order of ``agents``
        """
        return [
            AgentRunContext(
                self._run_dirs.article_file(run_dir),
                self._run_dirs.property_file(run_dir, agent.id),
                session,
            )
            for agent in agents
        ]
