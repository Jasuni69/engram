---
name: bootstrap
description: >
  First-run ENGRAM setup. Asks the user questions, populates SOUL.md, HEARTBEAT.md,
  MEMORY.md, claude_memory.json, and CLAUDE.md with their answers. Installs MCP
  dependencies, copies skills to ~/.claude/commands/, and patches claude_desktop_config.json.
  Deletes BOOTSTRAP.md on success. Run once to activate ENGRAM.
---

# ENGRAM Bootstrap

You are setting up ENGRAM for a new user. This runs once. Follow all steps in order.

## Step 0 — Pre-flight check

1. Detect the current working directory. This is `BASE_DIR` — where ENGRAM is installed.
2. Detect OS via Bash: `uname -s` (Linux/Mac = Unix, else = Windows)
3. Detect Python: try `python3 --version`, fallback `python --version`. Record the executable name.
4. Check if `core/SOUL.md` already exists AND contains a non-template name (no `{{name}}`).
   - If yes: tell the user "ENGRAM is already set up. Delete core/SOUL.md to re-run bootstrap." Stop.

## Step 1 — Ask the user questions

Use AskUserQuestion to collect (ask all at once, max 4 per call):

**Round 1:**
- "What's your full name?" (header: "Your name")
- "Company or organization?" (header: "Company")
- "City / country?" (header: "Location")
- "What's your role and what do you work on? (e.g. 'backend engineer — Python, Postgres')" (header: "Role & tools")

**Round 2:**
- "Todoist API token? (skip to disable Todoist integration)" (header: "Todoist")
  Options: "I have one — I'll paste it", "Skip — no Todoist"
- "Git remote for this ENGRAM repo? (e.g. https://github.com/you/engram.git)" (header: "Git remote")
  Options: "I'll provide it", "Skip — no git remote"
- [Windows only] "Register a daily heartbeat task in Windows Task Scheduler?" (header: "Heartbeat")
  Options: "Yes — run at 08:00 daily", "No thanks"

After getting answers, ask for the actual token/remote values if the user said they have them:
- If Todoist: "Paste your Todoist API token:"
- If git remote: "Paste the git remote URL:"

## Step 2 — Populate templates

Load and fill each template from the `templates/` directory.

Substitutions to apply (replace every `{{placeholder}}`):
- `{{name}}` → user's name
- `{{company}}` → company
- `{{location}}` → location
- `{{role}}` → role/tools answer
- `{{tools}}` → role/tools answer (same)
- `{{os}}` → detected OS
- `{{python_path}}` → detected Python executable path
- `{{base_dir}}` → BASE_DIR (absolute path, forward slashes)
- `{{date}}` → today's date (YYYY-MM-DD, from `date +%Y-%m-%d`)
- `{{journal_file}}` → `YYYY-MM.md` (current year-month)
- `{{todoist_project_line}}` → if Todoist enabled: `- **Todoist MCP** — task management` else `""`
- `{{todoist_status_line}}` → if Todoist enabled: `- ✅ Todoist MCP server (5 tools)` else `- ⬜ Todoist MCP — not configured`
- `{{git_remote_line}}` → if remote provided: `- Remote repo: {{git_remote}} — push completed work there` else `""`

Write the filled templates to:
- `templates/SOUL_TEMPLATE.md` → `core/SOUL.md`
- `templates/HEARTBEAT_TEMPLATE.md` → `core/HEARTBEAT.md`
- `templates/claude_memory_template.json` → `core/claude_memory.json`

Create empty files:
- `MEMORY.md` with content: `# MEMORY.md\n\n*Run context-pack.py to populate.*\n`
- `TASKS.md` with content: `# Tasks\n\n<!-- Add tasks here -->\n`

## Step 3 — Write CLAUDE.md

Fill `templates/CLAUDE_TEMPLATE.md` and write to `~/.claude/CLAUDE.md`.

**Important:** Check if `~/.claude/CLAUDE.md` exists first.
- If it exists: append a note at the bottom:
  ```
  <!-- ENGRAM appended below -->
  ```
  Then append the filled template content.
- If it doesn't exist: write the filled template as the full file.

## Step 4 — Install MCP dependencies

**memory-mcp:**
```bash
pip install mcp
```
(or `pip3 install mcp` — use whichever Python was detected)

**mcp-todoist (only if Todoist token was provided):**
```bash
cd "{BASE_DIR}/projects/mcp-todoist"
npm install
npm run build
```

If npm is not available, print a warning and continue — the user can run this manually.

## Step 5 — Copy skills to ~/.claude/commands/

For each file in `skills/` (except `bootstrap.md`):
1. Read the file
2. Replace all `{{base_dir}}` with BASE_DIR
3. Replace all `{{git_remote}}` with the git remote (if provided, else leave placeholder)
4. Write to `~/.claude/commands/{filename}`

## Step 6 — Patch claude_desktop_config.json

Locate the config file:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

If the file exists, read it and add/merge under `mcpServers`:
```json
"memory": {
  "command": "{python_path}",
  "args": ["{BASE_DIR}/projects/memory-mcp/server.py"]
}
```

If Todoist token was provided, also add:
```json
"todoist": {
  "command": "node",
  "args": ["{BASE_DIR}/projects/mcp-todoist/dist/index.js"],
  "env": {
    "TODOIST_API_TOKEN": "{todoist_token}"
  }
}
```

If the config file doesn't exist, create it with the full structure.

Write the patched JSON back to the file.

## Step 7 — Register heartbeat task (Windows only, if requested)

Run via Bash:
```powershell
$Action = New-ScheduledTaskAction -Execute "claude" -Argument "--dangerously-skip-permissions -p @\"{BASE_DIR}/core/HEARTBEAT.md\" --output-format stream-json" -WorkingDirectory "{BASE_DIR}"
$Trigger = New-ScheduledTaskTrigger -Daily -At "08:00"
$Settings = New-ScheduledTaskSettingsSet -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
Register-ScheduledTask -TaskName "ENGRAMHeartbeat" -Action $Action -Trigger $Trigger -Settings $Settings -Force
```

If this fails, print instructions for manual setup and continue.

## Step 8 — Initialize git (if remote was provided)

If not already a git repo:
```bash
cd "{BASE_DIR}"
git init
git add -A
git commit -m "initial ENGRAM setup"
git remote add origin {git_remote}
git push -u origin main
```

If already a git repo, just commit the new files:
```bash
cd "{BASE_DIR}"
git add -A
git commit -m "bootstrap: initialize ENGRAM for {name}"
```

## Step 9 — Self-destruct BOOTSTRAP.md

Delete `{BASE_DIR}/BOOTSTRAP.md` (this file contains the original design doc, not needed post-setup):
```bash
rm "{BASE_DIR}/BOOTSTRAP.md"
```

## Step 10 — Done

Print a success summary:
```
╔══════════════════════════════════════════════╗
║           ENGRAM is live.                    ║
╠══════════════════════════════════════════════╣
║  SOUL.md       → core/SOUL.md               ║
║  HEARTBEAT.md  → core/HEARTBEAT.md          ║
║  memory-mcp    → registered in Claude       ║
║  skills        → ~/.claude/commands/        ║
╚══════════════════════════════════════════════╝

Restart Claude Desktop to activate MCP servers.
Your first session starts with a clean memory slate.
Welcome to ENGRAM, {name}.
```

## Error handling

- If any step fails non-fatally (e.g. npm not found, Task Scheduler error): print a warning and continue.
- If a critical step fails (can't write SOUL.md, can't find templates): stop and report clearly.
- Never delete BOOTSTRAP.md unless Step 2–8 all succeeded.
