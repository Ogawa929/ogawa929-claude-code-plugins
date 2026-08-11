# CLAUDE.md and .claude/rules

Checklist for `CLAUDE.md`, `CLAUDE.local.md`, and `.claude/rules/*.md`. These load into every session (rules with `paths:` load when a matching file is touched), so every line is a permanent context cost paid by every conversation.

## Contents

- Hard limits
- What belongs here
- Writing quality
- Imports
- Rules and path scoping
- Placement and precedence
- Deletion candidates

## Hard limits

| Rule | Limit |
|------|-------|
| File size | target under 200 lines per file; longer files reduce adherence |
| `@path` imports | resolve to real files; max depth 4 hops; expanded into context at launch |

CLAUDE.md is context, not enforcement. An instruction that must hold regardless of Claude's judgement belongs in a hook or in `permissions.deny`, not here — flag "always/never" rules whose violation would be costly and suggest the enforcement mechanism.

## What belongs here

Facts worth holding in *every* session: build and test commands, project layout, conventions that differ from tool defaults, "always do X" rules, and pitfalls Claude would otherwise re-learn.

Move out anything that is:

| Content | Better home |
|---------|-------------|
| A multi-step procedure | a skill (loads only when relevant) |
| Guidance for one part of the tree | `.claude/rules/*.md` with `paths:` |
| Something that must run at a fixed moment | a hook |
| Personal, machine-specific, or secret | `CLAUDE.local.md` (gitignored) |
| Derivable from the codebase — directory listings, dependency lists, architecture tours | delete it |

## Writing quality

- **Specific enough to verify.** "Use 2-space indentation", not "format code properly". "API handlers live in `src/api/handlers/`", not "keep files organized".
- **Structured.** Headers and bullets, not dense paragraphs.
- **Internally consistent.** Two rules that contradict each other mean Claude picks one arbitrarily. Check the whole loaded set — parent-directory CLAUDE.md files, `.claude/rules/`, and user-level files all concatenate.
- **Current.** Rules for tools, directories, or workflows that no longer exist actively mislead.
- **No prose padding.** Greetings, motivation, and explanations of what Claude Code is are pure cost.
- **Maintainer notes in HTML comments.** Block-level `<!-- … -->` is stripped before loading, so notes for humans cost nothing there — but they are stripped, so anything Claude must read cannot live in a comment.

## Imports

- `@path/to/file` expands at launch; splitting content into imports organizes it but does **not** reduce context.
- Relative paths resolve against the importing file.
- An import resolving outside the working directory (e.g. `@~/.claude/…`) triggers a one-time approval dialog; flag it in a repo meant to be shared with a team.
- To mention a path without importing it, wrap it in backticks.
- `AGENTS.md` is not read by Claude Code. A repo that has one should have a `CLAUDE.md` that imports it, rather than a second copy of the same content.

## Rules and path scoping

- One topic per file, named for the topic (`testing.md`, `api-design.md`).
- A rule without `paths:` loads every session — flag any that is only relevant to part of the tree.
- `paths:` uses globs; brace groups multiply, and a rule's whole list shares a budget of 1,000 expanded patterns. A pattern with an unmatched `[` matches nothing.
- Path-scoped rules and nested CLAUDE.md files are **not** re-injected after `/compact`. Anything that must survive compaction belongs in the project-root CLAUDE.md.

## Placement and precedence

Load order, broadest first: managed policy → `~/.claude/CLAUDE.md` → project `./CLAUDE.md` or `./.claude/CLAUDE.md` → `./CLAUDE.local.md`. Everything is concatenated, so later files do not replace earlier ones — they just get read last. Files in subdirectories are not loaded at launch at all; they arrive when Claude reads a file there. `claudeMdExcludes` skips ancestor files by glob, which is the monorepo answer to another team's instructions leaking in.

Flag: team-wide rules sitting in a user-level file, personal preferences committed into the project file, and a `CLAUDE.local.md` that is not gitignored.

## Deletion candidates

Propose removing:

- Anything Claude can derive by reading the codebase (file trees, dependency lists, framework overviews).
- Restatements of universal good practice ("write clean code", "handle errors").
- Duplicates of a skill's content, or of another CLAUDE.md in the hierarchy.
- Rules for removed tooling, renamed directories, or abandoned workflows.
- Sections that grew into procedures — extract to a skill, then delete from here.
