from ai_reviewer.splitter import OutputWriteError


class OutputPathIsFileError(OutputWriteError):
    """The output path is occupied by a file instead of a folder."""
