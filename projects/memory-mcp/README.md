# memory-mcp

MCP server exposing SOUL.md, MEMORY.md, HEARTBEAT.md, and memory search as tools.

## Install

```bash
pip install mcp
```

## Tools

| Tool | Description |
|------|-------------|
| `read_soul` | Read SOUL.md |
| `read_heartbeat` | Read HEARTBEAT.md |
| `read_memory` | Read MEMORY.md |
| `read_daily_log` | Read memory/{date}.md (defaults to today) |
| `search_memory` | Keyword/TF-IDF search across all .md files |
| `append_heartbeat_log` | Append timestamped entry to HEARTBEAT.md |
| `run_context_pack` | Regenerate MEMORY.md via context-pack.py |
| `list_memory_files` | List all daily log files |

## Claude Desktop Config

Add to your `claude_desktop_config.json` (path set by bootstrap):

```json
{
  "mcpServers": {
    "memory": {
      "command": "python",
      "args": ["/your/engram/path/projects/memory-mcp/server.py"]
    }
  }
}
```

> `bootstrap` will patch this file automatically.
