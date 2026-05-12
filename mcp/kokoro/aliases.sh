# Shell helpers for controlling Simona's local TTS.
# Source from your ~/.zshrc:
#   source ~/projects/simona-ai-computer-operator/mcp/kokoro/aliases.sh

# Single entry point. All control flows through `simona <subcommand>`:
#   simona mute | unmute | stop | pause | continue | resume | replay | status
# Pure-stdlib Python — no venv activation needed.
simona() {
  python3 "$HOME/projects/simona-ai-computer-operator/mcp/simona/cli.py" "$@"
}

# Back-compat shims for muscle memory. Prefer the subcommand form above.
alias simona-mute='simona mute'
alias simona-unmute='simona unmute'
alias simona-shutup='simona stop'
