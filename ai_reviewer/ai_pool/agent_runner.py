import logging
from pathlib import Path

from cursor_sdk import Agent, CursorAgentError

from .agent_output_validator import AgentOutputValidator
from .cursor_agent_factory import CursorAgentFactory
from .entities import AgentDefinition, AgentRunContext, AgentStatus
from .errors import PropertyDocsError
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class AgentRunner:
    """Runs one review agent and reports its status."""

    def __init__(
        self,
        factory: CursorAgentFactory,
        prompts: PromptBuilder | None = None,
        validator: AgentOutputValidator | None = None,
    ) -> None:
        """
        Set up the runner.

        :param factory: factory of the agent options
        :param prompts: review prompt builder; default one when omitted
        :param validator: agent output validator; default one when omitted
        """
        self._factory = factory
        self._prompts = prompts or PromptBuilder()
        self._validator = validator or AgentOutputValidator()

    def run(
        self, agent: AgentDefinition, context: AgentRunContext
    ) -> AgentStatus:
        """
        Run one agent and check its output; remove the output on failure.

        Called in parallel from many threads, so it keeps no state.

        :param agent: agent to run
        :param context: run dir, API key and bridge client of the run

        :return: ok status, or failed status with the reason
        """
        output = context.run_dir / f"{agent.name}.json"
        reason = self._prompt_agent(agent, context)
        if reason is None:
            reason = self._validator.check(output)
        if reason is None:
            return AgentStatus(ok=True)
        logger.warning("agent %s failed: %s", agent.name, reason)
        self._remove_output(agent.name, output)
        return AgentStatus(ok=False, reason=reason)

    def _prompt_agent(
        self, agent: AgentDefinition, context: AgentRunContext
    ) -> str | None:
        """
        Send the review prompt to a new Cursor agent and wait for its run.

        :param agent: agent to prompt
        :param context: run dir, API key and bridge client of the run

        :return: why the run failed, or ``None`` when it finished
        """
        try:
            prompt = self._prompts.build(agent, context.run_dir)
        except PropertyDocsError as error:
            return f"cannot read property docs: {error}"
        options = self._factory.options(context.run_dir, context.api_key)
        agent_id = options.agent_id
        logger.info("agent %s starting, agent_id=%s", agent.name, agent_id)
        try:
            result = Agent.prompt(prompt, options, client=context.client)
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
