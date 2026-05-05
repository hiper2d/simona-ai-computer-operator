# Shell aliases for controlling Simona's local TTS.
# Source from your ~/.zshrc:
#   source ~/projects/simona-ai-computer-operator/mcp/kokoro/aliases.sh

# simona-mute: set persistent flag AND kill any in-flight playback / queue.
# Mirrors the chat-side `mute` interceptor so behavior is consistent regardless
# of where you trigger from.
alias simona-mute='touch ~/.simona-mute && pkill -f mcp/kokoro/cli.py 2>/dev/null; pkill -f mcp/kokoro/drainer.py 2>/dev/null; pkill -x afplay 2>/dev/null; rm -rf /tmp/simona-queue 2>/dev/null; rm -f /tmp/simona-drainer.pid /tmp/simona-last-queued.ts 2>/dev/null; echo muted'

alias simona-unmute='rm -f ~/.simona-mute && echo unmuted'

# simona-shutup: kill current playback only, leave mute flag untouched.
alias simona-shutup='pkill -f mcp/kokoro/cli.py 2>/dev/null; pkill -f mcp/kokoro/drainer.py 2>/dev/null; pkill -x afplay 2>/dev/null; rm -rf /tmp/simona-queue 2>/dev/null; rm -f /tmp/simona-drainer.pid 2>/dev/null; echo stopped'
