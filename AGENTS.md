# AI-reviewer

API server that reviews an academic article (`.docx`): parallel AI agents check it against academic-writing properties, then their findings are merged into a per-paragraph report.

## Commands

Python ≥ 3.12; run from repo root.

- Install: `pip install -e .[dev]`
- Test: `python -m pytest`
- Review an article: `python -m ai_reviewer.main <article.docx> <output_dir>` — splits the article, runs the agents of every property in `./properties` in a new run dir `<output_dir>/<N>/`, writes `report.json` and the printed files there; needs `CURSOR_API_KEY`.
- PDF needs Pango (Windows): install MSYS2, run `pacman -S mingw-w64-ucrt-x86_64-pango` in the UCRT64 shell, set `WEASYPRINT_DLL_DIRECTORIES=C:\msys64\ucrt64\bin`.

## Layout

- `ai_reviewer/main.py` — the CLI: wires the packages below into one run.
- `ai_reviewer/article/` — `Chapter` and the `article.txt` format.
- `ai_reviewer/splitter/` — `.docx` → chapters.
- `ai_reviewer/properties/` — catalog of `properties/`: agent definitions, type numbers, translations.
- `ai_reviewer/claims/` — `Claim` and the `<property>.json` parser.
- `ai_reviewer/ai_pool/` — `AIPool`: runs one agent per property in parallel in a new run dir; `cursor/` — the Cursor SDK adapter, needs `CURSOR_API_KEY`.
- `ai_reviewer/report/` — builds the report and owns the `report.json` format; `printer/` renders it as HTML/CSS/PDF.
- `ai_reviewer/run_dir/` — run dir files: numbering, reading, writing `report.json` and the printed files.
- `tests/` — pytest tests; `tests/data/` — sample articles.
- `properties/<property>/instruction.md` — prompt for the review agent of that property; `reference.md` — the property's criteria handbook the instruction relies on. One dir per property; the dir name is the property id: `<output_dir>/<N>/<id>.json`, the `report.json` key and the key in `properties/translation/<lang>.json`. `translation/` is not a property.
- `.agents/docs/` — agent-facing docs (index below).

## Docs

- [purpose.md](.agents/docs/purpose.md) — read when touching the API, the per-article file layout, or the `<output_dir>/<N>/*.json` / `report.json` formats.
- [onboarding.md](.agents/docs/onboarding.md) — read when wiring a new agent, adding a skill, or changing this agent setup.
- [python-guide.md](.agents/docs/python-guide.md) — read when writing or changing Python code.
- [commits.md](.agents/docs/commits.md) — read when writing a commit message.
- [Structure reference](.agents/docs/heuristics/structure-reference.md) — required shape of modules, files, names, and module dependencies
- [Structure how-to](.agents/docs/heuristics/structure-howto.md) — read when adding a file or module, naming, adding a dependency, or extracting shared code

## Plans

Save plans to `.agents/plans/` (gitignored).
