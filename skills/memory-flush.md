---
name: memory-flush
description: >
  Flush session memory to persistent storage. Use this skill whenever the user says
  "flush memory", "save to memory", "pre-compaction flush", "end session", "wrap up",
  or whenever a long session is winding down and facts/decisions should be persisted.
  Also trigger proactively when the conversation is getting long and context compression
  is a risk — don't wait for the user to ask.
---

# Memory Flush

You are persisting durable facts and decisions from this session to long-term memory files.

## Files involved

- `{{base_dir}}/core/HEARTBEAT.md` — session state + log
- `{{base_dir}}/MEMORY.md` — curated long-term facts
- `{{base_dir}}/memory/YYYY-MM-DD.md` — daily log (today's date)

## Steps

1. **Read HEARTBEAT.md** — focus on the `## Log` section, especially recent entries not yet in MEMORY.md.

2. **Read MEMORY.md** — understand what's already persisted so you don't duplicate.

3. **Extract new durable facts** from HEARTBEAT that are NOT already in MEMORY.md. A durable fact is:
   - A key decision that affects future sessions
   - A solved problem worth remembering
   - A stable architectural choice or path
   - A user preference or workflow rule confirmed across sessions

   Skip: session-specific context, in-progress tasks, obvious or trivial info.

4. **Append to MEMORY.md** under `## Durable Facts / Key Decisions`:
   ```
   - <concise fact>  *(from YYYY-MM-DD)*
   ```

5. **Write/append daily log** to `{{base_dir}}/memory/{today's date}.md`:
   - If file exists: append a new `### HH:MM` section
   - If not: create with `# Daily Log — YYYY-MM-DD` header
   - Include: what was built/changed, key decisions, things learned, files touched

6. **Append to HEARTBEAT.md** `## Log` section:
   ```
   ### YYYY-MM-DD HH:MM
   - Memory flush complete. <N> new facts saved to MEMORY.md.
   - Daily log updated at memory/YYYY-MM-DD.md
   ```

## Tone
Be concise in log entries. No fluff. Facts only.
