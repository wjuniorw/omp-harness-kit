#!/usr/bin/env python3
"""
next-round.py
Read-only CLI helper for smoke-test-rounds skill.
Inspects smoke-rounds/ directory and computes the next sequential round identifier.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import sys


def find_next_round(base_dir: str, env: str) -> tuple[int, str]:
    if not os.path.exists(base_dir):
        next_num = 1
    else:
        entries = os.listdir(base_dir)
        round_nums = []
        for entry in entries:
            m = re.match(r"^round-(\d+)", entry)
            if m:
                round_nums.append(int(m.group(1)))
        next_num = max(round_nums) + 1 if round_nums else 1

    round_id = f"round-{next_num:02d}"
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    folder_name = f"{round_id}-{env}-{today}"
    return next_num, folder_name


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute next sequential round identifier for smoke test rounds."
    )
    parser.add_argument(
        "--dir",
        default="smoke-rounds",
        help="Base directory containing smoke test rounds (default: smoke-rounds)",
    )
    parser.add_argument(
        "--env",
        default="staging",
        choices=["staging", "local", "test", "homologacao", "production"],
        help="Target environment name (default: staging)",
    )

    args = parser.parse_args()
    try:
        _, folder_name = find_next_round(args.dir, args.env)
        print(folder_name)
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error computing next round: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
