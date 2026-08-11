---
description: Execute the pending implementation plans in a task-set directory. The main session acts as leader and dispatches each plan to an implementation subagent sized to that plan's declared complexity, running independent plans in parallel within a single branch (Phase 3 of impl-flow: design -> plan -> implement)
argument-hint: [task-set directory, e.g. tasks/20260802-my-feature]
effort: medium
disable-model-invocation: true
---

# impl-flow: implement

You are about to act as the leader of the "implementation & verification" phase, executing the plans still pending in a task-set directory's `before/` folder. Actual code changes must always be made by subagents — do not edit code directly yourself. Focus on reading the plans, deciding execution order, dispatching subagents, committing, moving completed plans to `after/`, and aggregating results.

This command deliberately runs the leader at `medium` effort: the leader's job here is orchestration, not design. The reasoning depth for the actual code changes comes from the implementation subagents, whose own frontmatter `effort` overrides the session level.

All work happens directly on the current branch, in the current working tree — there is no branch-per-plan and no merging. Parallelism here means multiple plans get *implemented and verified* concurrently, not that git history forks and rejoins.

## Steps

1. **Identify the task-set directory**
   - If `$ARGUMENTS` is given, use it.
   - If not, look under the task directory (default `tasks`) for task-set directories that have pending plans in `before/`, and let the user pick if there are multiple candidates.
   - If `before/` is empty, tell the user this task set has nothing left to implement (everything is already in `after/`) and stop.

2. **Read the plans and check for dependency cycles**
   - Read every `{seq}-{title}.md` file in `{task-set directory}/before/`, in `seq` order.
   - Parse each plan's structured header (`depends_on`, `files`, `complexity`) — do not rely on guessing these from prose.
   - Build the dependency graph from `depends_on`. If it contains a cycle, stop immediately, report exactly which plans are involved, and do not batch or execute anything until the user resolves it.

3. **Design the execution batches**
   - Split the plans into batches (execution groups) using these criteria:
     - Plans with a dependency relationship must run in order: a later batch only starts once the batch containing its dependency has completed.
     - Even without a dependency relationship, **do not run two plans in the same batch in parallel if their declared `files` overlap** (this risks mixing up changes at commit time).
     - Plans with no dependency relationship and no overlap in `files` may run in parallel within the same batch, provided their verification steps either do not interfere with each other or can be verified together.
     - When in doubt, default to the safe option (sequential execution).
   - Report the batching result (which plan is in which batch, parallel or sequential, why, and which subagent each plan will be dispatched to per step 4) to the user as an informational summary, then proceed — this is not a confirmation gate; the design/plan phases already established what should be built, so do not block execution waiting for approval here.

4. **Pick the implementation subagent for each plan**
   - Each plan's declared `complexity` selects which subagent implements it. The Agent tool has no per-call effort parameter, so the effort level comes from these subagent definitions, which ship with this plugin:

     | `complexity` | `subagent_type` | Model / effort |
     | :-- | :-- | :-- |
     | `low` | `impl-flow:implementer-light` | sonnet, `medium` |
     | `medium` | `impl-flow:implementer-standard` | sonnet, `high` |
     | `high` | `impl-flow:implementer-deep` | opus, `xhigh` |

   - **Do not pass `model` on these dispatches** — it would override the model the subagent definition already pairs with its effort level.
   - If a plan has no `complexity` field, or an unrecognized value, treat it as `medium` and say so in the batching report rather than failing.
   - You may raise a plan one level above its declared complexity if you have a concrete reason from reading the plan (for example, it is a retry of a plan that already failed once). Say why in the report. Never lower a declared complexity.

5. **Execute each batch**
   - Process batches in list order, sequentially. Only run the parallel path below when a batch contains more than one plan.

   ### Parallel execution (batch contains multiple plans)

   - Call the Agent tool once per plan, all within a single message (so they run concurrently), each with the `subagent_type` chosen in step 4. Pass the full text of the corresponding plan file as the prompt. The subagents already carry the standing rules below in their own definitions, but restate them in the prompt so they survive regardless of which subagent was chosen:
     - Implement exactly per the plan, then run the verification it describes.
     - **Do not touch any file outside the plan's declared `files` list.** If the work turns out to require touching an undeclared file, stop without writing anything further and report that instead of proceeding.
     - **Do not run `git add` or `git commit` yourself.** Report back which files you changed and a suggested commit message; the leader will commit.
   - Wait for every agent in the batch to finish (this is a barrier).
   - For each plan in the batch, **in ascending `seq` order**, one at a time: stage exactly the files that agent reported changing and commit them (`git add <files> && git commit -m "..."`). Committing one at a time, strictly sequentially, is what keeps concurrent implementation safe without needing branch isolation — never stage or commit for two plans at once.
   - For each plan that committed successfully, move its file from `before/{seq}-{title}.md` to `after/{seq}-{title}.md`.
   - After all commits in the batch have landed, **always run one consolidated verification pass** on the resulting state (e.g. re-run the test suite), even if each plan verified individually — two plans with non-overlapping files can still be semantically coupled, and this is what catches that. Report the result; do not silently assume success just because the individual verifications passed.

   ### Sequential execution (batch contains exactly one plan)

   - Call the Agent tool once, with the `subagent_type` chosen in step 4. Give it the same instructions as above (stay within declared `files`, do not commit, report changed files + suggested message).
   - If verification fails, do not stage or commit anything for this plan — leave the working tree changes in place for inspection and report the failure, exactly as in the parallel path.
   - On success, stage and commit as above, then move the plan file from `before/` to `after/`.

   ### Handling failures

   - A plan whose implementation or verification fails must not be committed. Leave its changes in the working tree (or ask the user before discarding them) and leave its file in `before/`, and record the failure clearly.
   - If a later batch depends on the failed plan, stop there and report it. If there are independent plans that don't depend on it, they may continue.

6. **Final report**
   - After all batches finish, report to the user:
     - The list of commits created (plan seq, commit hash, commit message)
     - The verification result for each plan, plus the result of any consolidated post-batch verification
     - Which subagent each plan ran on, so a plan whose `complexity` was clearly mis-rated can be corrected before it is retried
     - How many plans are now in `after/` versus still remaining in `before/`
     - Any failed or incomplete plans, along with recommended next actions (plans left in `before/` can simply be retried with `/impl-flow:implement {task-set directory}` again later)
