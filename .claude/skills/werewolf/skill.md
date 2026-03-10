---
name: werewolf
description: Work with the AI Werewolf Party Game project — a Werewolf game where AI bots pretend to be humans. Use when the user asks about the werewolf game, wants to modify it, review gameplay, or create content for it.
argument-hint: <what to do with the werewolf project>
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Agent
---

Work on the AI Werewolf Party Game: $ARGUMENTS

## Project Location

`/Users/hiper2d/projects/werewolf-ai-party-game/`

## What is this?

A Werewolf party game where AI bots pretend to be humans. They don't know about other AI players and try their best to win. Each bot has personal goals, secret roles, enemies, and alliances. Live at **[aiwerewolf.net](https://aiwerewolf.net)**. Local dev runs on `localhost:3000` (same Firebase data).

## Supported AI Models

- **OpenAI**: GPT-5.4, GPT-5.3, GPT-5-mini
- **Anthropic**: Claude 4.6 Opus, Claude 4.6 Sonnet, Claude 4.5 Haiku (with or without Thinking)
- **Google**: Gemini 3.1 Pro Preview, Gemini 3 Flash Preview
- **DeepSeek**: DeepSeek Chat, DeepSeek Reasoner
- **Mistral**: Mistral Large 3, Mistral Medium 3.1, Magistral Medium 1.2 (Thinking)
- **xAI**: Grok 4, Grok 4.1 Fast Reasoning
- **Moonshot AI**: Kimi K2.5, Kimi K2 Turbo, Kimi K2 (with or without Thinking)

## Tech Stack

- Next.js 16 + React 19
- Firebase: Firestore, Auth
- BetterStack: logging and uptime
- All AI provider SDKs (no frameworks — custom agents per vendor)
- Custom voice framework (OpenAI and Gemini TTS) for character voices
- Real-time cost tracking per bot, per game, and per player

## Key Directories

All paths relative to `werewolf-client/`:

- `app/ai/` — AI agent implementations and prompts
- `app/api/` — Server actions for game/user operations
- `app/games/[id]/` — Game UI and components
- `firebase/` — Firebase config and rules
- `scripts/` — Utility scripts
- `components/` — Shared UI components

## Architecture

- **Agent System**: `AbstractAgent` base class → vendor-specific agents (OpenAiAgent, ClaudeAgent, GoogleAgent, etc.) → `AgentFactory` creates them based on model type
- **Structured Responses**: JSON schemas via `askWithSchema()`
- **Game States**: WELCOME → DAY_DISCUSSION → VOTE → VOTE_RESULTS → NIGHT_BEGINS → GAME_OVER
- **Message Flow**: Game Master → bots respond via AI agents → stored in Firestore → SSE for real-time updates
- **Auth**: NextAuth v5 with GitHub and Google OAuth
- **User API Keys**: Users provide their own AI provider keys via profile page

## Game Flow (what happens in each phase)

### 1. Game Creation
- User picks a theme (anything — Harry Potter, GoT, submarine crew, etc.), player count (up to 12), werewolf count, and special roles (Doctor, Detective, Maniac)
- "Generate Preview" calls an AI to create: game story, Game Master config (model + voice), and all player configs (name, gender, model, play style, voice, backstory, voice instructions)
- User can tweak everything before clicking "Create Game"

### 2. WELCOME Phase
- Game Master sets the scene with the game story
- Each bot introduces themselves in character, one by one
- Right panel shows "Introductions" progress bar
- Cost per bot is tracked in the participants sidebar

### 3. DAY_DISCUSSION Phase
- Human player chats with bots via text or voice (TTS/STT)
- Game Master picks which bots respond, OR user can "Select Bots Manually" (modal with all alive players, pick 1-5)
- Right panel shows "Discussion Queue" — which bots are thinking/responding, with a progress bar
- Buttons: Send, Vote, Go on (triggers more bot responses without human message)

### 4. VOTE Phase
- Click "Vote" to start voting
- All bots cast votes with explanations (shown in chat with 🗳️ emoji)
- Right panel shows "Voting Queue" with progress
- When it's the human's turn, a "Cast Your Vote" modal appears:
  - Select dropdown to pick a player
  - Textarea for reason (required — Cast Vote button is DISABLED until reason is provided)
  - Cancel / Cast Vote buttons
- Game Master announces results: vote counts, who's eliminated, and their true role

### 5. NIGHT_BEGINS Phase
- Click "Start Night" to begin
- Right panel shows "Night Actions" with processing order: Maniac → Werewolf → Doctor → Detective
- Werewolves chat privately to coordinate (only visible if you ARE a werewolf)
- Doctor protects, Detective investigates, Maniac abducts
- If you're a villager: no night actions, "Replay Night" button does nothing useful
- If you're a werewolf: you participate in the wolf chat and pick a target
- Game Master narrates results at dawn
- "Replay Night" / "Next Day" buttons appear

### 6. GAME_OVER Phase
- Game ends when all werewolves are eliminated (village wins) or werewolves outnumber villagers
- All roles are revealed
- "Post-Game Discussion" — bots stay in character and debrief, argue, confess

## Roles

- **Villager**: No special abilities
- **Werewolf**: Can eliminate players at night, coordinates with other wolves in private chat
- **Doctor**: Can protect one player from elimination each night
- **Detective**: Can investigate one player to learn their role each night
- **Maniac**: Abducts one player for the night, blocking their actions and any actions targeting them

## Browser Automation Notes (for playing via CDP)

When automating gameplay through the browser skill:

- **React controlled components**: Standard DOM manipulation (setting `.value`, dispatching `change` events) does NOT update React state. You must trigger React's own onChange handler via `__reactProps`:
  ```js
  // For <select>:
  var sel = document.querySelector('select');
  var propsKey = Object.keys(sel).find(k => k.startsWith('__reactProps'));
  sel[propsKey].onChange({target: {value: sel.options[INDEX].value}});

  // For <textarea>:
  var ta = document.querySelector('textarea');
  var propsKey = Object.keys(ta).find(k => k.startsWith('__reactProps'));
  ta[propsKey].onChange({target: {value: 'your text here'}});
  ```
- **Cast Vote modal**: Both the select (player name) AND textarea (reason) must have values in React state for the Cast Vote button to become enabled
- **Timing**: Bot responses take 10-60+ seconds depending on model and player count. Use `sleep` between actions. 12-player games take longer.
- **Viewport**: Chrome CDP windows may have small viewports. Use `Emulation.setDeviceMetricsOverride` to set 1400x900 for proper screenshots.
- **Use localhost:3000** for automation (same Firebase data as production). You must ensure the dev server is running first — run `cd /Users/hiper2d/projects/werewolf-ai-party-game/werewolf-client && npm run dev` in the background before navigating to localhost:3000

## Dev Commands

Run from `werewolf-client/`:

```bash
npm run dev      # Dev server on localhost:3000
npm run build    # Production build
npm run lint     # ESLint
npm run test     # Jest tests
```

## Images

Cover and screenshots are in `/Users/hiper2d/projects/werewolf-ai-party-game/images/`.

## Important Notes

- Always `cd /Users/hiper2d/projects/werewolf-ai-party-game/werewolf-client` before running npm commands
- Read the repo's own `CLAUDE.md` for the latest architecture details before making changes
- Users store their own API keys — never hardcode AI provider keys
