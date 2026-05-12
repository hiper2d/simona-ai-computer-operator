#!/bin/bash
# PreToolUse hook on Bash: blocks git commands that target the simona repo.
#
# Triggers I made twice in one session: ran git in simona (cwd drifted) and
# accidentally committed/force-pushed there. Memory alone isn't enforcement;
# this hook is.
#
# Reads tool call JSON on stdin. Blocks (exit 2 with stderr) if either:
#   1. cwd is inside simona AND command contains `git` AND command does NOT
#      use `git -C /some/path/outside/simona`
#   2. command explicitly references `git -C /Users/hiper2d/projects/simona-ai-computer-operator`
# Allows everything else.

INPUT=$(cat)
COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // ""')
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // ""')
SIMONA="/Users/hiper2d/projects/simona-ai-computer-operator"
MARLOW="/Users/hiper2d/projects/marlow"

# Fast path: not a git command at all.
if ! printf '%s' "$COMMAND" | grep -qE '\bgit\b'; then
    exit 0
fi

# Case 1: explicit -C targeting simona always blocks, regardless of cwd.
if printf '%s' "$COMMAND" | grep -qE "git[[:space:]]+-C[[:space:]]+${SIMONA}"; then
    cat >&2 <<EOF
BLOCKED: git command targets the simona-ai-computer-operator repo via -C.

Alex manages git for the simona repo himself. The harness blocks git
operations against it because Claude has confused cwd state and
accidentally committed marlow content into simona twice in one session.

Allowed: git operations against $MARLOW (use \`git -C $MARLOW ...\`).
Allowed: any non-git command in any directory.
See: ~/.claude/projects/-Users-hiper2d-projects-simona-ai-computer-operator/memory/feedback_no_git_in_simona.md
EOF
    exit 2
fi

# Case 2: cwd is inside simona AND command has no explicit -C redirecting elsewhere.
if [[ "$CWD" == "$SIMONA"* ]]; then
    # If the command uses -C with a path that isn't simona, allow it.
    if printf '%s' "$COMMAND" | grep -qE 'git[[:space:]]+-C[[:space:]]+/'; then
        # Has explicit -C — already would have matched case 1 if it pointed at simona.
        exit 0
    fi
    cat >&2 <<EOF
BLOCKED: git command run from inside the simona repo (cwd: $CWD).

Alex manages git for the simona repo himself. The harness blocks git
operations against it because Claude has confused cwd state and
accidentally committed marlow content into simona twice in one session.

If you meant to operate on marlow, run: \`git -C $MARLOW <command>\`.
That bypasses cwd entirely. Memory at:
~/.claude/projects/-Users-hiper2d-projects-simona-ai-computer-operator/memory/feedback_no_git_in_simona.md
EOF
    exit 2
fi

exit 0
