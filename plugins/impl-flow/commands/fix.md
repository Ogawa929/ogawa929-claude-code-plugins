---
description: Fix mode — diagnose a bug or revision against an existing use-case document, revise the affected use cases, plan the fix, and implement it, with a single checkpoint after the plans are drafted. Lighter than /impl-flow:all, and aimed at not missing anything a partial fix would leave behind.
argument-hint: [the bug report or change request]
model: opus
effort: high
disable-model-invocation: true
---

# impl-flow: fix

Read the following three files completely, in this exact order, and carry out everything they say — do not summarize, skip, or shortcut any step. `diagnose.md` and `plan.md` are internal instruction files, not standalone commands. Follow all three in sequence, passing `$ARGUMENTS` to the first one:

1. `${CLAUDE_SKILL_DIR}/diagnose.md`
2. `${CLAUDE_SKILL_DIR}/plan.md`
3. `${CLAUDE_SKILL_DIR}/implement.md`

This is the fix-mode sibling of `/impl-flow:all`. The only structural difference is the first file: `diagnose.md` replaces `design.md`, revising an **existing** use-case document instead of interviewing a new one into being. Files 2 and 3 are shared with the feature-mode pipeline and behave the same way, with the fix-mode specifics that `diagnose.md` hands them (see below).

There is exactly one deviation from running the files independently: after finishing everything in file 2 (the planning phase) and before starting anything in file 3 (the implementation phase), stop and use AskUserQuestion **exactly once** to ask the user whether to:

- proceed straight into the implementation phase now, or
- stop here, so the plans (already saved under the task set's `before/`) can be reviewed or revised first, and implementation can be started later — in this session or a new one — with `/impl-flow:implement {task-set directory}`.

If the user chooses to stop, end here. Only continue into file 3's instructions if they choose to proceed.

## What file 1 hands to file 2

`diagnose.md` settles four things that file 2 must carry through rather than re-derive:

- **The task-set directory** — the existing one that owns the affected behaviour. File 2 appends to its `before/`, continuing the `seq` numbering; it must not create a new dated directory.
- **The verification contract** — a test that fails for the reported symptom comes first in every plan, and the plan passes only once it goes green.
- **The re-verification scope** — the use cases marked "in scope, unchanged", which need verifying even though the document did not change for them.
- **The review's file scope** — every file a layer-2 or layer-3 omission finding landed on, each of which must appear in some plan's `files` list or be recorded as deliberately excluded.

## When to use `/impl-flow:spec` instead

Fix mode rests on the affected behaviour already having a use-case document. If `diagnose.md` finds none, or classifies the request as a broad new requirement, it stops and says so — that is working as intended, not a failure. Take the work to `/impl-flow:spec` in that case rather than forcing it through here: retro-generating a whole specification for existing code costs as much as a full design phase, and fix mode's omission review has nothing to check against without a recorded file set.

If `${CLAUDE_SKILL_DIR}/diagnose.md` (or either of the other two) cannot be read, stop and report that clearly rather than trying to improvise the workflow from memory — this command has no logic of its own beyond what those three files say.

Note on effort: this command's frontmatter sets `high` for the whole invocation, one level below `/impl-flow:all`'s `xhigh`. That is the intended difference. Fix mode does not have to discover requirements — they are already in the document — so the judgement it needs is concentrated in root-cause analysis and impact scoping rather than spread across an open-ended interview. A frontmatter effort level applies for the rest of the turn, so the implementation phase is also led at `high` here; that affects only the leader's orchestration, since the implementation subagents' own frontmatter `effort` overrides the session level. Run `/impl-flow:implement` as a separate invocation if you want the cheaper `medium` leader.
