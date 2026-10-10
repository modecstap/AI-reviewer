from dataclasses import dataclass


@dataclass(frozen=True)
class Block:
    """A non-empty top-level body element: a paragraph or a table."""

    text: str
    is_style_heading: bool = False
    is_heuristic_heading: bool = False
