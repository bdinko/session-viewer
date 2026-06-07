---
name: session-viewer
description: List and render previous Claude Code session transcripts in human-readable form. Use when the user wants to preview, view, render, read, or browse a past session/conversation, inspect a session .jsonl file, or "see what we did last session" in any project. Triggers on '/session-viewer', 'render a session', 'preview previous session', 'show me a past session', 'view session transcript', 'read the jsonl'.
---

# Session Viewer

Renders Claude Code's raw session transcripts (`.jsonl`, one JSON object per line)
into a clean, readable conversation so the developer can review what happened in a
past session without resuming it.

Sessions live at `~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl`, where
`<encoded-cwd>` is the project's working directory with every non-alphanumeric
character replaced by `-` (e.g. `D:\CarpioC11-1-810\C11MPCoord` →
`D--CarpioC11-1-810-C11MPCoord`). The bundled `render_session.py` resolves this
automatically from the current working directory.

## Workflow

The helper script is at `render_session.py` next to this file. Always invoke it with
an absolute path so it works regardless of cwd. On Windows use the `python` launcher;
fall back to `py` if `python` is not found.

### 1. List sessions (default first step)

When the user asks to see past sessions, run:

```
python "<skills-dir>/session-viewer/render_session.py" list
```

This prints all sessions for the **current project** (newest first), numbered, each with
its date, size, short id, and first substantive user message. Show this list to the user
and ask which one to render (by number or short id) — unless they already named one.

To target a different project, pass `--project "<path>"`.

### 2. Render the chosen session

```
python "<skills-dir>/session-viewer/render_session.py" render <number-or-id>
```

`<number-or-id>` accepts the list number (`1`, `2`, ...), the short 8-char id, or the
full uuid. The output uses `===== USER =====` for the developer's messages, `-- CLAUDE --`
for assistant replies, and indented `-> [Tool] key-arg` lines for each tool call.

Relay the rendered transcript to the user. For very long sessions, offer a short summary
of the key decisions/outcomes in addition to (or instead of) the full dump.

### 3. Resume a session by list number (no UUID memorizing)

When the user wants to **resume** a past session without hunting for its UUID in the
`/resume` picker (where mis-selection is easy), run:

```
python "<skills-dir>/session-viewer/render_session.py" resume <number-or-id>
```

This resolves the list number / short id to the full UUID and prints the exact
`claude --resume <full-uuid>` command. Relay that command to the user — they run it
themselves (e.g. `! claude --resume <uuid>` in the IDE terminal). The agent cannot
switch the active conversation itself; resuming is always a client action.

### 4. Resolve the transcript folder (utility)

```
python "<skills-dir>/session-viewer/render_session.py" path
```

Prints the resolved `~/.claude/projects/...` folder for the current (or `--project`)
directory — handy when the user wants to open the raw `.jsonl` files themselves.

## Notes

- The script is read-only — it never modifies session files.
- Greetings and system/command noise are filtered out so the transcript reads cleanly.
- If no transcript folder is found, it reports that Claude Code may never have run in
  that project (or suggests `--project`). It also fuzzy-matches on the folder basename
  if the exact encoded path isn't present.
- Output is UTF-8; encoding-sensitive content (e.g. Croatian diacritics) renders correctly.
