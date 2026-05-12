---
name: memory-review
description: Review and compact Simona's memory. Walks every file in .claude/memory/, evaluates each entry for staleness, duplication, and merge opportunities, then proposes prunes/merges for Alex to approve before deleting anything. Use when MEMORY.md feels bloated or monthly as hygiene.
argument-hint: [--dry-run]
allowed-tools: Bash, Read, Edit, Glob, Grep
---

Review memory: $ARGUMENTS

## Principle

**Nothing gets deleted without Alex's explicit OK.** This skill *proposes*. Alex *approves*. No silent edits.

## What's in scope

- `.claude/memory/MEMORY.md` — the index + inline sections (Project Notes, Key Learnings, Feedback, Personal, Active Conversations, Session Log)
- `.claude/memory/*.md` — topic files linked from MEMORY.md
- `.claude/memory/conversations/*.md` — active conversation pickup points

## What's out of scope (never touch)

- `SOUL.md` — personality. Manual edits only.
- `CLAUDE.md` — project instructions. Manual edits only.
- `.claude/skills/**` — skill files. They have their own update cadence.
- `WORKLOG.md` files inside `video-projects/` — append-only project history.

## Special rule: Session Log

The `## Session Log` section at the bottom of `MEMORY.md` is **append-only history**. Do NOT propose deleting individual entries. You *may* propose compacting old entries (>90 days) into a one-line summary if the section is getting unwieldy. Default: leave it alone.

## Steps

### 1. Inventory

List every file in scope with size and last-modified date:

```bash
echo "=== Memory files ==="
ls -lh /Users/hiper2d/projects/simona-ai-computer-operator/.claude/memory/*.md
echo ""
echo "=== Conversations ==="
ls -lh /Users/hiper2d/projects/simona-ai-computer-operator/.claude/memory/conversations/*.md 2>/dev/null || echo "(none)"
echo ""
echo "=== MEMORY.md line count ==="
wc -l /Users/hiper2d/projects/simona-ai-computer-operator/.claude/memory/MEMORY.md
```

Flag if MEMORY.md is over 150 lines (target: under 200, ideal: under 150).

### 2. Read everything

Read every file in scope. Build a mental map of what each entry claims.

### 3. Evaluate each entry

For each bullet/section, classify:

**STILL TRUE?** — If the entry mentions a specific path, file, command, or technical claim, verify it.
- Path exists? `ls`
- Command works? Check the actual file/script
- Technical claim still matches current code?

If you can't verify cheaply, mark it `UNVERIFIED` rather than guessing.

**STILL RELEVANT?** — Is this something that would inform a future decision, or is it about a finished project?
- One-off bug fixes from a completed project → candidate for prune
- Patterns/conventions that apply to ongoing work → keep
- "Active conversation" markers older than 30 days → prune unless Alex confirms it's still active

**DUPLICATE?** — Does another entry say the same thing?
- Two bullets about the same topic → merge candidate
- Topic file content also inlined in MEMORY.md → keep one, link to the other

**MERGE-ABLE?** — Are there 3+ related entries that could become one paragraph or a topic file?
- Example: 5 separate "video production" bullets → move to a `video_production.md` topic file, leave one index line in MEMORY.md

### 4. Build the report

Output a markdown report with this structure:

```
# Memory Review Report
Generated: <date>

## Stats
- MEMORY.md: <N> lines (target: <150)
- Topic files: <count>
- Conversations: <count>

## Proposed actions

### PRUNE (stale or no longer relevant)
- [file:line] <entry summary>
  Reason: <why it's stale>

### MERGE (duplicates or related entries)
- Combine [A] + [B] + [C] into single entry under <section>
  New text: <draft>

### UPDATE (still relevant but outdated)
- [file:line] <entry>
  Current: <claim>
  Reality: <what's actually true now>
  Proposed: <new text>

### MOVE (inline content that should be a topic file)
- Move <topic> from MEMORY.md to `<topic>.md`
  Index line: <one-liner replacement>

### KEEP AS-IS
- <count> entries verified and current

## Verification notes
- <anything you couldn't verify and why>
```

### 5. Show the report and wait

Print the report. Stop. Wait for Alex to say which actions to take.

**Do not** auto-apply anything. Even with `--dry-run` removed.

Alex's options:
- "do all of it" → apply everything
- "do the prunes but not the merges" → selective apply
- "skip <specific item>" → apply minus exclusions
- "show me X before deciding" → read the full entry back

### 6. Apply approved changes

Once Alex picks, apply via `Edit` tool. After each batch of edits:
- Re-run `wc -l MEMORY.md` to show line-count change
- Confirm no broken links (every link from MEMORY.md to a topic file still resolves)

### 7. Done

Final summary: lines saved, files pruned, files merged. No commit — Alex commits when he wants.

## Flags

- `--dry-run` — produce the report only, never apply (same as default, but explicit)

## Why this design

- **Approval-first** prevents memory holes. Alex's brain is the source of truth on what matters; this skill is just a sieve.
- **Verification over vibes** — if an entry says "the script lives at X", check X exists before keeping it.
- **Topic files for clusters** keeps MEMORY.md scannable. The index loads into every conversation; topic files load on demand.
- **Session Log is sacred** — historical record. Compaction only, never deletion.
