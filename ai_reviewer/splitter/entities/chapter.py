from dataclasses import dataclass, field

NO_HEADING = "Без заголовка"
CHAPTERS_FILE = "chapters.json"


@dataclass
class Chapter:
    """One chapter of the article and the folder it is written to."""

    name: str  # folder name = chapter id
    title: str | None  # whitespace-normalized heading text; None for NO_HEADING
    paragraphs: list[str] = field(default_factory=list)
