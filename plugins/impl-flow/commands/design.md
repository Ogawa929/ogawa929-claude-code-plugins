---
description: Interactively interview the user to nail down requirements for a new implementation, purely through dialogue — produces no file, feeds directly into the plan phase (Phase 1 of impl-flow: design -> plan -> implement). Not a standalone command — only invoked via /impl-flow:spec or /impl-flow:all.
argument-hint: [summary of what to implement]
model: opus
effort: xhigh
disable-model-invocation: true
user-invocable: false
---

# impl-flow: design

You are about to nail down the "design" for an implementation through a dialogue with the user. This phase runs on the opus model at `xhigh` effort — prioritize deep thinking and careful back-and-forth with the user. The effort level is fixed high here on purpose: how complex the work really is only becomes clear *through* this interview, so there is nothing to scale it against yet, and this is the cheapest phase in output tokens but the one every later phase inherits its quality from. Do not write any code, and do not write any file — the only deliverable of impl-flow is implementation plans, produced by `/impl-flow:plan`. This phase's job is purely to get the requirements right in conversation before that happens.

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

4. **Closing**
   - Summarize the finalized requirements back to the user in the conversation — background/purpose, scope (in/out), requirements list, key decisions and rejected alternatives, relevant files/interfaces found in step 2, open concerns — and do a final check for any misalignment. Do not write this to a file.
   - Tell the user that `/impl-flow:plan` can be used next to turn this into implementation plans. Note that since nothing was persisted to disk, running `/impl-flow:plan` in this same session is what carries these requirements forward; running it standalone in a new session later means restating the requirements to it directly (`/impl-flow:plan` supports that).
