---
name: harness-audit
description: Audits Claude Code instruction artifacts — SKILL.md files, slash commands, CLAUDE.md and .claude/rules, subagents, output styles, and plugin manifests — against Anthropic's published authoring guidance, then ends with concrete fix and deletion proposals. Use when reviewing, tuning, or cleaning up these files (e.g. "audit my skills", "review this SKILL.md", "CLAUDE.mdを見直して", "プロンプトを最適化して", "このコマンド定義は適切か"). Do NOT use for reviewing application source code, or for writing a new artifact from scratch.
argument-hint: [path or directory to audit, defaults to the current repository]
allowed-tools: Read Grep Glob
---

# Harness Audit

Audit the instruction surfaces that shape Claude's behaviour, and report what to fix and what to delete.

**This skill is read-only.** Do not edit, create, or delete any file during the audit. Changes are proposed at the end and applied only after the user picks them.

## Scope

`$ARGUMENTS` names the path to audit. With no argument, audit the current repository plus any `.claude/` directory inside it. Only audit paths outside the repository (such as `~/.claude/`) when the user names them.

| Artifact | Where it lives | Checklist |
|----------|----------------|-----------|
| Skills and slash commands | `skills/<name>/SKILL.md`, `commands/*.md` | [reference/skills-and-commands.md](reference/skills-and-commands.md) |
| Project/user instructions | `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/*.md` | [reference/claude-md.md](reference/claude-md.md) |
| Subagents, output styles, manifests | `agents/*.md`, `output-styles/*.md`, `.claude-plugin/*.json` | [reference/agents-and-manifests.md](reference/agents-and-manifests.md) |
| Report and proposals | — | [reference/report-format.md](reference/report-format.md) |

Read a checklist only when the audit actually covers that artifact kind.

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
python3 "${CLAUDE_PLUGIN_ROOT}/skills/harness-audit/scripts/scan.py" <path>
```

It prints an inventory table and every violation that can be decided from the file alone: name/description limits, body length, dead links and imports, orphaned or too-deeply-nested bundled files, Windows-style paths, broken manifests. Do not re-check those by hand.

If `python3` is unavailable, fall back to `Glob` for the inventory and check the numeric limits with `wc -l`; say in the report that the mechanical pass was degraded.

**Step 2: Triage.** Every scanner finding is real, but severity is yours to judge — see [reference/report-format.md](reference/report-format.md). Discard a finding only when you can state why it is a false positive in the report.

**Step 3: Judgement pass.** Read each artifact in full and apply the matching checklist. This is where the audit earns its keep: discoverability of descriptions, conciseness of bodies, whether instructions are specific enough to verify, whether the degree of freedom matches the task's fragility.

**Step 4: Cross-artifact pass.** The failures that matter most live between files, not inside them:

- **Contradictions** — two artifacts that instruct differently on the same behaviour. Claude picks one arbitrarily. Name both sides and which one should win.
- **Duplication** — the same rule stated in CLAUDE.md and a skill, or in a plugin skill and a project skill. Keep one, delete the rest.
- **Trigger collisions** — two descriptions covering overlapping situations with nothing telling them apart. Sharpen one description or merge the artifacts.
- **Wrong home** — a multi-step procedure sitting in CLAUDE.md (make it a skill), a per-directory rule loaded globally (give it `paths:`), or a "must always happen" instruction that only a hook can enforce.
- **Dead weight** — an artifact for a workflow that no longer exists, or a bundled file nothing links to.

**Step 5: Report.** Follow [reference/report-format.md](reference/report-format.md) exactly. It ends with the fix and deletion proposals, then asks the user which to apply.

## Rules of engagement

- **Cite everything.** Every finding names `file:line` and the rule it breaks. A finding you cannot anchor to a specific line and a specific rule from the checklists is an opinion — drop it.
- **Do not invent rules.** The checklists in `reference/` are the standard. If something looks wrong but no rule covers it, report it under "Observations", not as a violation.
- **Prefer deletion.** Context is a shared budget. Content Claude already knows, content derivable from the codebase, and content that never fires are all costs with no return — propose removing them rather than rewording them.
- **Say when a file is fine.** An artifact with no findings gets one line saying so. Do not manufacture work.
- **Write the report in the language the user is speaking**, keeping file paths, frontmatter keys, and rule codes verbatim.
