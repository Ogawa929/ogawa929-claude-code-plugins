#!/usr/bin/env python3
"""Inventory Claude Code instruction artifacts and report mechanically checkable violations.

Usage: python3 scan.py [ROOT ...]        (default root: the current directory)

Prints a markdown inventory table followed by findings. Every finding is a rule
that can be decided from the file alone; judgement calls are left to the caller.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field

# --- Limits, all taken from Anthropic's published authoring guidance -------------
# Skill/command frontmatter validation (Agent Skills spec).
NAME_MAX = 64
DESCRIPTION_MAX = 1024
# Claude Code truncates `description` + `when_to_use` in the skill listing.
LISTING_MAX = 1536
# "Keep SKILL.md body under 500 lines for optimal performance."
SKILL_BODY_MAX = 500
# "target under 200 lines per CLAUDE.md file"
CLAUDE_MD_MAX = 200
# "For reference files longer than 100 lines, include a table of contents."
REFERENCE_TOC_MIN = 100

RESERVED_NAME_WORDS = ("anthropic", "claude")
NAME_RE = re.compile(r"^[a-z0-9-]+$")

SKILL_FIELDS = {
    "name", "description", "when_to_use", "argument-hint", "arguments",
    "disable-model-invocation", "user-invocable", "allowed-tools",
    "disallowed-tools", "model", "effort", "context", "agent", "background",
    "hooks", "paths", "shell", "metadata", "license", "compatibility",
}
OUTPUT_STYLE_FIELDS = {"name", "description", "keep-coding-instructions", "force-for-plugin"}
AGENT_FIELDS = {
    "name", "description", "tools", "disallowedTools", "model", "permissionMode",
    "maxTurns", "skills", "mcpServers", "hooks", "memory", "background", "effort",
    "isolation", "color", "initialPrompt",
}

SKIP_DIRS = {".git", "node_modules", "dist", "build", "vendor", "__pycache__", ".venv"}

MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
IMPORT_RE = re.compile(r"(?<![`\w])@([\w./~-]+)")
WINDOWS_PATH_RE = re.compile(r"(?<![\w\\])[\w.-]+\\[\w.-]+\.(?:md|py|sh|js|ts|json|txt)")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


@dataclass
class Artifact:
    path: str
    kind: str
    frontmatter: dict
    body: str
    body_lines: int
    findings: list = field(default_factory=list)

    def add(self, code: str, message: str) -> None:
        self.findings.append((code, message))


def classify(path: str) -> str | None:
    """Return the artifact kind for a file path, or None if it is not an artifact."""
    name = os.path.basename(path)
    parts = path.replace(os.sep, "/").split("/")
    if name in ("CLAUDE.md", "CLAUDE.local.md"):
        return "claude-md"
    if name == "SKILL.md":
        return "skill"
    if name.endswith(".md"):
        if "rules" in parts and ".claude" in parts:
            return "rule"
        if "commands" in parts:
            return "command"
        if "agents" in parts:
            return "agent"
        if "output-styles" in parts:
            return "output-style"
    if name in ("plugin.json", "marketplace.json") and ".claude-plugin" in parts:
        return "manifest"
    return None


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse the leading YAML frontmatter block. Handles the scalar and list forms
    that instruction files actually use; anything else is kept as a raw string."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[text.find("\n") + 1:end]
    body = text[end + 4:].lstrip("\n")
    data: dict = {}
    key = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t", "-")) and key:
            item = line.strip().lstrip("- ").strip()
            if isinstance(data.get(key), list):
                data[key].append(item)
            elif data.get(key) in ("", None):
                data[key] = [item]
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            data[key] = value.strip().strip("'\"")
    return data, body


def strip_code_fences(body: str) -> str:
    out, inside = [], False
    for line in body.splitlines():
        if FENCE_RE.match(line):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def discover(roots: list[str]) -> list[Artifact]:
    artifacts: list[Artifact] = []
    seen: set[str] = set()
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for filename in sorted(filenames):
                path = os.path.normpath(os.path.join(dirpath, filename))
                if path in seen:
                    continue
                kind = classify(path)
                if not kind:
                    continue
                seen.add(path)
                try:
                    text = open(path, encoding="utf-8").read()
                except (OSError, UnicodeDecodeError) as exc:
                    print(f"<!-- skipped {path}: {exc} -->")
                    continue
                fm, body = ({}, text) if kind == "manifest" else parse_frontmatter(text)
                artifacts.append(
                    Artifact(path, kind, fm, body, len(body.splitlines()))
                )
    return artifacts


def check_name_and_description(art: Artifact, fields: set) -> None:
    name = art.frontmatter.get("name")
    if isinstance(name, str) and name:
        if len(name) > NAME_MAX:
            art.add("NAME-LEN", f"name is {len(name)} chars (max {NAME_MAX})")
        if not NAME_RE.match(name):
            art.add("NAME-CHARS", f"name '{name}' must be lowercase letters, numbers, hyphens")
        if any(word in name.lower() for word in RESERVED_NAME_WORDS):
            art.add("NAME-RESERVED", f"name '{name}' contains a reserved word")

    description = art.frontmatter.get("description")
    if not description:
        art.add("DESC-MISSING", "no description — discovery falls back to the first paragraph")
    elif isinstance(description, str):
        if len(description) > DESCRIPTION_MAX:
            art.add("DESC-LEN", f"description is {len(description)} chars (max {DESCRIPTION_MAX})")
        combined = len(description) + len(str(art.frontmatter.get("when_to_use", "")))
        if combined > LISTING_MAX:
            art.add("DESC-LISTING", f"description + when_to_use is {combined} chars, truncated at {LISTING_MAX}")
        if re.search(r"\b(I can|I will|you can use this|this lets you)\b", description, re.I):
            art.add("DESC-PERSON", "description is not in third person")

    unknown = sorted(set(art.frontmatter) - fields)
    if unknown:
        art.add("FM-UNKNOWN", f"unrecognized frontmatter key(s): {', '.join(unknown)}")


def check_links(art: Artifact, artifacts_by_path: dict) -> None:
    base = os.path.dirname(art.path)
    prose = strip_code_fences(art.body)
    for target in MD_LINK_RE.findall(prose):
        if target.startswith(("http://", "https://", "#", "mailto:", "$", "<")):
            continue
        resolved = os.path.normpath(os.path.join(base, target.split("#")[0]))
        if not os.path.exists(resolved):
            art.add("LINK-DEAD", f"link target does not exist: {target}")
    for hit in WINDOWS_PATH_RE.findall(prose):
        art.add("PATH-WINDOWS", f"Windows-style path '{hit}' — use forward slashes")


def check_skill_bundle(art: Artifact) -> None:
    """Body size, bundled-file wiring, and reference depth for a skill directory."""
    if art.body_lines > SKILL_BODY_MAX:
        art.add("BODY-LEN", f"body is {art.body_lines} lines (keep under {SKILL_BODY_MAX})")

    skill_dir = os.path.dirname(art.path)
    linked = {
        os.path.normpath(os.path.join(skill_dir, t.split("#")[0]))
        for t in MD_LINK_RE.findall(art.body)
        if not t.startswith(("http://", "https://", "#", "$", "<"))
    }
    for dirpath, dirnames, filenames in os.walk(skill_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            path = os.path.normpath(os.path.join(dirpath, filename))
            if path == art.path or filename.startswith("."):
                continue
            rel = os.path.relpath(path, skill_dir)
            if path not in linked and rel not in art.body:
                art.add("BUNDLE-ORPHAN", f"{rel} is never referenced from SKILL.md")

    for target in sorted(linked):
        if not target.endswith(".md") or not os.path.exists(target):
            continue
        try:
            ref_text = open(target, encoding="utf-8").read()
        except OSError:
            continue
        rel = os.path.relpath(target, skill_dir)
        if len(ref_text.splitlines()) > REFERENCE_TOC_MIN and "## Contents" not in ref_text:
            art.add("REF-TOC", f"{rel} is over {REFERENCE_TOC_MIN} lines with no '## Contents' section")
        ref_dir = os.path.dirname(target)
        for nested in MD_LINK_RE.findall(strip_code_fences(ref_text)):
            if nested.startswith(("http://", "https://", "#", "$", "<")) or not nested.endswith(".md"):
                continue
            nested_path = os.path.normpath(os.path.join(ref_dir, nested.split("#")[0]))
            if nested_path not in linked and nested_path != art.path:
                art.add("REF-DEPTH", f"{rel} links to {nested}, which SKILL.md does not link — keep references one level deep")


def check_claude_md(art: Artifact) -> None:
    if art.body_lines > CLAUDE_MD_MAX:
        art.add("BODY-LEN", f"{art.body_lines} lines (target under {CLAUDE_MD_MAX})")
    base = os.path.dirname(art.path)
    for target in IMPORT_RE.findall(strip_code_fences(art.body)):
        resolved = os.path.expanduser(target) if target.startswith("~") else os.path.normpath(os.path.join(base, target))
        if not os.path.exists(resolved) and not os.path.exists(resolved + ".md"):
            art.add("IMPORT-DEAD", f"@{target} does not resolve to a file")


def check_manifest(art: Artifact) -> None:
    try:
        data = json.loads(art.body)
    except json.JSONDecodeError as exc:
        art.add("JSON-INVALID", f"not valid JSON: {exc}")
        return
    if os.path.basename(art.path) == "plugin.json":
        for required in ("name", "description", "version"):
            if not data.get(required):
                art.add("MANIFEST-FIELD", f"plugin.json has no '{required}'")
        art.frontmatter = {"name": data.get("name", "")}
    else:
        names = [p.get("name", "?") for p in data.get("plugins", [])]
        for entry in data.get("plugins", []):
            source = entry.get("source", "")
            if isinstance(source, str) and source.startswith("./") and not os.path.isdir(
                os.path.normpath(os.path.join(os.path.dirname(art.path), "..", source))
            ):
                art.add("MANIFEST-SOURCE", f"plugin '{entry.get('name')}' points at a missing source: {source}")
        art.frontmatter = {"name": f"{len(names)} plugin(s)"}


def main(argv: list[str]) -> int:
    roots = argv[1:] or ["."]
    for root in roots:
        if not os.path.exists(root):
            print(f"error: no such path: {root}", file=sys.stderr)
            return 1

    artifacts = discover(roots)
    if not artifacts:
        print("No instruction artifacts found under: " + ", ".join(roots))
        return 0

    by_path = {a.path: a for a in artifacts}
    for art in artifacts:
        if art.kind in ("skill", "command"):
            check_name_and_description(art, SKILL_FIELDS)
            check_links(art, by_path)
            if art.kind == "skill":
                check_skill_bundle(art)
            elif art.body_lines > SKILL_BODY_MAX:
                art.add("BODY-LEN", f"body is {art.body_lines} lines (keep under {SKILL_BODY_MAX})")
        elif art.kind == "agent":
            check_name_and_description(art, AGENT_FIELDS)
            check_links(art, by_path)
            if ":" in str(art.frontmatter.get("name", "")):
                art.add("NAME-CHARS", "subagent name cannot contain ':'")
        elif art.kind in ("claude-md", "rule"):
            check_claude_md(art)
            check_links(art, by_path)
        elif art.kind == "output-style":
            # An output style's `name` is a display label, so the lowercase/hyphen
            # rule that governs skill and agent names does not apply here.
            if not art.frontmatter.get("description"):
                art.add("DESC-MISSING", "no description — the /config picker shows nothing")
            unknown = sorted(set(art.frontmatter) - OUTPUT_STYLE_FIELDS)
            if unknown:
                art.add("FM-UNKNOWN", f"unrecognized frontmatter key(s): {', '.join(unknown)}")
        elif art.kind == "manifest":
            check_manifest(art)

    print("## Inventory\n")
    print("| Path | Kind | Body lines | Description chars | Findings |")
    print("|------|------|-----------:|------------------:|---------:|")
    for art in sorted(artifacts, key=lambda a: (a.kind, a.path)):
        desc = art.frontmatter.get("description", "")
        desc_len = len(desc) if isinstance(desc, str) else 0
        print(f"| `{art.path}` | {art.kind} | {art.body_lines} | {desc_len or '-'} | {len(art.findings) or '-'} |")

    total = sum(len(a.findings) for a in artifacts)
    print(f"\n## Mechanical findings ({total})\n")
    if not total:
        print("None. Every hard limit and link resolves; the remaining checks are judgement calls.")
    for art in sorted(artifacts, key=lambda a: a.path):
        if not art.findings:
            continue
        print(f"\n### `{art.path}`\n")
        for code, message in art.findings:
            print(f"- **{code}** — {message}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
