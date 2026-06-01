# AI API Prices April-May 2026 — Article Workspace

## Sources

Werewolf pricing data sourced from git history of `werewolf-client/app/ai/ai-models.ts` in `~/projects/werewolf-ai-party-game/`:

- `11968eb` (2026-04-25) — GPT-5 → GPT-5.5, DeepSeek Chat→V4 Flash, DeepSeek Reasoner→V4 Pro, Kimi K2.5→K2.6
- `152cb56` (2026-04-25) — Grok 4 → 4.2, Claude 4.6 Opus → 4.7 Opus (price unchanged)
- `1e9e62a` (2026-05-07) — Mistral Medium 3.1 → 3.5, Mistral 4 Small added, Grok 4.2 → 4.3
- `9bc07e7` (2026-05-09) — GLM-5.1 added
- `bbd0e40` (2026-05-23) — Gemini 3 Flash → 3.5 Flash, Grok 4.3 model consolidation

GLM-5 → GLM-5.1 baseline comparison sourced from official Z.AI pricing page (Alex provided screenshot 2026-05-26): GLM-5 was $1.00/$3.20/$0.20, GLM-5.1 is $1.40/$4.40/$0.26.

## Outputs

- `~/projects/blog/posts/drafts/2026-05-26-ai-api-prices-april-may-2026.md` — full article draft
- `linkedin/teaser.txt` — LinkedIn teaser post

## Notes

- Unified metric used in article + teaser: average of input% change and output% change, cache excluded from the average per Alex's spec (cache shown in the table for completeness).
- DeepSeek comparison uses Reasoner → V4 Pro (apples-to-apples reasoning tier). DeepSeek Chat → V4 Flash actually got *cheaper* ($0.28/$0.42 → $0.14/$0.28) — not featured in article; could be added as a footnote.
- GLM-5.1 reseller-tier confusion: OpenRouter and pricepertoken.com list GLM-5.1 at $0.98/$3.08, but Z.AI's first-party rate card is $1.40/$4.40. Article uses Z.AI direct. Werewolf code matches Z.AI direct.

## Revisions

### 2026-05-30 — DeepSeek correction + cheap-disruptor speed footnote

Source: https://api-docs.deepseek.com/quick_start/pricing

DeepSeek made the 75%-off V4 Pro promo permanent effective **2026-05-31 15:59 UTC**. Permanent rates: input $0.435/M, output $0.87/M, cache hit $0.003625/M. Article and teaser previously used launch-day rates ($1.74 / $3.48 / $0.0145), which produced the +314% headline. Recomputed using the permanent rates:

- Input: $0.28 → $0.44 = +55%
- Output: $1.68 → $0.87 = −48%
- Avg (in/out): ~+3% (effectively flat)

Knock-on changes:
- Table row updated, daggered footnote added explaining the launch → promo → permanent sequence.
- "Three deserve a second look" → "Two deserve a second look" (dropped DeepSeek shock-number bullet, replaced with a dedicated "cheap-disruptor story always had a footnote" section).
- New section folds in Alex's lived experience: V3 and original Kimi K2 were cheap per token but too slow to actually deploy in latency-sensitive apps (Werewolf). Turbo variants cost meaningfully more — that's the real "cheap" tier most prod apps run, and it's not as cheap as the headlines.
- Reframed DeepSeek as "the only provider that flinched" rather than a shock-bump example.
- Summary stats updated: mean +108% → +74%, median +100% → +42%.
- Closing tally line rewritten: "five raised, one walked a 6x hike back to flat under pressure, one held, one cut."
- LinkedIn teaser updated with same numbers and footnote.

### 2026-05-31 — LIVE; deploy root cause found

Deploy went green and the article is verified live at https://azelianouski.dev/post/ai-api-prices-april-may-2026 (latest build: Tokens/Reasoning/Harness, Mythos, Grok 4.2→4.3, plan-B close, both images all confirmed). **Earlier "deploy stuck" diagnosis was WRONG** — git push DOES trigger a Cloudflare build; it was failing at the end on a `SESSION` KV-namespace binding set to auto-provision (`wrangler` tried to create `blog-session`, which already existed → error 10014 → deploy aborted after upload, site stayed on old build). Found via the Cloudflare build logs Alex pasted. Alex fixed it dashboard-side. (Full note saved to memory `project_alex_blog`.) The empty GitHub deployments API was a red herring — this build type doesn't populate it.

Cross-post status: LinkedIn ready (post-final.txt rewritten to match final article, ~2.7k chars, native image + first-comment link). Substack + HN planned Tue 2026-06-02; HN titles drafted.

### 2026-05-31 — LinkedIn posted; Substack assembled

