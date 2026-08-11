---
description: Install statusline-pack into ~/.claude/settings.json with a chosen layout preset (minimal, standard, or full). Can be undone at any time with /statusline-pack:restore.
argument-hint: [preset: minimal | standard | full]
disable-model-invocation: true
---

# statusline-pack: setup

Install the statusline-pack status line by running the plugin's `setup.py` script and reporting what it did. Follow these steps in order.

## 1. Decide the preset

Trim `$ARGUMENTS`. If it matches exactly `minimal`, `standard`, or `full`, use that preset and do not ask anything.

Otherwise, use `AskUserQuestion` (exactly one question) to let the user pick. If `$ARGUMENTS` was non-empty but did not match one of the three presets, do not silently ignore it — tell the user their input was not recognized before asking the question, then let them choose. Offer these three options, each with a short description of what it renders:

All three presets render on a single line and each one extends the previous, so the choice is
about how much detail to show on a wide terminal:

- `minimal` — model, dir, git branch, context bar (needs ~45 columns)
- `standard` — everything in minimal, plus cost, duration, effort (needs ~70 columns)
- `full` — everything in standard, plus PR, lines changed, thinking, output style, rate limits (needs ~130 columns)

Mention, alongside the options, that the order is a priority order: when the terminal is narrower than the line needs, segments are dropped from the end, so `full` degrades towards `standard` and then towards `minimal` rather than wrapping. Picking `full` on a narrow terminal is safe — the tail simply appears when the window is widened.

## 2. Run the script

Run this exactly, substituting the chosen preset, and nothing else:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup.py" <preset>
```

**Never edit `~/.claude/settings.json` yourself with the Edit or Write tool.** All reading and writing of that file is this script's job, so that formatting and untouched keys stay stable across runs.

If the script exits with a non-zero code, show the user its stderr output verbatim and stop there. Do not attempt any manual recovery or fall back to editing files by hand.

## 3. Report the result

From the script's stdout, read and report:

- which preset was installed
- the paths of the three files it wrote (the status line script, the layout config, and `settings.json`)
- whether a backup of the previous status line was taken, or skipped (and why)

Then show the preview section of the output (everything from the first `--- ... ---` sample header onward, covering all four bundled samples) **verbatim, inside a fenced code block**. Do not summarize or reconstruct it — paste the actual output exactly as printed. The script already strips ANSI escape codes when its output is not going to a terminal, so this is safe to paste as-is. Include each sample's name. If any sample run exited non-zero, include its stderr alongside it too.

## 4. Closing notes

Tell the user all of the following:

- Which segments are shown can be changed by hand-editing `~/.claude/statusline-pack.json`. Edits take effect from the next status line refresh — no need to re-run setup or restart Claude Code. Setting `color` or `emoji` to `false` in that file turns off ANSI colors or emoji respectively.
- **Running this command again overwrites `~/.claude/statusline-pack.json` with the newly chosen preset**, so any hand edits made to it will be lost.
- **Upgrading the plugin does not update the installed status line automatically.** The copy running lives under `~/.claude/`, so after a plugin update, `/statusline-pack:setup` needs to be run again to refresh the installed script.
- If a status line was already configured before this run, it was backed up, and `/statusline-pack:restore` can put it back at any time.
- The status line will show its new layout starting from the next refresh (e.g. after the assistant's next reply, a `/compact`, a permission mode change, or a vim mode switch).
