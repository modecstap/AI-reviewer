import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PropertyClaimsReader:
    """Reads the raw claim arrays of property files."""

    def read(self, files: list[Path]) -> dict[str, list[object]]:
        """
        Read the claim array of every property file; skip broken files.

        A broken file only loses its own claims, not the whole report.

        :param files: property files ``<property>.json``

        :return: claim array by property name, in ``files`` order
        """
        claims: dict[str, list[object]] = {}
        for path in files:
            array = self._array_of(path)
            if array is not None:
                claims[path.stem] = array
        return claims

    @staticmethod
    def _array_of(path: Path) -> list[object] | None:
        """
        Read the JSON array of one property file; log why it is skipped.

        :param path: property file

        :return: the array, or ``None`` when the file is skipped
        """
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            logger.warning("skip property file %s: %s", path.name, error)
            return None
        if not isinstance(data, list):
            logger.warning(
                "skip property file %s: JSON root is not an array", path.name
            )
            return None
        return data
