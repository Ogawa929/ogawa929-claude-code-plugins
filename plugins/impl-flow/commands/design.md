---
description: Interactively gather requirements and produce a design doc for a new implementation (Phase 1 of impl-flow: design -> plan -> implement)
argument-hint: [summary of what to implement]
model: opus
disable-model-invocation: true
---

# impl-flow: design

You are about to nail down the "design" for an implementation through a dialogue with the user. This phase runs on the opus model — prioritize deep thinking and careful back-and-forth with the user. Do not write any code yet.

## Steps

1. **Grasp the summary**
   - If `$ARGUMENTS` is given, treat it as the summary of what to implement.
   - If not, ask the user what they want to implement.

2. **Confirm the task directory and check for an existing task set**
   - Use AskUserQuestion to confirm the root directory name where implementation plans will be stored. Default: `task`.
   - Look under `{task_dir}` for a directory that clearly overlaps with what the user just described. A task-set directory has the shape `{task_dir}/{yyyymmdd}-{title}/`, and once planning has run it contains a `before/` subdirectory (plans not yet executed) and an `after/` subdirectory (plans already committed). Its state is always determined by these two subdirectories, never guessed:
     - `before/` has files and/or `after/` is empty or absent → this task set is **not finished**.
     - `before/` is empty or absent and `after/` has files → this task set **looks finished**.
     - Neither exists yet (only a bare `design.md`, or nothing at all) → planning has not started.
   - If a relevant directory exists, tell the user plainly which of these states it's in, and ask whether to reuse it or start a fresh dated one.
   - If reusing an existing directory and writing `design.md` would overwrite a file that's already there, do not overwrite silently — ask whether to overwrite, keep both (e.g. by renaming), or abort.

3. **Implementation title and directory creation**
   - Combine today's date (`{yyyymmdd}`) with a short title agreed on with the user (e.g. kebab-case) to create `{task_dir}/{yyyymmdd}-{title}/` if it doesn't already exist.
   - Refer to this directory as the "task-set directory" from now on. `design.md` lives directly inside it; the `before/`/`after/` split is created later by `/impl-flow:plan`.

4. **Explore the codebase before asking anything**
   - Before interviewing the user, read the parts of the codebase relevant to what they described: existing files, interfaces, and patterns this implementation would need to fit into or reuse.
   - Use this to ground the interview in reality — you should already know what's technically feasible, what conventions exist, and what's ambiguous purely because of the codebase, before asking the user anything.

5. **Brainstorm the requirements (most important step)**
   - Always stop and consider whether the given information is enough to start implementation.
   - Identify missing information, ambiguities, and points that need a decision, and confirm them with the user **using the AskUserQuestion tool**.
   - Cover technical implementation, UI/UX, edge cases, concerns, and trade-offs. **Do not ask obvious questions — dig into the hard parts the user may not have considered**, especially ones you surfaced by reading the codebase in step 4.
   - When asking, never just float a single option and ask "does this work?" — **always present multiple alternatives with their trade-offs** and let the user pick.
   - Do not stop after one round. If the answers raise new questions, run further rounds. Keep going until you can confidently say the requirements are fixed.
   - Explicitly listing what is out of scope ("things we will not do") should also be offered as one of the alternatives.

6. **Write the design document**
   - Write the finalized content to `{task-set directory}/design.md`, including:
     - Background / purpose
     - Scope (in scope / out of scope)
     - Requirements list
     - Relevant files / interfaces identified while exploring the codebase in step 4
     - Key decisions and their rationale (including alternatives considered and why they were rejected)
     - Open concerns / risks
     - Next steps

7. **Closing**
   - Summarize the contents of `design.md` for the user and do a final check for any misalignment.
   - Tell the user that `/impl-flow:plan {task-set directory}` can be used next to create the implementation plans.
