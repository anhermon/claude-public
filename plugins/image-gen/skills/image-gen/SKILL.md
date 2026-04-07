---
name: image-gen
description: >
  Generate images using AI image generation. Trigger on: "generate an image", "create an image",
  "make an image of", "draw", "design", "gen image", "/image-gen", "avatar for", "icon for",
  "logo for", "image of", "picture of", "photo of", "illustration of", "generate using nano banana",
  "use higgsfield", "use gemini to generate". Automatically engineers expert-quality prompts from
  brief descriptions. Supports API providers (fal.ai, Together AI, Replicate, OpenAI, Stability AI)
  and browser automation via Higgsfield Nano Banana Pro or Google Gemini when no API keys exist.
metadata:
  version: "0.2.0"
  author: "Angel Hermon"
---

# Image Generation Skill

Generates images from user descriptions. Performs expert prompt engineering automatically —
the user only needs to provide a brief description. Supports API-based and browser-based generation.

---

## Step 1: Parse the Request

Extract from the user's message:

- **Subject** (required): What to generate. Ask if missing.
- **Image type** (infer): One of → `app-icon`, `avatar`, `logo`, `character`, `scene`, `product`, `illustration`, `photo`, `concept-art`. Infer from context.
- **Style hints** (optional): flat, 3D, cinematic, minimal, dark, neon, etc.
- **Aspect ratio** (optional): `square` (default), `portrait`, `landscape`, `wide`, `tall`
- **Quality** (optional): `fast` (default) or `quality`/`hd`/`best`
- **Provider preference** (optional): explicit model or provider name in the message
- **Output path**: `C:/Users/User/paperclip/_tmp/images/` (default)

---

## Step 2: Engineer the Prompt

**This is the most important step.** Never pass the user's raw description directly to the model.
Transform it into a rich, model-optimized prompt using the rules below.

### 2a. Identify the generation path

Check provider preference from the message:
- Mentions "gemini" → **Gemini browser path** (Step 5B)
- Mentions "nano banana", "higgsfield", "NB2", "NB Pro" → **Higgsfield path** (Step 5C)
- Otherwise → check API keys first (Step 3), fall back to browser if none

### 2b. Build the base prompt by image type

**`app-icon`** — Square app icon for a software application:
```
Minimal flat-design app icon, [COLOR_PALETTE] palette, [SYMBOL] as the central motif,
rounded square format, clean vector aesthetic, bold shape with subtle depth,
no text, crisp edges, [BACKGROUND] background, professional app store quality
```

**`logo`** — Standalone brand mark:
```
Clean modern logo mark, [SYMBOL] as primary element, [STYLE] design language,
[COLOR_PALETTE], scalable vector composition, negative space used intentionally,
no gradients unless specified, balanced and geometric, white background for visibility
```

**`avatar`** — Profile / character avatar:
```
Portrait avatar, [CHARACTER DESCRIPTION], [STYLE] art style, centered composition,
facing slightly to the side, [LIGHTING] lighting, soft background blur,
high detail on face/focal point, [COLOR PALETTE], professional quality
```

**`character`** — Full or half-body character:
```
[CHARACTER DESCRIPTION], [POSE], [STYLE] art style, [LIGHTING],
dramatic composition, intricate detail on costume and face, [COLOR MOOD],
cinematic quality, sharp focus on subject
```

**`scene`** / **`concept-art`** — Environment or narrative scene:
```
[SCENE DESCRIPTION], [TIME OF DAY], [WEATHER/ATMOSPHERE], [ART STYLE],
wide establishing shot, cinematic composition, rich environmental detail,
[LIGHTING TYPE] lighting, [COLOR GRADING], high production value
```

**`product`** — Product photography or render:
```
Professional product shot of [PRODUCT], [BACKGROUND], studio lighting with
[KEY LIGHT] key and [FILL LIGHT] fill, [ANGLE] angle, sharp focus,
commercial photography quality, no reflections unless intentional
```

**`photo`** — Photorealistic image:
```
Professional photograph of [SUBJECT], [CAMERA: 85mm f/1.8 or similar],
[LIGHTING], [COMPOSITION: rule of thirds / centered / etc.],
photorealistic, high dynamic range, sharp focus
```

**`illustration`** — Hand-drawn or stylized:
```
[STYLE: watercolor / ink / digital painting / etc.] illustration of [SUBJECT],
[COLOR PALETTE], [MOOD], detailed linework, [COMPOSITION],
high quality, artbook level
```

