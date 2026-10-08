# AI-reviewer

API server that reviews an academic article (`.docx`): parallel AI agents check it against academic-writing properties, then their findings are merged into a per-paragraph report.

No code, build, test or run commands yet — add them here once they exist.

## Layout

- `properties/<property>/instruction.md` — prompt for the review agent of that property; `reference.md` — the property's criteria handbook the instruction relies on. One dir per property; the dir name is the property id used in `problems/<property>.json`.
- `.agents/docs/` — agent-facing docs (index below).

## Docs

- [purpose.md](.agents/docs/purpose.md) — read when touching the API, the per-article file layout, or the `problems/*.json` / `report.json` formats.
- [onboarding.md](.agents/docs/onboarding.md) — read when wiring a new agent, adding a skill, or changing this agent setup.

## Plans

Save plans to `.agents/plans/` (gitignored).
