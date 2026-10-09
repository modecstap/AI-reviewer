# AI-reviewer

API server that reviews an academic article (`.docx`): parallel AI agents check it against academic-writing properties, then their findings are merged into a per-paragraph report.

## Commands

Python ≥ 3.12; run from repo root.

- Install: `pip install -e .[dev]`
- Test: `python -m pytest`
- Split an article: `python -m ai_reviewer.splitter <article.docx> <refine dir>` — deletes and recreates the output dir.
- PDF needs Pango (Windows): install MSYS2, run `pacman -S mingw-w64-ucrt-x86_64-pango` in the UCRT64 shell, set `WEASYPRINT_DLL_DIRECTORIES=C:\msys64\ucrt64\bin`.

## Layout

- `ai_reviewer/` — Python package; `splitter/` turns `article.docx` into `refine/`.
- `ai_reviewer/ai_pool/` — `AIPool`: runs one Cursor SDK agent per property into `problems/<N>/`; needs `CURSOR_API_KEY`.
- `ai_reviewer/report/` — builds `report.json` of a run dir; `printer/` renders it as HTML/CSS/PDF.
- `ai_reviewer/printed_report_writer.py` — saves `report.html`/`.css`/`.pdf` into the run dir.
- `tests/` — pytest tests; `tests/data/` — sample articles.
- `properties/<property>/instruction.md` — prompt for the review agent of that property; `reference.md` — the property's criteria handbook the instruction relies on. One dir per property; the dir name is the property id used in `problems/<N>/<property>.json`.
- `.agents/docs/` — agent-facing docs (index below).

## Docs

- [purpose.md](.agents/docs/purpose.md) — read when touching the API, the per-article file layout, or the `problems/*.json` / `report.json` formats.
- [onboarding.md](.agents/docs/onboarding.md) — read when wiring a new agent, adding a skill, or changing this agent setup.
- [python-guide.md](.agents/docs/python-guide.md) — read when writing or changing Python code.
- [commits.md](.agents/docs/commits.md) — read when writing a commit message.
- [Structure reference](.agents/docs/heuristics/structure-reference.md) — required shape of modules, files, names, and module dependencies
- [Structure how-to](.agents/docs/heuristics/structure-howto.md) — read when adding a file or module, naming, adding a dependency, or extracting shared code

## Plans

Save plans to `.agents/plans/` (gitignored).
