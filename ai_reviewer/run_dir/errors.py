class RunDirReadError(Exception):
    """The run dir, ``article.txt`` or ``report.json`` cannot be read."""


class RunDirWriteError(OSError):
    """
    A run dir file cannot be written.

    It is an ``OSError`` so that ``RunDirs.create`` meets the contract of the
    ``ai_pool.RunDirLayout`` port.
    """
