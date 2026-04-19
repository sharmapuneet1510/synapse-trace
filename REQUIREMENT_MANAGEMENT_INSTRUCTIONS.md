# EXECPLANE_REQUIREMENT_MANAGEMENT_RULES.md

# ExecPlane Requirement Management Rules

## Objective
Use ExecPlane as the primary and only requirement management system for planning, decomposition, execution tracking, status updates, and work resumption.

ExecPlane endpoint:
`http://localhost:8000/docs`

ExecPlane credentials:
- User: `claude@execplane.local`
- Password: `Claude@123`

ExecPlane is the in-house Jira alternative and the system of record for requirement and execution tracking.

In addition to ExecPlane, Claude must maintain a local execution context file named:

`CLAUDE.md`

This file is used to preserve detailed working context so that execution can be resumed without repeating analysis or restarting from scratch.

---

## Core Rule
For every scope, Claude must do all of the following:
1. fetch or identify the relevant requirement set from ExecPlane
2. analyze the scope
3. break the work into small requirement units
4. update requirement, story, and task records with execution context
5. store assumptions, progress, decisions, and implementation notes in ExecPlane
6. mirror important execution state in `CLAUDE.md`
7. keep both systems current enough that work can resume from the latest point

Claude must not rely only on memory or chat history for continuation.

---

## System of Record Rule
ExecPlane is the main system of record for:
- requirements
- stories
- tasks
- subtasks
- status
- assumptions
- implementation context
- execution notes
- progress tracking
- blockers
- completion notes

`CLAUDE.md` is the local execution memory and resume log for the repository or workspace.

Both must be maintained together.

---

## Resume-Without-Restart Rule
Claude must always work in a resumable way.

That means it must leave behind enough detail so that on the next run it can:
- understand what was already analyzed
- know what assumptions were made
- know what was implemented
- know what remains
- know which files were touched
- know what tests were added
- know what blockers exist
- know what the next action should be

Claude must avoid redoing work from the start when the context already exists in ExecPlane or `CLAUDE.md`.

Before starting new work, Claude should first read:
1. relevant requirement/story/task details from ExecPlane
2. the local `CLAUDE.md`

Then continue from the latest known state.

---

## Requirement Breakdown Rule
For every scope, Claude must break work down progressively.

Expected hierarchy:
- Requirement
- Story
- Task
- Subtask if needed

Each item should be small, actionable, and traceable.

Claude must not leave large work items vague or oversized.

---

## Mandatory Context Update Rule
Whenever Claude works on a requirement, story, or task, it must update that item with useful context.

At a minimum, the item should contain or be updated with:
- business context
- technical context
- current assumptions
- implementation approach
- important design decisions
- dependencies
- blockers
- current progress
- remaining work
- completion notes when done

This is mandatory because future continuation should not depend on rediscovery.

---

## Status Management Rule
Claude must update requirement state as work progresses.

Minimum lifecycle:
- Pending or To Do
- In Progress
- Completed

### Move to In Progress when:
- the item has actually been started
- active analysis or implementation is underway

### Move to Completed when:
- implementation is done
- validation is done
- the item is genuinely complete for the current scope

### Do not mark Completed when:
- work is partial
- tests are pending
- implementation is blocked
- context is incomplete
- validation has not happened

---

## Detailed Work Logging Rule
Claude must store detailed execution notes, not just status changes.

The logged detail should include:
- what was done
- why it was done
- what assumptions were made
- which alternatives were considered if relevant
- what files were created or modified
- what tests were added or updated
- what infrastructure was reused
- what infrastructure was added locally
- what remains to be done
- how to continue from the current point

This detail should be added to ExecPlane task/story context where appropriate and also summarized in `CLAUDE.md`.

---

## CLAUDE.md Rule
Claude must maintain a local file named:

`CLAUDE.md`

This file acts as the local working journal and continuation context.

It must be updated during execution, especially when:
- a new scope is started
- a breakdown is created
- implementation begins
- a major assumption is made
- an important design choice is made
- files are modified
- tests are added
- blockers are found
- work stops before full completion
- work is completed

---

## What CLAUDE.md Must Contain
`CLAUDE.md` should contain enough detail to resume work safely.

Suggested structure:

### 1. Active Scope
- current requirement or feature being worked on
- linked requirement/story/task identifiers

### 2. Objective
- short summary of the goal

### 3. Requirement Breakdown
- requirement
- stories
- tasks
- subtasks

### 4. Current Status
- what is done
- what is in progress
- what is pending

### 5. Assumptions
- business assumptions
- technical assumptions
- temporary assumptions needing confirmation

### 6. Design / Implementation Decisions
- major approach chosen
- rejected alternatives if important
- architecture or UI decisions

### 7. Files Changed
- created files
- updated files
- deleted files if any

### 8. Tests
- tests added
- tests updated
- test status
- gaps remaining

### 9. Infra / Runtime Notes
- infra reused
- infra added
- environment or compose notes
- image build notes

### 10. Blockers / Risks
- current blockers
- open questions
- dependencies

### 11. Next Steps
- precise next actions to continue execution

### 12. Resume Instructions
- where to restart from
- what should not be redone
- what is already validated

---

## Read-Before-Continue Rule
Before resuming any unfinished scope, Claude must:
1. read the relevant ExecPlane requirement/story/task context
2. read `CLAUDE.md`
3. determine the latest completed point
4. continue from there

Claude must not re-plan the full task from scratch unless the saved context is missing or clearly outdated.

---

## Assumption Logging Rule
Every meaningful assumption must be recorded.

This includes:
- inferred requirement intent
- UI behavior assumptions
- backend contract assumptions
- infra assumptions
- temporary implementation assumptions
- test assumptions

Assumptions must be stored in:
- ExecPlane task or story context
- `CLAUDE.md`

This ensures continuation remains grounded.

---

## Execution Notes Rule
Claude must treat execution notes as part of the deliverable.

Execution notes should make it possible to answer:
- what has already been done
- why it was done that way
- what remains
- where to continue
- which risks still exist

A task with only a status and no meaningful notes is incomplete from a tracking perspective.

---

## Task and Story Update Rule
As Claude works, it must update the relevant task or story in ExecPlane with:
- latest execution summary
- current status
- implementation notes
- blockers
- assumptions
- next step

This must happen incrementally, not only at the end.

ExecPlane should always reflect near-current progress.

---

## Project Context Rule
Claude must use local `.env` for project-aware operations.

Required variables:

```env
EXECPLANE_BASE_URL=http://localhost:8000
EXECPLANE_USERNAME=claude@execplane.local
EXECPLANE_PASSWORD=Claude@123
EXECPLANE_PROJECT_ID=replace_with_project_id
