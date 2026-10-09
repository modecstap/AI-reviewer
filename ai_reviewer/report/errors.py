class ReportError(Exception):
    """The report of a run dir cannot be built."""


class RunDirReadError(ReportError):
    """The run dir or its ``article.txt`` cannot be read."""


class ReportWriteError(ReportError):
    """``report.json`` cannot be written."""
