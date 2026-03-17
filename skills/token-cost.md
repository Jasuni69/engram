---
name: token-cost
description: >
  List all Claude Code project directories and show token/cost usage. Use when the user
  asks about token usage, Claude Code costs, or "how much have I spent".
---

# Token Cost

List all subdirectories in `~/.claude/projects/`. Each subdirectory is a Claude Code project.
Show the directory name, number of `.jsonl` session files, and approximate line counts as a
proxy for usage.

## Steps

1. List all subdirectories in `~/.claude/projects/` using Bash:
   ```bash
   ls ~/.claude/projects/
   ```

2. For each project directory, count `.jsonl` files:
   ```bash
   find ~/.claude/projects -name "*.jsonl" | wc -l
   ```

3. Report: project name, session count, total lines across all jsonl files.

4. Note: exact token counts require parsing jsonl. Line count is a rough proxy.
   For exact costs, check console.anthropic.com.
