# CLAUDE.md

A personal plugin marketplace for Claude Code. Each plugin lives under `plugins/<name>/`, and the root `.claude-plugin/marketplace.json` registers them all.

## Branching

- **Never commit directly to `main`.** Always branch before making changes.
- Only three branch kinds: `main`, `feat/<topic>`, `fix/<topic>`. New capabilities go on `feat/`, bug fixes on `fix/`.
- Land work on `main` through a PR, **squash merge** by default. Delete the branch after merging.
- The squashed commit message becomes `main`'s history, so write the PR title as the history entry: English, imperative mood, ending with `(#<PR number>)` — e.g. `Add statusline-pack: a configurable status line plugin (#8)`.

## Layout

| Path | Role |
|------|------|
| `plugins/<name>/.claude-plugin/plugin.json` | Plugin manifest (name / version / description / author / license) |
| `plugins/<name>/commands/*.md` | Slash commands, invoked as `/<plugin>:<command>` |
| `plugins/<name>/skills/<name>/SKILL.md` | Auto-triggered skills |
| `plugins/<name>/agents/*.md` | Subagent definitions |
| `plugins/<name>/output-styles/*.md` | Output styles |
| `.claude-plugin/marketplace.json` | The registry — every new plugin must be added here too |
| `tasks/` | impl-flow working files. Git-ignored; never commit them |

## Adding or changing a plugin

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json` (`author` is `Teruyoshi Ogawa`, `license` is `MIT`, first release is `0.1.0`).
2. Add the command / skill / agent / output-style files themselves.
3. Add an entry to `.claude-plugin/marketplace.json` (`name`, `source`, `description`, plus `category` / `tags` where useful).
4. Update the "Available Plugins" table in `README.md`.
5. Bump `version` in `plugin.json` for any feature change or breaking change.

Keep the four sources of truth in sync: `plugin.json`, `marketplace.json`, the README table, and the actual files on disk.

## Validation

- Run `claude plugin validate .` before committing. CI (`.github/workflows/validate-plugins.yml`) runs the same check on changes under `.claude-plugin/**` and `plugins/**`.
- To try a plugin locally: `/plugin marketplace add .` then `/reload-plugins`.

## Writing style

- Plugin docs, descriptions, and commit messages are in English. `README.md` keeps its English section followed by the Japanese section.
- Conversation with the user is in Japanese.
