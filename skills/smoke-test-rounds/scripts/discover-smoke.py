#!/usr/bin/env python3
"""
discover-smoke.py
Read-only helper for smoke-test-rounds skill.
Detects specified features (.specs/features/* or .agent/specs/*), existing smoke runners
(scripts/smoke/, tests/smoke/, package.json scripts, Makefile targets), and QA skill availability
without creating or modifying any files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


def discover_features(root: Path) -> list[dict]:
    features: list[dict] = []
    specs_dir = root / ".specs" / "features"
    if specs_dir.is_dir():
        for d in sorted(specs_dir.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            artifacts = [f.name for f in d.iterdir() if f.is_file() and f.suffix == ".md"]
            features.append(
                {
                    "slug": d.name,
                    "spec_dir": str(d.relative_to(root)),
                    "artifacts": sorted(artifacts),
                }
            )
    agent_specs_dir = root / ".agent" / "specs"
    if agent_specs_dir.is_dir():
        known = {f["slug"] for f in features}
        for f in sorted(agent_specs_dir.glob("*.spec.md")):
            slug = f.name.replace(".spec.md", "")
            if slug not in known:
                features.append(
                    {
                        "slug": slug,
                        "spec_dir": str(f.relative_to(root)),
                        "artifacts": [f.name],
                    }
                )
    return features


def discover_smoke_runners(root: Path) -> dict:
    script_files: list[str] = []
    for rel_dir in ("scripts/smoke", "tests/smoke", "test/smoke", "e2e/smoke"):
        d = root / rel_dir
        if d.is_dir():
            for p in sorted(d.rglob("*")):
                if p.is_file() and not p.name.startswith("."):
                    script_files.append(str(p.relative_to(root)))

    package_scripts: dict[str, str] = {}
    pkg_json = root / "package.json"
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            for k, v in (data.get("scripts") or {}).items():
                if "smoke" in k.lower():
                    package_scripts[k] = str(v)
        except Exception:
            pass

    makefile_targets: list[str] = []
    makefile = root / "Makefile"
    if makefile.is_file():
        for line in makefile.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"^([A-Za-z0-9_.-]*smoke[A-Za-z0-9_.-]*)\s*:", line, re.I)
            if m:
                makefile_targets.append(m.group(1))

    return {
        "smoke_files": script_files,
        "package_scripts": package_scripts,
        "makefile_targets": makefile_targets,
    }


def discover_qa_skills(root: Path) -> dict[str, str | None]:
    home = Path.home()
    out: dict[str, str | None] = {}
    for skill in ("qa-report", "qa-execution"):
        found: str | None = None
        for base in (
            root / ".agent" / "skills",
            root / ".agents" / "skills",
            home / ".agents" / "skills",
        ):
            cand = base / skill / "SKILL.md"
            if cand.is_file():
                found = str(cand)
                break
        out[skill] = found
    return out


def match_feature_runners(features: list[dict], runners: dict) -> list[dict]:
    smoke_files = runners["smoke_files"]
    matched = []
    for feat in features:
        slug_norm = feat["slug"].lower().replace("-", "_")
        slug_dash = feat["slug"].lower()
        hits = [
            sf
            for sf in smoke_files
            if slug_norm in sf.lower().replace("-", "_") or slug_dash in sf.lower()
        ]
        matched.append(
            {
                **feat,
                "matched_smoke_files": hits,
                "coverage": "COVERED" if hits else "UNCOVERED",
            }
        )
    return matched


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover spec features and existing smoke test runners.")
    parser.add_argument("--root", default=".", help="Project root directory")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    features = discover_features(root)
    runners = discover_smoke_runners(root)
    qa = discover_qa_skills(root)
    result = {
        "root": str(root),
        "features": match_feature_runners(features, runners),
        "runners": runners,
        "qa_skills": qa,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
