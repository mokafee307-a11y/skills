# Feishu Knowledge Compounder

This skill has a single source of truth:

- Source directory: `/Users/mokafee/.codex/skills/feishu-knowledge-compounder`

Current usage:

- Codex reads this directory directly.
- Claude reads the symlink at `/Users/mokafee/.claude/skills/feishu-knowledge-compounder`, which points here.
- Cursor should keep using this same source directory.

Maintenance rule:

- Edit files in this directory only.
- Do not create a second copied version under `~/.cursor/skills/feishu-knowledge-compounder` unless you intentionally want a fork.
- If Cursor, Claude, and Codex should stay in sync, always update `SKILL.md`, `scripts/`, `references/`, and config files here.

Why:

- A copied skill can drift and become inconsistent across tools.
- One shared directory keeps behavior, prompts, scripts, and Feishu workflow logic aligned everywhere.
