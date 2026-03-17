#!/usr/bin/env python3
"""
memory-indexer.py — Keyword/TF-IDF search over all .md files.
No external dependencies (stdlib only). Uses TF-IDF scoring for ranking.
Usage:
  python memory-indexer.py "semantic search"
  python memory-indexer.py "query" --from 2026-03-01
  python memory-indexer.py "query" --to 2026-03-15
  python memory-indexer.py --list          # list all indexed files
  python memory-indexer.py --rebuild       # force rebuild index
"""
import json
import math
import re
import sys
from datetime import date as Date
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
INDEX_FILE = BASE / "memory" / ".index.json"
MD_ROOTS = [BASE / "memory", BASE, BASE / "core"]
TOP_K = 10


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_\-]{2,}", text.lower())


def collect_docs() -> dict[str, str]:
    """Return {rel_path: content} for all .md files under MD_ROOTS."""
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


def build_index(docs: dict[str, str]) -> dict:
    """Build inverted TF-IDF index."""
    tf: dict[str, dict[str, float]] = {}   # term -> {doc -> tf}
    df: dict[str, int] = defaultdict(int)  # term -> doc_count
    doc_tokens: dict[str, list[str]] = {}

    for doc_id, text in docs.items():
        tokens = tokenize(text)
        if not tokens:
            continue
        freq: dict[str, int] = defaultdict(int)
        for t in tokens:
            freq[t] += 1
        doc_tokens[doc_id] = list(freq.keys())
        total = len(tokens)
        tf[doc_id] = {t: count / total for t, count in freq.items()}
        for t in freq:
            df[t] += 1

    N = len(docs)
    idf = {t: math.log((N + 1) / (count + 1)) + 1 for t, count in df.items()}

    # inverted index: term -> [(doc_id, tfidf_score)]
    inverted: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for doc_id, term_tf in tf.items():
        for term, score in term_tf.items():
            inverted[term].append((doc_id, score * idf.get(term, 1.0)))

    return {
        "inverted": {t: v for t, v in inverted.items()},
        "idf": idf,
        "docs": list(docs.keys()),
        "built": __import__("datetime").datetime.now().isoformat(),
    }


def doc_date(doc_id: str) -> Date | None:
    """Extract date from filename like memory/2026-03-16.md, else None."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", Path(doc_id).stem)
    if m:
        try:
            return Date.fromisoformat(m.group(1))
        except ValueError:
            pass
    return None


def is_index_stale(docs: dict[str, str]) -> bool:
    """Return True if any .md file is newer than the saved index."""
    if not INDEX_FILE.exists():
        return True
    index_mtime = INDEX_FILE.stat().st_mtime
    for root in MD_ROOTS:
        if not root.exists():
            continue
        pattern = "*.md" if root == BASE else "**/*.md"
        for p in root.glob(pattern):
            if p.name.startswith("."):
                continue
            if p.stat().st_mtime > index_mtime:
                return True
    return False


def load_index() -> dict | None:
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return None


def save_index(index: dict) -> None:
    INDEX_FILE.parent.mkdir(exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")


def extract_snippet(text: str, terms: list[str]) -> str:
    """Return section header + matching bullet/line, up to 200 chars."""
    lines = text.splitlines()
    current_section = ""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            current_section = stripped
        if any(t in line.lower() for t in terms):
            # grab up to 3 lines of context from the match
            context = " ".join(l.strip() for l in lines[i:i+3] if l.strip())
            prefix = f"{current_section} > " if current_section else ""
            return (prefix + context)[:200]
    return ""


def search(
    query: str,
    index: dict,
    docs: dict[str, str],
    from_date: Date | None = None,
    to_date: Date | None = None,
) -> list[tuple[str, float, str]]:
    """Return [(doc_id, score, snippet)] sorted by score desc."""
    terms = tokenize(query)
    scores: dict[str, float] = defaultdict(float)
    inverted = index["inverted"]
    for term in terms:
        if term in inverted:
            for doc_id, score in inverted[term]:
                scores[doc_id] += score

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    results = []
    for doc_id, score in ranked:
        d = doc_date(doc_id)
        if from_date and d and d < from_date:
            continue
        if to_date and d and d > to_date:
            continue
        text = docs.get(doc_id, "")
        snippet = extract_snippet(text, terms)
        results.append((doc_id, score, snippet))
        if len(results) >= TOP_K:
            break
    return results


def main() -> None:
    args = sys.argv[1:]

    if "--list" in args:
        docs = collect_docs()
        for p in sorted(docs.keys()):
            print(p)
        print(f"\n{len(docs)} files indexed.")
        return

    rebuild = "--rebuild" in args
    query_args = [a for a in args if not a.startswith("--") and not re.match(r"\d{4}-\d{2}-\d{2}", a)]

    # Parse --from / --to date filters
    from_date: Date | None = None
    to_date: Date | None = None
    for i, a in enumerate(args):
        if a == "--from" and i + 1 < len(args):
            try:
                from_date = Date.fromisoformat(args[i + 1])
            except ValueError:
                pass
        if a == "--to" and i + 1 < len(args):
            try:
                to_date = Date.fromisoformat(args[i + 1])
            except ValueError:
                pass

    if not query_args and not rebuild:
        print("Usage: python memory-indexer.py <query> [--rebuild] [--list] [--from YYYY-MM-DD] [--to YYYY-MM-DD]")
        sys.exit(1)

    docs = collect_docs()
    index = None if rebuild else (None if is_index_stale(docs) else load_index())

    if index is None:
        print(f"[indexer] Building index over {len(docs)} docs...")
        index = build_index(docs)
        save_index(index)

    if not query_args:
        return

    query = " ".join(query_args)
    results = search(query, index, docs, from_date=from_date, to_date=to_date)

    if not results:
        print(f"No results for: {query!r}")
        return

    print(f"Results for: {query!r}\n")
    for i, (doc_id, score, snippet) in enumerate(results, 1):
        print(f"  {i}. [{score:.3f}] {doc_id}")
        if snippet:
            safe = snippet.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8")
            print(f"     > {safe}")
    print()


if __name__ == "__main__":
    main()