### 2c. Fill in the template variables

Infer from the user's subject + style hints. Apply smart defaults:

| Variable | Smart Defaults |
|---|---|
| `COLOR_PALETTE` | Derive from subject name/theme. "Anvil" → charcoal, iron grey, ember orange |
| `SYMBOL` | The core metaphor. "Anvil" app → stylized anvil silhouette |
| `BACKGROUND` | `app-icon`: dark/near-black. `logo`: white. `scene`: contextual |
| `LIGHTING` | `app-icon`: subtle gradient top-left. `character`: dramatic side-light |
| `STYLE` | Default `flat` for icons/logos. Default `cinematic` for scenes/photos |
| `CAMERA` | 85mm f/1.8 for portraits. 35mm f/2.8 for scenes |

### 2d. Add model-specific modifiers (append to prompt)

**For Higgsfield Nano Banana Pro:**
```
[append] ultra-detailed, Nano Banana Pro render, photographic quality,
crisp edges, natural texture, professional finish, no watermarks
```

Nano Banana Pro is a **cinematic/photorealistic** model. Reframe `app-icon` and `logo`
requests as stylized product renders rather than flat design:
> Instead of: "flat app icon"
> Use: "A dark studio product render of an [SYMBOL], isolated on [BACKGROUND], dramatic rim lighting, ultra sharp, icon crop"

**For Gemini (Google):**
```
[append] clean and precise, suitable for app store, high resolution
```
Gemini handles flat design and icons well. Keep the prompt clear and conceptual —
Gemini interprets intent, no need for excessive technical detail.

**For API providers (FLUX, DALL-E 3, Stability):**
```
[append for FLUX] --ar 1:1 high detail, no blur
[append for DALL-E] I NEED to test how the tool works with extremely accurate prompts.
[append for Stability] high quality, 4K, masterwork
```

### 2e. Write out the final engineered prompt

State it clearly before generation:
> Engineered prompt: `[FULL PROMPT TEXT]`

---

## Step 3: Check API Providers

Check for keys in environment AND `.env`:

```bash
set -a; source C:/Users/User/paperclip/.env 2>/dev/null; set +a
echo "=== Provider Check ==="
for VAR in FAL_KEY REPLICATE_API_TOKEN TOGETHER_API_KEY OPENAI_API_KEY STABILITY_API_KEY; do
  VAL="${!VAR}"
  [ -n "$VAL" ] && echo "$VAR: SET" || echo "$VAR: not set"
done
```

**If at least one key is SET** → proceed to **Step 4 (API Generation)**.
**If no keys found** → skip to **Step 5 (Browser Generation)**.

---

## Step 4: API Generation

Prepare output directory and filename:
```bash
mkdir -p "C:/Users/User/paperclip/_tmp/images"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
SLUG=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | cut -c1-40 | sed 's/-*$//')
OUTPUT_FILE="C:/Users/User/paperclip/_tmp/images/${TIMESTAMP}-${SLUG}.jpg"
```

**Size mapping:**

| Aspect | Together/FLUX | fal.ai | Replicate | DALL-E | Stability |
|---|---|---|---|---|---|
| square (default) | 1024×1024 | `square_hd` | `1:1` | `1024x1024` | `1:1` |
| landscape | 1792×1024 | `landscape_16_9` | `16:9` | `1792x1024` | `16:9` |
| portrait | 1024×1792 | `portrait_16_9` | `9:16` | `1024x1792` | `9:16` |

Try providers in priority order (highest configured priority first):

### Provider 1: Together AI (`TOGETHER_API_KEY`)

```bash
RESPONSE=$(curl -s -X POST "https://api.together.xyz/v1/images/generations" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"model\": \"black-forest-labs/FLUX.1-schnell-Free\", \"prompt\": \"$PROMPT\", \"width\": 1024, \"height\": 1024, \"steps\": 4, \"n\": 1}")
IMAGE_URL=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][0]['url'])" 2>/dev/null)
[ -n "$IMAGE_URL" ] && curl -sL "$IMAGE_URL" -o "$OUTPUT_FILE" && echo "DONE: $OUTPUT_FILE"
```

### Provider 2: fal.ai (`FAL_KEY`)

