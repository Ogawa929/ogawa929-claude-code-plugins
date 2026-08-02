---
description: Turn a design (or direct requirements) into commit-sized implementation plan files, each self-contained enough to run in a brand-new Claude Code session (Phase 2 of impl-flow: design -> plan -> implement)
argument-hint: [task-set directory, e.g. task/20260802-my-feature]
disable-model-invocation: true
---

# impl-flow: plan

You are about to create the "implementation plans". Do not write any code yet. The goal is to produce a set of plan documents at a granularity that lets each subsequent implementation phase run safely in its own independent session.

## Steps

1. **Identify the task-set directory**
   - If `$ARGUMENTS` is given, treat it as the task-set directory.
   - If not given, but `/impl-flow:design` was just run in this same session, use that directory.
   - Otherwise, look under the task directory (default `task`) for candidates: a directory with a `design.md` but no `before/`/`after/` split yet (planning hasn't happened there). Let the user pick if there are multiple. If there are no candidates, this command should still work standalone: gather the requirements directly from the user (briefly, without assuming a `design.md` exists) and create a new task-set directory.
   - If the chosen directory already has a `before/` and/or `after/` (i.e. planning already ran there before), tell the user plainly what's there — how many plans are still pending in `before/`, how many are already committed in `after/` — and confirm whether to add more plans, replace the pending ones, or abort, before writing anything. Never silently overwrite an existing plan file.

2. **Read the input**
   - If `{task-set directory}/design.md` exists, read it and use it as the input for planning.
   - If it doesn't exist (i.e. this command was invoked directly without the design phase), check whether enough information is available to plan the implementation, and ask the user about anything missing.

3. **Confirm the verification method**
   - Check whether the user has a preferred verification method to build into the plans (e.g. running the existing test suite, adding unit tests for the affected scope, lint/typecheck only, manual verification steps, etc.).
   - If not specified, propose several alternatives based on the state of the codebase and let the user choose via AskUserQuestion. Decide whether verification should differ per plan or be a single overall policy shared by all plans.

4. **Create the implementation plans (using the Plan agent)**
   - Delegate the actual planning to the Agent tool with `subagent_type: "Plan"` (Claude Code's standard implementation-planning agent). This agent cannot write files itself, so it must return each plan's full content directly in its response — see step 5. Do not just hand the task off blindly; make the following constraints explicit in the prompt:
     - **Granularity: one commit = one implementation plan.** Split the work into units that are easy to review and roll back.
     - **Each plan is assumed to run in a brand-new Claude Code session that holds none of this conversation's context.** The plan documents must not contain references that only make sense in this conversation (e.g. "as discussed above"). Write all necessary background, purpose, and technical context self-contained within each plan.
     - **Each plan must open with a small structured header** giving its dependencies and file scope, exactly in this form:
       ```
       ---
       depends_on: [none]   # or a list of seq numbers this plan requires to land first, e.g. [01, 02]
       files:
         - relative/path/to/file/one
         - relative/path/to/file/two
       ---
       ```
       This header is machine-read by `/impl-flow:implement` to decide what can run in parallel — it must be accurate and complete. A plan's `files` list is a hard boundary: the implementer must not touch files outside it (make this explicit in the plan body too, in the instructions the implementer will follow).
     - Include the verification method decided in step 3 in each plan.

5. **Save the plan files**
   - After the `Plan` agent returns the plans, **you** (the calling session, which has `Write`) save each one — the `Plan` agent cannot write files itself.
   - Create `{task-set directory}/before/` if it doesn't exist, and an empty `{task-set directory}/after/` alongside it.
   - Save each plan as `{task-set directory}/before/{seq}-{title}.md` (`seq` is `01`, `02`, ... in dependency order; if `before/` or `after/` already contain plans from an earlier run, continue the numbering from the highest existing `seq` instead of restarting at `01`).
   - Each file should include, after the structured header from step 4:
     - Purpose / goal
     - Prerequisites / dependencies on other plans, in prose (restating `depends_on`, for a human reader)
     - Implementation steps
     - Verification method and definition of done
     - Suggested commit message

6. **Closing**
   - Present the list of created plans (seq / title / dependencies / files touched) to the user as a table and invite review.
   - Let the user know that once review, revisions, or distribution are done (in this session or a later one), they can start implementation with `/impl-flow:implement {task-set directory}` whenever ready — it will pick up whatever is still in `before/`.
