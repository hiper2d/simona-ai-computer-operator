# Werewolf Rules v4 — Work Log

Append-only chronological record of every asset generation, edit, or external call. Goal: anyone (any future Simona session) can rebuild this project end-to-end from this file alone.

Format per entry:
- `### [timestamp] step-name` — short title
- **Inputs**: source files, refs, params
- **Tool/Model**: which API/skill
- **Prompt**: full prompt verbatim
- **Output**: filename(s) saved, dimensions, format
- **External URLs**: fal/api result URLs (may expire — re-upload if rebuilding from old log)
- **Cost**: USD
- **Seed / Request ID**: if applicable
- **Notes**: anything non-obvious

---

## Asset origin tracking

### Pre-existing (origin uncertain — predate this log)

These were locked in `script.md` Asset Inventory before WORKLOG.md existed. Rebuild prompts unknown — would need to re-prompt from scratch if lost.

| File | Source | Status after 2026-05-09 wipe |
|------|--------|------------------------------|
| `images/mansion-doors-close.png` | unknown earlier session | ✅ recovered (decoded from `/tmp/gemini_corridor_req.json`) |
| `images/werewolf-host-table-whiskey-start.jpg` | unknown earlier session | ✅ recovered (decoded from `/tmp/gemini_corridor_req.json`) |
| `images/werewolf-forest-cards-start.png` | unknown earlier session | ❌ LOST — needs regen |
| `images/werewolf-forest-cards-v1.png` | unknown earlier session | ❌ LOST — needs regen |
| `images/werewolf-forest-cards-end.png` | unknown earlier session | ❌ LOST — needs regen |
| `images/mansion-gates-werewolf-statues-start.png` | unknown earlier session | ❌ LOST — needs regen |
| `images/mansion-passage-mid.png` | unknown earlier session | ❌ LOST — needs regen |

---

## 2026-05-09 — Scene 5b corridor entry (Seedance)

### [13:33] crop-doors-zoomed-end

Goal: produce a Seedance start frame that matches the final state of the Ken Burns push-in on scene 5, so the cut into the Seedance clip is seamless.

- **Input**: `images/mansion-doors-close.png` (1792x1024)
- **Tool**: ffmpeg
- **Command**: `ffmpeg -y -i images/mansion-doors-close.png -vf "crop=1434:819:179:102,scale=1792:1024:flags=lanczos" images/mansion-doors-zoomed-end.png`
- **Output**: `images/mansion-doors-zoomed-end.png` (1792x1024 PNG, ~2.8MB) — 80% center crop rescaled back to 1792x1024
- **Cost**: $0
- **Notes**: 80% center crop = 1.25x zoom equivalent. The Ken Burns push-in for scene 5 should zoom from 1.0x → 1.25x to land on this frame.

### [13:35] gen-corridor-end (nanobanana / Gemini 3.1 Flash Image)

Goal: generate the Seedance end frame — POV looking down a candlelit corridor, gothic arch in foreground, far open door spilling warm orange light. Bridges the cold doors palette to the warm host-room palette.

- **Inputs (refs)**:
  - Ref 1: `images/mansion-doors-close.png` (style ref — gothic blue-grey stone)
  - Ref 2: `images/werewolf-host-table-whiskey-start.jpg` (style ref — warm mahogany + candlelight)
- **Tool**: nanobanana skill (multi-reference mode), `gemini-3.1-flash-image-preview`
- **API**: `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent`
- **imageConfig**: `aspectRatio: "16:9"`, `imageSize: "2K"`
- **Prompt** (verbatim):
  > First-person POV at the threshold of an opened gothic mansion door, looking straight down a long narrow corridor that recedes into the distance. Stone gothic archway in the immediate foreground (matching the cold dark stone style of the first reference image — same blue-grey carved stone, same gothic architecture). The corridor walls are paneled in dark mahogany wood further in, lined with heavy oil-painted ancestral portraits in ornate gilded frames, dim figures barely visible. Wrought-iron wall sconces with flickering candles every few meters cast warm amber pools of light leaving deep shadows between. Dark wooden floor with a long worn velvet runner. Cold blue stone tones near the camera transition gradually into warm candlelit interior as the corridor recedes. At the far end of the corridor: an open doorway spilling warm orange candlelight from a library beyond (matching the warm mahogany and candlelit palette of the second reference image — same color temperature, same bookshelves silhouette hint). Faint atmospheric haze, dust motes drifting in candlelight. Dark, gothic, cinematic, mysterious, deep depth of field. Shot on Canon EOS R5, 35mm, low angle, f/2.8, 8k, raw. Aspect ratio 16:9.
- **Output**: `images/mansion-corridor-end.jpg` (2752x1536 JPEG, ~2.6MB). Note: nanobanana saved as `.png` initially; magic bytes were JPEG, renamed to `.jpg`.
- **Cost**: $0.067 (logged to `api-spending.csv`)
- **Seed**: not returned by Gemini Image API
- **Notes**: First try worked. Output included a red velvet runner that wasn't explicitly prompted but adds nice eye-line.

