# Werewolf Rules Video — Version 04

## Concept
Cinematic intro arc (host appears in the forest → leads us to the mansion → invites us inside) → rules slideshow → live app demo. The host is the through-line. Single narrator voice across everything.

Pitch line that drives the app demo: **every major AI plays this game** (Claude, GPT, Gemini, Grok, DeepSeek, Mistral, Kimi).

## Locked decisions

- **Voice**: ElevenLabs **George** (storyteller British), pitched down 15% with hall echo (`asetrate=44100*0.85,aresample=44100,aecho=0.8:0.7:40:0.3`). Used for ALL narration — gen-AI clips, slideshow, app demo, outro. Drafts via Gemini TTS for timing.
- **Gen-AI video**: Seedance 2.0 silent + George dub on top. No native-voice clips — voice consistency wins over lip-sync. Reference-to-video skill update is nice-to-have, not blocking.
- **App demo target**: aiwerewolf.net (live) — same as v3.
- **Length target**: ~2:00-2:15 (stretched from v3's 1:40 to give the cinematic intro room to breathe).
- **Forest interpolation path**: option (c) — closed-cloak static preamble → Seedance interpolation v1→end (cards bunched → cards fanned).

## Asset inventory

### Locked (in `images/`)
- `werewolf-forest-cards-start.png` — closed cloak preamble (1792x1024) ✅ regenerated 2026-05-09 (gpt-image-2)
- `werewolf-forest-cards-v1.png` — cards bunched (Seedance start frame) ✅ regenerated 2026-05-09 (gpt-image-2)
- `werewolf-forest-cards-end.png` — cards fanned and offered (Seedance end frame) ✅ regenerated 2026-05-09 (gpt-image-2)
- `mansion-gates-werewolf-statues-start.png` — establishing shot ✅ regenerated 2026-05-09 (gpt-image-2)
- `mansion-passage-mid.png` — closer to mansion ✅ regenerated 2026-05-09 (gpt-image-2)
- `mansion-doors-close.png` — at the threshold ✅ recovered
- `werewolf-host-table-whiskey-start.jpg` — host at candlelit mahogany table ✅ recovered
- `mansion-doors-zoomed-end.png` — 80% center crop of doors, Seedance start frame (matches Ken Burns end of scene 5) ✅ recovered
- `mansion-corridor-end.jpg` — gothic candlelit corridor, Seedance end frame (paintings, sconces, far open door to host room) ✅ recovered

### Locked clips (in `clips/`)
- `corridor-entry-v1.mp4` — Seedance scene 5b (4.9s, 1280x720, 24fps). Doors open + camera dolly into corridor. ✅ recovered

### Reusable from project root (`generated-images/`)
- `werewolf-host-suit-v1.png` — host portrait (character ref)
- `werewolf-camp-day.png`, `werewolf-camp-night.png` — day/night cycle
- `werewolf-day-night-split.png` — day/night transition
- `werewolf-hidden-wolves.png` — wolves hiding among villagers
- `werewolf-villagers-table-oai.png` — villager council
- `werewolf-vs-villagers.png` — the conflict

### Still needed
- **Doctor** themed shot — healer over sleeping villager, candlelight, dark interior
- **Detective** themed shot — magnifying glass on a tarot/role card, investigative ledger, dark
- **Maniac** themed shot — lone hooded figure with a blade at night, unhinged
- Estimated cost: 3 × $0.13 ≈ $0.40 (OpenAI gpt-image-2)

## Structure

### Part 1: Intro arc (~27s) — gen-AI + Ken Burns

| # | Dur | Visual | Narration | Effect |
|---|-----|--------|-----------|--------|
| 1 | 4s  | `werewolf-forest-cards-start.png` (closed cloak) | "Some games you play to win." | Static + subtle Ken Burns push-in, ambient forest sfx |
| 2 | 5s  | Seedance: `werewolf-forest-cards-v1.png` → `werewolf-forest-cards-end.png` | "Others, you play to survive." | Seedance image-to-video w/ end-frame interpolation, silent, George dub |
| 3 | 5s  | `mansion-gates-werewolf-statues-start.png` | "Welcome to AI Werewolf." | Ken Burns slow zoom in toward gates |
| 4 | 4s  | `mansion-passage-mid.png` | *(silent — wind, footsteps)* | Ken Burns push-in toward mansion |
| 5 | 4s  | `mansion-doors-composited-feathered.png` | "Step inside." | Ken Burns push-in **1.0x → 1.4x** lands on central 1280x720 region == Seedance frame 1 (pixel-exact match, 40px feathered edges) |
| 5b | 5s | Seedance: `mansion-doors-zoomed-end.png` → `mansion-corridor-end.jpg` | *(silent — door creak, footsteps, candle flicker)* | Doors creak open inward, camera dollies forward into candlelit corridor. Cut from scene 5 zoom-end is frame-perfect |

### Part 2: Host welcome (~8s) — gen-AI

| # | Dur | Visual | Narration | Effect |
|---|-----|--------|-----------|--------|
| 6 | 8s  | Seedance: `werewolf-host-table-whiskey-start.jpg` | "I'm your host. The rules are simple. There are villagers — and there are werewolves." | Seedance image-to-video silent (host raises glass, looks up to camera), George dub |

### Part 3: Rules slideshow (~38s) — Ken Burns

| # | Dur | Visual | Narration | Effect |
|---|-----|--------|-----------|--------|
| 7 | 5s  | `werewolf-day-night-split.png` | "By day, villagers vote to kill anyone they suspect of being a werewolf." | Slow horizontal pan |
| 8 | 5s  | `werewolf-camp-night.png` | "By night, the werewolves choose a villager to eliminate." | Push-in |
| 9 | 6s  | `werewolf-hidden-wolves.png` | "The catch — werewolves look exactly like villagers. They lie. They strategize. They survive." | Slow zoom |
| 10 | 6s | NEW — Doctor | "Special roles change everything. The Doctor heals one player each night — they might just save you." | Slow zoom |
| 11 | 6s | NEW — Detective | "The Detective investigates one player a night and learns who's a werewolf." | Slow zoom |
| 12 | 6s | NEW — Maniac | "And the Maniac — not a werewolf, but kills like one. Two predators. One win." | Slow zoom |

### Part 4: Live app demo (~42s) — browser capture (aiwerewolf.net)

Reuse browser/highlight/cursor tooling from v3.

| # | Dur | Visual | Narration | Effect |
|---|-----|--------|-----------|--------|
| 13 | 3s | Landing page | "Here's where it gets interesting." | Static / subtle zoom |
| 14 | 4s | Cursor → "Go to Game Lobby" → click | "Every other player is an AI bot." | Cursor animation + click |
| 15 | 3s | Lobby loads | *(beat)* | Static |
| 16 | 3s | Cursor → "Create Game" → click | "You set up the game." | Cursor click |
| 17 | 5s | Theme input | "Pick any theme. Submarine crew. Royal court. Whatever fits the night." | Highlight on theme field |
| 18 | 4s | Player + werewolf count | "Set the player count. Choose how many werewolves stalk the table." | Scroll + highlight |
| 19 | 4s | Special roles toggles | "Add Doctor, Detective, Maniac — or all three." | Highlight |
| 20 | 8s | AI model selection | "Each bot gets its own brain — **Claude, GPT, Gemini, Grok, DeepSeek, Mistral, Kimi**. They're all here. And they all want to win." | Highlight + scroll through model list |
| 21 | 3s | Generate Preview → click | "Hit generate." | Cursor click |
| 22 | 5s | Preview shows bots → scroll + create | "Names, backstories, voices. Edit anything. Then create." | Scroll + highlight + cursor click |

### Part 5: Outro (~6s)

| # | Dur | Visual | Narration | Effect |
|---|-----|--------|-----------|--------|
| 23 | 6s  | `werewolf-host-table-whiskey-start.jpg` (still or short Seedance loop) + URL overlay | "The cards are dealt. Will you survive?" | Slow zoom + URL fade-in: **aiwerewolf.net** |

---

## Timing rollup

| Part | Duration |
|------|----------|
| 1. Intro arc | ~27s |
| 2. Host welcome | ~8s |
| 3. Rules slideshow | ~34s |
| 4. App demo | ~42s |
| 5. Outro | ~6s |
| **Total** | **~1:57** |

Slack: ~10-15s of breathing room available before hitting 2:15.

## Production order

1. **Generate 3 missing role images** (Doctor, Detective, Maniac) — OpenAI gpt-image-2, ~$0.40
2. **Write all narration text → ElevenLabs George (final voice)** — measure timings, lock the script
3. **Generate Seedance clips** — 2 needed: forest interpolation (v1→end, ~5s), host welcome (~8s). Cost: ~$3
4. **Build Ken Burns slideshow segments** — Part 1 (3 mansion shots), Part 3 (6 role shots), Part 5 (outro)
5. **Capture app demo** — browser CLI walkthrough on aiwerewolf.net, cursor + highlight overlays
6. **Assemble** — concat with proper acrossfade/xfade rules from past learnings (25fps, 48kHz audio, 4% bg music)

Estimated total cost: ~$4-5 (3 images + 2 Seedance clips + ElevenLabs narration ~3000 chars).

## Open questions

- Role images: generate fresh themed shots, or stick with existing v3 imagery (which doesn't visualize Doctor/Detective/Maniac directly)? Recommend: generate 3 new.
- Background music bed: same track as v3? Or fresh search? v3 was working — recommend: keep.
- Outro CTA — URL overlay only, or add a short subscribe/follow line? Recommend: URL only, keep it dignified.
