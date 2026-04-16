#!/usr/bin/env python3
"""
dispatch.py — Parallel autonomous agent dispatcher.

Reads tasks from tasks.json, spawns up to MAX_WORKERS concurrent claude
subprocesses. No polling, no idle loops — pure event-driven execution.

Usage:
    python dispatch.py                      # run all pending tasks
    python dispatch.py --dry-run            # show what would run
    python dispatch.py --push "prompt"      # push a task and run
    python dispatch.py --push "prompt" --category research  # push with category
    python dispatch.py --list               # show queue
    python dispatch.py --populate           # populate queue from SOUL.md tasks

Task schema (tasks.json):
    [
        {
            "id": "unique-id",
            "priority": 1-5 (1=highest),
            "category": "infrastructure|research|skill|memory|journal",
            "prompt": "...",
            "status": "pending|running|done|failed",
            "created": "ISO timestamp",
            "result_file": "logs/dispatch-<id>.txt"
        }
    ]
"""
import argparse
import json
import os
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
TASKS_FILE = BASE / "tasks.json"
LOGS_DIR = BASE / "logs"
MAX_WORKERS = 3
TIMEOUT_SECONDS = 300  # 5 min per task

# Detect claude executable
def _find_claude() -> str:
    for candidate in ["claude", "claude.exe"]:
        try:
            subprocess.run([candidate, "--version"], capture_output=True, timeout=5)
            return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    # fallback: user-local install
    home = Path.home()
    for p in [home / ".local/bin/claude", home / ".local/bin/claude.exe"]:
        if p.exists():
            return str(p)
    return "claude"

CLAUDE = _find_claude()
LOGS_DIR.mkdir(exist_ok=True)


# ── Queue management ─────────────────────────────────────────────────────────

def load_tasks() -> list[dict]:
    if not TASKS_FILE.exists():
        return []
    return json.loads(TASKS_FILE.read_text(encoding="utf-8"))


def save_tasks(tasks: list[dict]) -> None:
    TASKS_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")


def push_task(prompt: str, category: str = "infrastructure", priority: int = 3) -> dict:
    tasks = load_tasks()
    task = {
        "id": str(uuid.uuid4())[:8],
        "priority": priority,
        "category": category,
        "prompt": prompt,
        "status": "pending",
        "created": datetime.now().isoformat(),
        "result_file": None,
    }
    tasks.append(task)
    tasks.sort(key=lambda t: t["priority"])
    save_tasks(tasks)
    return task


def get_pending(tasks: list[dict], category: str | None = None) -> list[dict]:
    pending = [t for t in tasks if t["status"] == "pending"]
    if category:
        pending = [t for t in pending if t["category"] == category]
    return sorted(pending, key=lambda t: t["priority"])


# ── Execution ────────────────────────────────────────────────────────────────

def run_task(task: dict) -> dict:
    task_id = task["id"]
    log_path = LOGS_DIR / f"dispatch-{task_id}.txt"
    task["result_file"] = str(log_path)
    task["status"] = "running"

    cmd = [
        CLAUDE,
        "--dangerously-skip-permissions",
        "-p", task["prompt"],
        "--output-format", "text",
    ]

    start = datetime.now()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=str(BASE),
        )
        elapsed = (datetime.now() - start).seconds
        output = result.stdout or result.stderr or "(no output)"
        log_path.write_text(
            f"[{start.isoformat()}] Task {task_id} ({task['category']})\n"
            f"Prompt: {task['prompt']}\n\n"
            f"--- Output ({elapsed}s) ---\n{output}",
            encoding="utf-8",
        )
        task["status"] = "done" if result.returncode == 0 else "failed"
    except subprocess.TimeoutExpired:
        task["status"] = "failed"
        log_path.write_text(f"[TIMEOUT] Task {task_id} exceeded {TIMEOUT_SECONDS}s", encoding="utf-8")
    except Exception as e:
        task["status"] = "failed"
        log_path.write_text(f"[ERROR] Task {task_id}: {e}", encoding="utf-8")

    return task


def run_all(tasks: list[dict], pending: list[dict], dry_run: bool = False) -> None:
    if not pending:
        print("[dispatch] No pending tasks.")
        return

    print(f"[dispatch] {len(pending)} task(s) to run (workers={MAX_WORKERS})")
    if dry_run:
        for t in pending:
            print(f"  [{t['priority']}] {t['category']}: {t['prompt'][:80]}")
        return

    id_to_idx = {t["id"]: i for i, t in enumerate(tasks)}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(run_task, t): t for t in pending}
        for fut in as_completed(futures):
            result = fut.result()
            idx = id_to_idx.get(result["id"])
            if idx is not None:
                tasks[idx] = result
            save_tasks(tasks)
            status_icon = "✓" if result["status"] == "done" else "✗"
            print(f"  {status_icon} {result['id']} [{result['category']}] → {result['result_file']}")


# ── Populate ─────────────────────────────────────────────────────────────────

def populate_from_soul() -> list[dict]:
    """Push self-generate tasks from SOUL.md into queue."""
    soul_path = BASE / "core" / "SOUL.md"
    if not soul_path.exists():
        print("[dispatch] core/SOUL.md not found.")
        return []

    text = soul_path.read_text(encoding="utf-8")
    tasks = load_tasks()
    existing_prompts = {t["prompt"] for t in tasks}

    added = []
    in_section = False
    for line in text.splitlines():
        if "self-generate" in line.lower() or "autonomous" in line.lower():
            in_section = True
            continue
        if in_section and line.startswith("## "):
            in_section = False
        if in_section and line.strip().startswith("-"):
            prompt = line.strip().lstrip("- ").strip()
            if prompt and prompt not in existing_prompts:
                task = push_task(prompt, category="research", priority=3)
                added.append(task)
                existing_prompts.add(prompt)

    print(f"[dispatch] Populated {len(added)} task(s) from SOUL.md")
    return added


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="ENGRAM task dispatcher")
    parser.add_argument("--push", metavar="PROMPT", help="Push a new task and run")
    parser.add_argument("--category", default="infrastructure", help="Task category")
    parser.add_argument("--priority", type=int, default=3, help="Task priority (1=highest)")
    parser.add_argument("--list", action="store_true", help="Show task queue")
    parser.add_argument("--populate", action="store_true", help="Populate queue from SOUL.md")
    parser.add_argument("--dry-run", action="store_true", help="Show tasks without running")
    args = parser.parse_args()

    if args.list:
        tasks = load_tasks()
        if not tasks:
            print("[dispatch] Queue is empty.")
            return
        for t in tasks:
            icon = {"pending": "⏳", "running": "🔄", "done": "✓", "failed": "✗"}.get(t["status"], "?")
            print(f"  {icon} [{t['priority']}] {t['id']} {t['category']}: {t['prompt'][:70]}")
        return

    if args.populate:
        populate_from_soul()

    if args.push:
        push_task(args.push, category=args.category, priority=args.priority)
        print(f"[dispatch] Pushed task: {args.push[:60]}")

    tasks = load_tasks()
    pending = get_pending(tasks)
    run_all(tasks, pending, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