### [13:35] submit-seedance-corridor-entry

Goal: 5s Seedance image-to-video clip — doors creak open, camera dollies through into the corridor.

- **Inputs**:
  - Start frame: `images/mansion-doors-zoomed-end.png`
  - End frame: `images/mansion-corridor-end.jpg`
- **Tool**: seedance skill, `bytedance/seedance-2.0/image-to-video` via fal.ai queue API
- **Params**: `duration: "5"`, `generate_audio: false`, `resolution: "720p"`, `aspect_ratio: "16:9"`
- **Prompt** (verbatim):
  > The massive gothic stone doors slowly creak open inward, swinging away from the camera. Wisps of mist and dust drift through the opening. The camera then begins a smooth, steady forward dolly push, gliding through the now-open doorway and into the candlelit corridor beyond. Candle flames on wall sconces flicker gently. Slow cinematic tracking shot, deliberate and atmospheric, no cuts.
- **fal upload URLs** (may expire):
  - Start: `https://v3b.fal.media/files/b/0a998b41/QPn2PjklGGgGYHNcgkXaF_mansion-doors-zoomed-end.png`
  - End: `https://v3b.fal.media/files/b/0a998b41/PnEWS53dYzaVRn6VHpFS2_mansion-corridor-end.jpg`
- **Request ID**: `019e0dcf-db0d-7f90-bcb2-984d48e25a2f`
- **Status URL**: `https://queue.fal.run/bytedance/seedance-2.0/requests/019e0dcf-db0d-7f90-bcb2-984d48e25a2f`
- **Output URL** (may expire): `https://v3b.fal.media/files/b/0a998b55/7uSj_c20dykr4xETRN8IA_video.mp4`
- **Output file**: `clips/corridor-entry-v1.mp4` (1280x720, 24fps, 4.92s, 3.4MB)
- **Cost**: $1.51 (logged to `api-spending.csv`)
- **Seed**: 830506313 (re-roll with same seed for controlled variations)
- **Notes**: 24fps — must convert to 25fps with `fps=25` filter when assembling (project standard, see MEMORY.md xfade rule).

---

## 2026-05-09 — Recovery operation (post-wipe)

Another Simona session deleted everything in `video-projects/werewolf-rules-v3/` and `v4/`. Recovery actions:

- v4 fal URLs above were re-fetched (HTTP 200) → restored 3 files
- `/tmp/gemini_corridor_req.json` had base64 of doors + host originals → decoded both back into `images/`
- `/tmp/corridor_{start,mid,end}.jpg` preview frames moved into `clips/`
- `script.md` rewritten from this session's conversation context
- `.gitignore` updated: added `*.mp4` and `*.wav` so future commits never include generated media

Lost (not recoverable from any source):
- `werewolf-forest-cards-{start,v1,end}.png`
- `mansion-gates-werewolf-statues-start.png`
- `mansion-passage-mid.png`

---

## 2026-05-09 — Scene 5 doors-close re-anchor via outpainting

**Goal**: Eliminate the visible jump between scene 5's slideshow zoom-end and scene 5b's Seedance video. Seedance re-encoded its input frame (SSIM 0.52 between our crop `mansion-doors-zoomed-end.png` and Seedance frame 1). To get a frame-perfect seam, the slideshow zoom-in must land on Seedance's actual frame 1 — not on our pre-Seedance crop.

**Approach**: outpaint Seedance frame 1 outward to a 1792x1024 wider doors image. Ken Burns zoom 1.0x → 1.4x on the wider image lands on the central 1280x720 region == Seedance frame 1 == hard cut to Seedance video.

### [14:35] extract-seedance-frame-1-native

- **Input**: `clips/corridor-entry-v1.mp4`
- **Tool**: ffmpeg
- **Command**: `ffmpeg -y -i clips/corridor-entry-v1.mp4 -frames:v 1 images/seedance-frame-001-native.png`
- **Output**: `images/seedance-frame-001-native.png` (1280x720 PNG, native Seedance encode)
- **Cost**: $0
- **Notes**: Earlier rescaled-to-1792x1024 version (`seedance-frame-001.png`) is lower fidelity due to upscaling; native is the canonical truth.

### [14:36] build-padded-input-and-mask

- **Input**: `images/seedance-frame-001-native.png` (1280x720)
- **Tool**: ffmpeg
- **Padded input** (Seedance frame 1 centered on transparent 1792x1024 canvas):
  ```
  ffmpeg -y -i images/seedance-frame-001-native.png \
    -vf "format=rgba,pad=width=1792:height=1024:x=256:y=152:color=0x00000000" \
    images/seedance-frame-001-padded.png
  ```
