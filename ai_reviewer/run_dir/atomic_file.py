import logging
import os
from pathlib import Path

from .errors import RunDirWriteError

logger = logging.getLogger(__name__)


class AtomicFile:
    """Writes a file through a temporary file, so readers never see half."""

    def write(self, path: Path, content: str | bytes) -> None:
        """
        Write the file atomically; replace the previous one.

        :param path: target file path
        :param content: text, written as UTF-8, or raw bytes

        :raises RunDirWriteError: when the file cannot be written
        """
        temporary = path.with_name(path.name + ".tmp")
        try:
            if isinstance(content, bytes):
                temporary.write_bytes(content)
            else:
                temporary.write_text(content, encoding="utf-8", newline="")
            os.replace(temporary, path)
        except OSError as error:
            try:
                temporary.unlink(missing_ok=True)
            except OSError as cleanup_error:
                logger.warning("cannot remove %s: %s", temporary, cleanup_error)
            raise RunDirWriteError(f"cannot write {path}: {error}") from error
