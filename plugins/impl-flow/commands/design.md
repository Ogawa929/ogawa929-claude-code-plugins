---
description: Interactively interview the user to nail down requirements for a new implementation, then record them as a use-case document at the root of the task-set directory before feeding into the plan phase (Phase 1 of impl-flow: design -> plan -> implement). Not a standalone command — only invoked via /impl-flow:spec or /impl-flow:all.
argument-hint: [summary of what to implement]
model: opus
effort: xhigh
disable-model-invocation: true
user-invocable: false
---

# impl-flow: design

You are about to nail down the "design" for an implementation through a dialogue with the user. This phase runs on the opus model at `xhigh` effort — prioritize deep thinking and careful back-and-forth with the user. The effort level is fixed high here on purpose: how complex the work really is only becomes clear *through* this interview, so there is nothing to scale it against yet, and this is the cheapest phase in output tokens but the one every later phase inherits its quality from.

Do not write any code in this phase. This phase writes exactly one file — a **use-case document** capturing the requirements the interview settled on — and creates the task-set directory that holds it (step 4). That document is a specification for humans to read and review; it is not the implementation plan. The implementation plans are a separate deliverable, produced later by `/impl-flow:plan` into a `before/` folder beside this document, and they are written to be self-contained rather than to reference it.

## Steps

1. **Grasp the summary**
   - If `$ARGUMENTS` is given, treat it as the summary of what to implement.
   - If not, ask the user what they want to implement.

2. **Explore the codebase before asking anything**
   - Before interviewing the user, read the parts of the codebase relevant to what they described: existing files, interfaces, and patterns this implementation would need to fit into or reuse.
   - Use this to ground the interview in reality — you should already know what's technically feasible, what conventions exist, and what's ambiguous purely because of the codebase, before asking the user anything.

3. **Brainstorm the requirements (most important step)**
   - Always stop and consider whether the given information is enough to start implementation.
   - Identify missing information, ambiguities, and points that need a decision, and confirm them with the user **using the AskUserQuestion tool**.
   - Cover technical implementation, UI/UX, edge cases, concerns, and trade-offs. **Do not ask obvious questions — dig into the hard parts the user may not have considered**, especially ones you surfaced by reading the codebase in step 2.
   - When asking, never just float a single option and ask "does this work?" — **always present multiple alternatives with their trade-offs** and let the user pick.
   - Do not stop after one round. If the answers raise new questions, run further rounds. Keep going until you can confidently say the requirements are fixed.
   - Explicitly listing what is out of scope ("things we will not do") should also be offered as one of the alternatives.

4. **Write the use-case document**
   - Only start this step once the interview in step 3 has actually converged. This document records decisions; it is not a place to park open questions you could still have asked.
   - **Decide where it goes.** The document lives at the root of the task-set directory, as a sibling of the `before/` and `after/` folders the plan phase will create there:
     ```
     {task_dir}/{yyyymmdd}-{title}/
     ├── usecases.md   <- this document
     ├── before/       <- created later by /impl-flow:plan
     └── after/        <- created later by /impl-flow:plan
     ```
     - This means **the design phase is what fixes the task-set directory**, not the plan phase. Settle it here:
       - Confirm the root directory where task sets are stored with AskUserQuestion. Default: `task`. If `{task_dir}` already exists with dated task sets in it, use it without asking.
       - Look under `{task_dir}` for an existing `{yyyymmdd}-{title}/` that clearly covers the same requirements. If there is one, show the user what is in it and ask whether to reuse it (updating its `usecases.md`) or start a fresh dated one. Never silently overwrite an existing `usecases.md` — if the user chooses to update it, show what is changing.
       - Otherwise create `{task_dir}/{yyyymmdd}-{title}/`, where `{yyyymmdd}` is today's date and `{title}` is a short kebab-case title agreed on with the user. Create only that directory and `usecases.md` inside it — leave `before/` and `after/` to the plan phase, which uses their presence to judge whether planning has already run.
     - **Carry the chosen path forward.** The plan phase reuses this exact directory rather than picking its own, so state it explicitly when you close out in step 5.
   - **Structure.** Follow this outline:
     ```markdown
     # {Title}

     - Date: {yyyy-mm-dd}
     - Status: requirements fixed (not yet implemented)

     ## Background / Purpose
     ## Scope
     ### In scope
     ### Out of scope
     ## Key decisions and rejected alternatives
     | Decision | Chosen | Rejected alternatives | Why |
     ## Use cases
     | ID | Use case | Actor | Trigger | Expected result |
     | UC-01 | ... | ... | ... | ... |
     ### UC-01 {name}
     - Preconditions
     - Input
     - Main flow
     - Expected result
     - Alternative / exception flows — each one with its own expected result
     ## Relevant files and interfaces
     ## Open concerns
     ```
   - **The use-case list is the point of this document.** Hold it to these rules:
     - **Every use case must state a concrete, observable expected result** — a return value, a state change, what the user sees, the exact error surfaced. "Works correctly" or "handled appropriately" is not an expected result; if you cannot state what comes back, the requirement is not yet fixed and you should go back to step 3.
     - **Cover failure and boundary cases as their own use cases**, not as footnotes on the happy path. Invalid input, missing permissions, absent or conflicting state, empty and maximum sizes, concurrent or repeated invocation — whichever of these actually apply here.
     - Give each use case a stable `UC-nn` ID and keep the summary table consistent with the detail sections below it.
     - Every decision confirmed via AskUserQuestion in step 3 belongs in either the use-case list or the decisions table, and everything the user ruled out belongs under "Out of scope" or in the rejected-alternatives column.
   - **Write it self-contained**, for someone who was not part of this conversation: no "as discussed above", no references to the interview itself. Describe behaviour in terms of the system, not in terms of the diff that will produce it.

5. **Closing**
   - Show the user the path of the document you wrote and the task-set directory it now defines, summarize the finalized requirements back in the conversation, and do a final check for any misalignment. Invite them to review and correct the document by hand — it is a normal file in their repository.
   - Tell the user that `/impl-flow:plan` can be used next to turn this into implementation plans, and that it will fill in `before/` alongside this document. Note that the document is a specification, not a substitute for this conversation: running `/impl-flow:plan` in this same session carries the full context forward, while running `/impl-flow:plan {task-set directory}` standalone in a new session later means it works from `usecases.md` plus whatever they restate to it directly (`/impl-flow:plan` supports that).
