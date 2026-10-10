from dataclasses import dataclass, field


@dataclass
class Chapter:
    """One chapter of the article."""

    name: str  # chapter id
    paragraphs: list[str] = field(default_factory=list)
