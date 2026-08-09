#!/usr/bin/env python3
"""Install the statusline-pack status line into the user's Claude config.

This script owns every read and write of settings.json: the slash command must
never edit that file directly, so that formatting and untouched keys stay
stable across runs.

Usage:
    python3 setup.py <preset> [--config-dir DIR] [--no-preview]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# Make `import common` work no matter how this script was invoked (symlink,
# different cwd, ...). sys.path[0] usually covers it, but not always.
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import common  # noqa: E402  (must follow the sys.path fix-up above)

SOURCE_SCRIPT = SCRIPT_DIR / "statusline.py"
SAMPLES_DIR = SCRIPT_DIR / "samples"

PREVIEW_TIMEOUT_SEC = 5
DEFAULT_PREVIEW_COLUMNS = "100"

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

LABEL_WIDTH = 12
PREFIX = "statusline-pack:"


def emit(label: str, arrow: str, text: str) -> None:
    """Print one line of the run summary: one fact per line, easy to quote."""
    print(f"{PREFIX} {label:<{LABEL_WIDTH}}{arrow} {text}")


def warn(text: str) -> None:
    print(f"{PREFIX} warning: {text}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="setup.py",
        description="Install the statusline-pack status line into ~/.claude.",
    )
    parser.add_argument(
        "preset",
        choices=sorted(common.PRESETS),
        help="which layout preset to write to statusline-pack.json",
    )
    parser.add_argument(
        "--config-dir",
        metavar="DIR",
        default=None,
        help=(
            "Claude config directory to write to "
            "(default: $CLAUDE_CONFIG_DIR, else ~/.claude). For testing."
        ),
    )
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="do not render the bundled sample inputs after installing",
    )
    return parser


def load_settings(settings_path: Path) -> dict:
    """Read settings.json, or return {} when it does not exist yet.

    Raises SettingsError when the file exists but is unusable -- we must never
    overwrite a file we could not parse.
    """
    data = common.read_json(settings_path)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise common.SettingsError(
            f"{settings_path} does not contain a JSON object "
            f"(found {type(data).__name__}); refusing to modify it"
        )
    return data


def install_script(config_dir: Path) -> Path:
    """Copy statusline.py into the config directory and make it executable."""
    if not SOURCE_SCRIPT.is_file():
        raise common.SettingsError(f"cannot find the status line script at {SOURCE_SCRIPT}")
    dest = config_dir / common.SCRIPT_NAME
    try:
        shutil.copyfile(SOURCE_SCRIPT, dest)
    except OSError as exc:
        raise common.SettingsError(f"cannot copy {SOURCE_SCRIPT} to {dest}: {exc}") from exc
    try:
        os.chmod(dest, 0o755)
    except OSError as exc:
        # Not fatal: the preview runs the script through sys.executable, and
        # Claude Code invokes the command through a shell.
        warn(f"could not mark {common.display_path(dest)} executable: {exc}")
    return dest


def status_line_command(config_dir: Path, script_dest: Path) -> str:
    """Return the command string to store in settings.json.

    For the standard location we keep the literal "~/.claude/..." form: the
    shell expands it, and it survives a home directory that is spelled
    differently across machines.
    """
    if common.is_default_config_dir(config_dir):
        return f"~/.claude/{common.SCRIPT_NAME}"
    return str(script_dest)


def install(args: argparse.Namespace) -> None:
    config_dir = common.resolve_config_dir(args.config_dir)
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise common.SettingsError(f"cannot create {config_dir}: {exc}") from exc

    settings_path = config_dir / common.SETTINGS_NAME
    config_path = config_dir / common.CONFIG_NAME
    backup_path = config_dir / common.BACKUP_NAME

    # Read and validate settings.json before touching anything on disk, so a
    # broken file aborts the run without side effects.
    settings = load_settings(settings_path)
    settings_existed = settings_path.exists()
    current = settings.get("statusLine")
    already_ours = common.is_ours(current)

    # Back up the previous statusLine only when it is not ours. Re-running
    # setup (preset change, plugin upgrade) must never overwrite the backup
    # with our own entry, and must not create one where there was none.
    if already_ours:
        backup_note = (
            "skipped (statusline-pack was already applied; existing backup left untouched)"
        )
    else:
        common.write_json_atomic(backup_path, {"statusLine": current})
        backup_note = None

    script_dest = install_script(config_dir)

    config_existed = config_path.exists()
    common.write_json_atomic(
        config_path,
        {"lines": common.PRESETS[args.preset], "color": True, "emoji": True},
    )

    # Replace only the statusLine key; every other user setting is preserved.
    settings["statusLine"] = {
        "type": "command",
        "command": status_line_command(config_dir, script_dest),
        "padding": 2,
    }
    common.write_json_atomic(settings_path, settings)

    emit("preset", "=", args.preset)
    emit("script", "->", common.display_path(script_dest))
    emit(
        "config",
        "->",
        common.display_path(config_path)
        + (" (overwrote existing file)" if config_existed else " (created)"),
    )
    if backup_note is None:
        emit(
            "backup",
            "->",
            f"{common.display_path(backup_path)} (previous statusLine saved)",
        )
    else:
        emit("backup", "--", backup_note)
    emit(
        "settings",
        "->",
        common.display_path(settings_path)
        + (" (statusLine updated)" if settings_existed else " (created, statusLine set)"),
    )

    if not args.no_preview:
        try:
            preview(config_dir, script_dest)
        except Exception as exc:  # noqa: BLE001 - preview must never fail the install
            warn(f"preview failed: {exc}")


def preview_env(config_dir: Path) -> dict[str, str]:
    """Environment for preview runs: inherited, plus a stable terminal width.

    CLAUDE_CONFIG_DIR is pointed at the directory we just wrote to, so the
    preview reflects the preset that was actually installed. For the normal
    ~/.claude install this is a no-op; it only matters for --config-dir runs.
    """
    env = dict(os.environ)
    env["COLUMNS"] = os.environ.get("COLUMNS") or DEFAULT_PREVIEW_COLUMNS
    env["CLAUDE_CONFIG_DIR"] = str(config_dir)
    return env


def preview(config_dir: Path, script_dest: Path) -> None:
    """Render every bundled sample input with the script we just installed.

    Running the installed copy (not the source) also proves the copy works.
    """
    samples = sorted(SAMPLES_DIR.glob("*.json"))
    print()
    print(f"{PREFIX} preview (rendered by {common.display_path(script_dest)})")
    if not samples:
        print(f"  (no sample inputs found in {SAMPLES_DIR})")
        return

    strip_ansi = not sys.stdout.isatty()
    if strip_ansi:
        print("  (colors are stripped when output is not a terminal)")

    env = preview_env(config_dir)
    # The samples embed {CWD} inside JSON strings, so the replacement has to be
    # escaped the way a JSON string body would be.
    cwd_literal = json.dumps(os.getcwd())[1:-1]

    for sample in samples:
        print()
        print(f"--- {sample.stem} ---")
        try:
            payload = sample.read_text(encoding="utf-8").replace("{CWD}", cwd_literal)
        except OSError as exc:
            print(f"  (cannot read {sample.name}: {exc})")
            continue

        try:
            proc = subprocess.run(
                [sys.executable, str(script_dest)],
                input=payload,
                capture_output=True,
                text=True,
                timeout=PREVIEW_TIMEOUT_SEC,
                env=env,
            )
        except subprocess.TimeoutExpired:
            print(f"  (timed out after {PREVIEW_TIMEOUT_SEC}s)")
            continue
        except OSError as exc:
            print(f"  (could not run {script_dest}: {exc})")
            continue

        stdout = proc.stdout
        stderr = proc.stderr
        if strip_ansi:
            stdout = ANSI_RE.sub("", stdout)
            stderr = ANSI_RE.sub("", stderr)

        if stdout.strip():
            print(stdout.rstrip("\n"))
        elif proc.returncode == 0:
            print("  (no output)")

        if proc.returncode != 0:
            print(f"  [exited with code {proc.returncode}]")
        if proc.returncode != 0 or stderr.strip():
            if stderr.strip():
                print("  [stderr]")
                for line in stderr.rstrip("\n").splitlines():
                    print(f"  {line}")
            else:
                print("  [stderr] (empty)")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        install(args)
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
