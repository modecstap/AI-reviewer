from dataclasses import dataclass, field

from ai_reviewer.claims import Claim


@dataclass(frozen=True)
class ReportParagraph:
    """A paragraph with its text and its claims by property id."""

    number: int
    text: str
    claims: dict[str, list[Claim]] = field(default_factory=dict)


@dataclass(frozen=True)
class ReportChapter:
    """A chapter with its paragraphs that have claims."""

    name: str
    paragraphs: list[ReportParagraph] = field(default_factory=list)