- **LinkedIn: POSTED** by Alex (native-image post + first-comment link, from `linkedin/post-final.txt`).
- **Substack: assembled** at `linkedin/substack.md` — paste-ready full body, Substack fields (title/subtitle/Original URL/tags/cover), both tables converted to bullet lists (Substack composer doesn't render markdown tables and strips `<br>`), bills image marked for manual insert near end. Not yet posted.
- **HN plan change:** Tuesday 2026-06-02 HN submission is the **CTF/BSides article (article 1)**, not this API piece — Alex's call. Title already agreed: "A customized Claude Code setup placed 6th of 61 at BSides Tampa CTF". (API piece may go to Substack/HN separately, TBD.)

### 2026-05-31 — Full revision pushed; DEPLOY STILL DOWN [superseded — see entry above; it deployed once the SESSION KV binding was fixed]

Big collaborative revision pass with Alex (intro broadened; vantage line folded under intro, no heading; per-provider section reordered OpenAI→Google→Mistral→Kimi→GLM→DeepSeek→Grok→Anthropic and largely rewritten in Alex's voice; "what's going on" recast as **Tokens / Reasoning / Harness**; "Copilot story is the wrong frame" section deleted; plan-B close rewritten around local fallback (16GB AMD card, Qwen/Gemma/Mistral, Roo Code) + enterprise cost-pushback kicker; Mythos added to Anthropic — verified real via web (Anthropic class above Opus, gated security/enterprise preview); OpenAI cache corrected to $0.50). Local `npm run build` clean. Commits 6ef8d38, 5594162, **7f5b30d** all pushed to blog `master`.

**DEPLOY STILL NOT FIRING** as of 2026-05-31 ~16:02. azelianouski.dev serves an old build; `/post/ai-api-prices-april-may-2026/` 404s; homepage doesn't list the article. Three commits over two days, none deployed → Cloudflare Pages GitHub App integration is not triggering. Article is final and committed; only the deploy is blocked. FIX (Alex's accounts only): (1) https://github.com/settings/installations → Cloudflare → add/confirm `blog` repo in the App's repo-access list; or (2) Cloudflare dashboard → Pages project → Deployments → Create/Retry deployment. Once triggered, re-verify live URL + LinkedIn can go out.

### 2026-05-31 — OpenAI cache-price CORRECTION (Alex caught it)

Source: https://developers.openai.com/api/docs/pricing (fetched 2026-05-31). Official GPT-5.5 = $5 in / **$0.50 cached** / $30 out; GPT-5.4 = $2.50 / $0.25 / $15. The draft had GPT-5.5 cache at **$2.50** (a "+10x" error). Corrected table cell to $0.25 → $0.50 (**2x**). Rewrote the OpenAI bullet: removed the entire "the quieter move is worse / cache went up 10x / nobody wrote that headline" beat (it was built on the wrong number) and replaced with an accurate "cache doubled in lockstep, same 2x as everything else" note. Input/output unchanged (+100% each); cache is excluded from the per-model average, so the +100% row and the mean +74% / median +42% summary are unaffected. NOTE: one transcription error surfaced — worth a verification pass on the other providers' first-party numbers before any wider promotion.

### 2026-05-31 — Closing rework + DEPLOY NOT FIRING

- Reworked the ending per Alex: removed the unit-economics paragraph + the "By the time it shows up as a Copilot price hike" closer; added a new **"## Time to refresh plan B"** section (prices keep rising → what to do about it → GLM via Claude Code, opencode + Roo Code, DeepSeek's own coding assistant, local Qwen2.5-Coder on a 16GB Radeon RX 6950 XT fine-tuned on Cline's I/O; flagships still better but the gap narrows as price gap widens; labs have no incentive to stop). Bills figure kept as the final visual. Tool names left UNLINKED (Roo Code, opencode) to avoid shipping guessed URLs — offer to add.
- Local `npm run build` clean both times. Commits 6ef8d38 (initial publish) and 5594162 (rework) pushed to blog `master`.
- **DEPLOY ISSUE:** azelianouski.dev homepage is 200 but serves an OLD build — does not list the new article; `/post/ai-api-prices-april-may-2026/` returns 404 after both pushes (first push was 2026-05-30, still not live on 2026-05-31). No `.github/workflows` and no wrangler config in repo → deploy is the Cloudflare Pages GitHub App integration, which appears to have stopped firing. Matches the known failure mode in `project_alex_blog` memory. FIX (needs Alex's accounts): (1) https://github.com/settings/installations → Cloudflare → confirm `blog` repo is in the App's repo-access list; add if missing. (2) Manual fallback: Cloudflare dashboard → Pages project → Deployments → Create/Retry deployment. Article content is final and committed; only the deploy is blocked.

### 2026-05-30 — PUBLISHED

- Added pass@1 explanation to the DeepSWE section; tightened benchmark description.
- Fixed source-file link to `/blob/master/` (was `/blob/main/`).
- Added closing bills image: `images/cover-bill-coming-due.png` → converted to `~/projects/blog/public/images/ai-api-prices-bill-coming-due.jpg` (269KB), embedded as a `<figure>` after the final paragraph with caption "The invoice is the part you see. The rate card moved two months ago."
- Set `status: published`, `date: 2026-05-30`; moved file `posts/drafts/2026-05-26-...md` → `posts/2026-05-30-ai-api-prices-april-may-2026.md`.
- `npm run build` clean (route `/post/ai-api-prices-april-may-2026/` generated). Committed + pushed to `master` (blog repo, commit 6ef8d38) → Cloudflare auto-deploy.
- **Live URL:** https://azelianouski.dev/post/ai-api-prices-april-may-2026 (site moved to vanity domain azelianouski.dev; was workers.dev).
- LinkedIn `post-final.txt` + `teaser.txt` `[LINK]` placeholders filled with the live URL.
- NOTE: Mythos / "Anthropic pricier next family" claim left OUT — Anthropic bullet uses soft framing. Alex did not resolve before publishing.

### 2026-05-30 — Alex inline-comment pass

- Added GitHub link to the Werewolf project in the "weird vantage point" intro (https://github.com/hiper2d/werewolf-ai-party-game).
- Removed the † DeepSeek footnote and its dagger marker from the table; folded all of it (launch $1.74/$3.48, +314% launch headline, 75%-off promo → permanent $0.435/$0.87 as of May 31, output now below old Reasoner, +3% net) into the DeepSeek per-provider bullet. Dropped the now-dead "see the † above" reference.

### 2026-05-30 — Restructured into per-provider commentary + new pricing data

Per Alex: replaced the three thematic sections ("numbers that should stop you", "cheap-disruptor footnote", "counter-examples") with one annotated section, **"Going down the table, provider by provider"** — a short read per provider folding in Alex's takes. Cache-10x moved into the OpenAI bullet; 40-second-turn Werewolf anecdote preserved in the DeepSeek bullet; "check which SKU" point preserved in Kimi bullet. DeepSWE section's "throughput-tax footnote" antecedent fixed to "cheap-but-slow story above" since the section it referenced was removed.

New data gathered (Alex's two research asks):
- **Grok deprecated cheap models.** Source: pricepertoken.com (xai-grok-4-fast), mem0.ai/blog/xai-grok-api-pricing. `grok-4-fast` = $0.20/$0.50; `grok-code-fast-1` = $0.20/$1.50 (cache $0.02). Both ~6x cheaper on input than main Grok 4.3 ($1.25/$2.50); now consolidated/routed into Grok 4.3. Used in Grok bullet.
- **GLM price history.** Source: pricepertoken.com (z-ai-glm-4.5), docs.z.ai/guides/overview/pricing. GLM-4.5 = $0.60/$2.20 → GLM-5 = $1.00/$3.20 → GLM-5.1 = $1.40/$4.40. Across 4.5→5.1: input +133%, output +100% (doubling). Used in GLM bullet.
- Werewolf repo (`werewolf-client/app/ai/ai-models.ts`) confirmed current GLM-5.1 ($1.4/$4.4/$0.26) and Grok 4.3 ($1.25/$2.50/$0.20); repo does not track the deprecated Grok cheap SKUs or pre-5 GLM versions.

OPEN: Alex mentioned "Mythos" as a model more expensive than Opus + "Anthropic announced a new pricier family." Ambiguous (Mythos = his cybersecurity org's tool per memory, not a known public LLM) and unverified. Held OUT of the public draft pending his clarification; Anthropic bullet uses the safe framing "labs signaling even pricier top-tier families ahead" without naming Mythos or asserting the specific claim.

### 2026-05-30 — Opus 4.8 + DeepSWE benchmark added (article)

Two edits to the blog draft per Alex:

1. **Opus 4.8.** Anthropic shipped Opus 4.8, priced identical to 4.7 (and 4.6) — $5/$25. Extended the "held flat" story from one version bump to three (4.6 → 4.7 → 4.8). Table row relabeled "Claude 4.6 → 4.8 Opus", still 0%. Noted GPT-5.5 now exceeds Opus on output ($30 vs $25), so Opus is no longer strictly the most expensive on output, though still the premium flagship — phrasing kept accurate.

2. **DeepSWE benchmark.** Source: https://deepswe.datacurve.ai/ (fetched 2026-05-30). Datacurve's agentic-coding benchmark — 113 tasks, 91 repos, 5 languages, ~5.5x more code per solution than SWE-bench-style; evaluated via mini-swe-agent. Added a new section "What the price actually buys" with a curated pass@1 table (only the providers the post tracks). Full board pass@1 from source: gpt-5.5 70, claude-opus-4.8 58, gpt-5.4 56, claude-opus-4.7 54, claude-sonnet-4.6 32, gemini-3.5-flash 28, claude-opus-4.6 28, gpt-5.4-mini 24, kimi-k2.6 24, mimo-v2.5-pro 19, glm-5.1 18, grok-build-0.1 13, gemini-3.1-pro 10, deepseek-v4-pro 8, gemini-3-flash 5. Error bars ±4–5 pts (stated in article). Narrative: top of board = the aggressive price-raisers (GPT-5.5 at 70); bottom = DeepSeek V4 Pro at 8 (cheap-disruptor capstone); Anthropic = capability 28→54→58 across 4.6→4.7→4.8 at flat price (the one buyer-favorable datapoint).

### 2026-05-30 — LinkedIn finalized for native-image post

Decision (Alex): post as a **native image upload**, blog link in the **first comment** (not the body) — native images get better LinkedIn distribution than outbound-link posts.
- Staged image: `linkedin/post-image.png` (copy of selected `images/cover-token-meter.png`, 1792x1024, 2.5MB PNG).
- `linkedin/post-final.txt` — ready-to-paste version: posting instructions + POST BODY (the `[LINK]` line removed from the body) + FIRST COMMENT block (link goes here once published).
- `linkedin/teaser.txt` retained as the original single-block draft for reference.

### 2026-05-30 — DeepSeek tense fix

The permanent rate takes effect 2026-05-31 15:59 UTC — i.e. tomorrow relative to this edit. Article and teaser previously stated "on May 31 made the discount permanent" (past tense for a future event). Reworded to tense-robust phrasing ("as of May 31 the discount becomes the permanent rate" / "becomes the permanent rate as of May 31") so it reads correctly whether opened before or after the 31st. Three spots: draft footnote (†), draft body section, teaser bullet.

### 2026-05-30 — Cover image concepts (3 generated)

Tool/model: OpenAI gpt-image-2, `POST /v1/images/generations`, size 1792x1024, quality high, n=1 each. Cost: $0.19 each, $0.57 total. Logged in `api-spending.csv`. All written to `ai-api-prices-april-may-2026/images/`.

1. **cover-token-meter.png** — *selected as header candidate*. Prompt verbatim: "A dark, cinematic close-up of a vintage brushed-metal gas-pump meter reimagined as an AI token fuel meter, standing on a server-room floor. A round glass dial with a rolling mechanical numeric counter, the digits climbing high and glowing hot RED, a thin needle pushed deep into a red danger zone. Faint etched labels on the metal read like fuel grades. Rows of dark server racks with tiny blue indicator LEDs blur into the background. Moody neon underlighting, teal and red, volumetric haze, shallow depth of field. Shot on Canon EOS R5, 35mm, f/2.8, 8k, photorealistic, brushed metal texture and glass reflections, film noir mood." — Result rendered "AI TOKENS FUEL METER", counter pegged at 99999999, needle in red, fuel grades REGULAR/PLUS/PREMIUM labeled with context sizes. Tokens-as-fuel metaphor; most legible. **SELECTED by Alex 2026-05-30.** Converted to JPEG (q85, 462KB) and placed at `~/projects/blog/public/images/ai-api-prices-april-may-2026.jpg`; wired into draft frontmatter as `header_image`.

2. **cover-reversed-curve.png** — Prompt verbatim: "A minimal, abstract data-noir wall display in a dark room. A single glowing neon line chart drawn in cyan that starts by gently descending left-to-right (the expected cheap-tokens trend) then violently reverses and spikes sharply UPWARD into bright red at the right edge. One thin lone secondary line continues ticking downward in cool blue, a quiet counter-trend. No readable numbers, no text labels, just elegant glowing curves on a deep charcoal-black gridded surface. Soft bloom, volumetric glow, faint reflection on a glossy floor. Cinematic, moody, high contrast, 8k, photorealistic render." — Candidate for a mid-article section break.

3. **cover-bill-coming-due.png** — Prompt verbatim: "A moody noir desk scene shot in the dark, lit only by the cold glow of a computer monitor off-frame. A long white thermal-printer receipt unspools from a small printer on the desk, cascading over the edge and pooling in coils on the floor, an impossibly long itemized bill. A cold cup of coffee, a mechanical keyboard half in shadow. The room is dark, late-night-reckoning atmosphere, blue monitor light against warm desk-lamp fill. The receipt paper is blank-to-illegible fine print, no readable numbers. Shot on Canon EOS R5, 50mm, f/1.8, shallow depth of field, 8k, photorealistic, paper texture, dust particles in the light beam, cinematic film grain." — Moodiest, but reads "downstream invoice" more than "upstream rate card"; not selected.
