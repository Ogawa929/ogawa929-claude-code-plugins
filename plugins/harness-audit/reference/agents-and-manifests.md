# Subagents, output styles, and plugin manifests

Checklist for `agents/*.md`, `output-styles/*.md`, and `.claude-plugin/*.json`.

## Contents

- Subagents
- Output styles
- Plugin manifests

## Subagents

Frontmatter: `name` and `description` are required; `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation`, `color`, `initialPrompt` are optional. Unrecognized keys are dead configuration. `permissionMode`, `mcpServers`, and `hooks` are ignored for plugin subagents — flag them there as misleading.

Check:

- **`name`** — lowercase and hyphens, no `:` (reserved for plugin namespacing; a name containing one fails to load).
- **`description` is a delegation trigger.** It states when Claude should hand work to this agent, not what the agent is. Overlapping descriptions across agents make delegation a coin flip. If the agent should only be dispatched by a specific command, say so in the description.
- **`tools` is minimal but sufficient.** Omitting it inherits everything. A read-only reviewer that inherits `Write` is a real risk; an agent whose list resolves to zero tools fails to launch.
- **`model` and `effort` match the work.** Mechanical work on an expensive model, or genuine design judgement on a cheap one, are both defects. `inherit` is the default.
- **The body is a system prompt.** It should state the agent's role, its procedure, and the exact shape of its final report — a subagent returns only its summary, so an unspecified return format is a common failure. Every conciseness and specificity rule for skill bodies applies here too.
- **Self-contained.** The subagent does not inherit the parent conversation (a fork is the exception). Instructions that assume prior context will silently do nothing.
- **`isolation: worktree`** for agents that write, when the parent must keep working meanwhile.

## Output styles

An output style is appended to the system prompt and applies to every response, so it is the highest-leverage and highest-risk artifact in the set. Frontmatter: `name` (a display label — capitalization and spaces are fine), `description`, `keep-coding-instructions`, `force-for-plugin`. Nothing else is recognized.

- **`keep-coding-instructions`** defaults to `false`, which *removes* Claude Code's built-in software-engineering instructions. Flag any style used during coding work that leaves it unset — that is the single most common defect here.
- **`force-for-plugin: true`** overrides the user's own `outputStyle` setting whenever the plugin is enabled. Flag it unless the plugin exists solely to impose that style.
- `description` present, and it says when a user would want this style — it is all the `/config` picker shows.
- The body describes response shape and tone — length, ordering, what to lead with, what to leave out. It should not carry project facts or procedures; those belong in CLAUDE.md or a skill.
- Flag instructions that would suppress necessary information (error reports, failed test output, refusals) in the name of brevity.
- Flag contradictions with the project's CLAUDE.md.

## Plugin manifests

`plugin.json` needs `name`, `description`, and `version`; `author` and `license` are conventional. Check that:

- The manifest `name` matches the directory name and the namespace users type.
- `description` describes what the plugin provides, in the same what/when terms as a skill description — it is what a user sees when browsing the marketplace.
- `version` was bumped for the change under review.
- Every plugin directory listed in `marketplace.json` exists, and every plugin directory in the repository is listed.
- The manifest, the marketplace entry, the README, and the files on disk agree. Any drift between them is a finding.
