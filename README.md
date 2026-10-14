# AI-reviewer

AI-reviewer is a command-line tool that reviews an academic article in `.docx` format with AI agents. Each agent checks the article against one academic-writing property, such as conciseness or literacy. The tool merges the findings into a per-paragraph report, so problems with academic style are easy to find and fix before publication. It is for authors of academic articles and for reviewers and editors who check articles before publication.

## Contents

- [About](#about)
- [Features](#features)
- [Tech stack](#tech-stack)
- [Installation](#installation)
- [Running](#running)
- [Usage](#usage)
- [Project structure](#project-structure)
- [Configuration](#configuration)
- [Testing](#testing)
- [Roadmap](#roadmap)
- [License](#license)

## About

AI-reviewer takes an academic article (`.docx`) and splits it into chapters and paragraphs. Then it runs AI agents in parallel, one per academic-writing property. Each agent reads the article and writes its claims: a quote from the text, the violation types, and a description of the problem. When all agents finish, the tool merges their claims into one report, grouped by chapter and paragraph, and prints it as HTML and PDF.

Today the project is a CLI tool. The full spec of the file formats is in [.agents/docs/purpose.md](.agents/docs/purpose.md) (in Russian).

## Features

- Splits a `.docx` article into chapters and paragraphs.
- Runs one AI agent per property, all in parallel.
- Checks seven properties: `caution`, `conciseness`, `consistency`, `correctness`, `impersonality`, `literacy`, `structure`.
- Writes each run to a new numbered run dir `<output_dir>/<N>/`, so earlier runs are kept.
- Builds `report.json`: claims of all properties, grouped by chapter and paragraph.
- Prints the report as `report.html`, `report.css` and `report.pdf`, with a title page, a statistics page and a page per chapter with its claims.
- Prints the report in Russian.

## Tech stack

- Python ≥ 3.12
- [python-docx](https://python-docx.readthedocs.io/) — reads the `.docx` article.
- [Cursor SDK](https://pypi.org/project/cursor-sdk/) (`cursor-sdk`) — runs the review agents on the `composer-2.5` model.
- [WeasyPrint](https://weasyprint.org/) with Pango — renders the PDF report.
- [pytest](https://pytest.org/) — tests.

## Installation

1. Clone the repo and go to its root:

   ```sh
   git clone https://github.com/modecstap/AI-reviewer.git
   cd AI-reviewer
   ```

2. Install the dependencies:

   ```sh
   pip install -r requirements.txt
   ```

3. On Windows, install Pango for WeasyPrint:

   1. Install [MSYS2](https://www.msys2.org/).
   2. In the MSYS2 UCRT64 shell, run:

      ```sh
      pacman -S mingw-w64-ucrt-x86_64-pango
      ```

   3. Set the environment variable `WEASYPRINT_DLL_DIRECTORIES=C:\msys64\ucrt64\bin`.

## Running

Set `CURSOR_API_KEY` and run the CLI from the repo root:

```sh
python -m ai_reviewer.main <article.docx> <output_dir>
```

- `<article.docx>` — path to the article.
- `<output_dir>` — dir for the numbered run dirs; the run writes to a new `<output_dir>/<N>/`.

Run the command from the repo root: the CLI reads `properties/` relative to the working directory.

On success, the CLI prints the path of the new run dir and exits with code `0`. On an expected failure, it prints `error: <message>` to stderr and exits with code `1`.

## Usage

Each run creates a new run dir `<output_dir>/<N>/`. `<N>` is the largest existing number plus 1; the first run is `1`. The run dir holds:

- `article.txt` — the marked-up article text given to the agents.
- `<property>.json` — claims of one property, for example `caution.json`. Only agents that finished successfully write a file.
- `report.json` — the final report: claims of all properties, grouped by chapter and paragraph.
- `report.html` — the printed report as an HTML fragment.
- `report.css` — styles of `report.html`.
- `report.pdf` — the printed report as PDF.

The PDF has these pages:

1. Title page: VSRT, AI-Reviewer and the creation date.
2. Statistics page: the total number of claims and a table of claims per property and violation type, with a legend of type names.
3. One or more pages per chapter: paragraph text on the left with claim quotes highlighted, and its claims on the right.

The full spec of all run dir files is in [.agents/docs/purpose.md](.agents/docs/purpose.md) (in Russian).

## Project structure

```text
ai_reviewer/            Python package
  main.py               CLI: wires the packages below into one run
  article/              Chapter and the article.txt format
  splitter/             .docx to chapters
  properties/           catalog of properties/: agent definitions, type numbers, translations
  claims/               Claim and the <property>.json parser
  ai_pool/              AIPool: runs one agent per property in parallel in a new run dir
    cursor/             Cursor SDK adapter
  report/               builds the report and owns the report.json format
    printer/            renders the report as HTML/CSS/PDF
  run_dir/              run dir files: numbering, reading, writing
properties/             one dir per property
  <property>/
    instruction.md      prompt for the review agent of the property
    reference.md        criteria handbook the instruction relies on
  IO-structure.md       shared input/output contract of all agents
  translation/          property and type names per language (not a property)
tests/                  pytest tests
.agents/docs/           agent-facing docs
```

More docs:

- [AGENTS.md](AGENTS.md) — layout, commands and doc index for AI coding agents.
- [.agents/docs/onboarding.md](.agents/docs/onboarding.md) — how the AI coding agent setup works.
- [.agents/docs/purpose.md](.agents/docs/purpose.md) — spec of the run dir and report formats.

## Configuration

Environment variables:

- `CURSOR_API_KEY` — required. The Cursor SDK uses it to run the agents. The run fails when it is not set or blank.
- `WEASYPRINT_DLL_DIRECTORIES` — Windows only. Path to the Pango DLLs for the PDF, for example `C:\msys64\ucrt64\bin`.

Other settings:

- The model is hard-coded as `MODEL` in `ai_reviewer/main.py` (`composer-2.5`). Edit it there to use another model.
- The CLI reads `properties/` relative to the working directory, so run it from the repo root.

To add a property:

1. Create `properties/<id>/`. The dir name is the property id, used in `<id>.json` and as the key in `report.json`.
2. Add `instruction.md` — the prompt for the review agent. Follow the shared contract in [properties/IO-structure.md](properties/IO-structure.md).
3. Add `reference.md` — the criteria handbook. List violation types as `### N.` headings under `## Violation types`; `N` is the type number.
4. Optional: add Russian names of the property and its types to `properties/translation/ru.json`. Without a translation, the report prints the original name.

Every subdir of `properties/` with both `instruction.md` and `reference.md` is a property, except `translation/`.

## Testing

Run the tests from the repo root:

```sh
python -m pytest
```

The tests need no real `CURSOR_API_KEY`. The PDF tests run WeasyPrint, so they need Pango (see [Installation](#installation)).

## Roadmap

- An API server to upload an article and get the report.
- A choice of the report print language: English labels exist, but the CLI prints only in Russian.
