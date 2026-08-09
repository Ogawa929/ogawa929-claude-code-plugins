#!/usr/bin/env python3
"""Claude Code status line renderer for the statusline-pack plugin.

Claude Code pipes a JSON blob describing the current session into this script on
stdin and prints whatever the script writes to stdout underneath the prompt (one
output line per status line row, ANSI colors allowed).

This file is installed by copying it on its own to ``~/.claude/statusline-pack.py``,
so it MUST stay entirely self-contained: standard library only, no imports from
sibling scripts, no third-party packages.

Two invariants matter more than anything this renders:

* the process always exits with status 0 -- a crashing status line command breaks
  the Claude Code UI, so every failure degrades to a short one-line message;
* nothing ever prints a traceback.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from typing import Any, Callable, NamedTuple

# Default layout used when no config file exists. Keep in sync with the
# `standard` preset in `common.py`.
DEFAULT_LINES: list[list[str]] = [
    ["model", "dir", "git"],
    ["context", "cost", "duration", "effort"],
]

CONFIG_BASENAME = "statusline-pack.json"
SEPARATOR = " | "

# SGR parameter strings, one per segment. Segments return these; only the line
# assembler turns them into real escape sequences.
COLOR_MODEL = "1;36"
COLOR_DIR = "1;34"
COLOR_GIT = "32"
COLOR_REPO = "36"
COLOR_WORKTREE = "35"
COLOR_COST = "33"
COLOR_DURATION = "90"
COLOR_LINES = "32"
COLOR_EFFORT = "35"
COLOR_THINKING = "36"
COLOR_FAST = "1;33"
COLOR_STYLE = "36"
COLOR_VIM = "1;35"
COLOR_PR = "36"
COLOR_UNKNOWN = "90"
COLOR_CONTEXT_OK = "32"
COLOR_CONTEXT_WARN = "33"
COLOR_CONTEXT_HIGH = "31"

CONTEXT_WARN_PCT = 60.0
CONTEXT_HIGH_PCT = 80.0
CONTEXT_BAR_CELLS = 10

# (emoji form, ascii form) for every decorated label.
LABELS: dict[str, tuple[str, str]] = {
    "dir": ("\U0001f4c1 ", ""),
    "git": ("\U0001f33f ", "git:"),
    "worktree": ("⑂ ", "wt:"),
    "effort": ("⚡", "effort:"),
    "thinking": ("\U0001f9e0", "think:"),
    "fast": ("\U0001f680", ""),
    "style": ("✨", "style:"),
    "pr": ("\U0001f517", "PR"),
}

# (filled cell, empty cell) for the context bar.
BAR_CHARS: dict[str, tuple[str, str]] = {
    "emoji": ("▓", "░"),
    "ascii": ("#", "."),
}

GIT_TIMEOUT_SECONDS = 1.0


class Segment(NamedTuple):
    """One rendered chunk of a status line row.

    ``text`` is plain text and must never contain ANSI escapes; ``color`` is an
    SGR parameter string such as ``"36"`` or ``"1;34"``, or ``None`` for no
    color. Keeping color out of the text is what lets later features measure the
    display width of a segment without having to strip escapes first.
    """

    text: str
    color: str | None


class Ctx(NamedTuple):
    """Everything a segment function is allowed to look at."""

    data: dict[str, Any]
    emoji: bool
    color: bool


class ConfigError(Exception):
    """The config file exists but cannot be used."""

    def __init__(self, path: str) -> None:
        super().__init__(path)
        self.path = path


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------


def dig(data: Any, *keys: str) -> Any:
    """Return a nested value, or None if any level is missing or not a dict."""
    node = data
    for key in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def as_number(value: Any) -> float | None:
    """Return value as a finite float, or None if it is not a usable number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def as_text(value: Any) -> str | None:
    """Return value as a non-empty stripped string, or None."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def label(key: str, emoji: bool) -> str:
    forms = LABELS[key]
    return forms[0] if emoji else forms[1]


def color_for_percentage(pct: float) -> str:
    """Map a 0-100 usage percentage to the shared OK/WARN/HIGH color bands."""
    if pct < CONTEXT_WARN_PCT:
        return COLOR_CONTEXT_OK
    if pct < CONTEXT_HIGH_PCT:
        return COLOR_CONTEXT_WARN
    return COLOR_CONTEXT_HIGH


def rate_limit_percentage(value: Any) -> float | None:
    """Best-effort percentage extraction for one rate_limits window.

    The shape of a `rate_limits.<window>` value is not confirmed by any spec
    available here, so this accepts a bare number, or a dict carrying the
    percentage under `used_percentage`, `percentage`, or `used` (checked in
    that order); anything else fails closed with None.
    """
    number = as_number(value)
    if number is not None:
        return number
    if isinstance(value, dict):
        for key in ("used_percentage", "percentage", "used"):
            if key in value:
                number = as_number(value.get(key))
                if number is not None:
                    return number
    return None


def shorten_home(path: str) -> str:
    """Replace a leading home directory with '~' for display."""
    try:
        home = os.path.expanduser("~")
    except Exception:
        return path
    if home and home != os.sep:
        if path == home:
            return "~"
        if path.startswith(home + os.sep):
            return "~" + path[len(home) :]
    return path


# --------------------------------------------------------------------------
# configuration
# --------------------------------------------------------------------------


def config_path() -> str:
    """Resolve the config file path.

    STATUSLINE_PACK_CONFIG is an escape hatch for testing and debugging; normal
    installs fall back to $CLAUDE_CONFIG_DIR (default ~/.claude).
    """
    override = os.environ.get("STATUSLINE_PACK_CONFIG")
    if override:
        return override
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(
        os.path.expanduser("~"), ".claude"
    )
    return os.path.join(os.path.expanduser(base), CONFIG_BASENAME)


def valid_lines(value: Any) -> bool:
    """True when value is a list of lists of strings."""
    if not isinstance(value, list):
        return False
    for row in value:
        if not isinstance(row, list):
            return False
        for segment_id in row:
            if not isinstance(segment_id, str):
                return False
    return True


def load_config() -> tuple[list[list[str]], bool, bool]:
    """Read the config file and return (lines, color, emoji).

    The file is read on every invocation on purpose: hand edits must show up on
    the next status line refresh without restarting Claude Code.

    A missing or unreadable file falls back to the defaults. A file that exists
    but is malformed raises ConfigError, because silently ignoring a typo would
    hide the user's mistake.
    """
    path = config_path()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
    except OSError:
        # Missing file, permission denied, unreadable path: use the defaults.
        return DEFAULT_LINES, True, True

    try:
        parsed = json.loads(raw)
    except ValueError:  # json.JSONDecodeError is a ValueError
        raise ConfigError(path) from None
    if not isinstance(parsed, dict):
        raise ConfigError(path)

    if "lines" in parsed:
        if not valid_lines(parsed["lines"]):
            raise ConfigError(path)
        lines = [list(row) for row in parsed["lines"]]
    else:
        lines = [list(row) for row in DEFAULT_LINES]

    color = parsed.get("color")
    emoji = parsed.get("emoji")
    return (
        lines,
        color if isinstance(color, bool) else True,
        emoji if isinstance(emoji, bool) else True,
    )


# --------------------------------------------------------------------------
# segments
# --------------------------------------------------------------------------


def seg_model(ctx: Ctx) -> Segment | None:
    name = as_text(dig(ctx.data, "model", "display_name"))
    if name is None:
        return None
    return Segment(f"[{name}]", COLOR_MODEL)


def seg_dir(ctx: Ctx) -> Segment | None:
    current_dir = as_text(dig(ctx.data, "workspace", "current_dir"))
    if current_dir is None:
        return None
    base = os.path.basename(current_dir.rstrip("/")) or "/"
    return Segment(label("dir", ctx.emoji) + base, COLOR_DIR)


def seg_git(ctx: Ctx) -> Segment | None:
    """Current branch name, or None when there is nothing meaningful to show.

    No caching: the status line runs often, but a stale branch name is worse
    than the cost of a bounded `git branch --show-current` call.
    """
    current_dir = as_text(dig(ctx.data, "workspace", "current_dir"))
    if current_dir is None:
        # Without a workspace directory, any branch we found would describe some
        # unrelated directory, so show nothing at all.
        return None
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=current_dir,
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        # Outside a repository git exits 128. stderr is deliberately dropped.
        return None
    branch = result.stdout.strip()
    if not branch:
        # Detached HEAD prints nothing.
        return None
    return Segment(label("git", ctx.emoji) + branch, COLOR_GIT)


def seg_repo(ctx: Ctx) -> Segment | None:
    """GitHub `owner/name`, absent whenever there is no origin remote."""
    owner = as_text(dig(ctx.data, "workspace", "repo", "owner"))
    name = as_text(dig(ctx.data, "workspace", "repo", "name"))
    if owner is None or name is None:
        return None
    return Segment(f"{owner}/{name}", COLOR_REPO)


def seg_worktree(ctx: Ctx) -> Segment | None:
    """Git worktree name, falling back to `worktree.name` when unset."""
    name = as_text(dig(ctx.data, "workspace", "git_worktree"))
    if name is None:
        name = as_text(dig(ctx.data, "worktree", "name"))
    if name is None:
        return None
    return Segment(label("worktree", ctx.emoji) + name, COLOR_WORKTREE)


def seg_context(ctx: Ctx) -> Segment | None:
    """Context window usage bar. Always rendered, even when usage is unknown."""
    window = dig(ctx.data, "context_window")
    window = window if isinstance(window, dict) else {}
    pct = as_number(window.get("used_percentage"))
    # An explicit null current_usage means Claude Code could not measure usage.
    if "current_usage" in window and window["current_usage"] is None:
        pct = None

    filled_char, empty_char = BAR_CHARS["emoji" if ctx.emoji else "ascii"]
    if pct is None:
        bar = empty_char * CONTEXT_BAR_CELLS
        return Segment(f"{bar} --%", COLOR_UNKNOWN)

    pct = max(0.0, min(100.0, pct))
    filled = max(0, min(CONTEXT_BAR_CELLS, int(round(pct / 10))))
    bar = filled_char * filled + empty_char * (CONTEXT_BAR_CELLS - filled)
    return Segment(f"{bar} {int(round(pct))}%", color_for_percentage(pct))


def seg_cost(ctx: Ctx) -> Segment | None:
    total = as_number(dig(ctx.data, "cost", "total_cost_usd"))
    if total is None:
        return None
    # Zero is a real value: a fresh session shows $0.00 rather than nothing.
    return Segment(f"${total:.2f}", COLOR_COST)


def seg_duration(ctx: Ctx) -> Segment | None:
    total = as_number(dig(ctx.data, "cost", "total_duration_ms"))
    if total is None:
        return None
    ms = max(0, int(total))
    if ms < 60_000:
        text = f"{ms // 1000}s"
    elif ms < 3_600_000:
        text = f"{ms // 60_000}m"
    else:
        text = f"{ms // 3_600_000}h{(ms % 3_600_000) // 60_000}m"
    return Segment(text, COLOR_DURATION)


def seg_lines(ctx: Ctx) -> Segment | None:
    """Lines added/removed this session, only hidden when both are missing."""
    added = as_number(dig(ctx.data, "cost", "total_lines_added"))
    removed = as_number(dig(ctx.data, "cost", "total_lines_removed"))
    if added is None and removed is None:
        return None
    # A missing side counts as 0 rather than hiding the whole segment, so the
    # row layout stays stable even when only one count is present.
    added_count = int(added) if added is not None else 0
    removed_count = int(removed) if removed is not None else 0
    return Segment(f"+{added_count}/-{removed_count}", COLOR_LINES)


def seg_effort(ctx: Ctx) -> Segment | None:
    # The whole `effort` key is absent on models without effort levels.
    level = as_text(dig(ctx.data, "effort", "level"))
    if level is None:
        return None
    return Segment(label("effort", ctx.emoji) + level, COLOR_EFFORT)


def seg_thinking(ctx: Ctx) -> Segment | None:
    enabled = dig(ctx.data, "thinking", "enabled")
    if not isinstance(enabled, bool):
        return None
    state = "on" if enabled else "off"
    return Segment(label("thinking", ctx.emoji) + state, COLOR_THINKING)


def seg_fast(ctx: Ctx) -> Segment | None:
    # Only rendered when fast mode is actually on; false or missing hides it.
    fast_mode = dig(ctx.data, "fast_mode")
    if fast_mode is not True:
        return None
    return Segment(label("fast", ctx.emoji) + "fast", COLOR_FAST)


def seg_style(ctx: Ctx) -> Segment | None:
    name = as_text(dig(ctx.data, "output_style", "name"))
    if name is None or name.lower() == "default":
        # The default style carries no information, so hide it.
        return None
    return Segment(label("style", ctx.emoji) + name, COLOR_STYLE)


def seg_vim(ctx: Ctx) -> Segment | None:
    mode = as_text(dig(ctx.data, "vim", "mode"))
    if mode is None:
        return None
    return Segment(mode.upper(), COLOR_VIM)


def seg_pr(ctx: Ctx) -> Segment | None:
    number = as_number(dig(ctx.data, "pr", "number"))
    if number is None:
        return None
    text = label("pr", ctx.emoji) + f"#{int(number)}"
    state = as_text(dig(ctx.data, "pr", "review_state"))
    if state is not None:
        text += f" {state}"
    return Segment(text, COLOR_PR)


def seg_ratelimit(ctx: Ctx) -> Segment | None:
    """5h/7d Claude usage percentages, hidden only when both are unreadable."""
    five = rate_limit_percentage(dig(ctx.data, "rate_limits", "five_hour"))
    seven = rate_limit_percentage(dig(ctx.data, "rate_limits", "seven_day"))
    if five is None and seven is None:
        return None
    parts: list[str] = []
    if five is not None:
        parts.append(f"5h {int(round(five))}%")
    if seven is not None:
        parts.append(f"7d {int(round(seven))}%")
    worst = max(v for v in (five, seven) if v is not None)
    return Segment(" / ".join(parts), color_for_percentage(worst))


SEGMENTS: dict[str, Callable[[Ctx], Segment | None]] = {
    "model": seg_model,
    "dir": seg_dir,
    "git": seg_git,
    "repo": seg_repo,
    "worktree": seg_worktree,
    "context": seg_context,
    "cost": seg_cost,
    "duration": seg_duration,
    "lines": seg_lines,
    "effort": seg_effort,
    "thinking": seg_thinking,
    "fast": seg_fast,
    "style": seg_style,
    "vim": seg_vim,
    "pr": seg_pr,
    "ratelimit": seg_ratelimit,
}


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------


def build_segment(segment_id: str, ctx: Ctx) -> Segment | None:
    """Render one segment, absorbing anything it throws.

    A broken segment must never take the rest of the status line with it, and it
    must never leak a traceback into the UI.
    """
    render = SEGMENTS.get(segment_id)
    if render is None:
        return Segment("?" + segment_id, None)
    try:
        return render(ctx)
    except Exception:
        return None


def paint(segment: Segment, use_color: bool) -> str:
    if not use_color or not segment.color:
        return segment.text
    return f"\x1b[{segment.color}m{segment.text}\x1b[0m"


def render_line(ids: list[str], ctx: Ctx) -> str | None:
    """Join the segments of one row, or return None if the row is empty.

    Segments that render nothing disappear together with their separator, and a
    row whose segments all disappeared is dropped rather than printed blank.
    """
    parts: list[str] = []
    for segment_id in ids:
        segment = build_segment(segment_id, ctx)
        if segment is None or not segment.text:
            continue
        parts.append(paint(segment, ctx.color))
    if not parts:
        return None
    # The separator itself stays uncolored.
    return SEPARATOR.join(parts)


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------


def read_input() -> dict[str, Any]:
    """Parse the session JSON from stdin, degrading to {} on any problem."""
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except ValueError:  # json.JSONDecodeError is a ValueError
        return {}
    return parsed if isinstance(parsed, dict) else {}


def main() -> int:
    try:
        data = read_input()
        try:
            lines, color, emoji = load_config()
        except ConfigError as error:
            print(f"statusline-pack: config error ({shorten_home(error.path)})")
            return 0
        ctx = Ctx(data=data, emoji=emoji, color=color)
        for ids in lines:
            rendered = render_line(ids, ctx)
            if rendered is not None:
                print(rendered)
    except Exception as error:  # never surface a traceback to the UI
        print(f"statusline-pack: internal error: {type(error).__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
