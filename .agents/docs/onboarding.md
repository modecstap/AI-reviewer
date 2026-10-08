# Agent setup

One agent-neutral setup shared by every coding agent on the team.

## Layout

- `AGENTS.md` — canonical lean index: one-liner, commands, hard constraints, docs index, plans convention. Links docs with plain markdown links, never `@` imports (some agents load imports eagerly, defeating progressive disclosure).
- `CLAUDE.md` — only `@AGENTS.md`; Claude-only instructions may follow the import.
- `.agents/docs/` — governing docs, each linked from `AGENTS.md` with a "read when…" hook. Add a doc only when content exists for it.
- `.agents/skills/<name>/` — canonical project skills (none yet).
- `.agents/plans/` — agent plans, gitignored.

## Hooking up an agent

- **Claude Code** — reads `CLAUDE.md`, not `AGENTS.md`; the `@AGENTS.md` pointer covers it. Project skills: add a relative symlink `.claude/skills/<name>` → `../../.agents/skills/<name>` per skill, committed.
- **Cursor** — reads `AGENTS.md` natively; nothing to wire.
- **Any other agent** — point its entry-file mechanism at `AGENTS.md` (include syntax, or duplicated content if it has none), or re-run `/agentify-project` to research and wire it.

## Windows symlinks

Skill symlinks need `git config core.symlinks true` and Windows Developer Mode (or admin rights) before cloning/checkout; otherwise git checks them out as plain text files.
