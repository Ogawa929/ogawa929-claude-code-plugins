---
description: Run design then plan back to back in one invocation (no implementation) — the two phases that are almost always used together
argument-hint: [summary of what to implement]
model: opus
effort: xhigh
disable-model-invocation: true
---

# impl-flow: spec

Read the following two files completely, in this exact order, and carry out everything they say — do not summarize, skip, or shortcut any step. They are internal instruction files, not standalone commands (design and plan are one unit, invoked only through this command or `/impl-flow:all`). Follow them in sequence, passing `$ARGUMENTS` to the first one:

1. `${CLAUDE_SKILL_DIR}/design.md`
2. `${CLAUDE_SKILL_DIR}/plan.md`

Stop once file 2's instructions are complete — do not start implementing anything. Once the plans are saved, tell the user they can review, revise, or distribute them, and start implementation whenever ready with `/impl-flow:implement {task-set directory}` (in this session or a new one).

If either file cannot be read, stop and report that clearly rather than trying to improvise the workflow from memory — this command has no logic of its own beyond what those two files say.

Note on effort: this command's frontmatter sets `xhigh` for the whole invocation, and a frontmatter effort level applies for the rest of the turn — it cannot be switched between the two phases. That is the intended behaviour here, since both phases are judgement-heavy and light on output tokens. Scaling by complexity happens where it pays: the `Plan` agent dispatch inside `plan.md`, and the implementation subagents in `/impl-flow:implement`.
