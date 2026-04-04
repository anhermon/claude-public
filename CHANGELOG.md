# Changelog

## [0.2.0] — 2026-04-04

### Added — image-gen plugin

- **Prompt Engineering Engine** — detects image type (`app-icon`, `logo`, `avatar`, `character`,
  `scene`, `product`, `photo`, `illustration`) and builds rich, model-specific prompts
  automatically from brief descriptions
- **Higgsfield Nano Banana Pro browser path** — navigates higgsfield.ai, selects the model,
  submits prompt, waits for generation, downloads result
- **Google Gemini browser path** — fallback when no API keys and/or Higgsfield login unavailable;
  navigates gemini.google.com, submits engineered prompt, downloads result
- **API provider support** — fal.ai (FLUX schnell), Together AI (FLUX Free), Replicate,
  OpenAI DALL-E 3, Stability AI Core; auto-detected from `.env`
- **Provider memory** — caches detected providers so detection only runs once
- **Smart path selection** — checks explicit model mention in prompt → API keys → browser
  (Higgsfield first, Gemini fallback)

### Model-specific prompt modifiers

- **Nano Banana Pro** — reframes icon/logo requests as stylized product renders
  (cinematic model, not flat-design native)
- **Gemini** — keeps prompts clear and conceptual; handles flat design well
- **FLUX / DALL-E / Stability** — appended quality boosters per provider

### Tested

- Anvil app icon (`app-icon` type) via Gemini: charcoal + iron-grey + ember orange,
  3D metallic depth, forge-heat glow line across top face ✓
