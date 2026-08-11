---
description: Undo /statusline-pack:setup by putting the previous status line back into ~/.claude/settings.json. Does nothing if statusline-pack was never applied.
disable-model-invocation: true
---

# statusline-pack: restore

Undo statusline-pack's changes to `~/.claude/settings.json` by running the plugin's `restore.py` script and reporting what it did. Follow these steps in order.

## 1. Run the script

Run this exactly, with no arguments:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/restore.py"
```

**Never edit `~/.claude/settings.json` yourself with the Edit or Write tool.** All reading and writing of that file is this script's job, so that formatting and untouched keys stay stable across runs.

If the script exits with a non-zero code, show the user its stderr output verbatim and stop there. Do not attempt any manual recovery or fall back to editing files by hand.

## 2. Report the result

Read the script's stdout and report which of these three outcomes happened:

- the previous `statusLine` setting was put back
- the `statusLine` key was removed entirely (there was no status line configured before statusline-pack was applied)
- statusline-pack was not currently applied, so `settings.json` was left unmodified — in this case, also report what the current `statusLine` setting is (if any), as shown in the script's output

## 3. Closing note

If a status line was restored or removed (i.e. the first or second outcome above), tell the user that `~/.claude/statusline-pack.py` and `~/.claude/statusline-pack.json` were left in place, not deleted, so `/statusline-pack:setup` can reapply statusline-pack at any time without losing prior customization.
