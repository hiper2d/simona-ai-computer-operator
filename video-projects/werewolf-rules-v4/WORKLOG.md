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

## Gap — v3 and v4 iterations not logged

Between 2026-05-10 (v2) and 2026-05-19, Part 1 went through v3 and v4 without WORKLOG entries. Artifacts that exist on disk: `clips/part1-v{3,4}.mp4`, `clips/kenburns_v{3,4}/`, `audio/part1-narration-v{3,4}.wav`, `audio/raw/scene1_slow.mp3`, `audio/processed/scene1_slow.wav`, `clips/host-reveal-r2v-v1.mp4` (likely a reference-to-video re-roll of scene1). Prompts/params for these changes are not recorded — would need to be reverse-engineered from the files if reproducibility matters.

---

## 2026-05-19 — Part 1 v5 (faster mansion approach, scene-1-only voice)

Goal: tighten the Ken Burns slideshow (scenes 3, 4, 5) and drop all narration except the scene-1 host-reveal line. No transcript rewrite this round — that comes next.

### [<time>] ken-burns-v5-rebuild (scenes 3, 4, 5 at 2s each)

- **Tool**: ffmpeg (same anti-shake recipe as v2 — 8K prescale → 4K zoompan → 1080 lanczos)
- **Per scene**:

| Scene | Image | Dur | z_end | Output |
|-------|-------|-----|-------|--------|
| 3 | mansion-gates-werewolf-statues-start.png | 2s | 1.18 | clips/kenburns_v5/scene3.mp4 |
| 4 | mansion-passage-mid.png | 2s | 1.18 | clips/kenburns_v5/scene4.mp4 |
| 5 | mansion-doors-composited-feathered.png | 2s | 1.4 (unchanged — frame-perfect seam to 5b) | clips/kenburns_v5/scene5.mp4 |

- **Cost**: $0
- **Notes**: scenes 1, 2, 5b reused from `kenburns_v4/` (no change).

### [<time>] build-narration-v5 (scene-1 voice only, rest silent)

- **Inputs**: `audio/part1-narration-v4.wav` (29.76s; first speech segment runs 0–7.08s per silencedetect at -40dB)
- **Method**: `atrim=0:7.08` → `afade=t=out:st=6.58:d=0.5` → amix over 22.76s anullsrc base, `normalize=0`
- **Output**: `audio/part1-narration-v5.wav` (22.76s, 48kHz stereo)
- **Notes**: Preserves the existing v4 scene-1 narration verbatim (no transcript change yet). Everything from 7.08s onward is silence.

### [<time>] assemble-part1-v5

- **Concat** (hard, no transitions): scene1 (6.92s) + scene2 (4.92s) + scene3 (2s) + scene4 (2s) + scene5 (2s) + scene5b (4.92s) = **22.76s**
- **Mux**: video copy + AAC 192k @ 48kHz stereo
- **Output**: `clips/part1-v5.mp4` (~21MB, 1920x1080@25fps)
- **Cost**: $0

### Open for next round

