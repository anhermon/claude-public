# image-gen plugin

AI image generation with built-in expert prompt engineering.

## Skills

**image-gen** — Generate images from brief descriptions. Automatically engineers rich,
model-optimized prompts. No need to write detailed prompts yourself.

Trigger phrases: "generate an image", "create an avatar for", "icon for [app]",
"make me an image of", "design a logo for", "use nano banana", "use gemini to generate".

## How it works

1. **Prompt Engineering** — Analyzes your request (app icon? character? scene?) and builds
   a detailed, model-specific prompt automatically.

2. **Provider Selection** — Tries API keys first (fal.ai, Together AI, Replicate, OpenAI,
   Stability AI). If none configured, falls back to browser automation.

3. **Browser Paths:**
   - **Higgsfield Nano Banana Pro** (`higgsfield.ai`) — cinematic/photorealistic, best for
     characters, avatars, stylized product renders. Requires Higgsfield account.
   - **Google Gemini** (`gemini.google.com`) — great for icons, logos, flat design, concepts.
     Requires Google login.

4. **Auto-download** — Saves the generated image to `_tmp/images/` and reports the path.

## Prompt Engineering

The skill detects the image type (app-icon, avatar, logo, character, scene, product, photo,
illustration) and applies category-specific templates with smart defaults:
- Color palettes derived from subject name/theme
- Lighting and composition suited to the image type
- Model-specific modifiers (Nano Banana Pro vs Gemini vs FLUX vs DALL-E)

## Setup (API path — optional)

Add at least one key to your `.env`:

```
TOGETHER_API_KEY=...   # Free tier: FLUX.1-schnell-Free
FAL_KEY=...            # ~$0.003/image
REPLICATE_API_TOKEN=...
OPENAI_API_KEY=...     # DALL-E 3 — best for text-in-image
STABILITY_API_KEY=...
```

If no keys: the skill uses browser automation automatically.

## Setup (Browser path)

- **Higgsfield**: Log into higgsfield.ai in Chrome
- **Gemini**: Log into google.com in Chrome

## Source

`claude-public` — Angel Hermon's public Claude/Paperclip plugins.
