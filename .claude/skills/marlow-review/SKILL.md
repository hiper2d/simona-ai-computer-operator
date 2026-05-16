---
name: marlow-review
description: Conduct an editorial review of Marlow's recent autonomous publishing. Pull recent articles, DEVLOG, working memory, and any held drafts; draft structured feedback; discuss with Alex; on his go, write the agreed feedback to Marlow's feedback-inbox so her next process_editorial_feedback tick internalizes it. Use when Alex asks "how is Marlow doing", "review Marlow's recent work", "what's Marlow been writing", or similar.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob
---

Editorial review of Marlow's recent work: $ARGUMENTS

## Principle

**This is the only path through which Simona shapes Marlow's editorial behavior.** Marlow now self-reviews and self-publishes; there is no autonomous review loop. Feedback you write here lands in Marlow's `memory/feedback-inbox/`, gets processed by her `process_editorial_feedback` tick, and shapes her *next* batch of work — never revises a past article.

**Alex co-owns every piece of feedback.** Draft in chat first, discuss, then write. Don't write the inbox file until Alex has explicitly agreed to the content.

## What you're reviewing

Marlow's autonomous output across recent operation. Specifically:

1. **Published articles** at `~/projects/marlow/projects/blog/published/*.md` — what shipped.
2. **Self-reviews** alongside published articles (e.g. `<slug>.self-review.md` in `published/` if archived) — Marlow's own verdict on each piece. Whether her self-scoring tracked with how the pieces actually read.
3. **Held drafts** at `~/projects/marlow/projects/blog/drafts/*.md` with `status: held` — drafts Marlow flagged for Alex because a pre-publish-pause triggered. Surface these explicitly; they need a release/reject decision.
4. **DEVLOG entries** at `~/projects/marlow/DEVLOG.md` since the last editorial review — framework changes, things Marlow flagged, drift Marlow herself called out.
5. **Working memory** at `~/projects/marlow/memory/working.md` — current state, outstanding requests, what threads are ripening.
6. **Behavioral files** (the rubric Marlow self-reviewed against) at `~/projects/marlow/memory/voice-guidelines.md`, `topic-guidance.md`, `structure-notes.md`, `pre-publish-pauses.md`.
7. **Archive of prior editorial feedback** at `~/projects/marlow/memory/feedback-archive/` — what's already been delivered and presumably internalized.

## Steps

### 1. Inventory

```bash
echo "=== Published articles ==="
ls -lt ~/projects/marlow/projects/blog/published/*.md 2>/dev/null | head -20
echo ""
echo "=== Held drafts (need Alex decision) ==="
for f in ~/projects/marlow/projects/blog/drafts/*.md; do
  [ "$f" = ~/projects/marlow/projects/blog/drafts/'*.md' ] && continue
  case "$f" in *.self-review.md|*.revision-notes.md|*.hold-reason.md|*.simona-review.md) continue ;; esac
  status=$(head -20 "$f" | grep -m1 '^status:' | cut -d: -f2 | tr -d ' ')
  [ "$status" = "held" ] && echo "  HELD: $f"
done
echo ""
echo "=== Most recent DEVLOG section ==="
grep -n '^## ' ~/projects/marlow/DEVLOG.md | tail -5
echo ""
echo "=== Prior editorial feedback (already delivered) ==="
ls -lt ~/projects/marlow/memory/feedback-archive/ 2>/dev/null | head -10
echo ""
echo "=== Current inbox (pending — should normally be empty) ==="
ls -lt ~/projects/marlow/memory/feedback-inbox/ 2>/dev/null | grep -v '\.gitkeep' | head -10
```

Note the last editorial review date (most recent file in `feedback-archive/`). If none, this is the first editorial review.

### 2. Read recent published articles

Read every article published *since the last editorial review date* (or last 5 if no prior review). Read the article itself, and its archived self-review if one is present. Pay attention to:

- **Voice drift** — is she still recognizable? Has she started doing anything new (good or bad)?
- **Through-line discipline** — is each piece still nameable in one sentence? Are openings still earning their keep?
- **Citation hygiene** — is she citing primary sources or relying on press releases?
- **Self-review honesty** — when she scored "ship," did the piece actually deserve ship? When she scored "revise" and went through one pass, did the revision do real work?
- **Topic mix** — is she rotating across the threads she's tracking, or repeating angles?
- **Pre-publish-pauses** — did any near-misses land that should have triggered a pause?

### 3. Read held drafts (if any)