```bash
RESPONSE=$(curl -s -X POST "https://fal.run/fal-ai/flux/schnell" \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"$PROMPT\", \"image_size\": \"square_hd\", \"num_inference_steps\": 4, \"num_images\": 1, \"output_format\": \"jpeg\", \"sync_mode\": true}")
IMAGE_URL=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['images'][0]['url'])" 2>/dev/null)
[ -n "$IMAGE_URL" ] && curl -sL "$IMAGE_URL" -o "$OUTPUT_FILE" && echo "DONE: $OUTPUT_FILE"
```

### Provider 3: Replicate (`REPLICATE_API_TOKEN`)

```bash
RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
  -H "Content-Type: application/json" -H "Prefer: wait" \
  -d "{\"input\": {\"prompt\": \"$PROMPT\", \"num_outputs\": 1, \"aspect_ratio\": \"1:1\", \"output_format\": \"jpg\"}}" \
  "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions")
IMAGE_URL=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); out=d.get('output'); print(out[0] if isinstance(out,list) else out or '')" 2>/dev/null)
[ -n "$IMAGE_URL" ] && curl -sL "$IMAGE_URL" -o "$OUTPUT_FILE" && echo "DONE: $OUTPUT_FILE"
```

### Provider 4: OpenAI (`OPENAI_API_KEY`)

```bash
RESPONSE=$(curl -s -X POST "https://api.openai.com/v1/images/generations" \
  -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
  -d "{\"model\": \"dall-e-3\", \"prompt\": \"$PROMPT\", \"n\": 1, \"size\": \"1024x1024\", \"quality\": \"standard\", \"response_format\": \"url\"}")
IMAGE_URL=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][0]['url'])" 2>/dev/null)
[ -n "$IMAGE_URL" ] && curl -sL "$IMAGE_URL" -o "$OUTPUT_FILE" && echo "DONE: $OUTPUT_FILE"
```

### Provider 5: Stability AI (`STABILITY_API_KEY`)

```bash
HTTP_STATUS=$(curl -s -o "$OUTPUT_FILE" -w "%{http_code}" \
  -X POST "https://api.stability.ai/v2beta/stable-image/generate/core" \
  -H "Authorization: Bearer $STABILITY_API_KEY" -H "Accept: image/*" \
  -F "prompt=$PROMPT" -F "output_format=jpeg" -F "aspect_ratio=1:1")
[ "$HTTP_STATUS" = "200" ] && echo "DONE: $OUTPUT_FILE"
```

**After success** → jump to **Step 6 (Verify and Report)**.

---

## Step 5: Browser Generation (No API Keys)

Use browser automation tools (`mcp__Claude_in_Chrome__*`). Always use
`mcp__Claude_in_Chrome__tabs_context_mcp` first to get a valid `tabId`.

Choose path based on **Step 2a**:
- Explicit "gemini" request → **Step 5B**
- Explicit "higgsfield" / "nano banana" / "NB Pro" request → **Step 5C**
- No explicit preference → try **Step 5C** (Higgsfield) first; if not logged in → fall back to **Step 5B** (Gemini)

---

### Step 5A: Setup

```
Get tabs context → tabId
mkdir -p "C:/Users/User/paperclip/_tmp/images"
TIMESTAMP = date +%Y%m%d-%H%M%S
OUTPUT_FILE = C:/Users/User/paperclip/_tmp/images/{TIMESTAMP}-{slug}.jpg
```

---

### Step 5B: Gemini Browser Path

Gemini (gemini.google.com) is ideal for: app icons, logos, flat design, concept art.
No account setup needed if already logged into Google.

**Navigate:**
```
mcp__Claude_in_Chrome__navigate → https://gemini.google.com/app
```

**Check login:** Look for "Hi [name]" or the prompt input. If a login wall appears,
stop and tell the user to log into Google in the browser.

**Type the engineered prompt** into the "Ask Gemini" input and press Enter.

**Wait for generation:** Poll with screenshot every 5-10 seconds until the image appears.
Look for: an `<img>` element with a generated image src (not a profile pic or logo).

**Download:** Click the download button (↓ icon top-right of the image card).
Gemini downloads full size to the user's Downloads folder automatically.

**Locate the file:**
```bash
# Find the most recently downloaded image
ls -t ~/Downloads/*.png ~/Downloads/*.jpg 2>/dev/null | head -1
```

