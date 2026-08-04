---
description: Run the full impl-flow pipeline (design -> plan -> implement) in one invocation, with a single checkpoint after the plan is drafted before implementation begins
argument-hint: [summary of what to implement]
model: opus
disable-model-invocation: true
---

# impl-flow: all

Read the following three files completely, in this exact order, and carry out everything they say — do not summarize, skip, or shortcut any step. `design.md` and `plan.md` are internal instruction files, not standalone commands. Follow all three in sequence, passing `$ARGUMENTS` to the first one:

1. `${CLAUDE_SKILL_DIR}/design.md`
2. `${CLAUDE_SKILL_DIR}/plan.md`
3. `${CLAUDE_SKILL_DIR}/implement.md`

There is exactly one deviation from running them independently: after finishing everything in file 2 (the planning phase) and before starting anything in file 3 (the implementation phase), stop and use AskUserQuestion **exactly once** to ask the user whether to:

- proceed straight into the implementation phase now, or
- stop here, so the plans (already saved under the task-set directory's `before/`) can be reviewed, revised, or distributed first, and implementation can be started later — in this session or a new one — with `/impl-flow:implement {task-set directory}`.

If the user chooses to stop, end here. Only continue into file 3's instructions if they choose to proceed.

If `${CLAUDE_SKILL_DIR}/design.md` (or the other two) cannot be read, stop and report that clearly rather than trying to improvise the workflow from memory — this command has no logic of its own beyond what those three files say.
