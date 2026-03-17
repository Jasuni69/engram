# ENGRAM

> Persistent memory and identity for Claude Code.

ENGRAM gives Claude a home — a SOUL, a HEARTBEAT, and a memory that survives across sessions.
Run `/bootstrap` once. You're live.

---

## What you get

- **SOUL.md** — Claude's identity: who you are, what you work on, what you hate
- **HEARTBEAT.md** — session state tracker: what's in progress, what's pending
- **MEMORY.md** — curated durable facts across all sessions
- **memory-mcp** — MCP server exposing your memory to Claude Desktop (8 tools)
- **mcp-todoist** — MCP server for Todoist task management (5 tools)
- **Skills** — `/memory-flush`, `/git-push`, `/new-project`, `/token-cost`
- **Scripts** — context-pack, memory-indexer, session-summarizer, idea-collider

## Requirements

- [Claude Code](https://claude.ai/claude-code) installed
- Python 3.10+
- Node.js 18+ (for Todoist MCP, optional)
- A Todoist account + API token (optional)

## Setup

```bash
git clone https://github.com/yourusername/engram.git
cd engram
claude  # open Claude Code in this directory
```

Then in Claude Code:
```
/bootstrap
```

Answer 5–7 questions. ENGRAM sets itself up, installs MCPs, copies skills, patches your Claude Desktop config. Takes ~2 minutes.

Restart Claude Desktop when prompted.

---

## Structure

```
engram/
├── core/               # populated by /bootstrap
│   ├── SOUL.md
│   ├── HEARTBEAT.md
│   └── claude_memory.json
├── memory/             # daily logs, auto-written by Claude
├── scripts/            # context-pack, memory-indexer, etc.
├── projects/
│   ├── memory-mcp/     # Python MCP server
│   └── mcp-todoist/    # TypeScript MCP server
├── skills/             # Claude Code skill definitions
└── templates/          # filled by /bootstrap
```

## How it works

Every session, Claude reads your SOUL.md and HEARTBEAT.md before responding. It searches your memory for relevant context. At session end it writes a daily log and updates MEMORY.md.

You get a Claude that remembers you.

---

## Credits

Built by [Jason Nicolini](https://github.com/Jasuni69) and Claude.
Inspired by [OpenClaw](https://github.com/claw-so/openclaw).
