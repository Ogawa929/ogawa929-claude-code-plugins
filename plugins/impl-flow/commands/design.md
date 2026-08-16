---
description: Interactively interview the user to nail down requirements for a new implementation, record them as a use-case document at the root of the task-set directory, and harden it through an adversarial review by an independent agent before feeding into the plan phase (Phase 1 of impl-flow: design -> plan -> implement). Not a standalone command — only invoked via /impl-flow:spec or /impl-flow:all.
argument-hint: [summary of what to implement]
model: opus
effort: xhigh
disable-model-invocation: true
user-invocable: false
---

# impl-flow: design

You are about to nail down the "design" for an implementation through a dialogue with the user. This phase runs on the opus model at `xhigh` effort — prioritize deep thinking and careful back-and-forth with the user. The effort level is fixed high here on purpose: how complex the work really is only becomes clear *through* this interview, so there is nothing to scale it against yet, and this is the cheapest phase in output tokens but the one every later phase inherits its quality from.

Do not write any code in this phase. This phase writes exactly one file — a **use-case document** capturing the requirements the interview settled on — and creates the task-set directory that holds it (step 4). Before that document is handed to the user it is put through an adversarial review by an independent agent (step 5), and revised. That document is a specification for humans to read and review; it is not the implementation plan. The implementation plans are a separate deliverable, produced later by `/impl-flow:plan` into a `before/` folder beside this document, and they are written to be self-contained rather than to reference it.

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
       - Confirm the root directory where task sets are stored with AskUserQuestion. Default: `tasks`. If `{task_dir}` already exists with dated task sets in it, use it without asking.
       - Look under `{task_dir}` for an existing `{yyyymmdd}-{title}/` that clearly covers the same requirements. If there is one, show the user what is in it and ask whether to reuse it (updating its `usecases.md`) or start a fresh dated one. Never silently overwrite an existing `usecases.md` — if the user chooses to update it, show what is changing.
       - Otherwise create `{task_dir}/{yyyymmdd}-{title}/`, where `{yyyymmdd}` is today's date and `{title}` is a short kebab-case title agreed on with the user. Create only that directory and `usecases.md` inside it — leave `before/` and `after/` to the plan phase, which uses their presence to judge whether planning has already run.
     - **Carry the chosen path forward.** The plan phase reuses this exact directory rather than picking its own, so state it explicitly when you close out in step 5.
   - **Structure.** Follow this outline exactly — these sections and no others. Keep it lean: the interview is deliberately exhaustive, but the document that comes out of it is not a transcript of it. Resist the pull to add a scope section, a decisions table, or an alternatives log; everything that matters belongs in the use-case list.
     ```markdown
     # {Title}

     - Date: {yyyy-mm-dd}
     - Status: requirements fixed (not yet implemented)

     ## Background / Purpose
     ## Use cases
     | ID | Use case | Actor | Trigger | Expected result |
     | UC-01 | ... | ... | ... | ... |
     ### UC-01 {name}
     - Preconditions — omit the bullet entirely if there are none
     - Input
     - Main flow — the observable steps only, at most a handful
     - Expected result
     - Alternative / exception flows — each one with its own expected result; omit the bullet if there are none
     ## Relevant files and interfaces
     ## Open concerns
     ```
   - **The use-case list is the point of this document.** Hold it to these rules:
     - **Every use case must state a concrete, observable expected result** — a return value, a state change, what the user sees, the exact error surfaced. "Works correctly" or "handled appropriately" is not an expected result; if you cannot state what comes back, the requirement is not yet fixed and you should go back to step 3.
     - **Cover failure and boundary cases as their own use cases**, not as footnotes on the happy path. Invalid input, missing permissions, absent or conflicting state, empty and maximum sizes, concurrent or repeated invocation — but only the ones that genuinely produce a different expected result *and* that someone could get wrong. This is a prompt to check the list, not to work through it: a case whose answer is "same as UC-01" is not a use case, and manufacturing one costs the reader more than it tells them.
     - **Keep the detail sections short.** A detail section exists to pin down what a table row has no space for — a precondition, the exact shape of the input, the precise error that surfaces. One line per bullet is the norm; drop the bullets that have nothing to add. Do not narrate internals (what the runtime, the framework, or the kernel does in between), and do not restate the row in longer words. **If a detail section would say nothing beyond its row, do not write one** — the row stands on its own, and use cases with and without a detail section can sit side by side.
     - Give each use case a stable `UC-nn` ID and keep the summary table consistent with any detail sections below it.
     - **Every decision confirmed via AskUserQuestion in step 3 has to be visible in the use-case list itself** — as the behaviour a use case expects, not as a decision recorded next to it. What the user ruled out is expressed by its absence: it simply has no use case. Where that absence would read as an oversight rather than a choice, say so in one line under "Background / Purpose" ("{X} is not covered here") — do not reintroduce a scope section to hold it.
     - Keep the alternatives that lost out of the document entirely. They belong to the interview, not to the specification of what the system does.
   - **Write it self-contained**, for someone who was not part of this conversation: no "as discussed above", no references to the interview itself. Describe behaviour in terms of the system, not in terms of the diff that will produce it.