- Rewrite narration transcript (Alex flagged audio doesn't land — full rewrite, not tweaks)
- Decide whether shortened mansion approach reads as urgency or rush — review the cut

---

## 2026-05-19 — Part 1 v6–v12 (narration iteration, mostly kokoro)

Conversational iteration with Alex on the narration. Not every prototype is its own entry — this block summarizes the script evolution. Locked outcome shipped as v13.

### What we tried (all on the same v5 video)

- **v6**: kokoro `bm_george` at speed 1.0, sparse punctuation. Script: "A social deduction game. Two teams: villagers, and werewolves..." 12.2s treated → ~3.6s tail silence.
- **v6b / v6c**: same script, slower kokoro speed + ellipses for dramatic beats. v6c (speed 0.85) fit 15.5s exactly. Alex liked the kokoro voice; flagged that ellipses-as-pause kokoro produces feels flat (and would be far better on ElevenLabs).
- **v7 / v7b / v7c**: longer script with "Only the wolves know each other — but they're outnumbered" appended. Ran 16–19s — overran the 15.84s budget. v7c was kokoro at native speed 1.1 to fit.
- **v8**: trimmed script ("Pick a card to know your destiny..."), kokoro at 1.0. Fit cleanly at 15.07s. Alex flagged abrupt transition off "Welcome to AI Werewolf" — there was no real pause; the new audio overlapped scene 1's fade-out.
- **v9 / v9b**: Alex-authored rewrite — "Two teams, one goal: eliminate the other. Through voting, deception, alliances, and betrayal." v9 fit comfortably (12.1s, 3s tail). v9b added asymmetry beat → ran over.
- **v10**: tried adding kokoro ellipses to fill v9's tail. Sounded "weird" — kokoro doesn't theatricalize ellipses, just inserts dead silence. Confirmed we need real prosody.

### Key learnings from this round

- **kokoro is a script-prototyping tool only.** It measures word count vs duration well, but its pause/prosody control is limited to `--speed` and punctuation, with very flat results on ellipses. For final delivery, ElevenLabs George with SSML `<break>` tags is the right tool.
- **Pitch-down treatment slows audio ~18%.** `asetrate=44100*0.85` is the locked George character treatment; budget calculations must include this multiplier.
- **Locked Part 1 transcript** (after "Welcome to AI Werewolf"): "Pick a card to know your destiny — villager, or werewolf. Two teams, one goal: eliminate the other. Through voting, deception, alliances, and betrayal."

---

## 2026-05-19 — Part 1 v11/v12 (ElevenLabs George + loudness normalization)

### [time] elevenlabs-george-generation

- **Tool**: ElevenLabs `eleven_multilingual_v2`, voice George (`JBFqnCBsd6RMkjVDRZzb`), settings `stability=0.5, similarity_boost=0.75, style=0.5` (matches v2 locked config)
- **SSML**:
  > Pick a card to know your destiny. `<break time="0.5s"/>` Villager, or werewolf. `<break time="0.6s"/>` Two teams, one goal — eliminate the other. `<break time="0.4s"/>` Through voting, deception, alliances, and betrayal.
- **Outputs**:
  - `audio/elevenlabs_raw/narration-v11.mp3` — raw 11.33s
  - `audio/elevenlabs_raw/narration-v11-treated.wav` — pitch-down + echo treated, 13.37s, 48kHz stereo
  - `audio/elevenlabs_raw/scene1-welcome.mp3` + treated — fresh George read of "Welcome to AI Werewolf" (NOT used in final — kept for re-roll if needed)
- **Cost**: ~$0.06 ElevenLabs (logged to `api-spending.csv`)

### [time] loudness-normalization (v12)

Initial mix (v11) used a freshly generated scene-1 line. Alex feedback: keep the **original v4 scene-1 audio** (it works as-is) and just match the new narration's loudness to it.

- **Measurements**:
  - v4 scene 1 (0–7.08s): Integrated −20.5 LUFS, Peak −3.3 dBTP
  - New narration (treated): Integrated −25.1 LUFS, Peak −10.0 dBTP — ~4.6 LU quieter
- **Filter**: `loudnorm=I=-20.5:TP=-3.3:LRA=11:linear=true`
- **Output**: `audio/elevenlabs_raw/narration-v11-normalized.wav` — Integrated −20.6 LUFS (0.1 LU off target), Peak −4.4 dBTP
- **Notes**: Single-pass linear loudnorm — sufficient for matching. Two-pass would tighten peak by another ~1 dB but the gain isn't worth the complexity here.

---

## 2026-05-19 — Part 1 v13 (LOCKED) — slideshow speed-up + crossfade + final mix

### What changed from v12

1. **Slideshow scenes 3/4/5 trimmed to 1.5s each** (rendered as 1.48s = 37 frames @ 25fps). Was 2s in v5. Faster mansion approach matches narration pacing and removes ~1.5s of tail silence.
2. **0.5s dissolve crossfade between scene 2 (cards fan) and scene 3 (mansion gates)** — softens the otherwise-abrupt visual jump from gloved-hands-in-forest to wide mansion shot.
3. Total length: **20.72s** (was 22.76s in v5/v11/v12).

### [time] ken-burns-v6-rebuild (scenes 3, 4, 5 at 1.5s each)

Same anti-shake recipe as v2/v5 — 8K prescale → 4K zoompan → 1080 lanczos.

| Scene | Image | Dur | z_end | Output |
|-------|-------|-----|-------|--------|
| 3 | mansion-gates-werewolf-statues-start.png | 1.48s | 1.18 | clips/kenburns_v6/scene3.mp4 |
| 4 | mansion-passage-mid.png | 1.48s | 1.18 | clips/kenburns_v6/scene4.mp4 |
| 5 | mansion-doors-composited-feathered.png | 1.48s | 1.4 (frame-perfect seam to 5b unchanged) | clips/kenburns_v6/scene5.mp4 |

### [time] assemble-part1-v13 (xfade build)

- **Filter chain**:
  ```
  [scene1][scene2]concat=n=2[firstpair];
  [scene3][scene4][scene5][scene5b]concat=n=4[secondpart];
  [firstpair][secondpart]xfade=transition=fade:duration=0.5:offset=11.34,format=yuv420p[vout]
  ```
- **Output (video-only)**: `clips/part1-v13-video-only.mp4` — 20.72s, 1920x1080@25fps, H.264 yuv420p crf=18

### [time] final-mix (v13 audio)

- **Tracks**:
  - Scene 1 audio: `audio/part1-narration-v4.wav` atrim 0:7.08 (original v4 mix, untouched)
  - New narration: `audio/elevenlabs_raw/narration-v11-normalized.wav` (loudness-matched)
  - Silent 48kHz stereo base via anullsrc
- **Layout**: scene 1 placed at t=0; new narration `adelay=7350|7350` (lands at 7.35s, ends ~20.7s)
- **Output**: `audio/part1-narration-v13.wav`
- **Mux**: video copy + AAC 192k → `clips/part1-v13-locked.mp4`

### Locked artifacts

- **Final Part 1**: `clips/part1-v13-locked.mp4` (20.72s)
- **Building blocks** (kept for re-edit):
  - `clips/kenburns_v4/{scene1,scene2,scene5b}.mp4` — Seedance reused
  - `clips/kenburns_v6/{scene3,scene4,scene5}.mp4` — Ken Burns mansion approach
  - `clips/{corridor-entry-v1,forest-cards-fan-v1,host-reveal-v1,host-reveal-v2}.mp4` — original Seedance sources
  - `audio/elevenlabs_raw/{narration-v11.mp3,narration-v11-treated.wav,narration-v11-normalized.wav,scene1-welcome.mp3,scene1-welcome-treated.wav}`
  - `audio/part1-narration-v4.wav` — needed to extract scene 1 audio if rebuilding
  - `audio/part1-narration-v13.wav` — final mix
- **Locked transcript**:
  > "Welcome to AI Werewolf. [pause] Pick a card to know your destiny — villager, or werewolf. Two teams, one goal: eliminate the other. Through voting, deception, alliances, and betrayal."

### Cleanup (2026-05-19)

Moved superseded test artifacts to `_archive/` (reversible, not deleted):

- `_archive/clips/`: `corridor_{start,mid,end}.jpg`, `host-reveal-r2v-v1.mp4`, `kenburns_v1`, `kenburns_v2`, `kenburns_v3`, `kenburns_v5`, all `part1-v{1..12}*.mp4` intermediates and kokoro/EL test renders
- `_archive/audio/raw/`, `_archive/audio/processed/`: predate ElevenLabs final, kokoro intermediates
- `_archive/audio/`: all `part1-narration-v{2,3,5..12}.wav` intermediate mixes

---

## 2026-05-19 — Part 2 kick-off

Goal: ~8s host welcome — Seedance image-to-video from the host-table image, George narration.

### [time] part2-narration-generation

- **Script**: "I'm your host. `<break time="0.5s"/>` And yet... I might eat you. `<break time="0.8s"/>` But first, let me explain the rules."
- **Tool**: ElevenLabs `eleven_multilingual_v2`, voice George, same settings as Part 1
- **Output**: `audio/elevenlabs_raw/part2-host-welcome.mp3` (5.90s raw) → `part2-host-welcome-treated.wav` (6.98s pitch-down + echo)
- **Cost**: ~$0.04 ElevenLabs

### [time] part2-seedance-submit

- **Input**: `images/werewolf-host-table-whiskey-start.jpg` (2752x1536 JPEG)
- **Tool**: Seedance 2.0 image-to-video via fal.ai queue
- **Params**: `duration=8`, `resolution=720p`, `aspect_ratio=16:9`, `generate_audio=false`
- **Prompt** (verbatim):
  > The werewolf-headed host sits at the candlelit mahogany table. He looks up directly into the camera, intense yellow eyes locking with the viewer. He grasps the crystal whiskey tumbler, raises it slightly in a knowing, sardonic toast, then sets it back down. His lips curl into a faint, predatory smile revealing a hint of sharp teeth. Deliberate, calm, unsettling. Candle flames flicker softly. No cuts. Cinematic, gothic, slow.
- **fal upload URL** (may expire): `https://v3b.fal.media/files/b/0a9addff/u1EBgZS9-kFdpF1pfMn0Q_werewolf-host-table-whiskey-start.jpg`
- **Request ID**: `019e417f-c8c2-7ba0-8535-c095188833c4`
- **Status URL**: `https://queue.fal.run/bytedance/seedance-2.0/requests/019e417f-c8c2-7ba0-8535-c095188833c4`
- **Expected cost**: ~$2.40 (8s @ 720p)

### Part 2 iteration trail (what worked, what didn't)

Part 2 went through several aborted approaches before locking. Recording the *failure modes* so we don't repeat them:

1. **Seedance i2v, silent, George dub** (`part2-host-welcome-v1.mp4`) — host raises glass + sly grin, no talking. Cost $2.42. Alex rejected: wanted the host to actually speak.
2. **LTX-2.3 fast** (`part2-ltx-v1.mp4`) — talking head with LTX's native AI voice. Cost $0.32. Pacing was better than Seedance i2v, but LTX cannot accept a custom voice and its voice clashed with George.
3. **Seedance i2v with `generate_audio=true`** (`part2-seedance-talking-v1.mp4`) — host talks with Seedance's own voice, real lip sync. Cost $2.12. Mouth motion good but wrong voice.
4. **Dub George over Seedance talking visual** (`part2-v2.mp4`, `part2-v3.mp4`) — strip Seedance audio, mux normalized George. Lip sync broken because mouth motion was locked to Seedance's syllables, not George's. **Don't do this — naive audio swap on a video with existing mouth motion never works.**
5. **fal-ai/sync-lipsync swap** (`part2-lipsync-v1.mp4`) — feed the Seedance talking visual + George WAV to a lip-sync model. Cost $0.10. Mushy/glitchy mouth — sync-1 is trained on human faces and the wolf snout is out of distribution. **Lip-sync-swap models are unreliable on stylized/non-human characters; don't try this route on creature characters.**
6. **Seedance r2v with wrong schema** (`part2-r2v-v1.mp4`) — submitted `audio_url` (singular), which the model silently ignored. Got back a 10.1s video with a fully synthesized different voice. Cost $2.12 wasted.
7. **Seedance r2v with correct schema** (`part2-v-locked.mp4`) — `image_urls` + `audio_urls` (plural arrays) + explicit `@Image1`/`@Audio1` references in the prompt. Lip-syncs to the supplied George audio with the wolf-host visual. Cost $2.12. **Locked.**

### [time] part2-r2v-locked-build

- **Endpoint**: `bytedance/seedance-2.0/reference-to-video` (NOT image-to-video)
- **Inputs**:
  - `image_urls`: [host table image fal URL]
  - `audio_urls`: [George "yes" treated+normalized WAV fal URL]
- **Prompt** (verbatim, with @ asset references):
  > The werewolf-headed host from @Image1 speaks the dialogue from @Audio1 with synchronized lip movement matching every word and pause exactly. Preserve the exact voice character, timing, and pauses from @Audio1 — do not regenerate the voice. He sits at the candlelit mahogany table with a crystal whiskey tumbler. Calm, relaxed, conversational manner — never threatening, never menacing. Candle flames flicker softly in the background. Cinematic, intimate, gothic.
- **Params**: `duration=7`, `resolution=720p`, `aspect_ratio=16:9`, `generate_audio=true`
- **Request ID**: `019e432b-378e-75c0-bdcc-394a2302b331`
- **Output URL** (may expire): `https://v3b.fal.media/files/b/0a9ae90b/hpcPnNCVLQlpNLoVzNYzt_video.mp4`
- **Raw output**: 7.08s, 1280x720, 24fps, 44.1kHz AAC. Three speech segments with natural mid-pauses (silencedetect confirmed at 0.5s and 0.8s).
- **Conversion to project spec**: `fps=25,scale=1920:1080:flags=lanczos` + audio `loudnorm=I=-20.5:TP=-3.3:LRA=11:linear=true,aformat=sample_rates=48000:channel_layouts=stereo` + AAC 192k @ 48kHz. Final: 7.10s, 1920x1080, 25fps, 48kHz AAC.
- **Output**: `clips/part2-v-locked.mp4`
- **Cost**: $2.12 (logged)
- **Seed**: `193628540`

### Locked transcript (Part 2)

> "I'm your host. [0.3s break] And yes, I might eat you. [0.4s break] But first, let me explain the rules."

Audio source: `audio/elevenlabs_raw/part2-host-welcome-fix.mp3` → `part2-host-welcome-fix-normalized.wav` (treated with `asetrate=44100*0.85,aresample=44100,aecho=0.8:0.7:40:0.3,aresample=48000` then loudnorm to −20.5 LUFS to match Part 1).

---

## 2026-05-19 — Combined Parts 1+2 lock

### [time] assemble-parts1-2

Combined Part 1 (20.72s) + Part 2 (7.10s) with a 0.4s crossfade at the seam. Rationale for crossfade: Part 1 ends on the corridor with warm doorway light, Part 2 opens on the candlelit host room — both warm-orange palettes. Fade reads as "stepping through the door."

- **Filter**:
  ```
  [0:v][1:v]xfade=transition=fade:duration=0.4:offset=20.32,format=yuv420p[vout]
  [0:a][1:a]acrossfade=d=0.4[aout]
  ```
- **Output**: `clips/parts1-2-locked.mp4` — 27.42s, 1920x1080@25fps, AAC 48kHz stereo

### Cleanup (Part 2 round, 2026-05-19)

Moved to `_archive/`:
- `clips/part2-{v1,v1-video-only,v2,v2-video-only,v3,seedance-talking-v1,ltx-v1,lipsync-v1,r2v-v1,r2v-v1-spec,host-welcome-v1}.mp4`, `part2-r2v-v2.mp4` (raw before spec conversion)
- `audio/elevenlabs_raw/part2-host-welcome.{mp3,treated.wav,normalized.wav}` (the "yet" version, superseded by "yes")
- `audio/part2-narration-v{1,2,3}.wav` (intermediate mixes)

Surviving Part 2 building blocks:
- `clips/part2-v-locked.mp4` — final
- `audio/elevenlabs_raw/part2-host-welcome-fix.{mp3,_normalized.wav}` — George "yes" source + treated/normalized

---

## 2026-05-19 — Skill updates

Documented r2v + lip-sync findings in the production tooling:
- `.claude/skills/seedance/SKILL.md` — added r2v endpoint, plural-array schema (`image_urls`, `audio_urls`), `@Image1`/`@Audio1` prompt references, and a "Picking the right endpoint" decision section. Includes explicit warning that singular `audio_url` is silently ignored.
- `.claude/skills/ltx-video/SKILL.md` — added "When to use LTX vs Seedance" — LTX is drafts only, can't accept custom voice; Seedance r2v is the locked-voice path.
- Both skills now warn against `fal-ai/sync-lipsync` / `latentsync` for non-human / stylized faces.

---

## 2026-05-23 — Part 3 visual pivot: chalk-on-slate schematic slideshow

**Why the pivot**: prior Part 3 iterations were ultra-realistic ("AI bots around a table with a human", `slideshow-1-friendly-v{1,2,3}.png` and `slideshow-2-hidden-wolves-v1.png`). Beautiful but cognitively noisy — 8 unique robots, name tags, cards, central human, lighting drama. Eye can't find the read. Alex called for schematic.

**Direction explored, then locked**: chalk drawings on an aged slate blackboard in a heavy gothic wood frame, warm candlelight (real lit candle in frame on the left), hand-drawn imperfect chalk strokes. Compatible with the gothic candlelit host scene preceding it because the chalkboard literally sits in the same Victorian study; reads as "the host is teaching you the rules at his table."

Decision tree before locking style:
- Tarot card spread → rejected (Alex picked chalk)
- Woodcut / engraving → rejected
- Silhouette / shadow play → rejected
- **Chalk on blackboard** → picked. Alex flagged risk of lecture-hall feel; we mitigated by anchoring in slate (not green), gothic frame, warm candle in-frame, hand-drawn imperfect chalk.

### [12:27] gen-chalk-test-v1 (style probe — villagers vs wolves overview)

- **Tool**: openai-image skill, gpt-image-2 `/v1/images/generations` (text-to-image)
- **Params**: `size=1792x1024`, `quality=medium`
- **Prompt** (verbatim):
  > A close-up shot of an aged dark slate blackboard mounted in a heavy carved dark wood gothic frame, leaning against a wall in a candlelit Victorian study. The board surface is genuine deep charcoal-black slate with subtle grey streaks and faint chalk-dust residue (NOT modern green chalkboard). Warm orange candlelight from off-frame on the left bathes the surface, casting soft amber highlights along one edge while leaving the right side in deeper shadow. On the slate, hand-drawn in white chalk: on the LEFT side, a loose cluster of 7 small simple stick-figure villagers — round heads, simple bodies, slightly different sizes, drawn imperfectly like a teachers quick board sketch. Above them the word VILLAGERS written in chalk capital letters. On the RIGHT side, a smaller cluster of 2 stick figures with clear triangular wolf ears and pointed snouts. Above them the word WOLVES written in chalk capital letters. Between the two groups, a vertical wavy chalk line dividing them. The chalk strokes are imperfect, slightly smudged in places, drawn quickly by hand. ONLY these two words appear on the board — no other text, no other labels, no arrows, no decorations. Dark, gothic, atmospheric. Visible chalk dust particles in the warm candlelight. Subtle vignette. Shot on Canon EOS R5, 50mm, f/4, 8k, raw. Aspect ratio 16:9.
- **Output**: `images/slideshow-chalk-test-v1.png` → later archived to `_archive/images-chalk-rejected/` after high-quality re-roll
- **Cost**: $0.13
- **Notes**: First try nailed it. Bonus: model put a real lit candle on a holder at the bottom-left of the frame, partially in-shot — adds depth and ties visually back to the host's candlelit table.

### [13:10] gen-chalk-doctor-test (single-figure case probe)

Multi-figure case worked; needed to verify single-figure case wouldn't feel too sparse on a wide board.

- **Tool**: gpt-image-2 `/v1/images/generations`
- **Params**: `size=1792x1024`, `quality=medium`
- **Prompt** (verbatim):
  > [full chalkboard scene description as above]... a single simple stick-figure villager lying horizontal across the lower middle of the board (eyes drawn as X marks, looking unconscious or sleeping). Standing over them, leaning forward, a second stick figure wearing a wide doctors hat with a chalk-drawn cross symbol on it, holding a small bottle of medicine extended toward the lying figure. Above this scene the word DOCTOR written in chalk capital letters. A small chalk heart symbol floats above the lying villager. The chalk strokes are imperfect, slightly smudged in places, drawn quickly by hand like a teachers quick board sketch. ONLY the word DOCTOR appears as text on the board — no other labels, no captions...
- **Output**: `images/slideshow-chalk-doctor-test.png` → later archived
- **Cost**: $0.13
- **Notes**: Single-figure case works. Model added a small religious crest at top of frame on its own — keeps the gothic mood. Style confirmed for full set.

### [13:21–13:22] gen-7-final-slides (parallel batch, high quality)

After Alex approved the style, regenerated the 2 test images at high quality + generated the remaining 5 in parallel. 7 simultaneous `/v1/images/generations` calls.

- **Tool**: gpt-image-2 `/v1/images/generations`
- **Params**: `size=1792x1024`, `quality=high` for all
- **Shared scene preamble** (every prompt opened with): aged dark slate blackboard, heavy carved dark wood gothic frame, candlelit Victorian study, warm orange off-frame candlelight from the left, real lit candle on a holder bottom-left partially in frame, white chalk on charcoal-black slate (NOT green chalkboard), imperfect strokes, slight smudges, visible chalk dust in candlelight, subtle vignette. Shot on Canon EOS R5, 50mm, f/4, 8k, raw. Aspect ratio 16:9.

| Slug | File | Subject prompt fragment | Verdict |
|------|------|-------------------------|---------|
| `overview-v1` | `slideshow-chalk-overview-v1.png` | 7 stick-figure villagers LEFT (label VILLAGERS) + 2 wolf-headed figures RIGHT (label WOLVES) + vertical wavy chalk divider | ✅ locked |
| `day-vote-v1` | `slideshow-chalk-day-vote-v1.png` | top-down circle of 6 villagers, one pointing across the circle, sun upper-left, DAY label | ✅ locked (Alex prefers top-down over later side-view re-roll) |
| `night-hunt-v1` | `slideshow-chalk-night-hunt-v1.png` | 3 sleeping villagers (drawn as small heads with closed-eye dashes, gpt-image-2 wouldn't render full lying stick bodies), 2 wolves stalking from right, NIGHT label, moon upper-left | ✅ locked |
| `hidden-wolves-v1` | `slideshow-chalk-hidden-wolves-v1.png` | row of 7 identical stick villagers with question marks above each head, 2 of them with subtle triangular wolf ears (3rd and 7th), WHO? label | ✅ locked |
| `doctor-v1` | `slideshow-chalk-doctor-v1.png` | doctor with hat + cross + medicine bottle leaning over unconscious villager (X eyes), heart symbol above, DOCTOR label | ✅ locked |
| `detective-v1` | `slideshow-chalk-detective-v1.png` | villager holding magnifying glass examining a wolf-headed figure, exclamation mark above the wolf, DETECTIVE label | ✅ locked |
| `maniac-v1` | `slideshow-chalk-maniac-v1.png` | hooded figure with knife + two dead villagers (X eyes) at feet, MANIAC label | ❌ archived — wrong concept (maniac abducts, doesn't kill) |

- **Cost**: 7 × $0.19 = **$1.33**

### [13:38–13:40] re-rolls

**Day-vote v2** (side view with row of stick figures, leftmost pointing across with dashed line):
- Prompt explicitly forced SIDE VIEW with row of identical stick figures, leftmost arm raised pointing across, sun upper-left.
- Output: `slideshow-chalk-day-vote-v2.png` → archived
- Cost: $0.19
- Outcome: Composition clean and consistent with the doctor/detective row-of-figures style, but Alex preferred v1's top-down style as more graphically interesting (rejected this re-roll).

**Night-hunt v2** (lying stick figures with bodies, matching doctor slide):
- Prompt explicitly forced "LYING HORIZONTAL ... full stick figure bodies ... eyes drawn as small X marks or short closed-eye dashes". gpt-image-2 STILL refused — defaulted again to small head-only representations with closed-eye dashes and breath/Z motion lines.
- Output: `slideshow-chalk-night-hunt-v2.png` → archived
- Cost: $0.19
- Outcome: Visually similar story to v1; Alex preferred v1 (composition tighter).
- **Learning**: gpt-image-2 will not draw stick figures lying horizontal as full bodies — it abstracts "sleeping/lying" into head-only with closed eyes. Don't waste re-rolls trying to force it; accept the head-only convention.

**Maniac v2** (abduction concept — no weapon, dragging villager into darkness):
- Prompt explicitly: no knife, no blade, no weapon, no dead bodies, no X-eye corpses. Hooded figure with arms wrapped around a villager, lifting/dragging them backward, motion dashes trailing left, vertical chalk scratch marks on right edge representing the void.
- Output: `images/slideshow-chalk-maniac-v2.png` ✅ locked
- Cost: $0.19

### Final locked set (in `images/`, 7 chalk slides)

| # | File | Used for script scene |
|---|------|----------------------|
| 1 | `slideshow-chalk-overview-v1.png` | Scene 7 — "Two teams. Villagers, and werewolves." |
| 2 | `slideshow-chalk-day-vote-v1.png` | Scene 8 — Day vote |
| 3 | `slideshow-chalk-night-hunt-v1.png` | Scene 9 — Night hunt |
| 4 | `slideshow-chalk-hidden-wolves-v1.png` | Scene 10 — Hidden wolves |
| 5 | `slideshow-chalk-doctor-v1.png` | Scene 11 — Doctor |
| 6 | `slideshow-chalk-detective-v1.png` | Scene 12 — Detective |
| 7 | `slideshow-chalk-maniac-v2.png` | Scene 13 — Maniac (**abducts**, not kills — narration line in script.md updated to match) |

Archived (in `_archive/images-chalk-rejected/`):
- `slideshow-chalk-test-v1.png` (medium-quality test, superseded by `overview-v1`)
- `slideshow-chalk-doctor-test.png` (medium-quality test, superseded by `doctor-v1`)
- `slideshow-chalk-day-vote-v2.png` (rejected re-roll)
- `slideshow-chalk-night-hunt-v2.png` (rejected re-roll)
- `slideshow-chalk-maniac-v1.png` (wrong concept — killer not abductor)

### Session cost (2026-05-23)

| Item | Cost |
|------|------|
| 2 medium-quality style probes (overview, doctor) | $0.26 |
| 7 high-quality first-pass slides | $1.33 |
| 3 re-rolls (day-vote v2, night-hunt v2, maniac v2) | $0.57 |
| **Session total** | **$2.16** |

---

---

## 2026-05-23 (continued) — Part 3 restructure: chunked sub-parts (3a/3b/3c) + bridge

After the 7-slide chalk batch (above), the scene plan was re-architected. Instead of a single Part 3 with slide-per-narration-line (per old `script.md`), Part 3 became **three thematic sub-chunks** with their own narration blocks + multi-slide slideshows, plus a Seedance r2v host bridge between 3b and 3c. This pacing dramatically out-performed the old plan in playback.

### Final scene structure (locked)

| Chunk | Duration | Content |
|---|---|---|
| Parts 1+2 | 27.4s | Intro arc + host welcome (unchanged from 2026-05-19 lock) |
| Part 3a | 16.0s | "Villagers vs werewolves" — 3 chalk slides |
| Part 3b | 16.05s | "Day / night phases" — 4 chalk slides |
| Bridge | 8.10s | Seedance r2v host: "But the village has tricks of its own..." |
| Part 3c | 52.24s | "Special roles + all villagers" — 7 chalk slides |
| Outro | 6.10s | Seedance r2v host: "Now... you know the rules. The hunt begins." |
| **Total locked** | **2:05.04** | `clips/parts1-5-locked.mp4` |

### 4 additional chalk images for the expanded 3a/3b/3c

Generated using the same `openai-image` chalk-on-slate template (now canonicalized in that skill). All `quality=high`, `size=1792x1024`, $0.19 each.

| Slug | File | Used in |
|------|------|---------|
| `wolves-know-v1` | `images/slideshow-chalk-wolves-know-v1.png` | 3a slide 3 — "THEY KNOW" — 2 wolf-headed stick figures making eye contact with dashed line + paw print between |
| `aftermath-v1` | `images/slideshow-chalk-aftermath-v1.png` | 3b slide 4 — "GONE" — 4 standing villagers around a fallen one + dawn sun |
| `all-villagers-v1` | `images/slideshow-chalk-all-villagers-v1.png` | 3c slide 7 — "ALL VILLAGERS" — row of 5 stick figures, 3 with role symbols above (cross/magnifying glass/hood) |
| `doctor-kills-v1` | `images/slideshow-chalk-doctor-kills-v1.png` | 3c slide 2 — "MISTAKE" — doctor with syringe walking away from dead villager + skull + question mark |
| `detective-kills-v1` | `images/slideshow-chalk-detective-kills-v1.png` | 3c slide 4 — "SHOOTS ONCE" — detective with magnifying glass + revolver, dashed bullet line to falling target |
| `maniac-both-die-v1` | `images/slideshow-chalk-maniac-both-die-v1.png` | 3c slide 6 — "BOTH DIE" — wolf attacking maniac, abducted villager dead below, dashed line linking them |

### ElevenLabs narrations (all George `JBFqnCBsd6RMkjVDRZzb`, model `eleven_multilingual_v2`, settings `stability=0.5, similarity_boost=0.75, style=0.5`)

All raw output then treated with `asetrate=44100*0.85,aresample=44100,aecho=0.8:0.7:40:0.3,aresample=48000,loudnorm=I=-20.5:TP=-3.3:LRA=11:linear=true` and saved as 48kHz stereo WAV.

**Part 3a** (`audio/elevenlabs_raw/part3a-treated.wav`, treated 15.99s, cost $0.07):
> Villagers — and werewolves. `<break time="0.6s"/>` The villagers are many. `<break time="0.3s"/>` But blind. `<break time="0.4s"/>` They don't know who's who. `<break time="0.7s"/>` The werewolves are few. `<break time="0.3s"/>` But they know each other. `<break time="0.5s"/>` And they hide. `<break time="0.3s"/>` In plain sight.

**Part 3b** (`audio/elevenlabs_raw/part3b-treated.wav`, treated 16.05s, cost $0.07):
> Each day, the village debates. `<break time="0.4s"/>` Suspicions. `<break time="0.3s"/>` Accusations. `<break time="0.4s"/>` A vote is cast — and one of you is gone. `<break time="0.8s"/>` Each night, the wolves move. `<break time="0.5s"/>` Someone wakes up. `<break time="0.4s"/>` And one of you doesn't.

**Bridge** (`audio/elevenlabs_raw/bridge3bc-treated.wav`, treated 7.69s, cost $0.05):
> But the village has tricks of its own. `<break time="0.5s"/>` Some... `<break time="0.4s"/>` act at night. `<break time="0.5s"/>` They change everything.

**Part 3c v3** (`audio/elevenlabs_raw/part3c-v3-treated.wav`, treated 52.22s, cost $0.10) — *v1 and v2 superseded after Alex added "detective can also kill" and "all three count as villagers" beats*:
> The Doctor heals one player each night. `<break time="0.3s"/>` That player can't die. `<break time="0.4s"/>` Never the same one twice. `<break time="0.5s"/>` And once per game — `<break time="0.3s"/>` the Doctor can kill instead. `<break time="0.4s"/>` A medical mistake. `<break time="0.9s"/>` The Detective picks a player. `<break time="0.4s"/>` Learns one thing — good, or bad. `<break time="0.4s"/>` Bad means wolf. `<break time="0.3s"/>` Or Maniac. `<break time="0.5s"/>` And once per game — `<break time="0.3s"/>` the Detective can kill too. `<break time="0.9s"/>` The Maniac picks a player each night. `<break time="0.4s"/>` The victim vanishes 'til morning. `<break time="0.4s"/>` Untouchable. `<break time="0.5s"/>` But — `<break time="0.3s"/>` if the Maniac dies, the captive dies too. `<break time="0.9s"/>` And here's the catch. `<break time="0.4s"/>` All three count as villagers. `<break time="0.4s"/>` Same side. `<break time="0.4s"/>` Same goal: kill every wolf. `<break time="0.5s"/>` Even the Maniac.

**Outro** (`audio/elevenlabs_raw/outro-treated.wav`, treated 4.96s, cost $0.05):
> Now... `<break time="0.5s"/>` you know the rules. `<break time="0.7s"/>` The hunt begins.

### Slideshow timing pattern (used for all three 3a/3b/3c)

Run `silencedetect=noise=-30dB:d=0.5` on the treated WAV. Pauses >1.0s mark slide-section boundaries; pauses 0.7-1.0s are sub-beat moments. Map each visual slide to span between two pauses. Build scenes at those exact durations (slide_dur = section_dur + 0.5s for xfade overlap; sum to total = audio_duration + (N-1)*xfade_duration).

All scenes built with the locked anti-shake recipe: prescale 1792x1024 → 8K → `zoompan z=1+(zend-1)*on/(frames-1)` at 4K → `scale=1920:1080:flags=lanczos` → H.264 yuv420p high crf=18 @ 25fps, no audio.

Chunks assembled with `xfade=fade:duration=0.5` between slides + `acrossfade=d=0.5` (where audio exists). Top-level chunk files:
- `clips/part3/part3a-v3-swapped.mp4` (Alex's chosen order: overview → hidden-wolves → wolves-know)
- `clips/part3/part3b-v3.mp4` (day-topdown → day-pointing → night-hunt → aftermath)
- `clips/part3/part3c-v2.mp4` (doctor → mistake → detective → shoots-once → maniac-abducts → both-die → all-villagers)

### Seedance r2v jobs (bridge + outro)

Both use the same recipe as Part 2's locked clip: upload `images/werewolf-host-table-whiskey-start.jpg` + treated audio WAV to fal storage, submit to `bytedance/seedance-2.0/reference-to-video` with `image_urls` + `audio_urls` (plural) and `@Image1`/`@Audio1` references in the prompt. Output 1280x720@24fps + 44.1kHz audio → converted to 1920x1080@25fps + 48kHz AAC with `loudnorm=I=-20.5:TP=-3.3:LRA=11:linear=true` to match Parts 1/2.

**Bridge** (`clips/part3/bridge3bc-v1.mp4`, 8.10s, cost $2.42):
- Request ID: `019e563e-a980-7702-8f6e-88e6cd06f9fe`, seed `2044464666`
- Audio upload (may expire): `https://v3b.fal.media/files/b/0a9b65f3/aHbGROw_AEFRDFL_uMuQI_bridge3bc-treated.wav`
- Image upload (may expire): `https://v3b.fal.media/files/b/0a9b65f3/IJfqeRIWhgKjliv5h0EqS_werewolf-host-table-whiskey-start.jpg`
- Video output (may expire): `https://v3b.fal.media/files/b/0a9b6617/tFlw6-cASptSO1pOLLL5J_video.mp4`
- Params: `duration=8, resolution=720p, aspect_ratio=16:9, generate_audio=true`
- Prompt verbatim:
  > The werewolf-headed host from @Image1 speaks the dialogue from @Audio1 with synchronized lip movement matching every word and pause exactly. Preserve the exact voice character, timing, and pauses from @Audio1 — do not regenerate the voice. He sits at the candlelit mahogany table with a crystal whiskey tumbler. Calm, conversational, slightly amused — he hints at a secret. Brief subtle gesture with one hand toward the camera on the line 'tricks of its own'. Candle flames flicker softly in the background. Cinematic, intimate, gothic.

**Outro** (`clips/part3/outro-v1.mp4`, 6.10s, cost $1.81):
- Request ID: `019e5ab5-6260-7c51-b4ea-c293ae1c7152`, seed `1851109365`
- Audio upload (may expire): `https://v3b.fal.media/files/b/0a9b8335/WiUmgTjNVxv9iI2vECKUH_outro-treated.wav`
- Image: reused bridge upload URL above
- Video output (may expire): `https://v3b.fal.media/files/b/0a9b835e/KlhSmnjA5GO9qAtSLR4Lg_video.mp4`
- Params: `duration=6, resolution=720p, aspect_ratio=16:9, generate_audio=true`
- Prompt verbatim:
  > The werewolf-headed host from @Image1 speaks the dialogue from @Audio1 with synchronized lip movement matching every word and pause exactly. Preserve the exact voice character, timing, and pauses from @Audio1 — do not regenerate the voice. He sits at the candlelit mahogany table. On the word 'Now', he raises the crystal whiskey tumbler in a slow, knowing toast toward the camera and sets it back down. On 'you know the rules', his eyes lock with the camera. On 'The hunt begins', a subtle, predatory smile — the corners of his snout lift slightly, revealing a hint of teeth. He holds the look in silence after the line. Calm, conversational, slightly menacing. Candle flames flicker softly. Cinematic, intimate, gothic.

---

## 2026-05-24 — Full Parts 1-5 assembly (v1 → v6 lock)

Assembled `parts1-2-locked.mp4 + part3a + part3b + bridge + part3c + outro` end-to-end. Took 6 iterations to lock; the bugs and learnings are now also captured in `.claude/skills/ffmpeg/SKILL.md` ("Multi-chunk assembly pitfalls") and `.claude/skills/director/SKILL.md` ("Scene-change transition").

**v1** (`clips/parts1-3-v1.mp4`): naive xfade chain. Output reported as 118s but video stream only rendered 52s — Alex caught it ("there is no 3c part and there is no bridge part"). **Root cause:** `part3a-v3-swapped.mp4` had `format=duration` 15.99s but `stream:v duration` only 14.48s due to a `-t 16.05` flag that padded format without adding frames. xfade chain silently truncated past the first short stream. Also discovered same gap on `parts1-2-locked.mp4` (0.18s) and `bridge3bc-v1.mp4` (0.18s).

**v2** (`clips/parts1-3-v2.mp4`): rebuilt `part3a-v3-swapped.mp4` with scene durations summing exactly to audio length (overview 6.5s + hidden 5.5s + wolves-know 5.0s − 2×0.5s xfade = 16.0s). Added `tpad=stop_mode=clone:stop_duration=0.2` on parts1-2 and bridge in the assembly filter to mask their small video-shorter-than-audio gaps. Worked: video and audio durations matched at 118.2s. ✓

**v3** (after adding outro, `clips/parts1-5-v3.mp4`): switched parts1-2 → 3a transition from plain `xfade=fade` to `xfade=fadeblack:duration=1.0`. Felt good but Alex flagged the audio: George's "Villagers..." started during the fadeblack (acrossfade overlap), not after.

**v4** (`clips/parts1-5-v4.mp4`): tried adding 1.0s held-frame on parts1-2 before fadeblack to push the chalk start later. Audio overlap problem still present — acrossfade by definition overlaps both streams during its window.

**v5** (`clips/parts1-5-v5.mp4`): correct fix — switched from `xfade=fadeblack` to **manual** fade-out + black hold + fade-in built via `fade=t=out + tpad color=black + fade=t=in + concat`. Audio uses `apad` on stream 0 + `adelay` on stream 1 + hard `concat` (no acrossfade), so audio is genuinely silent during the black hold. Timing: 0.4 fade-out + 0.7 black hold + 0.4 fade-in + 0.4 audio delay = ~1.5s gap from "rules" to "Villagers." Hit a `timebase mismatch` error mid-build — `concat` outputs at `1/1000000`, subsequent `xfade` expects `1/12800`. Fixed with `concat=...,fps=25,settb=1/12800`.

**v6** (`clips/parts1-5-v6.mp4` → renamed `clips/parts1-5-locked.mp4`): Alex requested "a bit shorter pause". Trimmed all four components ~25%: fade-out 0.3 + black hold 0.4 + fade-in 0.3 + audio delay 0.3 = ~1.1s gap. **LOCKED at 2:05.04, 90MB.**

The other 4 chunk boundaries (3a→3b→bridge→3c→outro) all use plain `xfade=fade:duration=0.4` + `acrossfade=d=0.4` — those transitions are within the same narrative register (chalkboard-to-chalkboard or chalkboard-to-host-bridge-back) and the soft crossfade reads correctly without needing the black hold.

### Cost summary (2026-05-23 → 2026-05-24, this production arc)

| Category | Items | Cost |
|----------|-------|------|
| Pre-chalk rejected (realistic robot-table iterations before pivot) | 4 gpt-image-2 high | $0.76 |
| Chalk style probes (medium) | 2 gpt-image-2 medium | $0.26 |
| Chalk full set including re-rolls + expansions | 16 gpt-image-2 high | $3.04 |
| ElevenLabs narration | 6 George recordings (3a, 3b, bridge, 3c v1+v2+v3, outro) | $0.52 |
| Seedance r2v | bridge (8s) + outro (6s) | $4.23 |
| **Total this arc** | | **$8.81** |

Cumulative project spend per `api-spending.csv`: see lines tagged `werewolf-v4-*`, `slideshow-chalk-*`, `part3*`, `bridge3bc`, `outro`.

---

## Pickup notes — where to continue next session

**Locked artifact**: `clips/parts1-5-locked.mp4` (2:05.04). Standalone rules-explainer video — narratively complete on its own.

**Original v4 scope had Part 4 (live app demo)**. Alex decided 2026-05-24: app demo becomes a separate next video, NOT part of this lock. Don't append it here; spawn a new `video-projects/werewolf-app-demo-v1/` workspace when starting it. The demo plan in old `script.md` (lobby capture, theme/player count/roles toggles, AI model selection, generate→preview, names+backstories) is still the right material — just for the next project.

**Polish items considered but not done**:
- Background music bed at 4% volume (v3 track was working — see MEMORY for the rule). Not added because the chalk slideshow + Seedance r2v dialogue carries enough on its own. Alex didn't request it.
- URL overlay (`aiwerewolf.net`) was in the old Part 5 plan — moved to the future app demo video's outro, where it makes more sense.

**If reproducing the lock from scratch**: all source images in `images/`, all treated audio in `audio/elevenlabs_raw/`, all sub-chunk videos in `clips/part3/`. Final assembly recipe is the v5/v6 filter chain saved in this file (search "v5" above). Source-chunk durations to preserve: 3a=16.0, 3b=16.048, bridge=8.10, 3c=52.24, outro=6.10. The manual fade transition between parts1-2 and 3a is the only complex spot; everything else is standard `xfade=fade:0.4` + `acrossfade=d=0.4`.

**Skills updated 2026-05-25 with the learnings**: `.claude/skills/ffmpeg/SKILL.md`, `.claude/skills/director/SKILL.md`, `.claude/skills/openai-image/SKILL.md`. Future similar productions should be ~50% faster.