- **Mask** (transparent borders = edit, white center = preserve):
  ```
  ffmpeg -y \
    -f lavfi -i "color=c=black@0.0:s=1792x1024,format=rgba" \
    -f lavfi -i "color=c=white:s=1280x720,format=rgba" \
    -filter_complex "[0:v][1:v]overlay=256:152:format=auto" \
    -frames:v 1 images/outpaint-mask.png
  ```
- **Outputs**: `images/seedance-frame-001-padded.png` (1792x1024 RGBA), `images/outpaint-mask.png` (1792x1024 RGBA)
- **Notes**: Center placed at offset (256, 152) so frame 1 occupies x=256..1535, y=152..871.

### [14:37] gpt-image-2-outpaint

Goal: extend gothic mansion exterior outward.

- **Inputs**: `images/seedance-frame-001-padded.png` (image[]), `images/outpaint-mask.png` (mask)
- **Tool**: openai-image skill, `gpt-image-2` via `https://api.openai.com/v1/images/edits`
- **Params**: `size=1792x1024`, `quality=medium` (default since not specified)
- **Prompt** (verbatim):
  > Outpaint and extend the gothic mansion exterior outward from the central image. Continue the same carved blue-grey gothic stone archway, columns, gargoyles, and lantern fixtures outward into the new frame area. Show full wrought-iron lanterns on tall sconces on the left and right with visible flickering candle flames inside. Below the doors: stone steps descending, mist and fog rolling across the ground. Above the arch: more carved gothic stonework, gargoyle silhouettes against the night sky. The composition should feel like a wider establishing shot of the same doors. CRITICAL: preserve the central 1280x720 region of the input image exactly as it is — do not redraw, recolor, or alter the doors, the existing visible lanterns, or any pixel inside the central region. Only fill the transparent border area. Match the cool blue-grey moonlit palette and dark gothic atmosphere of the central image. No warm tones. Cinematic, photorealistic.
- **Output**: `images/mansion-doors-outpainted.png` (1792x1024 PNG)
- **Cost**: $0.13 (logged to api-spending.csv)
- **Tokens**: 1682 input (1479 image + 203 text), 1243 output
- **Notes**: gpt-image-2 ignored the "preserve center" instruction and the mask — regenerated the entire image. SSIM of outpaint-center vs Seedance frame 1 = 0.30 (worse than no outpaint). Confirmed gpt-image-2 edit endpoint does not strictly preserve masked regions even with explicit instructions. Workaround in next step.

### [14:38] composite-seedance-back-into-center

Goal: take outpainted borders, paste real Seedance frame 1 back into the center to recover pixel-exact match.

- **Inputs**: `images/mansion-doors-outpainted.png` (gpt-image-2 output), `images/seedance-frame-001-native.png` (canonical center)
- **Tool**: ffmpeg overlay
- **Hard composite** (no feather, exact pixel paste):
  ```
  ffmpeg -y \
    -i images/mansion-doors-outpainted.png \
    -i images/seedance-frame-001-native.png \
    -filter_complex "[0:v][1:v]overlay=256:152" \
    images/mansion-doors-composited-hard.png
  ```
- **Feathered composite** (40px alpha falloff at edges to hide the seam):
  ```
  ffmpeg -y \
    -i images/mansion-doors-outpainted.png \
    -i images/seedance-frame-001-native.png \
    -filter_complex "[1:v]format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='255*min(1,min(min(X,1279-X)/40,min(Y,719-Y)/40))'[feath];[0:v][feath]overlay=256:152" \
    images/mansion-doors-composited-feathered.png
  ```
- **Outputs**: `images/mansion-doors-composited-hard.png`, `images/mansion-doors-composited-feathered.png`
- **Cost**: $0
- **SSIM check** (hard composite center vs Seedance frame 1): 0.9987 / PSNR 54 dB — pixel-identical except for PNG re-encode noise.
- **Decision (locked 2026-05-09)**: `mansion-doors-composited-feathered.png` is the canonical scene-5 slideshow asset.

### Ken Burns geometry update

For scene 5: zoom range is **1.0x → 1.4x**, not 1.25x as in the old script. Reason: Seedance frame 1 is 1280x720, occupying the central 1280/1792 = 71.4% of the wider image. Inverse = 1.4x zoom. At full zoom we see only the central 1280x720 region — pixel-identical (modulo 40px feather at outer edge) to Seedance frame 1. Hard cut to Seedance video has zero seam.

Lessons learned:
- gpt-image-2 edit endpoint does NOT strictly honor the mask — it regenerates broadly. Workaround: composite the original back into the center via ffmpeg overlay, optionally with feathered alpha for soft seam.
- This pattern (outpaint → composite-paste) generalizes for any "extend an existing frame outward while preserving it exactly" need.

---

## 2026-05-09 — Regenerate 5 missing intro images (gpt-image-2)

After the wipe, all 5 intro images had to be regenerated. Used `openai-image` skill (gpt-image-2) per new default-model preference. All at `size=1792x1024`, `quality=high`. Cost $0.19 per generation × 5 = $0.95.

