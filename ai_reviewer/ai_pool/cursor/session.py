import dataclasses
import logging
import uuid

from cursor_sdk import Agent, AgentOptions, CursorAgentError, CursorClient

from .. import AgentRunError

logger = logging.getLogger(__name__)


class CursorAgentSession:
    """Runs local Cursor agents of one run through its bridge client."""

    def __init__(self, client: CursorClient, options: AgentOptions) -> None:
        """
        Set up the session.

        :param client: client connected to the bridge of the run
        :param options: options shared by every agent of the run
        """
        self._client = client
        self._options = options

    def prompt(self, property_id: str, prompt: str) -> None:
        """
        Run a new Cursor agent on the prompt and wait until its run ends.

        Called in parallel from many threads, so it keeps no state.

        :param property_id: property the agent reviews
        :param prompt: review prompt

        :raises AgentRunError: when the prompt fails or the run does not
            finish; the message is the reason
        """
        agent_id = f"agent-{uuid.uuid4()}"
        options = dataclasses.replace(self._options, agent_id=agent_id)
        logger.info("agent %s starting, agent_id=%s", property_id, agent_id)
        try:
            result = Agent.prompt(prompt, options, client=self._client)
        except CursorAgentError as error:
            logger.warning(
                "agent %s (agent_id=%s) raised %s, request_id=%s",
                property_id, agent_id, error, error.request_id,
            )
            raise AgentRunError(
                f"prompt failed: {type(error).__name__}: {error}"
            ) from error
        logger.info(
            "agent %s done, agent_id=%s, run_id=%s, status=%s",
            property_id, agent_id, result.id, result.status,
        )
        if result.status != "finished":
            raise AgentRunError(f"run status: {result.status}")