5. **Put the draft through an adversarial review**
   - The document written in step 4 is a **draft** until it survives this step. Do not present it to the user as finished before the review has run and its findings have been triaged.
   - **Ask the user how far to take the review before dispatching anything**, with AskUserQuestion. This review is the most expensive part of the design phase — an opus subagent generating dozens of mutants, possibly twice — and whether that is worth it depends on the work, so it is the user's call and not yours.
     - Ask it blind at your peril: state your recommendation first, grounded in the draft you just wrote — how many use cases it has, how many subsystems it touches, whether any expected result was hard to pin down in the interview. Put the recommended option first and label it as such.
     - Offer exactly these three:
       - **Full** — everything below as written: opus, all seven mutation operators, up to two rounds. Recommend it when the draft is large, spans subsystems, carries failure modes that are expensive to get wrong, or came out of an interview that kept uncovering new requirements.
       - **Light** — one round, no `model` override (inherit), and only the operators that bear on this draft — normally expected-result swap, boundary move, and failure-path swap. Report `blocker` and `should-fix` only; skip the structural list. The purpose verdict is still required — it is one question and it is the only check that can catch the document specifying the wrong system. Recommend it for a small, single-subsystem draft whose expected results were obvious from the start.
       - **Skip** — no review. The draft as written becomes the document. Say plainly, here and again in step 6, that it went unreviewed.
     - Whatever they choose, the rest of this step applies unchanged except where the chosen depth says otherwise. Do not quietly re-expand a Light review into a Full one because the findings look interesting — report what you found and let the user ask for the full run.
   - **Dispatch an independent reviewer** with the Agent tool: `subagent_type: "general-purpose"`, `model: "opus"`, and the word `ultrathink` in the prompt. Run it in the foreground — the rest of this phase depends on its result.
   - **Give it the document and the repository, and nothing from this conversation.** Pass the path to `usecases.md` and let it read the file and the codebase itself; do not summarize the interview, do not explain what you meant, do not tell it which parts you are confident about. It cannot inherit the assumptions the interview quietly settled into, which is the entire reason it is worth dispatching — it can only judge what the document actually says.
   - **Brief it to run mutation testing against the document, not to proofread it.** The use-case list is the test suite; a hypothetical implementation is the code under test. The reviewer's job is to write *mutants* — implementations that differ observably from what the requirements intend, yet violate no sentence in the document — and see which ones the use-case list fails to kill.
     - A mutant is **killed** when some use case's expected result contradicts it outright. That use case did its job; there is nothing to report.
     - A mutant **survives** when the document permits it. Every surviving mutant is a hole, and the hole is *the missing statement*, not the mutant.
   - **Mutation operators** — where to mutate. Work through all of them; each one is a way to build something defensibly different while conforming to the text:
     - Swap the expected result for another observable one (a different return value, a different visible state, silence instead of output).
     - Move the boundary: empty, zero-length, one, maximum, duplicate, absent, concurrent, repeated invocation.
     - Swap the failure path: swallow the error, surface a different error, throw instead of returning, retry instead of failing, fail instead of retrying.
     - Reinterpret the input: another type, another format, another default when it is omitted.
     - Change side effects: their presence, their order, whether repeating the operation repeats them.
     - Delete an unstated precondition — implement as if it were never guaranteed.
     - Diverge from the codebase: pick a different existing pattern, a different file, a different interface than the one the document names, or one that does not exist.
   - **Consolidate hard — one finding per missing statement, not per mutant.** This is a requirement on the report, not a suggestion:
     - Mutants that a single added or corrected sentence in `usecases.md` would kill together are **one** finding. Name that sentence's absence as the finding, and cite one representative mutant plus a count of the rest.
     - Merge until no two findings would be fixed by the same edit. A report where two findings resolve to the same edit is a malformed report.
     - Findings that are not about a surviving mutant — a missing `UC-nn` ID, a stray section, a table row with no counterpart below — go in a single structural bullet list at the end, never as individual findings.
     - Prefer the smallest set of findings that covers every surviving mutant. Ten scattered nits that one paragraph would fix is one finding.
   - **Ask it one question that mutation testing cannot reach**, alongside the mutant run and at every depth including Light: *does the use-case list, taken as a whole, achieve what "Background / Purpose" says the work is for?* Mutants measure whether the document pins an implementation down; they say nothing about whether the pinned-down implementation is the right one. A document can kill every mutant and still specify a system that does not serve its stated purpose.
     - Answer required in one of two forms: `reachable` — the purpose is met, with the chain of use cases that gets there — or a statement of what the purpose demands that no use case delivers.
     - This is where the reviewer may attack a requirement itself rather than its wording: a use case that works against the stated purpose, a purpose that the use cases only partially cover, an assumption in the background that the codebase contradicts.
     - It reports as a single verdict at the end of the report, next to the structural list — never split across the ranked findings, and never merged into them.
     - A `not reachable` verdict is a step 3 problem, not an editing problem. Take it to the user with AskUserQuestion; do not patch the purpose section to match the use cases you already have.
   - **Require a specific report shape:**
     - A count line first: mutants generated / killed / surviving. This is what makes a short report credible — a review that reports few findings after killing sixty mutants is a strong result, while one that reports few findings with no counts has not done the work.
     - Then the findings, ranked, each with: severity (`blocker` / `should-fix` / `nit`), the `UC-nn` IDs or section it lands on, the representative surviving mutant *stated as a concrete implementation someone would actually ship*, how many further mutants the same gap admits, and the one edit to `usecases.md` that would kill them all.
     - Then, last, the purpose verdict and the structural list — in that order, and outside the ranked findings.
     - Findings resting on guesses about the codebase must be labelled as unverified. The reviewer must not edit any file.
   - **Triage the findings yourself. Do not apply them wholesale** — the reviewer lacks the context you have, and some of its surviving mutants will be behaviour the interview deliberately left open. For each one:
     - Wrong, or already settled deliberately → drop it. Keep a one-line reason; you will report it in step 6.
     - A real gap you can close without a new decision → fix `usecases.md`.
     - A real gap that needs the user to decide → **return to step 3** and put it to them with AskUserQuestion, then fold the answer into the document.
   - **Re-dispatch the reviewer once** — Full depth only — if the revision was substantial — new use cases, or changed expected results. Tell the second run to re-derive its mutants from the revised document rather than re-check the first run's list: an edit that kills the reported mutants routinely opens new ones. One further round is the limit: needing a third means the requirements never converged, and that belongs back in step 3, not in another review.
   - The review is not part of the deliverable. No findings log, no review section, no "reviewed by" line goes into `usecases.md` — the document records what the system does, and the findings live in the conversation.

6. **Closing**
   - Show the user the path of the document you wrote and the task-set directory it now defines, summarize the finalized requirements back in the conversation, and do a final check for any misalignment. Invite them to review and correct the document by hand — it is a normal file in their repository.
   - Report the outcome of the adversarial review in a few lines, naming the depth that was run: the mutant counts, what it found that changed the document, and what you deliberately dropped and why. If the review was skipped, or run at Light depth, say so here as a plain statement of what the document has not been checked against — and that either can still be run on the document as it stands. The user is the one who can overrule a dropped finding, so a finding you rejected is only actually rejected once they have seen it.
   - Tell the user that `/impl-flow:plan` can be used next to turn this into implementation plans, and that it will fill in `before/` alongside this document. Note that the document is a specification, not a substitute for this conversation: running `/impl-flow:plan` in this same session carries the full context forward, while running `/impl-flow:plan {task-set directory}` standalone in a new session later means it works from `usecases.md` plus whatever they restate to it directly (`/impl-flow:plan` supports that).
