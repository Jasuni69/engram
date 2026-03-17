---
name: new-project
description: >
  Scaffold a new project under the ENGRAM projects directory. Use this skill whenever
  the user says "new project", "scaffold project", "start project", "create project",
  "spin up a project", or names a project they want to begin building.
---

# New Project

Scaffold a new project under `{{base_dir}}/projects/`.

## Steps

1. **Get the project name** from the user's message. Slugify it (lowercase, hyphens).

2. **Create the directory**: `{{base_dir}}/projects/<project-name>/`

3. **Scaffold based on type**:
   - Python: `__init__.py`, `README.md`, `requirements.txt`
   - Node/TS: `package.json`, `tsconfig.json`, `src/index.ts`, `README.md`
   - General: `README.md` only

4. **Write a minimal README.md** with project name and one-line description.

5. **Report**: tell the user what was created. One line.

## Notes
- Don't over-scaffold. Minimum viable structure only.
- Ask if type is ambiguous.
