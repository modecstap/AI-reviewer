import json
from pathlib import Path


class AgentOutputValidator:
    """Checks that an agent wrote its findings as a JSON array."""

    def check(self, output: Path) -> str | None:
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
