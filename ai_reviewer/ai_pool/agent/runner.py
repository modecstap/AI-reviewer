import logging
from pathlib import Path

from ai_reviewer.properties import AgentDefinition

from .context import AgentRunContext
from .errors import AgentRunError, PropertyDocsError
from .output_validator import AgentOutputValidator
from .prompt import PromptBuilder
from .status import AgentStatus

logger = logging.getLogger(__name__)


class AgentRunner:
    """Runs one review agent and reports its status."""

    def __init__(
        self,
        prompts: PromptBuilder | None = None,
        validator: AgentOutputValidator | None = None,
    ) -> None:
        """
        Set up the runner.

        :param prompts: review prompt builder; default one when omitted
        :param validator: agent output validator; default one when omitted
        """
        self._prompts = prompts or PromptBuilder()
        self._validator = validator or AgentOutputValidator()

    def run(
        self, agent: AgentDefinition, context: AgentRunContext
    ) -> AgentStatus:
        """
        Run one agent and check its output; remove the output on failure.

        Called in parallel from many threads, so it keeps no state.

        :param agent: agent to run
        :param context: article, output file and session of the agent

        :return: ok status, or failed status with the reason
        """
        reason = self._prompt_agent(agent, context)
        if reason is None:
            reason = self._validator.check(context.output)
        if reason is None:
            return AgentStatus(ok=True)
        logger.warning("agent %s failed: %s", agent.id, reason)
        self._remove_output(agent.id, context.output)
        return AgentStatus(ok=False, reason=reason)

    def _prompt_agent(
        self, agent: AgentDefinition, context: AgentRunContext
    ) -> str | None:
        """
        Send the review prompt through the session and wait for the run.

        :param agent: agent to prompt
        :param context: article, output file and session of the agent

        :return: why the run failed, or ``None`` when it finished
        """
        try:
            prompt = self._prompts.build(agent, context)
        except PropertyDocsError as error:
            return f"cannot read property docs: {error}"
        try:
            context.session.prompt(agent.id, prompt)
        except AgentRunError as error:
            return str(error)
        return None

    @staticmethod
    def _remove_output(property_id: str, output: Path) -> None:
        """
        Remove the output of a failed agent; only log if removal fails.

        One failed removal must not stop the other agents.

        :param property_id: property of the failed agent
        :param output: agent output file
        """
        try:
            output.unlink(missing_ok=True)
        except OSError as error:
            logger.warning(
                "agent %s: cannot remove %s: %s", property_id, output, error
            )
