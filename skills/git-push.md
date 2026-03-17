---
name: git-push
description: >
  Commit and push all changes in the ENGRAM base directory to GitHub. Use this skill
  whenever the user says "push", "commit and push", "push to github", "save to github",
  "sync to git", "ship it", or finishes a build/session and wants to persist their work.
  Also trigger when the user says "we're done" or "wrap up" if there are uncommitted changes.
---

# Git Push — ENGRAM

Commit and push all pending changes to `{{git_remote}}`.

## Working directory
`{{base_dir}}`

## Steps

1. **Check git status** — run `git -C "{{base_dir}}" status --short` to see what changed.
   - If nothing to commit: tell the user, stop here.

2. **Draft a commit message** based on the changed files:
   - Imperative present tense, concise, no period (e.g., `add memory-flush skill`)
   - For multiple unrelated changes: use a broader message

3. **Stage, commit, push** — no confirmation needed:
   ```bash
   cd "{{base_dir}}"
   git add -A
   git commit -m "<message>"
   git push origin main
   ```

4. **Report result** — show the commit hash and push confirmation. One line.

## Safety
- Never force push. Never amend published commits.
- Don't stage files matching: `*.env`, `*token*.txt`, `*secret*`, `*password*` — warn the user if any match.
