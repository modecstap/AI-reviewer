import re

from .chapter import CHAPTERS_FILE, NO_HEADING


class ChapterNamer:
    """Turns chapter titles into unique, filesystem-safe folder names."""

    FORBIDDEN_CHARACTERS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
    RESERVED_NAMES = frozenset({
        "CON", "PRN", "AUX", "NUL",
        *(f"{prefix}{number}"
          for prefix in ("COM", "LPT") for number in range(1, 10)),
    })
    MAX_LENGTH = 100

    def folder_name(self, title: str) -> str:
        """
        Build a folder name valid on Windows and POSIX from a title.

        :param title: chapter title

        :return: folder name, `NO_HEADING` when nothing usable is left
        """
        name = self.FORBIDDEN_CHARACTERS.sub("_", title).rstrip(". ")
        name = name[:self.MAX_LENGTH].rstrip(". ") or NO_HEADING
        if name.upper() in self.RESERVED_NAMES:
            name += "_"
        return name

    def unique_names(self, names: list[str]) -> list[str]:
        """
        Suffix repeated names with ` (2)`, ` (3)`, ...

        Comparison ignores case because Windows folders do.

        :param names: folder names in document order

        :return: unique names, also distinct from `CHAPTERS_FILE`
        """
        used = {CHAPTERS_FILE.casefold()}
        unique = []
        for name in names:
            candidate, number = name, 2
            while candidate.casefold() in used:
                candidate, number = f"{name} ({number})", number + 1
            used.add(candidate.casefold())
            unique.append(candidate)
        return unique
