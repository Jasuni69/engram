#!/usr/bin/env python3
"""
memory-mcp/server.py — MCP server exposing SOUL.md, MEMORY.md, HEARTBEAT.md as tools.
Transport: stdio (works with Claude Desktop's MCP config).
Install: pip install mcp
Run via Claude Desktop mcpServers config — see README.md.
"""
import json
import math
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, date as Date
from pathlib import Path

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
except ImportError:
    print("ERROR: mcp package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

BASE = Path(__file__).parent.parent.parent  # → E:\2026\Claude's Corner
SOUL = BASE / "core" / "SOUL.md"
HEARTBEAT = BASE / "core" / "HEARTBEAT.md"
MEMORY = BASE / "MEMORY.md"
MEMORY_DIR = BASE / "memory"
INDEX_FILE = MEMORY_DIR / ".index.json"
CONTEXT_PACK = BASE / "scripts" / "context-pack.py"
MD_ROOTS = [MEMORY_DIR, BASE, BASE / "core"]
TOP_K = 10


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_\-]{2,}", text.lower())


def _collect_docs() -> dict[str, str]:
    docs: dict[str, str] = {}
    for root in MD_ROOTS:
        if not root.exists():
            continue
        pattern = "*.md" if root == BASE else "**/*.md"
        for p in sorted(root.glob(pattern)):
            if p.name.startswith("."):
                continue
            rel = str(p.relative_to(BASE))
            try:
                docs[rel] = p.read_text(encoding="utf-8")
            except Exception:
                pass
    return docs


def _build_index(docs: dict[str, str]) -> dict:
    tf: dict[str, dict[str, float]] = {}
    df: dict[str, int] = defaultdict(int)
    for doc_id, text in docs.items():
        tokens = _tokenize(text)
        if not tokens:
            continue
        freq: dict[str, int] = defaultdict(int)
        for t in tokens:
            freq[t] += 1
        total = len(tokens)
        tf[doc_id] = {t: c / total for t, c in freq.items()}
        for t in freq:
            df[t] += 1
    N = len(docs)
    idf = {t: math.log((N + 1) / (c + 1)) + 1 for t, c in df.items()}
    inverted: dict[str, list] = defaultdict(list)
    for doc_id, term_tf in tf.items():
        for term, score in term_tf.items():
            inverted[term].append((doc_id, score * idf.get(term, 1.0)))
    return {"inverted": dict(inverted), "idf": idf, "docs": list(docs.keys())}


def _is_stale(docs: dict[str, str]) -> bool:
    if not INDEX_FILE.exists():
        return True
    mtime = INDEX_FILE.stat().st_mtime
    for root in MD_ROOTS:
        if not root.exists():
            continue
        pattern = "*.md" if root == BASE else "**/*.md"
        for p in root.glob(pattern):
            if not p.name.startswith(".") and p.stat().st_mtime > mtime:
                return True
    return False


def _load_index() -> dict | None:
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return None


