from pathlib import Path

from ai_reviewer.properties import AgentDefinition

from .context import AgentRunContext
from .errors import PropertyDocsError

PROMPT = """You are a reviewer of a scientific article with respect to the academic quality property "{name}".
Read the annotated article text from the file {article}.
Evaluate it according to the instructions and reference guide below.
Write the result only to the file {output}, strictly following the format specified in the IO-structure.md section.
Do not create or modify any other files.

# File IO-structure.md
{io}

# File instruction.md
{instruction}

# File reference.md
{reference}
"""


class PromptBuilder:
    """Fills the review prompt with the property docs of an agent."""

    def build(self, agent: AgentDefinition, context: AgentRunContext) -> str:
        """
        Fill the review prompt with the agent's property docs.

        :param agent: agent whose docs go into the prompt
        :param context: article and output file of the agent in the run

        :raises PropertyDocsError: when a docs file cannot be read as UTF-8

        :return: prompt text
        """
        return PROMPT.format(
            name=agent.id,
            article=context.article.as_posix(),
            output=context.output.as_posix(),
            io=self._read(agent.io_structure),
            instruction=self._read(agent.instruction),
            reference=self._read(agent.reference),
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