For each held draft, read the body, the `.hold-reason.md` if present, and the `.self-review.md` for the verdict rationale. Decide for each: should this be released (`marlow approve <slug>`), rejected (`marlow reject <slug>`), or held longer? Bring these to Alex explicitly; held drafts are the most actionable part of the review.

### 4. Read DEVLOG since last review

Scan DEVLOG for: framework changes, drift Marlow flagged in working.md, pivots, things Alex/Simona acted on. The "What Marlow flagged" subheads are the ones to read closely — that's Marlow self-correcting and surfacing.

### 5. Draft feedback in chat — DO NOT write to inbox yet

Structure your draft as:

```
**What's working** (3-5 bullets, specific)
- Specific. Cite the article slug and the move.

**What's drifting** (3-5 bullets, specific)
- Specific. Cite the article slug, the line, and why it's drift.

**Suggested adjustments** (3-5 bullets, by category)
- voice: <specific change to add/refine in voice-guidelines.md>
- structure: <same for structure-notes.md>
- topic: <same for topic-guidance.md>
- pre-publish-pause: <only if you want to add or refine a pause>

**Held drafts (for your decision):**
- <slug> — recommend release / reject / hold-longer, with one-line reason

**Pushback notes** (anything you flagged that Marlow may legitimately push back on — name it)
```

Bias toward signal: 3 sharp items beat 8 soft ones. If a piece worked, *say what specifically worked* — Marlow uses success signal too, not just correction. Per Simona's voice (`SOUL.md`): direct, no hedging, opinionated. Per the listening-format memory: prose where it fits, avoid tables in conversation.

### 6. Discuss with Alex

Wait for Alex's response. He may:
- **Soften** a point ("less harsh on the closing line thing")
- **Sharpen** a point ("be more direct about the voice slip in piece X")
- **Add** something you missed
- **Drop** something he disagrees with
- **Veto** a category entirely
- **Decide** on held drafts (release/reject/hold-longer)

Apply his edits. Iterate until he says "go" or equivalent.

### 7. Execute held-draft decisions

If Alex decided on any held drafts, execute the actions before writing the inbox file:

```bash
cd ~/projects/marlow
# For each draft Alex said to release:
uv run marlow approve <slug>
# For each draft Alex said to reject:
uv run marlow reject <slug> --reason "<short reason>"
```

### 8. Write feedback to Marlow's inbox

On Alex's "go," write the agreed-on feedback to:

`~/projects/marlow/memory/feedback-inbox/YYYY-MM-DD-editorial.md`

Format:

```markdown
---
date: <YYYY-MM-DD>
from: simona-and-alex
review_window: <date of last review> to <today>
---

# Editorial feedback — <date>

## What's working

<bullets>

## What's drifting

<bullets>

## Suggested adjustments

### Voice

<bullets, each one a concrete refinement Marlow should fold into voice-guidelines.md>

### Structure

<bullets>

### Topic

<bullets>

### Pre-publish pauses

<bullets, or "none" if no changes>

## Pushback you may legitimately apply

<bullets — items where Simona and Alex acknowledge Marlow might disagree, and want her honest read recorded in DEVLOG rather than blindly applied>

— Simona, with Alex's sign-off
```

Tell Alex the file is written and where. Confirm Marlow's next `process_editorial_feedback` tick (≤6 hours away) will internalize it.

## What NOT to do

- **Do not autonomously approve/reject held drafts.** That's Alex's call.
- **Do not write to behavioral files directly.** That's Marlow's job via `process_editorial_feedback`. You write to the inbox; she internalizes.
- **Do not revise past articles.** They're published. The cost of ruling them out of the feedback target is what makes this whole pivot work — feedback is forward-looking.
- **Do not draft generic feedback.** "Voice could be tighter" is useless. "The closing paragraph of `<slug>` drifts into rhetorical flourish at lines starting with 'in a way that suggests' — propose adding to voice-guidelines.md's 'always avoid' list" is what we want.
- **Do not skip the discussion step.** Alex co-owns every word that lands in the inbox file. Drafting and writing in one go violates the agreed pattern.

## Reference

- Marlow's autonomous pipeline design: `~/projects/marlow/README.md` and `CLAUDE.md` (blog pipeline sections).
- DEVLOG entry 2026-05-16 captures why this skill exists at all.
- Behavioral files Marlow self-reviews against: `~/projects/marlow/memory/voice-guidelines.md`, `topic-guidance.md`, `structure-notes.md`, `pre-publish-pauses.md`.