def _save_index(index: dict) -> None:
    INDEX_FILE.parent.mkdir(exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")


def _snippet(text: str, terms: list[str]) -> str:
    lines = text.splitlines()
    section = ""
    for i, line in enumerate(lines):
        if line.strip().startswith("#"):
            section = line.strip()
        if any(t in line.lower() for t in terms):
            ctx = " ".join(l.strip() for l in lines[i:i+3] if l.strip())
            return ((section + " > " if section else "") + ctx)[:200]
    return ""


def _search_memory(query: str, from_date: str | None = None, to_date: str | None = None) -> str:
    docs = _collect_docs()
    index = None if _is_stale(docs) else _load_index()
    if index is None:
        index = _build_index(docs)
        _save_index(index)
    terms = _tokenize(query)
    scores: dict[str, float] = defaultdict(float)
    for term in terms:
        for doc_id, score in index["inverted"].get(term, []):
            scores[doc_id] += score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    fd = Date.fromisoformat(from_date) if from_date else None
    td = Date.fromisoformat(to_date) if to_date else None
    lines = [f"Results for: {query!r}\n"]
    count = 0
    for doc_id, score in ranked:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", Path(doc_id).stem)
        if m:
            d = Date.fromisoformat(m.group(1))
            if fd and d < fd:
                continue
            if td and d > td:
                continue
        snippet = _snippet(docs.get(doc_id, ""), terms)
        lines.append(f"  {count+1}. [{score:.3f}] {doc_id}")
        if snippet:
            lines.append(f"     > {snippet}")
        count += 1
        if count >= TOP_K:
            break
    if count == 0:
        return f"No results for: {query!r}"
    return "\n".join(lines)

server = Server("memory-mcp")


def _read(p: Path) -> str:
    if p.exists():
        return p.read_text(encoding="utf-8")
    return f"[{p.name} not found]"


def _run_script(script: Path, args: list[str] = []) -> str:
    try:
        python = sys.executable if sys.executable else r"C:\Python314\python.exe"
        result = subprocess.run(
            [python, str(script)] + args,
            capture_output=True, text=True, timeout=30,
            cwd=str(BASE),
        )
        out = result.stdout + result.stderr
        return out.strip() or "[no output]"
    except subprocess.TimeoutExpired:
        return "[script timed out after 30s]"
    except Exception as e:
        return f"[error running script: {e}]"


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="read_soul",
            description="Read SOUL.md — Jason's identity, purpose, personality context.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="read_heartbeat",
            description="Read HEARTBEAT.md — current session state, OpenClaw parity, log of recent sessions.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="read_memory",
            description="Read MEMORY.md — curated durable facts and key decisions across all sessions.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="read_daily_log",
            description="Read a specific daily memory log. Defaults to today.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format. Defaults to today.",
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="search_memory",
            description="Keyword/TF-IDF search across all .md memory files. Supports date filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "from_date": {"type": "string", "description": "Filter results from this date (YYYY-MM-DD)"},
                    "to_date": {"type": "string", "description": "Filter results up to this date (YYYY-MM-DD)"},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="append_heartbeat_log",
            description="Append a timestamped entry to the ## Log section of HEARTBEAT.md.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Log entry text (one or more lines)"}
                },
                "required": ["message"],
            },
        ),
        types.Tool(
            name="run_context_pack",
            description="Run context-pack.py to regenerate MEMORY.md from all memory sources.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="list_memory_files",
            description="List all daily memory log files.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    def text(s: str) -> list[types.TextContent]:
        return [types.TextContent(type="text", text=s)]

    if name == "read_soul":
        return text(_read(SOUL))

    if name == "read_heartbeat":
        return text(_read(HEARTBEAT))

    if name == "read_memory":
        return text(_read(MEMORY))

    if name == "read_daily_log":
        date_str = arguments.get("date") or datetime.now().strftime("%Y-%m-%d")
        log_file = MEMORY_DIR / f"{date_str}.md"
        return text(_read(log_file))

    if name == "search_memory":
        query = arguments.get("query", "")
        if not query:
            return text("[error: query is required]")
        out = _search_memory(query, arguments.get("from_date"), arguments.get("to_date"))
        return text(out)

    if name == "append_heartbeat_log":
        message = arguments.get("message", "").strip()
        if not message:
            return text("[error: message is required]")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n### {ts}\n{message}\n"
        hb_text = _read(HEARTBEAT)
        if "## Log" not in hb_text:
            hb_text += "\n## Log\n"
        HEARTBEAT.write_text(hb_text + entry, encoding="utf-8")
        return text(f"[appended to HEARTBEAT.md at {ts}]")

    if name == "run_context_pack":
        out = _run_script(CONTEXT_PACK)
        return text(out)

    if name == "list_memory_files":
        if not MEMORY_DIR.exists():
            return text("[memory/ directory not found]")
        files = sorted(MEMORY_DIR.glob("????-??-??.md"))
        if not files:
            return text("[no daily logs found]")
        listing = "\n".join(f.name for f in files)
        return text(f"Daily memory logs:\n{listing}")

    return text(f"[unknown tool: {name}]")


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
