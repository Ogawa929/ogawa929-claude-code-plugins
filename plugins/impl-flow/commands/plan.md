---
description: Turn a design (or direct requirements) into commit-sized implementation plan files, each self-contained enough to run in a brand-new Claude Code session (Phase 2 of impl-flow: design -> plan -> implement). Not a standalone command — only invoked via /impl-flow:spec or /impl-flow:all.
argument-hint: [task-set directory, e.g. task/20260802-my-feature]
disable-model-invocation: true
user-invocable: false
---

# impl-flow: plan

You are about to create the "implementation plans". Do not write any code yet. The goal is to produce a set of plan documents at a granularity that lets each subsequent implementation phase run safely in its own independent session.

## Steps

1. **Gather the input**
   - If `/impl-flow:design` was just run in this same session, use the requirements finalized there. It also settled the task-set directory and wrote `{task-set directory}/usecases.md`; treat that document as the authoritative statement of *what behaviour is expected*, and this conversation as the additional context around it. If the user edited the document after it was written, re-read it — their edits win over what was said in the conversation.
   - Otherwise (this command was invoked directly, standalone), check whether enough information is available to plan the implementation:
     - Look for a `usecases.md` at the root of the task-set directory you are being pointed at (or, if `$ARGUMENTS` is absent, under the existing task sets). If you find a plausible one, tell the user which file you intend to plan from and confirm it before relying on it — never silently plan from a document they did not point you at.
     - If there is no such document and the request is under-specified, interview the user briefly yourself before continuing (you don't need the full multi-round rigor of `/impl-flow:design`, but don't guess at missing specifics either). Do not write a use-case document yourself in this path — that is the design phase's deliverable, and `/impl-flow:spec` is the way to get one.

2. **Identify or create the task-set directory**
   - If `/impl-flow:design` ran in this session, it already settled the task-set directory and put `usecases.md` there. **Use that directory and skip the rest of this step** — do not ask the user to choose again, and do not create a second dated directory for the same work.
   - If `$ARGUMENTS` is given, treat it as the task-set directory and skip the rest of this step.
   - Otherwise, use AskUserQuestion to confirm the root directory name where implementation plans are stored. Default: `task`.
   - Look under `{task_dir}` for a directory that clearly overlaps with the requirements gathered in step 1. A task-set directory has the shape `{task_dir}/{yyyymmdd}-{title}/`; once planning has run in it, it contains a `before/` subdirectory (plans not yet executed) and an `after/` subdirectory (plans already committed). Its state is always determined by these two subdirectories, never guessed:
     - `before/` has files and/or `after/` is empty or absent → this task set is **not finished**.
     - `before/` is empty or absent and `after/` has files → this task set **looks finished**.
     - Neither exists (a bare task-set directory holding only `usecases.md`, an empty one, or nothing at all) → planning hasn't happened there yet. A directory left by the design phase looks exactly like this, and is the normal case to plan into.
   - If a relevant directory exists, tell the user plainly which of these states it's in, and ask whether to reuse it (adding more plans, or replacing the pending ones in `before/`) or start a fresh dated one. Never silently overwrite an existing plan file.
   - If starting fresh, combine today's date (`{yyyymmdd}`) with a short title agreed on with the user (e.g. kebab-case) to create `{task_dir}/{yyyymmdd}-{title}/`. Reaching this point means there is no `usecases.md` to plan from — say so plainly, since the plans will then rest on this conversation alone.

3. **Confirm the verification method**
   - Check whether the user has a preferred verification method to build into the plans (e.g. running the existing test suite, adding unit tests for the affected scope, lint/typecheck only, manual verification steps, etc.).
   - If not specified, propose several alternatives based on the state of the codebase and let the user choose via AskUserQuestion. Decide whether verification should differ per plan or be a single overall policy shared by all plans.

4. **Create the implementation plans (using the Plan agent)**
   - Delegate the actual planning to the Agent tool with `subagent_type: "Plan"` (Claude Code's standard implementation-planning agent). This agent cannot write files itself, so it must return each plan's full content directly in its response — see step 5.
   - **Scale the planning run to the requirements.** By the time this step runs, the design phase has already established the shape of the work, so you know how hard it is. The Agent tool has no per-call effort parameter, so `model` and the `ultrathink` keyword are the only levers available at dispatch time:
     - Requirements that are broad, architecturally load-bearing, span several subsystems, or still carry unresolved technical risk → dispatch with `model: "opus"` and include the word `ultrathink` in the prompt (Claude Code recognizes the keyword and adds an in-context instruction for deeper reasoning on that turn; it does not change the effort level sent to the API).
     - Narrow, mechanical, or well-trodden requirements — one subsystem, an established pattern to copy — → dispatch with `model: "sonnet"`.
     - Otherwise omit `model` and let it inherit. Either way the subagent inherits the session's effort level; do not try to pass `effort` to the Agent tool, it is not a parameter there.
   - Do not just hand the task off blindly; make the following constraints explicit in the prompt:
     - **Granularity: one commit = one implementation plan.** Split the work into units that are easy to review and roll back.
     - **Each plan is assumed to run in a brand-new Claude Code session that holds none of this conversation's context.** The plan documents must not contain references that only make sense in this conversation (e.g. "as discussed above"). Write all necessary background, purpose, and technical context self-contained within each plan.
     - **Each plan must open with a small structured header** giving its dependencies, file scope, and complexity, exactly in this form:
       ```
       ---
       depends_on: [none]   # or a list of seq numbers this plan requires to land first, e.g. [01, 02]
       files:
         - relative/path/to/file/one
         - relative/path/to/file/two
       complexity: medium   # low | medium | high
       ---
       ```
       This header is machine-read by `/impl-flow:implement` to decide what can run in parallel and which implementation subagent to dispatch — it must be accurate and complete. A plan's `files` list is a hard boundary: the implementer must not touch files outside it (make this explicit in the plan body too, in the instructions the implementer will follow).
     - **Each plan must declare its own `complexity`**, judged on its own merits rather than inherited from the overall feature — a large feature routinely contains `low` plans, and a small one can contain a `high` plan:
       - `low` — mechanical and well-scoped. Config or wiring changes, a rename, one more case in an existing switch, copying an established pattern into one more place. Little judgement needed while implementing.
       - `medium` — the default. New code following an existing pattern, a handful of files, ordinary edge cases and error handling.
       - `high` — real design judgement is required *during* implementation: non-trivial algorithms or state management, concurrency, data migrations, cross-cutting refactors, tricky failure modes, or anywhere the plan unavoidably leaves decisions to the implementer.
       - When torn between two levels, pick the higher one. This field selects the model and effort level the implementation subagent runs at, so under-rating a plan costs correctness while over-rating it only costs tokens.
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
   - Present the list of created plans (seq / title / dependencies / files touched / complexity) to the user as a table and invite review. Mention that `complexity` decides which model and effort level each plan is implemented at, so it is worth correcting by hand if a rating looks wrong.
   - Let the user know that once review, revisions, or distribution are done (in this session or a later one), they can start implementation with `/impl-flow:implement {task-set directory}` whenever ready — it will pick up whatever is still in `before/`.
