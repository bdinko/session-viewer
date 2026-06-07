# Proposal: bundle `session-viewer` with the ClarionAssistant plugin

**To:** ClarionAssistant maintainer (John Hickey)
**From:** Dinko Bačun
**Status:** Suggestion — your call on whether it fits the bundle

---

## TL;DR

`session-viewer` is a small, **read-only** Claude Code skill that lists and renders
**previous session transcripts** (`~/.claude/projects/**/*.jsonl`) as clean, readable
conversations, and turns a list number into the exact `claude --resume <uuid>` command
so users never have to memorize a session UUID or risk a mis-click in the `/resume` picker.

It's a self-contained skill folder (`SKILL.md` + one Python script + `README.md`). Dropping
it into the plugin is **one `Source:` line** in the installer plus a README row.

## Honest fit caveat (read this first)

This skill is **not Clarion-specific** — it has no MCP tools, no Clarion language code, and
works in any Claude Code project regardless of language. So it doesn't belong in the
"Clarion development skills" category the way `clarion-convert-driver` or `clarioncom-build` do.

The case for bundling it anyway: **every** Clarion dev who installs ClarionAssistant is
working inside Claude Code in the IDE, and reviewing/resuming past sessions is a daily pain
point the picker handles poorly. It's a *general developer-productivity* convenience that
complements the Clarion toolset rather than extending it.

Your call: include it as a general-purpose extra (and maybe reword the README count from
"22 Clarion-specific skills" to "22 Clarion skills + general productivity skills"), or keep
the bundle pure and let this live as a standalone skill. Either is reasonable.

---

## What it does

| User says | Result |
|---|---|
| *"list sessions"* / `/session-viewer` | Numbered list (newest first) for the current project: date, size, short id, first real message |
| *"render 4"* | Session #4 printed as a readable transcript (USER / CLAUDE / tool-call lines) |
| *"resume 4"* | Resolves #4 to its full UUID → prints the exact `claude --resume <uuid>` command |
| *"where are the session files?"* | Prints the raw `~/.claude/projects/...` folder |

- **Read-only** — never modifies session files.
- UTF-8 output (renders accented content correctly).
- Requires Python 3 on `PATH` (already a dependency-light assumption; the skill degrades
  with a clear message if Python is absent).

## Files in this skill

```
session-viewer/
  SKILL.md            # skill definition (triggers + workflow)
  render_session.py   # the list/render/resume/path engine (read-only)
  README.md           # human usage guide
```

---

## Integration steps (for the maintainer)

These mirror exactly how the other 22 skills are wired. Nothing here touches the
ClarionAssistant *repo* source — the skills are staged from your local plugin marketplace
folder (`#SrcPlugin`), so the steps are: drop the folder, add one installer line, bump the
README.

### 1. Stage the skill folder

Copy the `session-viewer/` folder into your plugin source:

```
%SrcPlugin%\skills\session-viewer\
```
i.e. `…\.claude\plugins\marketplaces\clarionassistant-marketplace\plugins\clarion-assistant\skills\session-viewer\`

(Claude Code auto-discovers any folder containing a `SKILL.md` under `skills\`, so no
plugin manifest edit is needed unless your plugin keeps a hand-maintained skill list —
if it does, add a `session-viewer` entry there too.)

### 2. Add one line to `installer\ClarionAssistant.iss`

Immediately **after** the last skill line (`…\skills\lsp-diagnostics\*`, just before the
`; Plugin Hooks` comment), add:

```iss
Source: "{#SrcPlugin}\skills\session-viewer\*"; DestDir: "{%USERPROFILE}\.claude\plugins\marketplaces\clarionassistant-marketplace\plugins\clarion-assistant\skills\session-viewer"; Components: plugin\skills; Flags: ignoreversion recursesubdirs createallsubdirs
```

### 3. Update `README.md`

- Line ~207: `**22 Clarion development skills**` → `**23 Claude Code skills**`
  (or `22 Clarion skills + 1 general productivity skill`, whichever framing you prefer)
- Line ~497: `The installer includes 22 Clarion-specific skills…` → adjust count/wording
- Add a row to the skills table (after `clarioncom-webview2-validate`):

```md
| `session-viewer` | List, render, and resume previous Claude Code session transcripts (general productivity) |
```

### 4. (Optional) Python note

If your install docs enumerate runtime prerequisites, note that `session-viewer` uses
Python 3 (`python`/`py`). It's read-only and fails gracefully with a message if Python
isn't present, so it won't break installs that lack it.

---

## How to get it

Public repo: **https://github.com/bdinko/session-viewer**

```bash
git clone https://github.com/bdinko/session-viewer.git
```

The folder is self-contained — copy `SKILL.md`, `render_session.py`, and `README.md`
into your plugin's `skills\session-viewer\` as-is (the `contrib/` folder is just this
proposal and can be ignored when bundling).
