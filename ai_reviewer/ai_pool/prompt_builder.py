from pathlib import Path

from .entities import AgentDefinition
from .errors import PropertyDocsError
from .prompt import PROMPT


class PromptBuilder:
    """Fills the review prompt with the property docs of an agent."""

    def build(self, agent: AgentDefinition, run_dir: Path) -> str:
        """
        Fill the review prompt with the agent's property docs.

        :param agent: agent whose docs go into the prompt
        :param run_dir: run dir the agent works in

        :raises PropertyDocsError: when a docs file cannot be read as UTF-8

        :return: prompt text
        """
        return PROMPT.format(
            name=agent.name,
            run_dir=run_dir.as_posix(),
            io=self._read(agent.io_structure),
            instruction=self._read(agent.docs / "instruction.md"),
            reference=self._read(agent.docs / "reference.md"),
        )

    @staticmethod
    def _read(path: Path) -> str:
        """
        Read one docs file.

        :param path: docs file

        :raises PropertyDocsError: when the file cannot be read as UTF-8

        :return: file text
        """
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise PropertyDocsError(str(error)) from error
