---
description: Audit Claude Code instruction artifacts — SKILL.md files, slash commands, CLAUDE.md and .claude/rules, subagents, output styles and plugin manifests — against Anthropic's published authoring guidance, ending with fix and deletion proposals to approve. Pass a path to narrow the scope; defaults to the current repository.
argument-hint: [path or directory to audit, defaults to the current repository]
allowed-tools: Read Grep Glob Bash(python3 *scan.py *)
disable-model-invocation: true
---

# harness-audit: audit

Audit the instruction surfaces that shape Claude's behaviour, and report what to fix and what to delete.

**The audit itself is read-only.** Do not edit, create, or delete any file while investigating or reporting. The report ends in proposals; only once the user has picked from them may you change anything.

## Scope

`$ARGUMENTS` names the path to audit. With no argument, audit the current repository plus any `.claude/` directory inside it. Only audit paths outside the repository (such as `~/.claude/`) when the user names them.

The checklists live in this plugin's `reference/` directory. Resolve the plugin root once with `echo "${CLAUDE_PLUGIN_ROOT}"`, then read a checklist only when the audit actually covers that artifact kind:

| Artifact | Where it lives | Checklist |
|----------|----------------|-----------|
| Skills and slash commands | `skills/<name>/SKILL.md`, `commands/*.md` | `reference/skills-and-commands.md` |
| Project/user instructions | `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/*.md` | `reference/claude-md.md` |
| Subagents, output styles, manifests | `agents/*.md`, `output-styles/*.md`, `.claude-plugin/*.json` | `reference/agents-and-manifests.md` |
| Report and proposals | — | `reference/report-format.md` |

## Workflow

Copy this checklist and tick items off as you go:

```
Audit progress:
- [ ] 1. Inventory (scan.py)
- [ ] 2. Mechanical findings triaged
- [ ] 3. Judgement pass per artifact
- [ ] 4. Cross-artifact pass
- [ ] 5. Report + fix/delete proposals
```

**Step 1: Inventory.** Run the scanner over the audit scope:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scan.py" <path>
```

It prints an inventory table and every violation that can be decided from the file alone: name/description limits, body length, dead links and imports, orphaned or too-deeply-nested bundled files, Windows-style paths, broken manifests. Do not re-check those by hand.

If `python3` is unavailable, fall back to `Glob` for the inventory and check the numeric limits with `wc -l`; say in the report that the mechanical pass was degraded.

**Step 2: Triage.** Every scanner finding is real, but severity is yours to judge — see `reference/report-format.md`. Discard a finding only when you can state why it is a false positive in the report.

**Step 3: Judgement pass.** Read each artifact in full and apply the matching checklist. Work in load-frequency order — CLAUDE.md, rules and output styles first (they load every session), then skill and command descriptions (always in context), then bodies (loaded on invocation). If the scope is too large to read exhaustively, stop at a boundary you can name and say in the report which artifacts were not read.

**Step 4: Cross-artifact pass.** The failures that matter most live between files, not inside them:

- **Contradictions** — two artifacts that instruct differently on the same behaviour. Name both sides and which one should win.
- **Duplication** — the same rule stated in CLAUDE.md and a skill, or in a plugin skill and a project skill. Keep one, delete the rest.
- **Trigger collisions** — two descriptions covering overlapping situations with nothing telling them apart. Sharpen one description or merge the artifacts.
- **Wrong home** — a multi-step procedure sitting in CLAUDE.md (make it a skill), a per-directory rule loaded globally (give it `paths:`), or a "must always happen" instruction that only a hook can enforce.
- **Dead weight** — an artifact for a workflow that no longer exists, or a bundled file nothing links to.

**Step 5: Report.** Follow `reference/report-format.md` exactly. It ends with the fix and deletion proposals, then asks the user which to apply.

## Rules of engagement

- **Cite everything.** Every finding names the rule it breaks and at least one `file:line`. A cross-artifact finding cites every file involved and states the relationship between them.
- **Do not invent rules.** The checklists in `reference/` are the standard. Something that looks wrong but breaks no rule goes under "Observations" — never dress it up as a violation, and never drop it silently.
- **Prefer deletion.** Content Claude already knows, content derivable from the codebase, and content that never fires are costs with no return — propose removing them rather than rewording them.
- **Say when a file is fine.** An artifact with no findings gets one line saying so. Do not manufacture work.
- **Write the report in the language the user is speaking**, keeping file paths, frontmatter keys, and rule codes verbatim.