### [14:50] gen-werewolf-forest-cards-v1 (anchor)

Goal: forest-cards anchor image — gloved hands holding wolf-sigil cards in dark forest at twilight.

- **Tool**: gpt-image-2, `/v1/images/generations` (text-to-image)
- **Inputs**: none
- **Prompt** (verbatim):
  > Close-up POV looking at gloved hands holding a tight stack of dark tarot-sized cards face-down — black ornate backs with silver wolf-head sigil. The cards are bunched together, edges tightly aligned. Hands wear black leather gloves with subtle embossed pattern. Sleeves of a heavy black hooded cloak fall around the wrists. Background: dark forest at twilight, bare gnarled trees, soft lantern-orange backlight bleeding through fog, cool blue-grey shadow tones in foreground. Shot on Canon EOS R5, 85mm, f/2.8, shallow depth of field, 8k, raw. Cinematic, gothic, mysterious. Aspect ratio 16:9.
- **Output**: `images/werewolf-forest-cards-v1.png` (1792x1024 PNG)
- **Tokens**: 143 input, 5063 output
- **Cost**: $0.19
- **Notes**: gpt-image-2 chose to feature one wolf-sigil card prominently front-on (it's still the "back" of a face-down card, so prompt intent honored). This image becomes the visual anchor for the chain.

### [14:51] gen-mansion-gates-werewolf-statues-start

Goal: wide establishing shot of mansion gate with werewolf statues, centered for zoom-in.

- **Tool**: gpt-image-2, `/v1/images/edits` (single ref)
- **Inputs**: `images/mansion-doors-close.png` (style ref — gothic stone palette)
- **Prompt** (verbatim):
  > Reference image shows the gothic mansions main doors style — carved blue-grey gothic stone, gargoyles, wrought-iron lanterns. Generate a NEW WIDE establishing shot of the same mansions outer wrought-iron entrance gate at night. CENTERED COMPOSITION (mansion squarely centered in the frame for a zoom-in effect). Two large stone werewolf statues flank the gate on tall stone plinths — snarling, mid-howl, weathered dark blue-grey stone matching the reference images stone style. The mansion looms in the distance behind the gate, massive silhouette with a few warm-lit windows. Wrought-iron lanterns burn on either side of the gate. Cobblestone path leads from camera through the gate toward the mansion. Heavy fog at ground level, bare trees on either side. Cool blue moonlight from above. Cinematic, dark, gothic, atmospheric. Shot on Canon EOS R5, 24mm wide, f/4, 8k, raw. Aspect ratio 16:9.
- **Output**: `images/mansion-gates-werewolf-statues-start.png` (1792x1024 PNG)
- **Tokens**: 1694 input (1479 image + 215 text), 5063 output
- **Cost**: $0.19

### [14:52] gen-werewolf-forest-cards-end

Goal: cards fanned out, faces hidden showing wolf-sigil backs. Same scene/lighting as v1.

- **Tool**: gpt-image-2, `/v1/images/edits` (single ref = v1)
- **Inputs**: `images/werewolf-forest-cards-v1.png`
- **Prompt** (verbatim):
  > Reference image shows the canonical scene: black-gloved hands holding cards with intricate silver wolf-sigil backs, in a dark forest at twilight with warm lantern backlight bleeding through bare trees. Generate the same scene but with the cards now FANNED OUT in a wide arc across both hands, like a magician offering a choice — five visible tarot-sized cards spread in an arc, all face-down, each showing the same intricate silver wolf-sigil back as the reference. The hands are held forward, presenting the fan toward the camera. Same gloves, same cloak sleeves, same dark forest background, same lighting, same depth of field, same atmosphere as the reference. Cinematic, gothic, mysterious. Aspect ratio 16:9.
- **Output**: `images/werewolf-forest-cards-end.png` (1792x1024 PNG)
- **Cost**: $0.19

### [14:52] gen-werewolf-forest-cards-start

Goal: hooded figure with hands folded inside closed cloak, no cards visible. Slight zoom-out from v1.

- **Tool**: gpt-image-2, `/v1/images/edits` (single ref = v1)
- **Inputs**: `images/werewolf-forest-cards-v1.png`
- **Prompt** (verbatim):
  > Reference image shows the canonical scene: black-gloved hands holding cards in a dark forest at twilight with warm lantern backlight bleeding through bare trees. Generate the same scene but with the cards NO LONGER VISIBLE — both gloved hands are folded together, drawn close to the body and partially tucked into the heavy black hooded cloak, only the dark fabric and embossed glove edges showing at the wrists. Slightly wider framing than the reference (zoomed out about 10%) to include more of the cloaked figures torso, but the same forest background, same lighting, same atmosphere. The hooded figure stands ready, anticipatory, before revealing the cards. Cinematic, gothic, mysterious. Aspect ratio 16:9.
- **Output**: `images/werewolf-forest-cards-start.png` (1792x1024 PNG)
- **Cost**: $0.19

### [14:52] gen-mansion-passage-mid

Goal: mid-distance mansion approach, larger than gates shot, centered for zoom-in.

- **Tool**: gpt-image-2, `/v1/images/edits` (multi-ref)
- **Inputs**:
  - `images/mansion-gates-werewolf-statues-start.png` (composition ref)
  - `images/mansion-doors-close.png` (style ref)
- **Prompt** (verbatim):
  > Reference images show the gothic mansion: a wrought-iron entrance gate with werewolf statues flanking it (first ref), and the close-up doors style with carved blue-grey stonework and lanterns (second ref). Generate a NEW MID-DISTANCE shot looking down the cobblestone path INSIDE the gate, halfway between the gate and the mansions main entrance. CENTERED COMPOSITION with the mansion entrance squarely centered for a zoom-in effect — noticeably larger and closer in the frame than in the gate shot. The mansions facade fills the upper half of the frame — dark blue-grey stone matching the references, warm lantern-lit windows, towers and gargoyle silhouettes against the night sky. Ornate stone urns or smaller statues line the path. Wrought-iron lanterns on tall posts cast pools of warm amber light onto wet cobblestones. Heavy fog rolls across the ground. Bare branches frame the edges. POV walking toward the entrance, the mansions main doors visible at center but still in the middle distance. Cinematic, gothic, dramatic perspective. Shot on Canon EOS R5, 35mm, f/4, 8k, raw. Aspect ratio 16:9.
- **Output**: `images/mansion-passage-mid.png` (1792x1024 PNG)
- **Cost**: $0.19

---

## Cost summary so far

| Date | Item | Cost |
|------|------|------|
| 2026-05-09 | nanobanana corridor end frame | $0.067 |
| 2026-05-09 | Seedance corridor-entry-v1.mp4 (5s 720p) | $1.51 |
| 2026-05-09 | gpt-image-2 doors outpaint | $0.13 |
| 2026-05-09 | gpt-image-2 forest-cards-v1 | $0.19 |
| 2026-05-09 | gpt-image-2 mansion-gates | $0.19 |
| 2026-05-09 | gpt-image-2 forest-cards-end | $0.19 |
| 2026-05-09 | gpt-image-2 forest-cards-start | $0.19 |
| 2026-05-09 | gpt-image-2 mansion-passage-mid | $0.19 |
| **Total** | | **$2.66** |

---

## 2026-05-09 — Part 1 production (assembly to v1)

Goal: complete intro arc (scenes 1, 2, 3, 4, 5, 5b) end-to-end with narration. Total 26.84s.

### [15:50] submit-seedance-forest-cards-fan

- **Inputs**: `images/werewolf-forest-cards-v1.png` (start), `images/werewolf-forest-cards-end.png` (end)
- **Tool**: seedance, `bytedance/seedance-2.0/image-to-video`
- **Params**: duration=5, generate_audio=false, resolution=720p, aspect_ratio=16:9
- **Prompt**: "The black-gloved hands holding a tight stack of dark cards smoothly fan the cards outward into a wide arc, like a magician revealing the deck. The fingers spread, the cards slide apart and bloom into a spread, faces still hidden showing the silver wolf-sigil backs. Subtle camera hold, just the hands moving. Slow, deliberate, gothic magician motion. Forest backdrop unchanged, candle/lantern flicker in the distance."
- **Request ID**: `019e0e4b-82de-7c52-be4f-3d3927ad0890`
- **Seed**: 1847308206
- **Output URL** (may expire): `https://v3b.fal.media/files/b/0a998e7c/S2PmZ-au9_QufrTUHOA2S_video.mp4`
- **Output file**: `clips/forest-cards-fan-v1.mp4` (1280x720, 24fps, 4.92s)
- **Cost**: $1.51

### [15:52] gen-elevenlabs-george-narration

Goal: 4 narration lines for Part 1, ElevenLabs George with pitch-down + hall echo voice processing.

- **Tool**: elevenlabs skill, voice George (`JBFqnCBsd6RMkjVDRZzb`)
- **Model**: `eleven_multilingual_v2` (NOT turbo per memory)
- **Voice settings**: `{stability: 0.5, similarity_boost: 0.75, style: 0.5}`
- **Lines**:
  - `audio/raw/scene1.mp3` ← "Some games you play to win."
  - `audio/raw/scene2.mp3` ← "Others, you play to survive."
  - `audio/raw/scene3.mp3` ← "Welcome to AI Werewolf."
  - `audio/raw/scene5.mp3` ← "Step inside."
- **Cost**: $0.05 (4 lines, ~85 chars total)

### [15:53] post-process-narration-pitch-echo

- **Filter**: `asetrate=44100*0.85,aresample=44100,aecho=0.8:0.7:40:0.3,aresample=48000`
- **Output format**: `-ar 48000 -ac 2 -c:a pcm_s16le` (48kHz stereo WAV per video-concat audio-sync rule)
- **Outputs**: `audio/processed/scene{1,2,3,5}.wav`
- **Measured durations**: scene1=2.116s, scene2=2.116s, scene3=2.225s, scene5=1.461s

### [15:54] build-ken-burns-clips (scenes 1, 3, 4, 5)

- **Tool**: ffmpeg (zoompan + 4K prescale)
- **Workflow per scene**:
  1. Prescale source 1792x1024 → 3840x2196 with lanczos, crop to 3840x2160
  2. zoompan with `z='1+(z_end-1)*on/(frames-1)'`, centered, output 1920x1080@25fps
  3. Output H.264 yuv420p high profile crf=18, no audio
- **Per scene**:

| Scene | Image | Dur | z_start → z_end | Output |
|-------|-------|-----|-----------------|--------|
| 1 | werewolf-forest-cards-start.png | 4s | 1.0 → 1.10 | clips/kenburns/scene1.mp4 |
| 3 | mansion-gates-werewolf-statues-start.png | 5s | 1.0 → 1.15 | clips/kenburns/scene3.mp4 |
| 4 | mansion-passage-mid.png | 4s | 1.0 → 1.15 | clips/kenburns/scene4.mp4 |
| 5 | mansion-doors-composited-feathered.png | 4s | **1.0 → 1.4** | clips/kenburns/scene5.mp4 |

- **Scene 5 zoom math**: source is 1792x1024, Seedance frame 1 occupies central 1280x720. zoom=1.4 lands viewport on exactly that central region. Frame-perfect seam to scene 5b.

### [15:55] convert-seedance-clips-to-project-spec

- Scene 2 (forest-cards-fan): 1280x720@24fps → 1920x1080@25fps via `fps=25,scale=1920:1080:flags=lanczos`. Output: `clips/kenburns/scene2.mp4` (4.92s)
- Scene 5b (corridor-entry-v1): same conversion. Output: `clips/kenburns/scene5b.mp4` (4.92s)

### [15:55] build-narration-track

- **Goal**: 26.84s narration track aligned to scene boundaries
- **Scene start times**: 0, 4.0, 8.92, 13.92, 17.92, 21.92
- **Narration delays** (ms): scene1@300, scene2@4500, scene3@10000, scene5@19000
- **Method**: ffmpeg amix with anullsrc base + adelay per line
  ```
  ffmpeg -y \
    -f lavfi -t 26.84 -i "anullsrc=r=48000:cl=stereo" \
    -i audio/processed/scene1.wav -i audio/processed/scene2.wav \
    -i audio/processed/scene3.wav -i audio/processed/scene5.wav \
    -filter_complex "[1:a]adelay=300|300[a1];[2:a]adelay=4500|4500[a2];[3:a]adelay=10000|10000[a3];[4:a]adelay=19000|19000[a4];[0:a][a1][a2][a3][a4]amix=inputs=5:duration=first:normalize=0[out]" \
    -map "[out]" -ar 48000 -ac 2 -c:a pcm_s16le audio/part1-narration.wav
  ```
- **Output**: `audio/part1-narration.wav` (26.84s, 48kHz stereo)
- **Note**: `normalize=0` keeps narration at full volume (default amix divides by N inputs, would dim).

### [15:56] concat-part1-and-mix

- **Concat**: hard concat (no transitions) of 6 clips: scene1, scene2, scene5b... wait reorder: scene1, scene2, scene3, scene4, scene5, scene5b. Filter: `concat=n=6:v=1:a=0`.
- **Mix narration**: ffmpeg map video from concat + audio from narration track, encode AAC 192k 48kHz stereo
- **Output**: `clips/part1-v1.mp4` (26.84s, 1920x1080@25fps, H.264 + AAC, 18MB)

### Verification (visual QA)

- Frame-perfect scene 5 → 5b seam: extracted t=21.91 (last frame of zoom) and t=21.93 (first frame of corridor). Side-by-side comparison confirms identical content (wolf knockers, lanterns, gothic stonework all line up). Cut is invisible.
- All scenes maintain 1920x1080@25fps consistently.
- Audio at 48kHz stereo throughout, no drift.

---

## Cost summary so far (updated)

| Date | Item | Cost |
|------|------|------|
| 2026-05-09 | nanobanana corridor end frame | $0.067 |
| 2026-05-09 | Seedance corridor-entry-v1.mp4 (5s 720p) | $1.51 |
| 2026-05-09 | gpt-image-2 doors outpaint | $0.13 |
| 2026-05-09 | gpt-image-2 forest-cards-v1 | $0.19 |
| 2026-05-09 | gpt-image-2 mansion-gates | $0.19 |
| 2026-05-09 | gpt-image-2 forest-cards-end | $0.19 |
| 2026-05-09 | gpt-image-2 forest-cards-start | $0.19 |
| 2026-05-09 | gpt-image-2 mansion-passage-mid | $0.19 |
| 2026-05-09 | Seedance forest-cards-fan-v1.mp4 (5s 720p) | $1.51 |
| 2026-05-09 | ElevenLabs George 4 lines (~85 chars) | $0.05 |
| **Total** | | **$4.24** |

---

## 2026-05-10 — Part 1 v2 (host reveal + shake fix + new narration)

After v1 review, three issues to fix:
1. Scene 1 too static — replace with gen-AI host hood-reveal clip
2. Slideshow zoom (Ken Burns) was shaky
3. Narration weak — rewrite to introduce host, set up game mechanics

### [15:43] gen-werewolf-forest-host-revealed (end frame for host reveal)

- **Tool**: gpt-image-2, `/v1/images/edits` (multi-ref)
- **Inputs**:
  - `images/werewolf-forest-cards-start.png` (cloaked figure, body/cloak/forest ref)
  - `images/werewolf-host-table-whiskey-start.jpg` (wolf-headed host character ref)
- **Prompt** (verbatim):
  > Reference images: the first shows a black-cloaked figure standing in a dark forest at twilight, hood up completely obscuring the face, intricate embossed cloak fabric, gloved hands folded together, warm lantern glow visible through bare trees in the background. The second shows the wolf-headed host character — a powerful werewolf with dark grey/black fur, intense intelligent yellow eyes, a sharp wolf snout. Generate a NEW image: the SAME cloaked figure from the first reference, now stepped slightly closer to the camera, with the HOOD THROWN BACK off the head and falling onto the shoulders, and the wolf head from the second reference clearly REVEALED. The werewolfs face — same dark fur, same intense eyes, same character — looks directly into the camera. The figure still wears the same heavy black embossed cloak. Same dark forest background, same bare gnarled trees, same warm lantern backlight bleeding through fog as the first reference. Cinematic, gothic, mysterious, photorealistic. Shot on Canon EOS R5, 50mm, f/2.8, 8k, raw. Aspect ratio 16:9.
- **Output**: `images/werewolf-forest-host-revealed.png` (1792x1024 PNG)
- **Tokens**: 3230 input (2987 image + 243 text), 5063 output
- **Cost**: $0.19

### [15:44] submit-seedance-host-reveal

- **Inputs**: `images/werewolf-forest-cards-start.png` (start), `images/werewolf-forest-host-revealed.png` (end)
- **Tool**: seedance, `bytedance/seedance-2.0/image-to-video`
- **Params**: duration=6, generate_audio=false, resolution=720p, aspect_ratio=16:9
- **Prompt**: "The hooded cloaked figure stands still for a moment in the dark forest, then steps slowly toward the camera. With deliberate motion, a black-gloved hand rises and grasps the edge of the hood, then smoothly pulls the hood back off the head. The hood falls onto the shoulders, revealing the wolf-headed host beneath — dark fur, intense yellow eyes locking with the camera. The wolf face holds the gaze, predatory and intelligent. Slow, cinematic, no cuts. Lantern flicker in the background. Subtle ambient mist."
- **Request ID**: `019e136a-a84b-7e53-828e-d3c612a5aead`
- **Seed**: 1719798134
- **Output URL** (may expire): `https://v3b.fal.media/files/b/0a99b00d/4ShgdPWArUX_NaxnZ-xK4_video.mp4`
- **Output file**: `clips/host-reveal-v1.mp4` (1280x720, 24fps, 5.92s) → `clips/kenburns_v2/scene1.mp4` (1920x1080, 25fps after conversion)
- **Cost**: $1.81 (6s @ 720p)

### [15:43] regen-narration-v2 (ElevenLabs George)

- **Tool**: elevenlabs, voice George (`JBFqnCBsd6RMkjVDRZzb`), model `eleven_multilingual_v2`, settings stability=0.5/sim=0.75/style=0.5
- **Lines** (raw → processed via `asetrate=44100*0.85,aresample=44100,aecho=0.8:0.7:40:0.3,aresample=48000`, 48kHz stereo):
  - `audio/processed/scene1_v2.wav` ← "Welcome to AI Werewolf." (2.116s)
  - `audio/processed/scene2_v2.wav` ← "Before we begin, pick a card to know your destiny." (3.537s)
  - `audio/processed/slideshow_v2.wav` ← "A card defines your role, your team — a werewolf, or a villager. The villagers are many, but blind, never knowing who's who. The werewolves are few — but they know each other. They hide. They hunt. Only one team survives." (17.851s)
- **Cost**: $0.10

### [15:44] rebuild-ken-burns-v2 (anti-shake)

**Root cause of v1 shake**: zoompan was rendering directly at 1920x1080 output. Per-frame zoom delta for small-zoom scenes (0.001/frame at 1.0→1.10) was below sub-pixel precision at that resolution → integer rounding → visible jitter.

**Fix**: prescale source to 8K (per gpt-image-2 memory rule), zoompan output at 4K (s=3840x2160) for higher precision motion, then separate lanczos downscale to 1920x1080. The downscale anti-aliases the integer rounding, smoothing motion.

```bash
ken_burns_v2() {
  local img="$1"; local out="$2"; local dur="$3"; local z_end="$4";
  local fps=25; local frames=$(awk "BEGIN{print int($dur*$fps)}");
  local pre="/tmp/$(basename $out .mp4)_pre8k.png";
  ffmpeg -y -i "$img" -vf "scale=7680:-1:flags=lanczos,crop=7680:4320" "$pre";
  ffmpeg -y -loop 1 -framerate $fps -i "$pre" \
    -vf "zoompan=z='1+(${z_end}-1)*on/(${frames}-1)':d=${frames}:x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':s=3840x2160:fps=${fps},scale=1920:1080:flags=lanczos" \
    -frames:v ${frames} \
    -c:v libx264 -pix_fmt yuv420p -profile:v high -preset medium -crf 18 -movflags +faststart \
    -an "$out";
}
```

| Scene | Image | Dur | z_end | Output |
|-------|-------|-----|-------|--------|
| 3 | mansion-gates-werewolf-statues-start.png | 5s | 1.18 (was 1.15) | clips/kenburns_v2/scene3.mp4 |
| 4 | mansion-passage-mid.png | 4s | 1.18 (was 1.15) | clips/kenburns_v2/scene4.mp4 |
| 5 | mansion-doors-composited-feathered.png | 4s | 1.4 (unchanged — frame-perfect seam) | clips/kenburns_v2/scene5.mp4 |

Slight zoom bumps for scenes 3 and 4 (1.15 → 1.18) add visible motion, making any residual jitter less perceptible.

### [15:47] assemble-part1-v2

- **Scene timeline** (cumulative):

| Scene | Start | End | Type | Notes |
|-------|-------|-----|------|-------|
| 1 | 0 | 5.92 | Seedance host reveal | hood pull, face reveal at end |
| 2 | 5.92 | 10.84 | Seedance forest cards fan | unchanged from v1 |
| 3 | 10.84 | 15.84 | Ken Burns gates | rebuilt anti-shake |
| 4 | 15.84 | 19.84 | Ken Burns passage | rebuilt anti-shake |
| 5 | 19.84 | 23.84 | Ken Burns doors | rebuilt anti-shake, zoom 1.0→1.4 |
| 5b | 23.84 | 28.76 | Seedance corridor | unchanged from v1 |
| **Total** | | **28.76s** | | |

- **Narration positions**: scene1_v2@t=4.0s (lands on face reveal), scene2_v2@t=6.5s, slideshow_v2@t=10.84s (covers scenes 3-5b in one block)
- **Hard concat** (no transitions), output `clips/part1-v2-video-only.mp4`
- **Mix**: video + narration WAV → AAC 192k → `clips/part1-v2.mp4` (22MB)

### Verification
- Frame-perfect scene 5 → 5b seam preserved (t=23.83 vs t=23.85: visually identical)
- Host reveal motion arc lands cleanly: t=0.5 hood up → t=3.0 hands grasping hood → t=5.5 wolf face revealed
- Slideshow scenes 3, 4, 5 motion smoother (subjective; needs full playback for verification)

---

## Cost summary so far (updated)

| Date | Item | Cost |
|------|------|------|
| 2026-05-09 | nanobanana corridor end frame | $0.067 |
| 2026-05-09 | Seedance corridor-entry-v1.mp4 | $1.51 |
| 2026-05-09 | gpt-image-2 doors outpaint | $0.13 |
| 2026-05-09 | gpt-image-2 forest-cards-v1 | $0.19 |
| 2026-05-09 | gpt-image-2 mansion-gates | $0.19 |
| 2026-05-09 | gpt-image-2 forest-cards-end | $0.19 |
| 2026-05-09 | gpt-image-2 forest-cards-start | $0.19 |
| 2026-05-09 | gpt-image-2 mansion-passage-mid | $0.19 |
| 2026-05-09 | Seedance forest-cards-fan-v1.mp4 | $1.51 |
| 2026-05-09 | ElevenLabs George v1 (4 lines) | $0.05 |
| 2026-05-10 | gpt-image-2 host-revealed end frame | $0.19 |
| 2026-05-10 | Seedance host-reveal-v1.mp4 (6s) | $1.81 |
| 2026-05-10 | ElevenLabs George v2 (new narration) | $0.10 |
| **Total** | | **$6.34** |

---

## TODO (next steps in production order)

1. Regenerate the 5 missing intro images (forest cards x3, mansion gates, mansion passage). Fresh prompts — no record of original prompts.
2. Generate 3 role images (Doctor, Detective, Maniac) — OpenAI gpt-image-2.
3. Finalize narration text → ElevenLabs George (final voice) → measure timings.
4. Generate 2 remaining Seedance clips (forest interpolation, host welcome ~8s).
5. Build Ken Burns slideshow segments.
6. Capture app demo on aiwerewolf.net.
7. Assemble final cut.
