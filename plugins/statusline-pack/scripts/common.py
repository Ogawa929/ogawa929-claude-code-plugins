#!/usr/bin/env python3
"""Shared helpers for the statusline-pack setup/restore scripts.

Only ``setup.py`` and ``restore.py`` import this module. ``statusline.py`` is
deliberately standalone: it is copied on its own into the user's Claude config
directory, so it must not depend on anything that stays in the plugin.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

# Substring used to recognise a statusLine entry that this plugin installed.
MARKER = "statusline-pack"

# File names created inside the Claude config directory (usually ~/.claude).
SCRIPT_NAME = "statusline-pack.py"
CONFIG_NAME = "statusline-pack.json"
BACKUP_NAME = "statusline-pack.backup.json"
SETTINGS_NAME = "settings.json"

# Layout presets written to statusline-pack.json.
#
# Every preset is a single line, and each one extends the previous one: the
# order within the line is a priority order, because width fitting drops
# segments from the end when the terminal is too narrow. Put anything you
# always want to see first. A wide terminal shows all of "full"; a narrow one
# degrades it towards "standard", then towards "minimal".
#
# NOTE: the "standard" preset must stay in sync with DEFAULT_LINES in
# statusline.py -- they describe the same default layout, and statusline.py
# falls back to DEFAULT_LINES when no config file is present.
PRESETS: dict[str, list[list[str]]] = {
    "minimal": [
        ["model", "dir", "git", "context"],
    ],
    "standard": [
        ["model", "dir", "git", "context", "cost", "duration", "effort"],
    ],
    "full": [
        ["model", "dir", "git", "context", "cost", "duration", "effort",
         "pr", "lines", "thinking", "style", "ratelimit"],
    ],
}


class SettingsError(Exception):
    """A settings or config file could not be read, parsed or written."""


def resolve_config_dir(cli_value: str | None) -> Path:
    """Return the Claude config directory to operate on.

    Precedence: explicit CLI value > $CLAUDE_CONFIG_DIR > ~/.claude.
    The directory does not need to exist yet.
    """
    raw = cli_value or os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude"
    return Path(os.path.abspath(os.path.expanduser(raw)))


def default_config_dir() -> Path:
    """Return the standard config directory (~/.claude), ignoring overrides."""
    return Path(os.path.abspath(os.path.expanduser("~/.claude")))


def is_default_config_dir(p: Path) -> bool:
    """Return True when ``p`` points at ~/.claude."""
    default = default_config_dir()
    if p == default:
        return True
    try:
        return p.resolve() == default.resolve()
    except OSError:
        return False


def read_json(path: Path) -> Any | None:
    """Read JSON from ``path``.

    Returns None when the file does not exist. Raises SettingsError when the
    file exists but cannot be read or is not valid JSON, so that callers can
    refuse to overwrite a file they do not understand.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise SettingsError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(text)
    except UnicodeDecodeError as exc:
        raise SettingsError(f"{path} is not valid UTF-8: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SettingsError(f"{path} is not valid JSON: {exc}") from exc


def _new_file_mode() -> int:
    """Return the mode a newly created file should get, honouring umask."""
    mask = os.umask(0)
    os.umask(mask)
    return 0o666 & ~mask


def write_json_atomic(path: Path, obj: Any) -> None:
    """Write ``obj`` as pretty JSON to ``path`` atomically.

    The data is written to a temporary file in the same directory and then
    moved into place with os.replace(), so a crash can never leave a partially
    written settings file behind. An existing file keeps its permissions.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SettingsError(f"cannot create {path.parent}: {exc}") from exc

    try:
        mode = path.stat().st_mode & 0o777
    except OSError:
        mode = _new_file_mode()

    tmp_path: Path | None = None
    try:
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
        )
        tmp_path = Path(tmp_name)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(obj, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
        tmp_path = None
    except OSError as exc:
        raise SettingsError(f"cannot write {path}: {exc}") from exc
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink()
            except OSError:
                pass


def is_ours(status_line: Any) -> bool:
    """Return True when a settings.json statusLine value came from this plugin.

    The check is intentionally shape-agnostic (the value may be a dict today
    and something else tomorrow): it just looks for MARKER anywhere in the
    JSON rendering of the value.
    """
    if status_line is None:
        return False
    try:
        blob = json.dumps(status_line, ensure_ascii=False)
    except (TypeError, ValueError):
        blob = str(status_line)
    return MARKER in blob


def display_path(p: Path) -> str:
    """Return a human-friendly path with the home directory shown as "~".

    For output only -- never feed the result back into the filesystem API.
    """
    try:
        home = Path.home()
    except (RuntimeError, OSError):
        return str(p)
    try:
        rel = p.relative_to(home)
    except ValueError:
        return str(p)
    return "~" if str(rel) == "." else f"~/{rel}"
