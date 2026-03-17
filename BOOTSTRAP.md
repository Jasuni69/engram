# BOOTSTRAP

> This file is deleted automatically when `/bootstrap` completes.

This is ENGRAM's first-run setup tracker. If you're reading this, ENGRAM has not been bootstrapped yet.

## How to bootstrap

1. Open Claude Code in this directory
2. Run `/bootstrap`
3. Answer the questions
4. Restart Claude Desktop

That's it.

---

## What bootstrap does

1. Asks your name, company, role, tools, base directory
2. Optionally configures Todoist integration
3. Writes `core/SOUL.md`, `core/HEARTBEAT.md`, `core/claude_memory.json`
4. Writes `MEMORY.md` and `TASKS.md` (empty)
5. Installs MCP server dependencies
6. Copies skills to `~/.claude/commands/`
7. Patches `claude_desktop_config.json`
8. Optionally registers a daily heartbeat scheduled task
9. Deletes this file
10. Prints: "ENGRAM is live."
