# ogawa929-claude-code-plugins

[日本語版はこちら](#日本語)

This repository is a personal plugin marketplace for [Claude Code](https://docs.anthropic.com/claude/code), hosting a curated collection of reusable skills that extend Claude's capabilities directly inside your editor. Each plugin lives under the `plugins/` directory with its own `plugin.json` manifest and one or more skill files, and the top-level `.claude-plugin/marketplace.json` file registers them so Claude can discover and install them by name.

## Install

Add this marketplace to Claude Code, then install any plugin by its namespaced name:

```
/plugin marketplace add Ogawa929/ogawa929-claude-code-plugins
/plugin install hello-world@ogawa929
```

Plugin skills are namespaced to their plugin name, so the example skill above is invoked as:

```
/hello-world:greet
```

## Available Plugins

| Name | Description |
|------|-------------|
| `hello-world` | A minimal example plugin with a single `/hello-world:greet` skill — useful as a template for building your own plugins. |
| `impl-flow` | Interviews you into a use-case document that an independent agent then reviews adversarially, breaks the feature down into commit-sized implementation plans, and executes them with subagents sized to each plan's declared complexity: `/impl-flow:spec` (design+plan) and `/impl-flow:implement` run independently, or `/impl-flow:all` runs the full pipeline in one go. `/impl-flow:fix` is the lighter **fix mode** for changing something that already exists — instead of interviewing a new document into being, it classifies the report as an implementation defect, a specification defect or a new requirement, revises the affected use cases in the existing document, and runs a three-layer omission review (use-case consistency, the file set recorded in the task set's plans, then the repository at large) to catch what a partial fix would leave behind. Every plan it produces starts with a test that fails for the reported symptom. |
| `reduce-hallucinations` | An auto-triggered skill (no slash command) that grounds answers in direct quotes and citations during investigation/research tasks, while staying out of implementation work. |
| `robotic-persona` | A `Robotic` [output style](https://code.claude.com/docs/en/output-styles) (not a skill) that reduces answers to telegraphic output: one fact per line, no copula, no connectives, no evaluative or emotional words. Japanese output drops です・ます and unambiguous particles — but accuracy overrides terseness, so anything whose absence would permit two readings comes back. Enable it under `/config` → Output style, then `/clear`. |
| `git-commit` | An auto-triggered skill (no slash command) that applies a house commit convention when committing: prefix-tagged subjects (`feat`/`fix`/`docs`/`refactor`/`chore`/`revert`), a 50-character noun-phrase summary with no trailing period, What in the subject and Why in the body, and revert-safe commit granularity. Follows whatever language the repository's existing commits use. |
| `harness-audit` | A `/harness-audit:audit [path]` command (never auto-triggered) that audits the files shaping Claude's behaviour — `SKILL.md` files, slash commands, `CLAUDE.md` and `.claude/rules`, subagents, output styles and plugin manifests. It inventories them with a bundled scanner, checks hard limits, discoverability, conciseness and cross-file conflicts against [Anthropic's authoring guidance](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), and ends with ranked fix and deletion proposals you approve before anything is changed. |
| `statusline-pack` | A configurable status line for Claude Code — model, directory, git branch, context bar, cost and more. `/statusline-pack:setup` installs a preset into `~/.claude` and wires up `settings.json`; edit `~/.claude/statusline-pack.json` to change the segments, and `/statusline-pack:restore` puts your previous status line back. |
| `drawio-diagram` | An auto-triggered skill (no slash command) for draw.io / diagrams.net files, applying layout rules that keep a diagram readable to a human: no overlapping shapes, edges or labels, text that fits inside its shape, categories shown through both colour and position, concise supplementary text, and a canvas enlarged to fit the content — with a confirmation step when the drawing area is fixed. Ships `scripts/validate_drawio.py`, which checks the generated XML for spacing, label fit, page overflow and shared edge ports, plus `references/diagram-types.md` covering ER, sequence, state, network and class notations. |

## Adding a New Plugin

1. **Create the directory** – add a new folder under `plugins/`, e.g. `plugins/my-plugin/`.
2. **Add a manifest** – create `.claude-plugin/plugin.json` inside that folder describing the plugin's name, version, and author.
3. **Add skills** – place one or more skill files (`.md` or `.js`) inside the plugin directory and reference them in `plugin.json`.
4. **Register the plugin** – add an entry to `.claude-plugin/marketplace.json` at the repository root so Claude's marketplace index picks it up.

## Local Development

Validate a plugin while working on it locally, then load it directly without publishing:

```
claude plugin validate .
/plugin marketplace add ./claude-plugins
/reload-plugins
```

## License

This project is released under the [MIT License](LICENSE).

---

## 日本語

このリポジトリは[Claude Code](https://docs.anthropic.com/claude/code)向けの個人用プラグインマーケットプレイスです。エディタ上でClaudeの機能を拡張する再利用可能なスキルを集めています。各プラグインは`plugins/`ディレクトリ以下に配置されており、Claude CodeからそのままインストールしてすぐにSlashコマンドとして利用できます。

### インストール

```
/plugin marketplace add Ogawa929/ogawa929-claude-code-plugins
/plugin install hello-world@ogawa929
```

スキルはプラグイン名でnamespace管理されているため、上記の例では`/hello-world:greet`として呼び出します。

### 詳細について

プラグイン一覧・新規プラグインの追加方法・ローカル開発手順については、上記の英語セクションをご参照ください。
