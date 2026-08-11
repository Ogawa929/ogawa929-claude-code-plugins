# Report format

The audit ends in one report. Findings first, proposals last, nothing applied without the user choosing.

## Severity

| Level | Meaning | Examples |
|-------|---------|----------|
| **Blocker** | The artifact fails to load, fails to be discovered, or actively misleads | invalid `name` on a plugin skill, dead `@import`, contradicting rules, side-effecting skill that Claude can self-invoke |
| **Should fix** | It works, but measurably underperforms | vague or missing `description` (discovery falls back to the first paragraph), body over the line limit, orphaned bundled file, over-broad `allowed-tools`, unverifiable instruction |
| **Consider** | A judgement call with a defensible status quo | naming style, whether to split a reference file, tone |

Rank by severity, then by how many sessions the problem touches — a defect in a file loaded every session outranks the same defect in a rarely-invoked skill.

## Structure

```markdown
## Audit scope
<paths audited, artifact counts, anything skipped and why>

## Summary
<2-4 sentences: overall state, the single most important problem, the headline number of findings by severity>

## Findings

### Blocker
1. **`path/to/file.md:12` — <one-line defect>**
   Rule: <the rule from the checklist>
   Why it matters: <the concrete consequence>
   Fix: <the specific change; quote the replacement text when short>

### Should fix
...

### Consider
...

## Clean
- `path/to/file.md` — no findings.

## Observations
<things that look off but no rule covers, or facts the user should know>

## Proposals
```

`## Proposals` is the deliverable. Everything above it is evidence.

## Proposals

Two lists, each ordered by value:

**Fixes** — one row per change, phrased so the user can approve individually:

| # | File | Change | Severity |
|---|------|--------|----------|
| F1 | `skills/deploy/SKILL.md` | Rewrite `description` to name the trigger phrases and add a negative trigger | Blocker |
| F2 | `CLAUDE.md` | Move the release procedure (lines 40-78) into a new `releasing` skill | Should fix |

For any fix whose wording is the point — descriptions, frontmatter values, rewritten rules — quote the exact proposed text under the table. A proposal the user cannot evaluate without asking follow-up questions is not finished.

**Deletions** — the same, with the reason it earns removal rather than a rewrite:

| # | Target | Lines | Reason |
|---|--------|------:|--------|
| D1 | `CLAUDE.md` "Project structure" section | 22-51 | Derivable from the repository; costs context in every session |
| D2 | `skills/legacy-import/` | whole skill | Trigger no longer exists — the importer was removed |

State the estimated context saved when it is material (line counts are enough).

Deleting a whole artifact is the least reversible proposal in the set. Never propose one on the assumption that its trigger is gone: cite the search that found no remaining reference to it, and mark the row irreversible. Say the same for anything else that cannot be undone by editing text back — changing an output style, widening `permissionMode`.

Line numbers go stale as soon as an earlier proposal lands. Two proposals against one file must not overlap, and proposals within a file are listed bottom-up so they can be applied in order.

## Closing

End by asking the user which proposals to apply, using `AskUserQuestion` with options along the lines of: apply everything, apply blockers only, apply only the rows they name (F1, D2, …), or nothing for now.

Applying is a separate phase from the audit: it starts only after that answer, it covers only what the user picked, and it ends with a report of what actually changed.

If there is nothing to propose, say exactly that and stop. Do not pad the report to look productive.
