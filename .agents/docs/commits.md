# Commits

Conventional Commits; applies to new commits only, history stays as is.

## Format

```
<type>(<scope>): <description>

<body>

<footer>
```

`<type>(<scope>): <description>` is the header. Body and footer are optional; a blank line separates each part.

## Header

- English, lowercase first letter, no trailing period, max 80 characters.
- Description starts with an imperative verb: `add`, `update`, `remove`, not `added`, `updates`.
- Description says what changed, e.g. `add comment section`.

## Types

- `feat` — new functionality.
- `fix` — bug fix.
- `docs` — documentation.
- `style` — formatting only (whitespace, commas).
- `refactor` — code change without new features or fixes.
- `perf` — performance.
- `test` — add or update tests.
- `build` — build system.
- `ci` — CI/CD.
- `chore` — other tasks, e.g. `.gitignore`.
- `revert` — revert a previous commit.

## Scopes

- `splitter` — `ai_reviewer/splitter/`.
- `pool` — `ai_reviewer/ai_pool.py`.
- `properties` — `properties/` instructions and references.
- `api` — API server.
- `tests` — `tests/` and test data.
- `docs` — `AGENTS.md`, `.agents/docs/`.
- `deps` — dependencies.
- `config` — configuration files.
- `build` — build scripts and files.

## Body and footer

- Body: why the change was made and why this way, not another.
- Footer: breaking changes, linked issues and tickets.
