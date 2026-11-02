#!/usr/bin/env python3
"""premium-web-imagery pipeline: capability detection, art-directed prompts, post-processing, procedural fallback.

  python3 pipeline.py detect                      what this machine can generate with (MCP tools are session-level: check your tool list too)
  python3 pipeline.py prompts [--config C]        one prompt per asset, same style sheet + seed -> prompts.json
  python3 pipeline.py post ID|FILE [--config C]   trim, matte, grade, grain, resize, AVIF/WebP, srcset, budget check
  python3 pipeline.py fallback ID [--config C]    procedural plate from the palette (use when nothing can generate; flagged in the manifest)

Pillow only (no numpy). Never writes generated assets into the skill: raw/ and out/ are paths in YOUR project (config.paths).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageFilter

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE / "imagery.config.json"
GRAIN_TILE = 256            # px; tiled noise, seeded so reruns are byte-identical
GRAIN_SIGMA = 0.5           # std-dev of the noise tile = GRAIN_SIGMA * 255 / 4 around mid grey
GRAIN_GAIN = 8.0            # config grain_amount -> overlay blend factor
TRIM_TOLERANCE = 12         # per-channel distance from the border colour still counted as background
TRIM_PAD = 8                # px kept around the trimmed subject
VIGNETTE_STRENGTH = 0.35    # fallback plate edge darkening
ASPECT_BASE = 1536          # px, long edge of a generated/fallback source
RASTER_FORMATS = {"avif": "AVIF", "webp": "WEBP"}
QUALITY = {"avif": 55, "webp": 80}   # visually safe starting points; lower for backdrops via budget loop
QUALITY_STEP = 8
QUALITY_FLOOR = 30

CAPABILITY_BINARIES = {"codex": "codex image generation (ChatGPT login)", "ffmpeg": "video/scrub-media encode",
                       "cwebp": "WebP CLI (optional)", "localgen": "local FLUX / Z-Image CLI (optional)"}
CAPABILITY_ENV = {"OPENAI_API_KEY": "openai image API", "GEMINI_API_KEY": "gemini image API", "FAL_KEY": "fal.ai",
                  "TOGETHER_API_KEY": "together.ai", "REPLICATE_API_TOKEN": "replicate"}


def load(path: str | None) -> dict:
    p = Path(path) if path else DEFAULT_CONFIG
    cfg = json.loads(p.read_text())
    cfg["_dir"] = str(p.resolve().parent)
    return cfg


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def aspect_size(aspect: str, base: int = ASPECT_BASE) -> tuple[int, int]:
    a, b = (int(v) for v in aspect.split(":"))
    return (base, round(base * b / a)) if a >= b else (round(base * a / b), base)


# ------------------------------------------------------------------ detect
def detect() -> dict:
    found = {k: {"available": bool(shutil.which(k)), "for": v} for k, v in CAPABILITY_BINARIES.items()}
    keys = {k: {"available": bool(os.environ.get(k)), "for": v} for k, v in CAPABILITY_ENV.items()}
    local_cfg = os.environ.get("IMAGEGEN_LOCALGEN")
    if local_cfg and Path(local_cfg).exists():
        found["localgen"] = {"available": True, "for": CAPABILITY_BINARIES["localgen"]}
    can_generate = found["codex"]["available"] or found["localgen"]["available"] or any(v["available"] for v in keys.values())
    return {"binaries": found, "api_keys_in_env": keys, "can_generate_here": can_generate,
            "mcp_note": "MCP image/video tools cannot be seen from a script: list your session tools (premium-web-imagegen, any *image*/*video* tool).",
            "fallback": None if can_generate else "procedural: python3 pipeline.py fallback ID, or hand off to premium-web-svg / premium-web-webgl"}


# ------------------------------------------------------------------ prompts
def build_prompt(cfg: dict, asset: dict) -> dict:
    s, slot = cfg["style"], cfg["slots"][asset["slot"]]
    w, h = aspect_size(slot["aspect"], 1024)
    pal = s["palette"]
    look = (f"{s['mood']}; {s['light']}; {s['material']}; {s['grain']}; deep ground {pal['ground']}, "
            f"single accent {pal['accent']}, highlights {pal['highlight']}")
    text = f"{slot['aspect']} image ({w}x{h}). {asset['brief'].strip().rstrip('.')}. {slot['note']} {look}. {s['negative']}."
    return {"id": asset["id"], "slot": asset["slot"], "aspect": slot["aspect"], "seed": s["seed"], "prompt": text}


def cmd_prompts(cfg: dict) -> list[dict]:
    out = [build_prompt(cfg, a) for a in cfg["assets"]]
    Path(cfg["_dir"], "prompts.json").write_text(json.dumps(out, indent=2))
    return out


# ------------------------------------------------------------------ post
def grain_tile(seed: int) -> Image.Image:
    rng = random.Random(seed)
    data = bytes(max(0, min(255, round(rng.gauss(128, GRAIN_SIGMA * 255 / 4)))) for _ in range(GRAIN_TILE * GRAIN_TILE))
    return Image.frombytes("L", (GRAIN_TILE, GRAIN_TILE), data)


def add_grain(img: Image.Image, amount: float, seed: int) -> Image.Image:
    """Seeded mid-grey noise overlaid and blended by `amount` (0.03-0.05 is visible on dark grounds, invisible on JPEG-ish compression)."""
    if amount <= 0:
        return img
    tile, layer = grain_tile(seed), Image.new("L", img.size)
    for x in range(0, img.width, GRAIN_TILE):
        for y in range(0, img.height, GRAIN_TILE):
            layer.paste(tile, (x, y))
    return Image.blend(img, ImageChops.overlay(img, layer.convert("RGB")), min(1.0, amount * GRAIN_GAIN))


def trim(img: Image.Image, matte: tuple[int, int, int]) -> Image.Image:
    """Crop uniform border (alpha or matte colour) so the subject sits tight; keeps TRIM_PAD."""
    if img.mode == "RGBA":
        box = img.getchannel("A").point(lambda a: 255 if a > TRIM_TOLERANCE else 0).getbbox()
    else:
        diff = ImageChops.difference(img.convert("RGB"), Image.new("RGB", img.size, matte)).convert("L")
        box = diff.point(lambda v: 255 if v > TRIM_TOLERANCE else 0).getbbox()
    if not box:
        return img
    l, t, r, b = box
    return img.crop((max(0, l - TRIM_PAD), max(0, t - TRIM_PAD), min(img.width, r + TRIM_PAD), min(img.height, b + TRIM_PAD)))


def process(src: Path, cfg: dict, asset_id: str) -> dict:
    p = cfg["post"]
    img = Image.open(src)
    asset = next((a for a in cfg["assets"] if a["id"] == asset_id), {})
    if asset.get("trim"):       # cut-out subjects only: a full-bleed plate must not be trimmed
        img = trim(img, hex_rgb(p["matte"]))
    if img.mode == "RGBA":   # flatten transparency onto the page ground
        base = Image.new("RGB", img.size, hex_rgb(p["matte"]))
        base.paste(img, mask=img.getchannel("A"))
        img = base
    img = img.convert("RGB")
    g = p["grade"]
    img = ImageEnhance.Contrast(img).enhance(g["contrast"])
    img = ImageEnhance.Color(img).enhance(g["saturation"])
    img = ImageEnhance.Brightness(img).enhance(g["brightness"])
    img = add_grain(img, p["grain_amount"], cfg["style"]["seed"])
    slot = asset.get("slot", "")
    budget = p["budget_kb"].get(slot, p["default_budget_kb"]) * 1024
    out_dir = Path(cfg["_dir"], cfg["paths"]["out"])
    out_dir.mkdir(parents=True, exist_ok=True)
    files, srcset, warnings = [], {}, []
    widths = sorted({w for w in p["widths"] if w <= img.width}) or [img.width]   # never upscale
    for fmt in p["formats"]:
        for w in widths:
            im = img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
            q, path = QUALITY[fmt], out_dir / f"{asset_id}-{w}.{fmt}"
            while True:
                im.save(path, RASTER_FORMATS[fmt], quality=q)
                if path.stat().st_size <= budget or q <= QUALITY_FLOOR:
                    break
                q -= QUALITY_STEP
            if path.stat().st_size > budget:
                warnings.append(f"{path.name} {path.stat().st_size // 1024} KB > budget {budget // 1024} KB at q{q}")
            files.append({"file": str(path), "w": w, "h": im.height, "kb": round(path.stat().st_size / 1024, 1), "q": q})
            srcset.setdefault(fmt, []).append(f"{cfg['paths']['out']}/{path.name} {w}w")
    return {"id": asset_id, "source": str(src), "files": files,
            "srcset": {k: ", ".join(v) for k, v in srcset.items()}, "warnings": warnings}


def find_raw(cfg: dict, target: str) -> tuple[Path, str]:
    if Path(target).is_file():
        return Path(target), Path(target).stem
    raw = Path(cfg["_dir"], cfg["paths"]["raw"])
    hits = [q for ext in ("png", "jpg", "jpeg", "webp") for q in raw.glob(f"{target}*.{ext}")]
    if not hits:
        sys.exit(f"no raw image for '{target}' in {raw}")
    return sorted(hits)[0], target


# ------------------------------------------------------------------ fallback
def fallback_plate(cfg: dict, asset_id: str) -> Path:
    """Soft light field + vignette in the palette. A background plate, not a subject: say so in the report."""
    a = next(x for x in cfg["assets"] if x["id"] == asset_id)
    w, h = aspect_size(cfg["slots"][a["slot"]]["aspect"])
    pal = {k: hex_rgb(v) for k, v in cfg["style"]["palette"].items()}
    rng = random.Random(f"{cfg['style']['seed']}-{asset_id}")
    cx, cy = rng.uniform(0.55, 0.85) * w, rng.uniform(0.2, 0.5) * h
    img = Image.new("RGB", (w, h), pal["ground"])
    glow = Image.new("L", (w // 8, h // 8))
    gw, gh = glow.size
    glow.putdata([int(255 * math.exp(-(((x * 8 - cx) / (0.55 * w)) ** 2 + ((y * 8 - cy) / (0.55 * h)) ** 2) * 2.2))
                  for y in range(gh) for x in range(gw)])
    glow = glow.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
    tint = Image.blend(Image.new("RGB", (w, h), pal["accent"]), Image.new("RGB", (w, h), pal["highlight"]), 0.25)
    img = Image.composite(Image.blend(img, tint, 0.55), img, glow)
    vig = Image.new("L", (w // 8, h // 8))
    vig.putdata([int(255 * min(1, ((x / gw - .5) ** 2 + (y / gh - .5) ** 2) * 2.4 * VIGNETTE_STRENGTH * 2))
                 for y in range(gh) for x in range(gw)])
    img = Image.composite(Image.new("RGB", (w, h), pal["ground"]), img, vig.resize((w, h), Image.BICUBIC))
    raw = Path(cfg["_dir"], cfg["paths"]["raw"])
    raw.mkdir(parents=True, exist_ok=True)
    out = raw / f"{asset_id}-procedural.png"
    img.save(out)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["detect", "prompts", "post", "fallback"])
    ap.add_argument("target", nargs="?")
    ap.add_argument("--config")
    x = ap.parse_args(argv)
    if x.cmd == "detect":
        res = detect()
    else:
        cfg = load(x.config)
        if x.cmd == "prompts":
            res = cmd_prompts(cfg)
        elif x.cmd == "fallback":
            res = {"procedural": True, "file": str(fallback_plate(cfg, x.target))}
        else:
            src, aid = find_raw(cfg, x.target)
            res = process(src, cfg, aid)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
