# Skills and slash commands

Checklist for `skills/<name>/SKILL.md` and `commands/*.md`. Both use the same frontmatter, so the same rules apply; `commands/*.md` simply has no bundled files to check.

## Contents

- Hard limits (mechanical, checked by scan.py)
- Frontmatter fields
- Naming
- Description quality
- Body quality
- Invocation control
- Bundled files and progressive disclosure
- Deletion candidates

## Hard limits

| Rule | Limit |
|------|-------|
| `name` | ≤64 chars, lowercase letters/numbers/hyphens only, no XML tags, must not contain `anthropic` or `claude` — binding for a **plugin** skill, whose `name` sets the command users type, and for anything packaged for claude.ai or the Skills API. In a personal or project skill the command comes from the directory and `name` is only a display label, so treat a violation there as a packaging risk, not a defect |
| `description` | non-empty, ≤1,024 chars, no XML tags |
| `description` + `when_to_use` | truncated at 1,536 chars in the skill listing — put the key use case first |
| SKILL.md body | under 500 lines |
| Reference files | linked one level deep from SKILL.md; a table of contents once over 100 lines |
| Paths | forward slashes only, on every platform |

## Frontmatter fields

Recognized by Claude Code: `name`, `description`, `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `background`, `hooks`, `paths`, `shell`, `metadata`, `license`, `compatibility`. Anything else is ignored — flag it as dead configuration.

A skill that also ships to claude.ai, the Skills API, or `package_skill.py` may use only `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`; any other field makes packaging fail with a hard error. Flag this only when the user says the skill targets those paths.

Check the fields that carry cost:

- `allowed-tools` — pre-approves tools for the invoking turn. Flag grants wider than the skill needs (e.g. bare `Bash` where `Bash(git status *)` would do).
- `model` / `effort` — an override that pins every invocation to an expensive setting needs a reason in the body.
- `context: fork` — appropriate for long, self-contained jobs whose intermediate output the main conversation does not need; wrong when the skill's findings must stay in the main context.
- `paths` — a skill that only applies to part of the tree should carry it.

## Naming

Gerund form (`processing-pdfs`) is the house style in Anthropic's guidance; noun phrases (`pdf-processing`) and action forms (`process-pdfs`) are acceptable. Flag vague or generic names — `helper`, `utils`, `tools`, `documents`, `data` — and names inconsistent with the rest of the collection.

For a plugin skill the frontmatter `name` sets the last segment of the invoked command; for a personal or project skill the command comes from the directory name and `name` is only a display label. Flag a `name` that disagrees with its directory in a way that will confuse users.

## Description quality

The description is the only part loaded at startup, so discovery lives or dies here.

- **What and when.** It must say what the skill does *and* the situations that should trigger it. "Helps with documents" fails both.
- **Third person.** "Processes Excel files…", never "I can help you…" or "You can use this to…". Inconsistent point of view degrades discovery.
- **Concrete trigger terms.** Include the words a user would actually type, including file extensions, tool names, and — for a multilingual user — the phrasings in the languages they work in.
- **Negative triggers.** When a skill sits next to an adjacent one, a closing "Do NOT use for …" clause is what keeps them apart.
- **Front-loaded.** The primary use case goes first, before the caveats, because the tail is what gets truncated.

## Body quality

- **Conciseness.** Claude is already smart; only content Claude does not already have earns its tokens. Challenge every paragraph: does it justify its cost? Explanations of well-known formats, libraries, or concepts are pure overhead. This is the most common defect in a skill body — flag it aggressively.
- **Degrees of freedom matched to the task.** Fragile, order-dependent, high-stakes operations get exact commands and explicit prohibitions. Open-ended judgement work gets direction and trust. A rigid script for an open task makes the skill brittle; loose prose for a fragile one makes it unreliable.
- **Workflows.** Multi-step procedures should be numbered steps, with a copyable checklist when the process is long enough to lose track of.
- **Feedback loops.** Quality-critical work needs a validate → fix → re-validate loop with an explicit "only proceed when it passes".
- **Verifiable instructions.** "Run `npm test` before committing" beats "test your changes".
- **Consistent terminology.** One term per concept throughout — mixing "field", "box", and "element" for one thing costs adherence.
- **No time-sensitive content.** Anything phrased as "before/after <date>" will rot; move superseded material into a collapsed "Old patterns" section or delete it.
- **Concrete examples.** Where output format matters, input/output pairs convey it better than description. Where it does not, examples are filler.
- **Standing instructions, not one-time steps.** Skill content stays in context for the rest of the session and is not re-read, so guidance meant to apply throughout a task must be written as a standing rule.
- **Few options.** Give one default with an escape hatch, not a menu of equivalent approaches.
- **Fully qualified MCP tool names** (`ServerName:tool_name`) wherever MCP tools are referenced.
- **Explicit dependencies.** Scripts and commands the skill relies on must be named, with install instructions or an availability check.

For bundled scripts, additionally: errors handled in the script rather than deferred to Claude, constants justified by a comment, and an explicit statement of whether Claude should *execute* the script or *read* it as reference.

## Invocation control

| Situation | Expected frontmatter |
|-----------|---------------------|
| Workflow with side effects (deploy, commit, send) | `disable-model-invocation: true` |
| Background knowledge, not an action a user would invoke | `user-invocable: false` |
| Reference knowledge Claude should apply when relevant | neither (the default) |
| A user-invoked workflow with no side effects, where auto-triggering would be noise | `disable-model-invocation: true` |

Flag a side-effecting skill that Claude can trigger on its own, and a knowledge-only skill cluttering the `/` menu.

## Bundled files and progressive disclosure

- SKILL.md is the table of contents; detail belongs in bundled files that load on demand.
- Every bundled file is linked from SKILL.md, with a sentence saying what it contains and when to read it. A file nothing links to is dead weight.
- References stay one level deep. A reference that links onward to another reference gets partially read.
- Files are named for their content (`form-validation-rules.md`, not `doc2.md`), and organized by domain when a skill spans several.
- A skill whose body is well under the limit and whose references are all read every time does not need the split — collapsing it back into SKILL.md is a valid proposal.

## Deletion candidates

Propose removing:

- Explanations of things Claude already knows.
- Content duplicated from CLAUDE.md, another skill, or the codebase itself.
- Bundled files nothing references.
- Dated notes, migration instructions for migrations already done, changelog-style narration.
- Whole skills whose trigger no longer exists, or that are fully covered by another artifact.
