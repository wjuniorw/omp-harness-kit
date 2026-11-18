#!/usr/bin/env python3
"""
assert-task-skills.py — Deterministic Meta-Harness skill binding validator for TLC tasks.md.

Survives upstream updates to `tlc-spec-driven` because it lives outside the skill directory
in `.agent/harness/` and reads stack-specific mappings from `.agent/harness/skill-map.json`.

Checks each `T<n>` task in `tasks.md`:
  ERROR  - declared `Skill:` does not exist in `.agent/skills/`, `.agents/skills/`, or `~/.agents/skills/`
  ERROR  - task matches a rule in `skill-map.json` (by path regex or keyword) with `Skill: NONE` / missing
  WARN   - task modifies code files (`Where:` has source extensions) but declares `Skill: NONE` / missing
           when `require_for_code_tasks` is true (promotable to ERROR via `--strict`)

Exit codes: 0 pass, 1 violations found, 2 usage error.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

TASK_HEADER_RE = re.compile(r"^#{2,4}\s+(T\d+)\s*:\s*(.*)$", re.IGNORECASE)
SKILL_LINE_RE = re.compile(r"^\s*[-*]?\s*\*{0,2}Skill\*{0,2}\s*:\s*(.+)$", re.IGNORECASE)
WHERE_LINE_RE = re.compile(r"^\s*[-*]?\s*\*{0,2}Where\*{0,2}\s*:\s*(.+)$", re.IGNORECASE)
CODE_EXT_RE = re.compile(
    r"\.(ts|tsx|js|jsx|mjs|cjs|go|rs|py|java|kt|swift|rb|cs|vue|svelte)\b",
    re.IGNORECASE,
)


def discover_installed_skills(root: Path) -> set[str]:
    skills: set[str] = set()
    search_dirs = [
        root / ".agent" / "skills",
        root / ".agents" / "skills",
        root / ".claude" / "skills",
        Path.home() / ".agents" / "skills",
        Path.home() / ".claude" / "skills",
    ]
    for base in search_dirs:
        if not base.is_dir():
            continue
        for entry in base.iterdir():
            if entry.is_dir() and (entry / "SKILL.md").is_file():
                skills.add(entry.name)
    return skills


def resolve_tasks_file(target: str | None, root: Path) -> Path | None:
    if target:
        p = Path(target)
        if not p.is_absolute():
            p = (root / p).resolve()
        if p.is_file():
            return p
        if p.is_dir():
            cand = p / "tasks.md"
            if cand.is_file():
                return cand
        feat = root / ".specs" / "features" / target / "tasks.md"
        if feat.is_file():
            return feat
        return None

    cands = sorted(glob.glob(str(root / ".specs" / "features" / "*" / "tasks.md")))
    if len(cands) == 1:
        return Path(cands[0])
    return None


def load_skill_map(root: Path) -> dict:
    for rel in [".agent/harness/skill-map.json", ".agent/skill-map.json"]:
        p = root / rel
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
    return {"require_for_code_tasks": True, "rules": []}


def parse_tasks(tasks_path: Path) -> list[dict]:
    lines = tasks_path.read_text(encoding="utf-8").splitlines()
    tasks: list[dict] = []
    current: dict | None = None

    for idx, line in enumerate(lines, start=1):
        m = TASK_HEADER_RE.match(line)
        if m:
            if current:
                tasks.append(current)
            current = {
                "id": m.group(1).upper(),
                "title": m.group(2).strip(),
                "line": idx,
                "skill": None,
                "where": "",
                "body": [],
            }
            continue
        if current:
            current["body"].append(line)
            sm = SKILL_LINE_RE.match(line)
            if sm and current["skill"] is None:
                raw = sm.group(1).strip().strip("`").strip()
                # Take first token before parens or comma explanation if present
                current["skill"] = raw.split()[0].rstrip(",") if raw else ""
            wm = WHERE_LINE_RE.match(line)
            if wm:
                current["where"] += " " + wm.group(1).strip()

    if current:
        tasks.append(current)
    return tasks


def main() -> int:
    parser = argparse.ArgumentParser(description="Assert Meta-Harness Skill bindings in tasks.md")
    parser.add_argument("target", nargs="?", help="Path to tasks.md, feature dir, or feature name")
    parser.add_argument("--root", default=".", help="Project root (default: .)")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    tasks_path = resolve_tasks_file(args.target, root)
    if not tasks_path:
        print("INFO: No single tasks.md resolved; pass target path or feature name.", file=sys.stderr)
        return 2

    installed = discover_installed_skills(root)
    skill_map = load_skill_map(root)
    rules = skill_map.get("rules", [])
    require_code = skill_map.get("require_for_code_tasks", True)
    tasks = parse_tasks(tasks_path)

    errors: list[str] = []
    warnings: list[str] = []

    for t in tasks:
        tid = t["id"]
        skill = (t["skill"] or "").strip()
        is_none = not skill or skill.upper() == "NONE" or skill.lower() in {"n/a", "-"}
        haystack = f"{t['title']} {t['where']} {' '.join(t['body'][:8])}"

        if not is_none and skill not in installed:
            errors.append(
                f"{tid} (line {t['line']}): declares unknown skill `{skill}` "
                f"(not found in .agent/skills, .agents/skills, or ~/.agents/skills)"
            )

        matched_suggestions: list[str] = []
        for rule in rules:
            pattern = rule.get("match", "")
            req_skill = rule.get("skill", "")
            if not pattern or not req_skill:
                continue
            if re.search(pattern, haystack, re.IGNORECASE):
                if req_skill in installed or not rule.get("only_if_installed", True):
                    matched_suggestions.append(req_skill)

        if is_none and matched_suggestions:
            uniq = ", ".join(dict.fromkeys(matched_suggestions))
            errors.append(
                f"{tid} (line {t['line']}): `Skill: {skill or 'MISSING'}` violates skill-map rule; "
                f"expected one of [{uniq}] for `{t['where'].strip() or t['title']}`"
            )
        elif is_none and require_code and CODE_EXT_RE.search(t["where"]):
            warnings.append(
                f"{tid} (line {t['line']}): touches code ({t['where'].strip()}) with `Skill: {skill or 'MISSING'}` — "
                "bind the appropriate project/global skill to enforce rules without context bloat"
            )

    print(f"assert-task-skills: checked {len(tasks)} task(s) in {tasks_path}")
    for w in warnings:
        print(f"  WARN: {w}")
    for e in errors:
        print(f"  ERROR: {e}")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
