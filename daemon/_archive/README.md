# Archived simona-daemon files

Retired 2026-05-16 when the autonomous-publishing pipeline landed. Marlow now
self-reviews and self-publishes; the simona-side automated review loop is gone.

Kept here as historical reference, not active code. If you re-introduce a
Simona-driven editorial loop, copy from here — don't link back.

- `handlers/review_drafts.py` — Simona's tick handler that read Marlow's drafts
  and wrote `<slug>.simona-review.md` files for the old multi-version review
  loop.
- `tasks/review_drafts.yaml` — task definition that fired the handler every 2
  hours.

The new editorial path is on-demand via Alex's interactive Claude Code session
using the `.claude/skills/marlow-review/` skill.
