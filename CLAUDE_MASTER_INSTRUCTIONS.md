# CLAUDE_MASTER_INSTRUCTIONS.md

# Claude Master Instructions

## Purpose
This is the master instruction file Claude must read first before starting any work in this project.

This file defines the mandatory instruction loading order and the priority rules across all supporting instruction files.

Claude must treat this file as the entry point for project execution.

---

## Mandatory Read Order
Before doing any planning, requirement analysis, coding, refactoring, or execution, Claude must read these files in the following order if they exist:

1. `NON_NEGOTIABLE_DEVELOPMENT_RULES.md`
2. `AI_USAGE_INSTRUCTIONS.md`
3. `EXECPLANE_REQUIREMENT_MANAGEMENT_RULES.md`
4. `EXECPLANE_MEMORY_MANAGEMENT_INSTRUCTIONS.md`
5. `FRONTEND_INSTRUCTIONS.md`
6. `BACKEND_INSTRUCTIONS.md`
7. `CLAUDE.md`

Claude must load and apply all relevant instructions before starting work.

If a file is missing, Claude should continue with the remaining files, but must not ignore the files that do exist.

---

## Priority Order
If instructions conflict, follow this priority order:

1. `NON_NEGOTIABLE_DEVELOPMENT_RULES.md`
2. `EXECPLANE_REQUIREMENT_MANAGEMENT_RULES.md`
3. `EXECPLANE_MEMORY_MANAGEMENT_INSTRUCTIONS.md`
4. `AI_USAGE_INSTRUCTIONS.md`
5. `BACKEND_INSTRUCTIONS.md`
6. `FRONTEND_INSTRUCTIONS.md`
7. `CLAUDE.md`

`CLAUDE.md` is execution memory and working context, but it must not override non-negotiable rules.

---

## Core Operating Rules

### 1. Standard Infra Must Be Reused First
Always use the standard infrastructure from:

`/Users/puneetsharma/Workspace/projects/ai-lab/ai-infra/docker-compose.yml`

Before adding any infrastructure, Claude must first check whether the required service already exists there.
If it exists, reuse it.
If it does not exist, add only the missing service locally.

---

### 2. ExecPlane Is the Requirement System of Record
Use ExecPlane as the primary requirement management and execution tracking system.

ExecPlane endpoint:
`http://localhost:8000/docs`

ExecPlane credentials:
- username: `claude@execplane.local`
- password: `Claude@123`

Claude must:
- fetch requirements based on scope
- break them into smaller requirement units
- create or update stories, tasks, and subtasks
- update status as work progresses
- store execution context, assumptions, blockers, and progress notes
- keep work resumable

Claude must not treat ExecPlane as optional documentation.
It is part of the working workflow.

---

### 3. CLAUDE.md Must Be Maintained
`CLAUDE.md` is the local execution memory file.

Claude must update it continuously with:
- active scope
- requirement mapping
- assumptions
- implementation notes
- files changed
- tests added or updated
- blockers
- next steps
- resume instructions

Before resuming work, Claude must read:
- ExecPlane context
- `CLAUDE.md`

Claude must continue from the latest known point instead of restarting the task from scratch.

---

### 4. TDD Is Mandatory
For implementation work, use test-driven development wherever practical.

Expected flow:
1. understand scope
2. break down work
3. write or update tests first
4. implement minimum code
5. make tests pass
6. refactor safely
7. validate full scope

No implementation should be considered complete without appropriate tests.

---

### 5. Never Commit to Git
Claude must never:
- commit to Git
- push to Git
- create Git commits
- treat Git commit as part of completion

Claude may:
- modify local files
- build Docker images
- push Docker images if required

Git commit and Git push are forbidden.

---

### 6. Dockerization Is Mandatory
Where applicable, the application or service must be runnable in Docker.

Claude must:
- create or maintain Dockerfile support
- make sure Docker image builds successfully
- reuse shared infra when possible
- avoid leaving work in a source-only state when containerization is expected

---

### 7. Model Usage Must Be Intentional
Follow `AI_USAGE_INSTRUCTIONS.md`.

Default model usage:
- Use **Opus** for thinking, planning, architecture, breakdown, and difficult reasoning
- Use **Sonnet** for very complex project execution
- Use local coding models for coding where appropriate

Preferred local coding models:
- Qwen2.5-Coder 14B or 32B
- DeepSeek-Coder V2 Lite
- Gemma 3 27B
- Llama 3.3 70B when supported
- WizardLM-2 7B for simple boilerplate or quick UI adjustments

Use stronger reasoning models for backend-heavy, multi-file, or architecture-sensitive work.
Use lighter models for simple frontend or boilerplate work when sufficient.

---

## Execution Workflow
For every new scope, Claude must follow this sequence:

1. Read this master file
2. Read all supporting instruction files in the required order
3. Read `.env` if relevant
4. Read `CLAUDE.md`
5. Authenticate to ExecPlane
6. Read `EXECPLANE_PROJECT_ID`
7. Fetch or identify the relevant requirement(s)
8. Break work into requirement, story, task, and subtask units
9. Update ExecPlane with structure and status
10. Update `CLAUDE.md` with current context
11. Plan implementation
12. Write or update tests first
13. Implement incrementally
14. Update ExecPlane progress continuously
15. Update `CLAUDE.md` continuously
16. Build Docker image where applicable
17. Mark items completed only after validation
18. Leave resumable notes if work stops before completion

---

## Required Local Configuration
Claude must use local `.env` values where applicable.

Expected minimum ExecPlane config:

```env
EXECPLANE_BASE_URL=http://localhost:8000
EXECPLANE_USERNAME=claude@execplane.local
EXECPLANE_PASSWORD=Claude@123
EXECPLANE_PROJECT_ID=replace_with_project_id
