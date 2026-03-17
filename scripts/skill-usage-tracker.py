#!/usr/bin/env python3
"""
skill-usage-tracker.py — parse Claude Code session logs, count skill invocations,
append weekly stats to SKILL_STATS.md.
"""

import json
import glob
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).parent.parent
SKILL_STATS_FILE = BASE / "SKILL_STATS.md"
PROJECTS_DIR = Path.home() / ".claude" / "projects"


def scan_skills(since_days: int = 7) -> Counter:
    """Scan all project jsonl files for Skill tool invocations in the last N days."""
    cutoff = (date.today() - timedelta(days=since_days)).isoformat()
    counts: Counter = Counter()

    for jsonl_path in PROJECTS_DIR.rglob("*.jsonl"):
        try:
            with open(jsonl_path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Only assistant messages within the time window
                    if obj.get("type") != "assistant":
                        continue
                    ts = obj.get("timestamp", "")
                    if ts and ts[:10] < cutoff:
                        continue

                    for block in obj.get("message", {}).get("content", []):
                        if (
                            isinstance(block, dict)
                            and block.get("type") == "tool_use"
                            and block.get("name") == "Skill"
                        ):
                            skill = block.get("input", {}).get("skill", "unknown")
                            counts[skill] += 1
        except OSError:
            continue

    return counts


def append_stats(counts: Counter, since_days: int = 7) -> None:
    today = date.today().isoformat()
    since = (date.today() - timedelta(days=since_days)).isoformat()

    lines = [f"\n## {today} (last {since_days}d: {since} → {today})\n"]
    if not counts:
        lines.append("No skill invocations found.\n")
    else:
        lines.append(f"{'Skill':<35} {'Count':>5}\n")
        lines.append(f"{'─' * 35} {'─' * 5}\n")
        for skill, count in counts.most_common():
            lines.append(f"{skill:<35} {count:>5}\n")
        lines.append(f"\nTotal invocations: {sum(counts.values())}\n")

    if not SKILL_STATS_FILE.exists():
        SKILL_STATS_FILE.write_text("# SKILL_STATS\n\nTracked by skill-usage-tracker.py.\n", encoding="utf-8")

    with SKILL_STATS_FILE.open("a", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Appended stats to {SKILL_STATS_FILE}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Track Claude Code skill usage")
    parser.add_argument("--days", type=int, default=7, help="Look-back window in days (default: 7)")
    parser.add_argument("--print-only", action="store_true", help="Print results without writing to file")
    args = parser.parse_args()

    print(f"Scanning {PROJECTS_DIR} for skill invocations (last {args.days}d)...")
    counts = scan_skills(since_days=args.days)

    if not counts:
        print("No skill invocations found.")
    else:
        for skill, count in counts.most_common():
            print(f"  {skill:<35} {count}")
        print(f"  {'TOTAL':<35} {sum(counts.values())}")

    if not args.print_only:
        append_stats(counts, since_days=args.days)


if __name__ == "__main__":
    main()
