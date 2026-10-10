from pathlib import Path

from ai_reviewer.claims import ClaimsFormatError, ClaimsParser


class AgentOutputValidator:
    """Checks that an agent wrote its findings as a property file."""

    def check(self, output: Path) -> str | None:
        """
        Check that the agent wrote a valid property file.

        :param output: agent output file

        :return: why the output is a failure, or ``None`` when it is valid
        """
        if not output.is_file():
            return f"{output.name} not written"
        try:
            text = output.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            return f"invalid JSON: {error}"
        except OSError as error:
            return f"cannot read {output.name}: {error}"
        try:
            ClaimsParser().check(text)
        except ClaimsFormatError as error:
            return str(error)
        return None
