# statusline-pack

A configurable status line for Claude Code: model name, working directory, git branch, a context
usage bar, cost, session duration, and more, rendered on a single line. Claude Code plugins
cannot ship a `statusLine` through their own `settings.json`, so this plugin instead provides a
setup command that copies the renderer into your user config and wires `~/.claude/settings.json`
to point at it.

## Install / Usage

```
/plugin install statusline-pack@ogawa929
/statusline-pack:setup
/statusline-pack:restore
```

`/statusline-pack:setup` asks you to pick a layout preset unless you pass one directly as an
argument, e.g. `/statusline-pack:setup full`. `/statusline-pack:restore` puts back whatever
`statusLine` value `settings.json` had before setup ran.

## Presets

All three presets are a single line, and each one extends the one above it.

| Preset | Segments | Width needed |
| --- | --- | --- |
| `minimal` | `model`, `dir`, `git`, `context` | ~45 cols |
| `standard` | …plus `cost`, `duration`, `effort` | ~70 cols |
| `full` | …plus `pr`, `lines`, `thinking`, `ratelimit`, `style` | ~130 cols |

(Measured with a short project name and branch; a long directory or branch name pushes these up.)

Example output for `standard`:

```
[Opus] | 📁 my-app | 🌿 main | ▓▓▓░░░░░░░ 31% | $0.42 | 12m | ⚡high
```

**The order within a line is a priority order.** When the terminal is narrower than the line
needs, segments are dropped from the end (see *Width fitting* below), so `full` degrades towards
`standard` and then towards `minimal` as the window shrinks. Put whatever you always want to see
first. Picking `full` on an 80-column terminal is therefore not wasteful — it just means the tail
only appears when you widen the window.

## Configuration

Segments and display options live in `~/.claude/statusline-pack.json`:

```json
{
  "lines": [
    ["model", "dir", "git", "context", "cost", "duration", "effort"]
  ],
  "color": true,
  "emoji": true
}
```

- `lines`: one array per output line — the presets ship a single line, but more than one is
  supported. Segments within a line are joined with ` | `. A segment that has no value to show
  disappears along with its separator, and a line whose segments all disappeared is not printed
  at all.
- `color`: set to `false` to disable ANSI escape codes entirely.
- `emoji`: set to `false` to replace emoji with ASCII labels; the context bar switches from
  `▓░` to `#.`.
- Hand edits take effect from the **next status line refresh** — no need to re-run setup or
  restart Claude Code.
- Running `/statusline-pack:setup` again overwrites this file with the newly chosen preset, so
  any hand edits are lost.

## Segments

| ID | Example | Source field | Notes |
| --- | --- | --- | --- |
| `model` | `[Opus]` | `model.display_name` | |
| `dir` | `📁 my-app` | `workspace.current_dir` | basename only |
| `git` | `🌿 main` | `git branch --show-current` | hidden outside a git repo |
| `repo` | `ogawa929/plugins` | `workspace.repo.owner` / `.name` | not in any preset |
| `worktree` | `⑂ feature-x` | `workspace.git_worktree`, else `worktree.name` | not in any preset |
| `context` | `▓▓▓░░░░░░░ 31%` | `context_window.used_percentage` | bold at 60%, red at 80%; `--%` while unknown |
| `cost` | `$0.42` | `cost.total_cost_usd` | client-side estimate |
| `duration` | `12m` | `cost.total_duration_ms` | |
| `lines` | `+156/-23` | `cost.total_lines_added` / `_removed` | |
| `effort` | `⚡high` | `effort.level` | absent on models without effort levels |
| `thinking` | `🧠 on` | `thinking.enabled` | |
| `fast` | `🚀fast` | `fast_mode` | only rendered when enabled; not in any preset |
| `style` | `✨ Concise` | `output_style.name` | hidden for the `default` style |
| `vim` | `NORMAL` | `vim.mode` | not in any preset |
| `pr` | `🔗#42 pending` | `pr.number` / `pr.review_state` | |
| `ratelimit` | `5h 24% / 7d 41%` | `rate_limits.five_hour` / `.seven_day` | yellow at 60%, red at 80% |

## Files written to `~/.claude`

| Path | Purpose |
| --- | --- |
| `~/.claude/statusline-pack.py` | the status line script itself; `settings.json` points at this copy |
| `~/.claude/statusline-pack.json` | display config; this is the file you hand-edit |
| `~/.claude/statusline-pack.backup.json` | your previous `statusLine`, saved before the first apply |

`/statusline-pack:setup` only ever writes the `statusLine` key in `settings.json`; every other
key in that file is left untouched.

## Notes and caveats

- **Upgrading the plugin does not update the installed status line automatically.** The copy
  that actually runs lives under `~/.claude/`, so after a plugin update, re-run
  `/statusline-pack:setup` to refresh it.
- `cost.total_cost_usd` is a client-side estimate and may not match your actual bill. It resets
  on `/clear`.
- `rate_limits` is only sent to Claude Code on Claude.ai Pro/Max plans, and only after the
  session's first API response, so the `ratelimit` segment may stay hidden even in the `full`
  preset.
- Terminal-width-aware truncation depends on the `COLUMNS` environment variable and only works
  on Claude Code v2.1.153 and later; on older versions lines are never truncated.
- Supported platforms are macOS, Linux, and WSL. Windows is untested — Claude Code runs status
  line scripts through Git Bash / PowerShell there, and the shebang and path handling have not
  been verified.
- For debugging, set the `STATUSLINE_PACK_CONFIG` environment variable to point at a different
  config file. To preview the renderer locally:
  ```
  sed "s|{CWD}|$PWD|g" scripts/samples/01-full.json | python3 scripts/statusline.py
  ```

## License

MIT
