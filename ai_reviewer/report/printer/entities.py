from dataclasses import dataclass, field


@dataclass(frozen=True)
class ClaimType:
    """Type of a claim; each part is ``None`` when absent."""

    number: str | None
    name: str | None


@dataclass(frozen=True)
class Claim:
    """One claim of a property; text fields are ``None`` when absent."""

    quote: str | None
    problem: str | None
    types: list[ClaimType] = field(default_factory=list)


@dataclass(frozen=True)
class PrintedParagraph:
    """A paragraph with its text and its claims by property name."""

    number: int
    text: str
    claims: dict[str, list[Claim]] = field(default_factory=dict)


@dataclass(frozen=True)
class PrintedChapter:
    """A chapter with its paragraphs that have claims."""

    name: str
    paragraphs: list[PrintedParagraph] = field(default_factory=list)
