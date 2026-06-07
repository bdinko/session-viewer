#!/usr/bin/env python3
"""
render_session.py - List and render Claude Code session transcripts in human-readable form.

Claude Code stores each session as a .jsonl file (one JSON object per line) under
    ~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl
where <encoded-cwd> is the project's working directory with every non-alphanumeric
character replaced by '-'.

Usage:
    python render_session.py list [--project <path>]
        List sessions for a project (default: current working directory),
        newest first, numbered, with date + first substantive user message.

    python render_session.py render <id-or-index> [--project <path>]
        Render one session as a readable transcript. <id-or-index> may be the
        list number (1,2,3...), the short 8-char id, or the full uuid.

    python render_session.py path [--project <path>]
        Print the resolved transcript folder for a project.
"""
import sys, os, re, json, argparse
from pathlib import Path
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def projects_root() -> Path:
    return Path.home() / ".claude" / "projects"


def encode_cwd(p: str) -> str:
    # Claude Code encodes the project path by replacing every non-alphanumeric char with '-'
    return re.sub(r"[^A-Za-z0-9]", "-", str(p))


def resolve_project_dir(project: str | None) -> Path:
    cwd = project or os.getcwd()
    root = projects_root()
    encoded = encode_cwd(cwd)
    candidate = root / encoded
    if candidate.is_dir():
        return candidate
    # Fallback: fuzzy-match on the basename of the path
    base = encode_cwd(Path(cwd).name).lower()
    matches = [d for d in root.iterdir() if d.is_dir() and base in d.name.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        # Prefer the longest matching encoded name (most specific)
        matches.sort(key=lambda d: len(d.name), reverse=True)
        return matches[0]
    return candidate  # return non-existent path; caller reports a clean error


def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


def _tool_calls(content):
    out = []
    if isinstance(content, list):
        for b in content:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                inp = b.get("input", {}) or {}
                key = (
                    inp.get("description")
                    or inp.get("command")
                    or inp.get("file_path")
                    or inp.get("pattern")
                    or inp.get("query")
                    or inp.get("prompt")
                    or inp.get("skill")
                    or ""
                )
                out.append((b.get("name", ""), " ".join(str(key).split())[:100]))
    return out


def _is_noise(t: str) -> bool:
    if not t:
        return True
    if t.startswith("<"):
        return True
    for marker in ("command-name", "command-message", "local-command-stdout", "tool_result"):
        if marker in t:
            return True
    return False


def iter_records(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def first_timestamp(path: Path) -> str:
    for o in iter_records(path):
        ts = o.get("timestamp")
        if ts:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
            except Exception:
                return ts[:16]
    # Fallback to file mtime
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


def first_substantive(path: Path) -> str:
    for o in iter_records(path):
        if o.get("type") != "user":
            continue
        t = " ".join(_text(o.get("message", {}).get("content")).split())
        if not _is_noise(t) and len(t) > 25:
            return t[:120]
    # fall back to any user line
    for o in iter_records(path):
        if o.get("type") == "user":
            t = " ".join(_text(o.get("message", {}).get("content")).split())
            if t and not t.startswith("<"):
                return t[:120]
    return "(no readable user message)"


def list_sessions(proj: Path):
    if not proj.is_dir():
        print(f"No transcript folder found at:\n  {proj}\n"
              f"(Has Claude Code ever run in this project?)")
        return []
    files = sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print(f"No .jsonl sessions in {proj}")
        return []
    print(f"Sessions in {proj.name}  ({len(files)} total)\n")
    rows = []
    for i, f in enumerate(files, 1):
        ts = first_timestamp(f)
        size = f.stat().st_size
        size_s = f"{size/1024:.0f} KB" if size < 1024 * 1024 else f"{size/1024/1024:.1f} MB"
        msg = first_substantive(f)
        rows.append((i, f, ts, size_s, msg))
        print(f"  {i:>2}. {ts}  {size_s:>8}  {f.name[:8]}  {msg}")
    return rows


def find_session(proj: Path, ref: str) -> Path | None:
    files = sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if ref.isdigit():
        idx = int(ref)
        if 1 <= idx <= len(files):
            return files[idx - 1]
        return None
    ref = ref.lower()
    for f in files:
        if f.stem.lower() == ref or f.stem.lower().startswith(ref):
            return f
    return None


def render(path: Path):
    print(f"### Transcript: {path.name}\n")
    for o in iter_records(path):
        ty = o.get("type")
        content = o.get("message", {}).get("content")
        if ty == "user":
            t = " ".join(_text(content).split())
            if _is_noise(t):
                continue
            print("\n===== USER =====")
            print(t)
        elif ty == "assistant":
            t = " ".join(_text(content).split())
            calls = _tool_calls(content)
            if t:
                print("\n-- CLAUDE --")
                print(t)
            for name, key in calls:
                print(f"    -> [{name}] {key}")


def resume_cmd(proj: Path, ref: str):
    f = find_session(proj, ref)
    if not f:
        print(f"No session matching '{ref}' in {proj}. Run 'list' to see options.")
        sys.exit(1)
    uuid = f.stem
    print(f"# Resume this session by running:")
    print(f"claude --resume {uuid}")


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("mode", choices=["list", "render", "path", "resume"])
    ap.add_argument("ref", nargs="?", help="session index, short id, or uuid (render/resume mode)")
    ap.add_argument("--project", help="project path (default: cwd)")
    args = ap.parse_args()

    proj = resolve_project_dir(args.project)

    if args.mode == "path":
        print(proj)
        return
    if args.mode == "list":
        list_sessions(proj)
        return
    if args.mode == "render":
        if not args.ref:
            print("render needs a session reference (index, short id, or uuid). Run 'list' first.")
            sys.exit(2)
        f = find_session(proj, args.ref)
        if not f:
            print(f"No session matching '{args.ref}' in {proj}. Run 'list' to see options.")
            sys.exit(1)
        render(f)
        return
    if args.mode == "resume":
        if not args.ref:
            print("resume needs a session reference (index, short id, or uuid). Run 'list' first.")
            sys.exit(2)
        resume_cmd(proj, args.ref)


if __name__ == "__main__":
    main()
