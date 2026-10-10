from typing import Protocol


class AgentSession(Protocol):
    """Connection to the agent backend shared by the agents of one run."""

    def prompt(self, property_id: str, prompt: str) -> None:
        """
        Run a new agent on the prompt and wait until its run ends.

        Called in parallel from many threads.

        :param property_id: property the agent reviews
        :param prompt: review prompt

        :raises AgentRunError: when the run fails or does not finish; the
            message is the reason
        """
        ...
