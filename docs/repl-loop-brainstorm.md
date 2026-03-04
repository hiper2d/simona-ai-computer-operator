# REPL Loop Brainstorm

## Concept

Split Simona into two roles:
- **Controller** (main Claude Code session) — Alex interacts here, creates tasks, adds automations, does manual work
- **Worker** (autonomous Claude Code session) — picks up tasks, executes them in a loop, generates its own tasks when the queue is empty

## Approach Options

### Option 1: Claude Code subprocess via `claude` CLI (Recommended starting point)
Spawn `claude` CLI in headless mode with a prompt per task. Loop wrapper (shell script or Python) manages the cycle: pick task → run claude → mark done → repeat. All tools, skills, and MCP servers come for free.

### Option 2: Claude API + custom agent loop
Python script calling Claude API directly. More control over context and tool dispatch, but requires reimplementing all tool calling (file editing, bash, etc.). Heavy plumbing cost.

### Option 3: Claude Code with a "daemon" skill
A skill that loops internally — check queue, pick task, execute, repeat. Simpler than a separate process but loses controller/worker separation.

## Open Design Questions

### Task Queue
Where do tasks live?
- Markdown file — simple, fragile
- JSON or SQLite — structured, queryable
- GitHub Issues — built-in UI, but slower

### Autonomous Task Generation
When the queue is empty, the worker needs enough context to generate meaningful work:
- Access to SOUL.md, MEMORY.md, project goals
- A "current objectives" doc that defines what Simona should be working toward
- Without this, it'll just invent busywork

### Guardrails
Autonomous loop with bash access and no human = horror movie. Needs:
- Boundaries on what the worker can do without approval
- Maybe a "safe mode" for unsupervised work (no destructive git ops, no external API calls)
- Logging everything for controller review

### Communication Between Controller and Worker
- Shared files (task queue, logs)
- Git commits as audit trail
- Message queue (overkill for now)

## Decision

Start with Option 1. Keep it dumb and simple. Iterate once we have real tasks flowing through it.

## Status

**Parked** — training more skills first, then revisiting.
