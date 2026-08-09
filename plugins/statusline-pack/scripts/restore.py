#!/usr/bin/env python3
"""Undo what setup.py did: put the previous statusLine back (or remove it).

This script owns every read and write of settings.json: the slash command
must never edit that file directly, so that formatting and untouched keys
stay stable across runs.

Usage:
    python3 restore.py [--config-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent

# Make `import common` work no matter how this script was invoked (symlink,
# different cwd, ...). sys.path[0] usually covers it, but not always.
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import common  # noqa: E402  (must follow the sys.path fix-up above)

LABEL_WIDTH = 12
PREFIX = "statusline-pack:"


def emit(label: str, arrow: str, text: str) -> None:
    """Print one line of the run summary: one fact per line, easy to quote."""
    print(f"{PREFIX} {label:<{LABEL_WIDTH}}{arrow} {text}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="restore.py",
        description="Put the previous statusLine setting back into settings.json.",
    )
    parser.add_argument(
        "--config-dir",
        metavar="DIR",
        default=None,
        help=(
            "Claude config directory to operate on "
            "(default: $CLAUDE_CONFIG_DIR, else ~/.claude). For testing."
        ),
    )
    return parser


def read_settings_or_none(settings_path: Path) -> dict | None:
    """Read settings.json, returning None when the file does not exist.

    Raises SettingsError when the file exists but cannot be parsed or does
    not contain a JSON object -- restore must never touch a file it does not
    understand.
    """
    data = common.read_json(settings_path)
    if data is None:
        return None
    if not isinstance(data, dict):
        raise common.SettingsError(
            f"{settings_path} does not contain a JSON object "
            f"(found {type(data).__name__}); refusing to modify it"
        )
    return data


def load_backup(backup_path: Path) -> tuple[Any, str | None]:
    """Read the backup file and return (previous_status_line, warning).

    Never raises: a missing or unreadable backup is not fatal for restore. A
    missing file simply yields (None, None) -- that is the normal case for a
    settings.json that never had a status line before this plugin was
    applied. A backup that exists but cannot be parsed also yields prev=None,
    plus a warning string describing the problem so it ends up in the run
    summary instead of silently being ignored.
    """
    try:
        data = common.read_json(backup_path)
    except common.SettingsError as exc:
        return None, f"{common.display_path(backup_path)} could not be read ({exc}); ignoring it"
    if data is None:
        return None, None
    if not isinstance(data, dict):
        return None, (
            f"{common.display_path(backup_path)} does not contain a JSON object; ignoring it"
        )
    return data.get("statusLine"), None


def describe_status_line(status_line: Any) -> str:
    """Return a short, human-readable description of a foreign statusLine."""
    if isinstance(status_line, dict) and "command" in status_line:
        return str(status_line["command"])
    return json.dumps(status_line, ensure_ascii=False)


def restore(args: argparse.Namespace) -> None:
    config_dir = common.resolve_config_dir(args.config_dir)
    settings_path = config_dir / common.SETTINGS_NAME
    backup_path = config_dir / common.BACKUP_NAME
    script_path = config_dir / common.SCRIPT_NAME
    config_path = config_dir / common.CONFIG_NAME

    # Read and validate settings.json before touching anything on disk, so a
    # broken file aborts the run without side effects (see main()).
    settings = read_settings_or_none(settings_path)

    if settings is None:
        emit(
            "settings",
            "--",
            f"{common.display_path(settings_path)} does not exist; nothing to restore",
        )
        emit("not applied", "--", "there is no statusLine to restore")
        return

    current = settings.get("statusLine")

    if not common.is_ours(current):
        emit("settings", "--", f"{common.display_path(settings_path)} was not modified")
        if "statusLine" not in settings or current is None:
            emit("not applied", "--", "there is no statusLine configured")
        else:
            emit(
                "not applied",
                "--",
                f"current statusLine command is: {describe_status_line(current)}",
            )
        return

    # From here on statusline-pack owns the current statusLine, so it is safe
    # to restore whatever was there before.
    prev, backup_warning = load_backup(backup_path)

    emit("settings", "->", common.display_path(settings_path))
    if backup_warning:
        emit("backup", "--", backup_warning)

    if prev is not None:
        settings["statusLine"] = prev
        common.write_json_atomic(settings_path, settings)
        emit(
            "restored",
            "--",
            f"previous statusLine put back (from {common.display_path(backup_path)})",
        )
    else:
        settings.pop("statusLine", None)
        common.write_json_atomic(settings_path, settings)
        emit("removed", "--", "statusLine key deleted (there was no status line before)")

    emit(
        "kept",
        "--",
        f"{common.display_path(script_path)} and {common.display_path(config_path)} "
        "were left in place",
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        restore(args)
    except common.SettingsError as exc:
        print(f"{PREFIX} error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"{PREFIX} error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print(f"{PREFIX} error: interrupted", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - report, never traceback at the user
        print(f"{PREFIX} unexpected error: {exc!r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
