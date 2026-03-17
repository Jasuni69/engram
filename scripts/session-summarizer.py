#!/usr/bin/env python3
"""
session-summarizer.py — Distill heartbeat_run.log into memory/{date}.md.
Parses bracketed timestamps from the log, extracts per-session output,
and appends a structured summary to today's daily memory file.
Run after a weekend build: python session-summarizer.py
"""
import re
import sys
from pathlib import Path
from datetime import datetime, date

BASE = Path(__file__).parent.parent
LOG_FILE = BASE / "logs" / "heartbeat_run.log"
MEMORY_DIR = BASE / "memory"


_TS_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]")


def parse_log(log_text: str) -> list[dict]:
    """Split log into sessions keyed by timestamp."""
    sessions: list[dict] = []
    current: dict | None = None
    for line in log_text.splitlines():
        m = _TS_RE.match(line)
        if m and "Weekend build triggered" in line:
            if current:
                sessions.append(current)
            current = {"ts": m.group(1), "lines": []}
        elif current is not None:
            current["lines"].append(line)
    if current:
        sessions.append(current)
    return sessions


def summarize_session(session: dict) -> str:
    ts = session["ts"]
    lines = session["lines"]
    total = len(lines)

    # Detect git push line
    pushed = any("Git push complete" in l for l in lines)
    push_note = "Git push: YES" if pushed else "Git push: NO"

    # Detect WRAP UP section (Claude writes this in STEP 5)
    wrap_lines: list[str] = []
    in_wrap = False
    for line in lines:
        if "WRAP UP" in line or "## Completed" in line:
            in_wrap = True
        if in_wrap and line.strip().startswith(("-", "*", "✅", "🔲", "[")):
            wrap_lines.append(f"  {line.strip()}")
        if in_wrap and len(wrap_lines) > 10:
            break

    summary_lines = [
        f"### Build session — {ts}",
        f"- Log lines: {total}",
        f"- {push_note}",
    ]
    if wrap_lines:
        summary_lines.append("- Wrap-up notes:")
        summary_lines.extend(wrap_lines)
    else:
        # Fallback: grab last 5 non-blank lines as context
        tail = [l for l in lines if l.strip()][-5:]
        summary_lines.append("- Session tail (last 5 lines):")
        for l in tail:
            summary_lines.append(f"  {l.strip()}")

    return "\n".join(summary_lines)


def append_to_daily(target_date: date, content: str) -> Path:
    MEMORY_DIR.mkdir(exist_ok=True)
    out_file = MEMORY_DIR / f"{target_date.isoformat()}.md"
    header = f"# {target_date.isoformat()}\n\n## Session Summaries (from heartbeat_run.log)\n\n"
    if out_file.exists():
        existing = out_file.read_text(encoding="utf-8")
        if "## Session Summaries" not in existing:
            out_file.write_text(existing + "\n\n## Session Summaries (from heartbeat_run.log)\n\n" + content, encoding="utf-8")
        else:
            out_file.write_text(existing + "\n\n" + content, encoding="utf-8")
    else:
        out_file.write_text(header + content, encoding="utf-8")
    return out_file


def main() -> None:
    if not LOG_FILE.exists():
        print(f"[summarizer] No log file found at {LOG_FILE}")
        sys.exit(0)

    log_text = LOG_FILE.read_text(encoding="utf-8")
    sessions = parse_log(log_text)

    if not sessions:
        print("[summarizer] No sessions found in log.")
        sys.exit(0)

    today = date.today()
    # Only summarize sessions from today (or pass --all to get everything)
    all_mode = "--all" in sys.argv
    target_sessions = sessions if all_mode else [
        s for s in sessions if s["ts"].startswith(today.isoformat())
    ]

    if not target_sessions:
        print(f"[summarizer] No sessions from {today} in log. Use --all to summarize all.")
        sys.exit(0)

    summaries = "\n\n".join(summarize_session(s) for s in target_sessions)
    out_file = append_to_daily(today, summaries)
    print(f"[summarizer] Appended {len(target_sessions)} session(s) to {out_file}")


if __name__ == "__main__":
    main()
