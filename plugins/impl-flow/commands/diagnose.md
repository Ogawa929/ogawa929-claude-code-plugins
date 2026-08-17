---
description: Pin down a bug or change request against an existing use-case document, find the root cause, revise the affected use cases, and hunt for what a partial fix would miss through a three-layer omission review (Phase 1 of impl-flow's fix mode: diagnose -> plan -> implement). Not a standalone command — only invoked via /impl-flow:fix.
argument-hint: [the bug report or change request]
model: opus
effort: high
disable-model-invocation: true
user-invocable: false
---

# impl-flow: diagnose

You are about to pin down a **change to something that already exists** — a bug, a regression, or a revision to behaviour that was already specified. This is the fix-mode counterpart of `design.md`, and the difference between them is where the hard work sits: in design, *what to build* is unknown and the interview carries the weight; here, what to build is largely known and **where the change spreads to** is the unknown that carries it.

Do not write any code in this phase. This phase revises exactly one file — the **existing use-case document** of the task set that owns the affected behaviour — and then puts the revision through an omission review (step 7). The implementation plans are a separate deliverable, produced afterwards by `plan.md` into the same task set's `before/`.

Everything here assumes the affected behaviour already has a use-case document. Step 2 is what establishes that, and it is also the step that sends the work elsewhere when it does not hold.

## Steps

1. **Grasp the report**
   - If `$ARGUMENTS` is given, treat it as the reported symptom or change request.
   - If not, ask the user what is wrong, or what needs to change.
   - Keep the user's own wording — you will hand it to the reviewer verbatim in step 7, and their phrasing of the symptom is evidence.

2. **Find the task set that owns the behaviour, and read all of it**
   - Look under the task directory (default `tasks`) for the task set whose `usecases.md` covers the reported behaviour. If several are plausible, show the user what each one covers and let them pick with AskUserQuestion.
   - Then read, completely:
     - `{task-set directory}/usecases.md` — the current specification of what the system does.
     - **Every plan in `after/` and `before/`.** Their `files:` headers, taken as a union, are the recorded set of files this task set has touched. This is the single most valuable input to step 7 — it is a record, not a guess, and no amount of grepping reconstructs it as reliably.
   - **If no `usecases.md` covers the reported behaviour, stop and put it to the user** rather than improvising. Do not retro-generate a whole specification for existing code — that costs exactly as much as a full design phase and produces a document nobody reviewed. Offer:
     - Run `/impl-flow:spec` instead, treating this as new work.
     - Proceed here anyway against a fresh task set whose `usecases.md` covers **only the scope being touched**, not the surrounding system. Say plainly that step 7's layer 2 will be weak in that case, because there is no recorded file set to check against.

3. **Reproduce the symptom and classify it**
   - Establish the reproduction conditions, the actual observable result, and the result the document leads a reader to expect. Run the code or the tests where that is possible; say so plainly when it is not.
   - Then classify the report as exactly one of these, and report which:
     - **A — implementation defect.** A use case already states the correct expected result and the code violates it. `usecases.md` needs no change, or at most a sharpening of wording that was loose enough to permit the bug.
     - **B — specification defect.** The code matches what the document says, and what the document says is wrong or missing. The document has to change, and so does the code.
     - **C — new requirement.** Behaviour no use case covers, that nobody implemented wrongly. This is an addition, not a fix.
   - The classification decides how much of the document moves, so do not skip it. **A broad C belongs in `/impl-flow:spec`, not here** — say so and stop, rather than growing this phase into a design phase. A narrow C (one or two use cases inside an existing task set) is fine to carry on with.
   - **Interview only where the expected result is genuinely undecided**, using AskUserQuestion, and cap it at one or two rounds. Do not re-run design's requirements interview: the surrounding requirements are already fixed and already in the document. Ask about what the corrected behaviour should be, not about what the feature is for.

4. **Find the root cause**
   - Read the code until you can name the mechanism: the file and line where the behaviour diverges, and why. Do not patch anything.
   - Being able to state the cause is a precondition for planning a fix. **If you cannot pin it down, stop and report that**, together with what you ruled out — a plan built on a guessed cause produces a fix that changes symptoms rather than behaviour.
   - Note whether the cause sits inside the file set gathered in step 2 or outside it. Outside means the task set's recorded scope was already incomplete, which raises the stakes for step 7.

5. **Decide the use-case diff, explicitly, before editing anything**
   - Write the diff out in the conversation first, as a table: the `UC-nn` ID, the operation, and what changes.
   - Four operations, and no others:
     - **rewrite** — the use case stays, its expected result (or input, or flow) changes. Keep the same ID.
     - **add** — new behaviour, new ID, continuing from the highest ID in the document.
     - **retire** — the behaviour goes away. Remove the use case and **leave its ID as a gap.**
     - **in scope, unchanged** — the use case is correct as written but the fix touches its implementation, so it has to be re-verified. It appears in the diff and in the plans, but the document does not change.
   - **Never reuse a retired ID.** The plans in `after/` reference use cases by ID, and reusing one silently re-points that history at different behaviour. Gaps in the numbering are the intended, permanent record of a retirement.
   - Update the `Status` line to reflect reality — the document is no longer "requirements fixed (not yet implemented)" as a whole. State what is implemented and what is pending, e.g. `implemented; UC-03 revised and UC-08 pending`.
   - **Do not add a change-log, a revision-history section, or a "fixed in" note.** `git` holds the diff, and the document's job is to state what the system does now. This is the same constraint design.md places on scope sections and decision tables, for the same reason.

6. **Apply the diff**
   - Edit `usecases.md` **in the task set found in step 2.** Do not create a new dated task-set directory: the document is the single current statement of the behaviour, and a second copy elsewhere immediately starts to rot. New plans go into the same task set's `before/`, and `plan.md` continues the `seq` numbering from what is already there.
   - Every rule design.md puts on this document still applies: concrete observable expected results, failure and boundary cases as their own use cases, short detail sections, no reference to this conversation.
   - Show the user the resulting diff of the file.

7. **Put the revision through a three-layer omission review**
   - The revision is a **draft** until this step has run and its findings are triaged. This is the step that earns fix mode its existence: the failure mode of a partial fix is not a wrong specification but an **incomplete** one, applied in one of several places that needed it.
   - **Ask the user how far to take the review before dispatching anything**, with AskUserQuestion, stating your recommendation first and putting it first in the list. Ground the recommendation in what you found: the classification from step 3, the size of the file set from step 2, and whether the root cause sat outside it.
     - **Full** — opus, `ultrathink`, all three layers, every omission type in layer 3, up to two rounds. Recommend it when the cause sat outside the recorded file set, when layer 2's file set is large, when the fix changes an expected result other use cases build on, or when the behaviour is expensive to get wrong.
     - **Light** — one round, no `model` override (inherit). Layers 1 and 2 in full — they are cheap, because both run against records you already gathered — plus only the layer-3 omission types that bear on the diagnosed cause. Report `blocker` and `should-fix` only. The resolution verdict is still required. Recommend it for a class-A defect with a single, clearly localized cause.
     - **Skip** — no review. Say plainly, here and again in step 9, that the revision went unreviewed and that a partial fix is the risk being accepted.
   - **Dispatch an independent reviewer** with the Agent tool: `subagent_type: "general-purpose"`, and for Full, `model: "opus"` with the word `ultrathink` in the prompt. Run it in the foreground.
   - **Give it the artefacts and the repository, not your reasoning.** Pass: the path to the revised `usecases.md`, the task-set directory, the reported symptom in the user's own words, and the root-cause location you identified in step 4. Withhold why you believe the diff is correct and complete — that belief is precisely what the review exists to test. Unlike design.md's reviewer, this one does need the symptom and the cause, because without them it cannot judge the resolution verdict; it does not need anything else from the interview.
   - **The three layers** — each one asks "what else needed to change?" against a different source of truth:

     | Layer | Source of truth | The question |
     | :-- | :-- | :-- |
     | 1. Specification consistency | the revised `usecases.md` alone | Does any other use case still assume the old behaviour? A rewritten expected result in one use case routinely contradicts a precondition, an input, or an alternative flow stated in another. |
     | 2. Implementation coverage | the union of `files:` across `after/` and `before/`, plus the document's "Relevant files and interfaces" | Is the changed behaviour realized in more than one place inside this recorded set? Every file in the set is in scope for the question, and the answer is checkable rather than speculative. |
     | 3. External spillover | the repository at large — `git log`, grep, the test suite | What outside the recorded set depends on the behaviour that is changing? |

   - **Layer 3 omission types** — work through these by name; they are the recurring shapes of a missed edit, and a review that reports nothing must state which of them it checked:
     - **Copy-paste sibling** — the same defective logic exists elsewhere, duplicated rather than shared. This is the single most common omission in a bug fix, and the one a plan scoped to the reported symptom is most likely to miss.
     - **Contract change** — the fix alters a return value, an exception, a nullability, or a thrown-versus-returned decision, and callers were written against the old contract.
     - **Stale test** — an existing assertion encodes the old expected result and will keep passing, or will start failing for the right reason and get "fixed" back.
     - **Paired-update miss** — a type, schema, migration, config key, constant table, or fixture that has to move in lockstep with the code and does not.
     - **One-sided path** — the write path is corrected and the read path is not, or the reverse; likewise serialize/deserialize, encode/decode, add/remove.
     - **Documentation drift** — a README, comment, or another task set's `usecases.md` still describes the old behaviour.
   - **Ask it one question the layers cannot reach**, at every depth including Light: *does the revised use-case list, taken as a whole, actually resolve the reported symptom?* The three layers measure whether the revision is complete and consistent; none of them checks that it is aimed at the right thing. A diff can be internally flawless and still leave the reported bug in place.
     - Answer required in one of two forms: `resolves` — with the chain from symptom to cause to the use case to its expected result — or a statement of what the symptom demands that no use case delivers.
     - A `does not resolve` verdict sends the work back to step 3 or step 4, not to the editor. Take it to the user with AskUserQuestion.
   - **Require a specific report shape:**
     - A coverage line first, per layer: how many use cases layer 1 compared, how many files layer 2 examined out of the recorded set, and which layer-3 types layer 3 checked. This is what makes a short report credible — three findings after examining forty files is a strong result; three findings with no coverage line has not done the work.
     - Then the findings, ranked, each with: severity (`blocker` / `should-fix` / `nit`), the layer, the file or `UC-nn` it lands on, the concrete thing that would still be wrong after the fix as currently specified, and the one edit that would prevent it.
     - Then, last, the resolution verdict.
     - **Consolidate hard — one finding per missing edit.** Findings that a single change would resolve together are one finding. If two findings resolve to the same edit, the report is malformed.
     - Findings resting on guesses about the codebase must be labelled unverified. The reviewer must not edit any file.
   - **Triage the findings yourself. Do not apply them wholesale.** For each one: wrong or deliberately out of scope → drop it and keep a one-line reason for step 9; a real gap you can close without a new decision → fix `usecases.md`, or note it as a file that must appear in a plan's `files` list; a real gap needing a decision → back to step 3 with AskUserQuestion.
   - **Re-dispatch once, Full depth only,** if the revision changed substantially — new use cases, or changed expected results. Tell the second run to re-derive its layers from the revised document. One further round is the limit.
   - The review is not part of the deliverable. No findings log and no "reviewed by" line goes into `usecases.md`.

8. **Set the verification contract**
   - `plan.md` will ask the user how to verify. Fix mode fixes one part of that answer in advance, and it is not negotiable: **every plan must first add a test that fails for the reported symptom, and pass only once it goes green.** Neither the layered review nor any amount of grepping proves the fix is complete; a regression test is the only thing here that proves anything, and it is what stops the same bug returning through a later refactor.
   - Where the symptom genuinely cannot be captured by an automated test, say so explicitly and record the manual reproduction steps in its place. Do not let that be the default.
   - Carry two more things forward for `plan.md` to fold into the plans:
     - Every "in scope, unchanged" use case from step 5 has to be re-verified, even though the document did not change for it.
     - Every file a layer-2 or layer-3 finding landed on has to appear in some plan's `files` list, or be explicitly recorded as deliberately excluded. This is the mechanism that carries the review's result into execution instead of leaving it in the conversation.

9. **Closing**
   - Show the user the path of the revised document, the classification from step 3, the root cause, and the use-case diff as applied.
   - Report the review outcome in a few lines, naming the depth that ran: the coverage line, what changed the document or the file scope, and what you dropped and why. If it was skipped or run Light, state plainly what has not been checked, and that either depth can still be run on the document as it stands. A finding you rejected is only actually rejected once the user has seen it.
   - State the task-set directory explicitly. `plan.md` reuses this exact directory and appends to its `before/` — it does not create a new one.