Copy to output path:
```bash
DOWNLOADED=$(ls -t ~/Downloads/*.png ~/Downloads/*.jpg 2>/dev/null | head -1)
cp "$DOWNLOADED" "$OUTPUT_FILE"
```

---

### Step 5C: Higgsfield Nano Banana Pro Browser Path

Nano Banana Pro is a cinematic/photorealistic model. Best for: characters, scenes,
product renders, stylized avatars. Requires a Higgsfield account.

**Navigate:**
```
mcp__Claude_in_Chrome__navigate → https://higgsfield.ai/image/nano_banana_2
```

**Check login:** Take a screenshot. If the page shows the prompt input at the bottom
with "Nano Banana Pro" selected → logged in, proceed. If the sign-in page appears →
tell the user: "You need to be logged into Higgsfield. Please sign in at
https://higgsfield.ai/auth/sign-in and then retry." → fall back to **Step 5B**.

**Type the engineered prompt** in the "Describe the scene you imagine" input.

**Verify model:** Check the model chip reads "Nano Banana Pro". If not:
- Click the model chip
- Select "Nano Banana Pro" from the Models dropdown

**Click Generate** (yellow "Generate → 2" button, bottom right).

**Wait for generation:** Take screenshots every 5 seconds. Watch for:
- The loading spinner to disappear
- Generated image cards to appear in the main area

**Download:** Hover the generated image to reveal controls. Click the download (↓) icon.
Higgsfield downloads to the user's Downloads folder.

**Locate the file:**
```bash
DOWNLOADED=$(ls -t ~/Downloads/*.jpg ~/Downloads/*.png ~/Downloads/*.webp 2>/dev/null | head -1)
cp "$DOWNLOADED" "$OUTPUT_FILE"
```

---

## Step 6: Verify and Report

```bash
if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
  FILE_SIZE=$(wc -c < "$OUTPUT_FILE")
  echo "SUCCESS: $OUTPUT_FILE ($FILE_SIZE bytes)"
else
  echo "ERROR: Output file missing or empty"
fi
```

Report to user:
- Full output path
- Provider / model used
- The engineered prompt that was used
- Approximate cost (API) or "free" (browser)
- Whether it was downloaded to Downloads folder or saved directly

**Example:**
> Generated: `C:/Users/User/paperclip/_tmp/images/20260404-143022-anvil-icon.jpg`
> Provider: Gemini (browser) — free
> Model: Gemini 2.0 Flash (image generation)
> Prompt used: `Minimal flat-design app icon, charcoal and iron grey palette with ember orange accent, stylized anvil silhouette as the central motif, rounded square format, clean vector aesthetic, bold shape with subtle depth, no text, crisp edges, near-black background, professional app store quality, clean and precise, suitable for app store, high resolution`

---

## Step 7: Update Provider Memory

After any successful generation, update:
`C:/Users/User/.claude/projects/C--Users-User-paperclip/memory/image-gen-providers.md`

Record:
- Last successful provider
- Date
- First 60 chars of engineered prompt

---

## Error Reference

| Error | Cause | Fix |
|---|---|---|
| Sign-in wall on Higgsfield | Not logged in | Fall back to Gemini (Step 5B) |
| Sign-in wall on Gemini | Not logged into Google | Ask user to log into Google |
| `401` on API | Invalid key | Check key in `.env` |
| `402` on API | No credits | Add credits or switch provider |
| `429` on API | Rate limit | Switch provider |
| Download not found | Browser save dialog appeared | Check Downloads folder manually |
| Image card not appearing | Generation still running | Wait longer, poll again |

---

## Provider / Model Reference

| Method | Model | Quality | Cost | Best for |
|---|---|---|---|---|
| Higgsfield (browser) | Nano Banana Pro | Excellent | ~$0.03/img or plan | Cinematic, characters, stylized |
| Gemini (browser) | Gemini 2.0 Flash | Good | Free (account) | Icons, logos, flat design, concepts |
| Together AI | FLUX.1-schnell-Free | Good | Free (rate limited) | General purpose |
| fal.ai | FLUX schnell | Good | ~$0.003/img | Fast, general |
| Replicate | FLUX schnell | Good | ~$0.003/img | General |
| OpenAI | DALL-E 3 | Excellent | ~$0.04/img | Text in image, precise concepts |
| Stability AI | Core | Great | ~$0.03/img | Photorealism |
