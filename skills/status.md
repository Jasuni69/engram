---
name: status
description: >
  Show current situational awareness: pending tasks from HEARTBEAT.md, recent log
  entries, and memory freshness (age of today's daily log).
  Use when user says "/status", "what's the status", "what's pending", "what did we do last",
  or wants a quick state-of-the-world summary.
---

# Status — ENGRAM

Show a situational awareness snapshot. Do ALL steps in order, in parallel where possible.

## Working directory
`{{base_dir}}`

## Steps

1. **Pending tasks** — Read `{{base_dir}}/core/HEARTBEAT.md`, list all `- [ ]` items from `## Pending Tasks`. If none, say "no pending tasks".

2. **Recent heartbeat log** — Read `{{base_dir}}/core/HEARTBEAT.md`, show the last 3 entries from `## Log` (most recent sessions). If Log section is empty, say so.

3. **Memory freshness** — Check if `{{base_dir}}/memory/<today's date>.md` exists.
   - If yes: show its last modified time and first 3 bullet points.
   - If no: flag as **STALE** — memory has not been flushed today.

4. **Task queue** (optional) — If `{{base_dir}}/tasks.json` exists, read it and show:
   - Count of pending tasks by category
   - Any tasks with priority 1 or 2

## Output format

Format as a compact markdown summary with short sections. Scannable, no prose — just facts.

```
## Status — YYYY-MM-DD HH:MM

**Pending tasks (N)**
- [ ] ...

**Recent log**
- YYYY-MM-DD: ...

**Memory:** fresh / STALE

**Queue:** N pending (K high-priority)
```

Keep the whole output under 30 lines.
