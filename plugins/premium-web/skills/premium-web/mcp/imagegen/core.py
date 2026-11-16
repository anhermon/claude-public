"""premium-web imagegen core: art direction, providers, manifest, compare, optimise.

One module, three fronts: server.py (MCP over stdio), the CLI below, and the
skill's scripts/gen-image.sh + scripts/optimize-images.sh.

Rules this module enforces:
- Never write to stdout from library code (the MCP stdio transport owns it).
  Every child process (codex, vaultlet) gets stdout/stderr redirected to a log file.
- Secrets never enter this process. API providers run a child through
  `vaultlet run --ref vaultlet://<group>/<KEY>=<ENV> -- python3 api_call.py ...`,
  so only the child sees the key and vaultlet redacts it from the child's output.
- Idempotent output names: <slug>-<sha1(prompt|aspect|provider|variant)[:8]>.png.
  If the file exists, generation is skipped (a retry never regenerates or spends quota).
- Global limiter (all processes): min interval + hourly cap, file-locked.

Stdlib only, except Pillow for compare/optimise (imported lazily).
"""
from __future__ import annotations

import fcntl
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = Path(os.environ.get("IMAGEGEN_STATE", Path.home() / ".cache" / "premium-web-imagegen"))
VAULT_GROUP = os.environ.get("IMAGEGEN_VAULT_GROUP", "imagegen")
MIN_INTERVAL = float(os.environ.get("IMAGEGEN_MIN_INTERVAL", "5"))   # seconds between generations
HOURLY_CAP = int(os.environ.get("IMAGEGEN_HOURLY_CAP", "40"))        # generations per rolling hour
CODEX_TIMEOUT = int(os.environ.get("IMAGEGEN_CODEX_TIMEOUT", "600"))

# ---------------------------------------------------------------- art direction

NEGATIVE = (
    "Absolutely no text, letters, numbers, captions, watermarks, logos, user interface, screens, "
    "people, faces or hands. No glowing brains, robots, circuit boards, binary rain, "
    "fibre-optic stock imagery, lens-flare cliches or isometric icon clutter."
)

STYLE_PRESETS = {
    # Dark studio: what worked for anhermon v3 (one key light, one material, film grain).
    "dark-studio": (
        "Cinematic editorial product photography (or high-end 3D render), deep near-black ground {ground}, "
        "a single accent colour {accent} as the only saturated light, warm off-white {highlight} highlights, "
        "one soft key light from upper left, subtle film grain, shallow depth of field, calm expensive mood, "
        "generous negative space."
    ),
    # Light editorial: paper and daylight for warm, human subjects.
    "paper-editorial": (
        "Editorial still-life photography on a seamless warm paper sweep {ground}, soft north-window daylight, "
        "gentle long shadows, one accent object or detail in {accent}, ink-dark {highlight} shapes, "
        "fine grain, quiet premium print-magazine mood, generous negative space."
    ),
    # Neutral product: clean seamless studio, for hardware / physical products.
    "neutral-product": (
        "Clean studio product photography on a seamless mid-grey sweep {ground}, large soft box key light, "
        "subtle floor reflection, accent colour {accent} used once, crisp {highlight} edge highlights, "
        "photographic realism, generous negative space."
    ),
    # Tactile / clay (pebble, approved): soft matte 3D objects, consistent soft light, colour blocks.
    "tactile-clay": (
        "Soft matte clay 3D render, rounded chunky forms with subtle fingerprint-free surface texture, "
        "placed on a flat colour-block ground {ground}, one object or detail in {accent}, cream {highlight} "
        "secondary forms, large soft key light from upper left with a gentle contact shadow, playful but calm, "
        "consistent lighting across the set, generous negative space."
    ),
    # Cinematic film still (halcyon, approved): one light direction, film grade, a real place or object.
    "cinematic-film": (
        "Cinematic film still, anamorphic feel, shot on 35mm, natural light from one direction, deep shadows "
        "{ground}, a single warm accent of light {accent}, {highlight} highlights, gentle halation and film grain, "
        "a real place or physical object at human scale, quiet and expensive, generous negative space."
    ),
    # Terminal brand world: the place a CLI lives, never a picture of a terminal.
    "terminal-world": (
        "Night-time editorial photograph of the physical world a developer tool lives in (a machine room, a desk "
        "at 3am, a rack, a keyboard), practical light only, near-black ground {ground}, one coloured light source "
        "{accent}, {highlight} highlights, fine grain, documentary realism, no screens showing content, "
        "generous negative space."
    ),
    # Abstract material: texture plates, backdrops, grain tiles.
    "material-texture": (
        "Abstract macro material texture, evenly lit, low contrast, ground {ground}, faint {accent} tint, "
        "{highlight} micro highlights, no focal object, suitable as a quiet background."
    ),
}
DEFAULT_COLOURS = {"ground": "#0E0F12", "accent": "#7FA2FF", "highlight": "#ECE8DC"}

# slot -> (aspect, composition note)
SLOTS = {
    "hero": ("3:2", "Subject in the right third; the left 40% stays dark and empty for a headline."),
    "hero-mobile": ("4:5", "Subject centred in the upper half; the lower third stays empty for text."),
    "plate": ("4:5", "Single clear subject, centred, with breathing room on all sides."),
    "card": ("1:1", "Single small object, centred, lots of empty ground around it."),
    "backdrop": ("16:9", "No focal point; even, low-contrast field that text can sit on."),
    "og": ("16:9", "Subject in the right 45%; left 55% empty for text composited later (crop to 1.91:1)."),
    "texture": ("1:1", "Even, tileable-looking texture with no focal point."),
}

ASPECTS = {"1:1": (1024, 1024), "3:2": (1536, 1024), "2:3": (1024, 1536), "4:5": (1024, 1280),
           "5:4": (1280, 1024), "16:9": (1536, 864), "9:16": (864, 1536), "21:9": (1536, 658)}


def art_direct(brief: str, slot: str = "plate", style_preset: str = "dark-studio",
               colours: dict | None = None) -> dict:
    """Expand a one-line subject brief into a full, art-directed prompt."""
    if slot not in SLOTS:
        raise ValueError(f"unknown slot {slot!r}; one of {sorted(SLOTS)}")
    if style_preset not in STYLE_PRESETS:
        raise ValueError(f"unknown style_preset {style_preset!r}; one of {sorted(STYLE_PRESETS)}")
    aspect, comp = SLOTS[slot]
    w, h = ASPECTS[aspect]
    look = STYLE_PRESETS[style_preset].format(**{**DEFAULT_COLOURS, **(colours or {})})
    prompt = f"{aspect} image ({w}x{h}). {brief.strip().rstrip('.')}. {comp} {look} {NEGATIVE}"
    return {"prompt": prompt, "aspect": aspect, "slot": slot, "style_preset": style_preset,
            "checklist": ["Does it explain its section without a caption? If not, cut it.",
                          "Any stray text, letters, logos or UI? Reject.",
                          "Same light, palette and grain as the other images in the set?",
                          "Is the empty area where the copy will sit actually empty?"]}


# ---------------------------------------------------------------- naming, manifest, limiter

def slugify(s: str, n: int = 32) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n].strip("-") or "image"


def output_path(out_dir: str | Path, name: str | None, prompt: str, aspect: str, provider: str, variant: int) -> Path:
    key = hashlib.sha1(f"{prompt}|{aspect}|{provider}|{variant}".encode()).hexdigest()[:8]
    return Path(out_dir).expanduser() / f"{slugify(name or prompt)}-{key}.png"


def _manifest_path(img: Path) -> Path:
    return img.parent / "MANIFEST.md"


def manifest_add(img: Path, prompt: str, provider: str, status: str, aspect: str) -> None:
    mf = _manifest_path(img)
    if not mf.exists():
        mf.write_text("# Image manifest\n\n| file | provider | aspect | time | status | review | prompt |\n|---|---|---|---|---|---|---|\n")
    text = mf.read_text()
    if f"| {img.name} |" in text:  # idempotent: one row per file
        return
    p = prompt.replace("|", "/").replace("\n", " ")
    with mf.open("a") as f:
        f.write(f"| {img.name} | {provider} | {aspect} | {time.strftime('%Y-%m-%d %H:%M')} | {status} | TODO | {p} |\n")


def record_review(path: str, verdict: str, note: str = "") -> dict:
    """Set the review cell for an image in its MANIFEST.md (verdict: keep / cut / redo)."""
    img = Path(path).expanduser()
    mf = _manifest_path(img)
    if not mf.exists():
        raise FileNotFoundError(mf)
    lines = mf.read_text().splitlines()
    cell = f"{verdict}{(': ' + note.replace('|', '/')) if note else ''}"
    for i, ln in enumerate(lines):
        if ln.startswith(f"| {img.name} |"):
            cols = ln.split(" | ")
            cols[5] = cell
            lines[i] = " | ".join(cols)
            mf.write_text("\n".join(lines) + "\n")
            return {"file": str(img), "review": cell}
    raise KeyError(f"{img.name} not in {mf}")


class RateLimited(RuntimeError):
    pass


def limiter_acquire(now: float | None = None) -> None:
    """Global (cross-process) limiter. Raises RateLimited when the hourly cap is hit; sleeps for the min interval."""
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / "limiter.json", "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        try:
            stamps = json.loads(f.read() or "[]")
        except json.JSONDecodeError:
            stamps = []
        t = now if now is not None else time.time()
        stamps = [s for s in stamps if t - s < 3600]
        if len(stamps) >= HOURLY_CAP:
            raise RateLimited(f"hourly cap {HOURLY_CAP} reached; next slot in {int(3600 - (t - stamps[0]))}s")
        wait = MIN_INTERVAL - (t - stamps[-1]) if stamps else 0
        if wait > 0 and now is None:
            time.sleep(wait)
            t = time.time()
        stamps.append(t)
        f.seek(0); f.truncate(); f.write(json.dumps(stamps))


# ---------------------------------------------------------------- providers

@dataclass
class Result:
    status: str          # generated | exists | failed | needs_browser_agent
    path: str
    provider: str
    detail: str = ""
    job_id: str = ""


class Provider:
    name = "base"

    def available(self) -> tuple[bool, str]:
        raise NotImplementedError

    def generate(self, prompt: str, aspect: str, out: Path, log: Path) -> Result:
        raise NotImplementedError


class CodexProvider(Provider):
    """Shells out to `codex exec`; Codex's built-in image tool writes to ~/.codex/generated_images/<session>/."""
    name = "codex"

    def available(self):
        if not shutil.which("codex"):
            return False, "codex CLI not on PATH"
        return True, "codex CLI found (uses the ChatGPT-plan image tool; quota-limited)"

    def generate(self, prompt, aspect, out, log):
        w, h = ASPECTS.get(aspect, (1024, 1024))
        job = (f"Generate exactly one image with your image generation tool from this prompt, and save it as {out} "
               f"(copy the generated file there). Do not add any text to the image. Honor the requested aspect ratio "
               f"{aspect} ({w}x{h}). Prompt: {prompt}")
        start = time.time()
        try:
            with open(log, "w") as lf:
                subprocess.run(["codex", "exec", "--skip-git-repo-check", "--sandbox", "workspace-write",
                                     "-C", str(out.parent), "-"], input=job.encode(), stdout=lf, stderr=subprocess.STDOUT,
                                    timeout=CODEX_TIMEOUT, check=False)
        except subprocess.TimeoutExpired:
            return Result("failed", str(out), self.name, f"codex timed out after {CODEX_TIMEOUT}s; see {log}")
        text = log.read_text(errors="replace") if log.exists() else ""
        if not out.exists():
            # Codex generated but did not copy. Only adopt a generated_images path named in OUR log. Never "newest
            # file after start": other codex sessions write there too, and on 2026-10-01 that adopted another
            # agent's image while this run had actually hit the usage limit (codex still exited 0).
            gen = os.environ.get("CODEX_GENERATED_DIR", str(Path.home() / ".codex" / "generated_images"))
            named = [p for p in re.findall(re.escape(gen) + r"/[\w-]+/[\w.-]+\.png", text) if os.path.exists(p)]
            if named:
                shutil.copy(named[-1], out)
        if out.exists():
            return Result("generated", str(out), self.name, f"log: {log}")
        m = re.search(r"usage limit.*?(try again at [^.\n]+)", text, re.I)
        hint = f"codex quota/usage limit ({m.group(1)})" if m else ("codex quota/usage limit" if re.search(r"usage limit|rate limit|quota", text, re.I) else "no image produced")
        return Result("failed", str(out), self.name, f"{hint}; see {log}")


# API providers: (vault key name, env var name, adapter in api_call.py)
API_PROVIDERS = {
    "openai": "OPENAI_API_KEY",
    "fal": "FAL_KEY",
    "gemini-api": "GEMINI_API_KEY",
    "together": "TOGETHER_API_KEY",
    "replicate": "REPLICATE_API_TOKEN",
}


def vault_keys(group: str = VAULT_GROUP) -> set[str]:
    """Key NAMES in a vaultlet/sealref group (never values)."""
    exe = shutil.which("vaultlet") or shutil.which("sealref")
    if not exe:
        return set()
    try:
        r = subprocess.run([exe, "keys", group], capture_output=True, text=True, timeout=15)
    except (subprocess.TimeoutExpired, OSError):
        return set()
    return {ln.split()[0] for ln in r.stdout.splitlines() if ln.strip()}


class ApiProvider(Provider):
    def __init__(self, name: str, key: str):
        self.name, self.key = name, key

    def available(self):
        if not (shutil.which("vaultlet") or shutil.which("sealref")):
            return False, "vaultlet/sealref not on PATH"
        if self.key not in vault_keys():
            return False, f"no {self.key} in vaultlet group '{VAULT_GROUP}' (add it with vaultlet request {VAULT_GROUP} {self.key})"
        return True, f"{self.key} present in vaultlet group '{VAULT_GROUP}'"

    def generate(self, prompt, aspect, out, log):
        exe = shutil.which("vaultlet") or shutil.which("sealref")
        ref = f"vaultlet://{VAULT_GROUP}/{self.key}={self.key}"
        cmd = [exe, "run", "--ref", ref, "--", sys.executable, str(HERE / "api_call.py"), self.name, aspect, str(out)]
        try:
            with open(log, "w") as lf:
                subprocess.run(cmd, input=prompt.encode(), stdout=lf, stderr=subprocess.STDOUT, timeout=300, check=False)
        except subprocess.TimeoutExpired:
            return Result("failed", str(out), self.name, f"timed out; see {log}")
        if out.exists():
            return Result("generated", str(out), self.name, f"log: {log}")
        return Result("failed", str(out), self.name, f"no image written; see {log}")


BROWSER_STEPS = {
    "gemini-web": [
        "Use the claude-in-chrome tools in Angel's own logged-in Chrome (tabs_context_mcp, then tabs_create_mcp).",
        "Open https://gemini.google.com/app and start a new chat.",
        "Paste the prompt below exactly; ask for one image at the stated aspect ratio.",
        "Wait for the image. KNOWN: the UI download button and blob->localhost POST both FAILED in 2026-10 tests; "
        "capture with a tight screenshot of the image only (computer tool zoom/screenshot), not the chat chrome.",
        "Save the capture to a local file, then call complete_browser_job(job_id, path). Note in the review that it is a screenshot (lower resolution).",
        "Stop on any CAPTCHA, login prompt or credential request: do not solve or enter anything; report back.",
    ],
    "higgsfield": [
        "Use the claude-in-chrome tools in Angel's own logged-in Chrome.",
        "Open https://higgsfield.ai and choose the Nano Banana Pro image model (or the model named in the job).",
        "Paste the prompt below; set the aspect ratio; generate one image.",
        "Try the site's own download first; if it fails, take a tight screenshot of the image.",
        "Save it locally, then call complete_browser_job(job_id, path).",
        "Stop on any CAPTCHA, paywall, login or credential request; never enter credentials; report back.",
    ],
}


class BrowserProvider(Provider):
    """Handoff: an MCP server cannot drive Angel's Chrome. Writes a job file for an agent with claude-in-chrome."""

    def __init__(self, name: str):
        self.name = name

    def available(self):
        return True, "handoff only: returns needs_browser_agent with a job file for a claude-in-chrome agent"

    def generate(self, prompt, aspect, out, log):
        jobs = STATE / "browser-jobs"
        jobs.mkdir(parents=True, exist_ok=True)
        job_id = f"{self.name}-{out.stem}"
        job = {"job_id": job_id, "provider": self.name, "prompt": prompt, "aspect": aspect,
               "expected_output": str(out), "steps": BROWSER_STEPS[self.name],
               "terms_note": "Grey area: automating a consumer web UI. Allowed here only as Angel-authorised, "
                             "his own session, low volume, no CAPTCHA solving, no credential entry.",
               "created": time.strftime("%Y-%m-%dT%H:%M:%S")}
        (jobs / f"{job_id}.json").write_text(json.dumps(job, indent=2))
        return Result("needs_browser_agent", str(out), self.name, f"job file: {jobs / (job_id + '.json')}", job_id)


class LocalProvider(Provider):
    """Local MLX fallback (Apple Silicon): FLUX.2-klein-4B draft / Z-Image-Turbo final. No network, no quota."""
    name = "local"
    LG = Path(os.environ.get("IMAGEGEN_LOCALGEN", Path.home() / "dev" / "local-imagegen" / "localgen"))

    def available(self):
        return (self.LG.exists(), "localgen found (offline, ~1-3 min/img, needs ~12GB free RAM)" if self.LG.exists() else f"{self.LG} missing")

    def generate(self, prompt, aspect, out, log):
        w, h = ASPECTS.get(aspect, (1024, 1024))
        q = os.environ.get("IMAGEGEN_LOCAL_QUALITY", "final")  # draft|final per localgen --help
        with open(log, "w") as lf:
            subprocess.run([str(self.LG), prompt, "--size", f"{w}x{h}", "--quality", q, "--out", str(out)],
                           stdout=lf, stderr=subprocess.STDOUT, timeout=900, check=False)
        return Result("generated" if out.exists() else "failed", str(out), self.name, f"log: {log}")


def providers() -> dict[str, Provider]:
    ps: dict[str, Provider] = {"codex": CodexProvider(), "local": LocalProvider()}
    ps.update({n: ApiProvider(n, k) for n, k in API_PROVIDERS.items()})
    ps.update({n: BrowserProvider(n) for n in BROWSER_STEPS})
    return ps


def list_providers() -> list[dict]:
    out = []
    for name, p in providers().items():
        ok, why = p.available()
        out.append({"provider": name, "usable": ok, "why": why})
    return out


AUTO_ORDER = ["codex", "local", "openai", "gemini-api", "fal", "together", "replicate", "gemini-web"]


def generate_image(prompt: str, aspect: str = "1:1", out_dir: str = ".", name: str | None = None,
                   provider: str = "auto", variants: int = 1, style_preset: str | None = None,
                   colours: dict | None = None) -> list[dict]:
    """Generate `variants` images. With style_preset set, `prompt` is treated as a brief and art-directed (slot 'plate'
    unless aspect says otherwise). Returns one dict per variant."""
    if aspect not in ASPECTS:
        raise ValueError(f"unsupported aspect {aspect!r}; one of {sorted(ASPECTS)}")
    if style_preset:
        slot = next((s for s, (a, _) in SLOTS.items() if a == aspect), "plate")
        prompt = art_direct(prompt, slot, style_preset, colours)["prompt"]
    ps = providers()
    if provider == "auto":
        # Fall through to the next usable provider when one fails (e.g. codex quota / usage limit).
        tried = []
        for n in [n for n in AUTO_ORDER if ps[n].available()[0]] or ["gemini-web"]:
            res = _generate_with(ps, n, prompt, aspect, out_dir, name, variants)
            if not any(r["status"] == "failed" for r in res):
                return res
            tried.append(f"{n}: {res[0].get('detail', '')}")
            last = res
        for r in last:
            r["detail"] = f"{r.get('detail', '')} [auto tried: {' | '.join(tried)}]"
        return last
    return _generate_with(ps, provider, prompt, aspect, out_dir, name, variants)


def _generate_with(ps, provider, prompt, aspect, out_dir, name, variants) -> list[dict]:
    if provider not in ps:
        raise ValueError(f"unknown provider {provider!r}; one of {sorted(ps)}")
    p = ps[provider]
    ok, why = p.available()
    if not ok:
        return [{"status": "failed", "provider": provider, "detail": why}]
    Path(out_dir).expanduser().mkdir(parents=True, exist_ok=True)
    results = []
    for v in range(max(1, min(int(variants), 4))):
        vp = prompt if v == 0 else f"{prompt} (variation {v + 1}: a different composition of the same idea)"
        out = output_path(out_dir, name, vp, aspect, provider, v)
        if out.exists():
            results.append(Result("exists", str(out), provider, "already generated; delete it to regenerate").__dict__)
            continue
        if not isinstance(p, BrowserProvider):
            try:
                limiter_acquire()
            except RateLimited as e:
                results.append(Result("failed", str(out), provider, str(e)).__dict__)
                break
        r = p.generate(vp, aspect, out, out.with_suffix(".log"))
        if r.status == "generated":
            manifest_add(out, vp, provider, "generated", aspect)
            r.detail += f"; {image_info(out)}"
        results.append(r.__dict__)
    return results


def complete_browser_job(job_id: str, path: str) -> dict:
    job_file = STATE / "browser-jobs" / f"{job_id}.json"
    job = json.loads(job_file.read_text())
    src, dst = Path(path).expanduser(), Path(job["expected_output"])
    if not src.exists():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() != ".png":
        from PIL import Image
        Image.open(src).convert("RGB").save(dst)
    elif src.resolve() != dst.resolve():
        shutil.copy(src, dst)
    manifest_add(dst, job["prompt"], job["provider"] + " (browser capture)", "captured", job["aspect"])
    job["completed"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    job_file.write_text(json.dumps(job, indent=2))
    return {"status": "registered", "path": str(dst), "info": image_info(dst)}


# ---------------------------------------------------------------- compare / optimise (Pillow)

def image_info(path: str | Path) -> str:
    try:
        from PIL import Image
        with Image.open(path) as im:
            return f"{im.width}x{im.height} {Path(path).stat().st_size // 1024}KB"
    except Exception as e:  # Pillow missing or unreadable
        return f"info unavailable ({e.__class__.__name__})"


def dhash(path: str | Path, size: int = 8) -> int:
    from PIL import Image
    with Image.open(path) as im:
        g = im.convert("L").resize((size + 1, size), Image.LANCZOS)
        px = list(g.getdata())
    bits = 0
    for r in range(size):
        for c in range(size):
            bits = (bits << 1) | (px[r * (size + 1) + c] > px[r * (size + 1) + c + 1])
    return bits


def compare(paths: list[str], out: str | None = None, target_aspect: str | None = None, max_kb: int = 4096) -> dict:
    """Contact sheet + checks: dimensions, aspect drift, file size, near-duplicates (dHash). No text detection:
    there is no cheap reliable heuristic, so stray text stays a human check."""
    from PIL import Image, ImageDraw
    ps = [Path(p).expanduser() for p in paths]
    rows, hashes = [], {}
    for p in ps:
        with Image.open(p) as im:
            w, h = im.size
        row = {"file": str(p), "w": w, "h": h, "kb": p.stat().st_size // 1024, "flags": []}
        if target_aspect:
            tw, th = ASPECTS[target_aspect]
            if abs(w / h - tw / th) > 0.03:
                row["flags"].append(f"aspect {w}:{h} != {target_aspect}")
        if row["kb"] > max_kb:
            row["flags"].append(f"source {row['kb']}KB > {max_kb}KB (fine for a master; optimise before shipping)")
        hashes[str(p)] = dhash(p)
        rows.append(row)
    keys = list(hashes)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            d = bin(hashes[a] ^ hashes[b]).count("1")
            if d <= 6:
                for r in rows:
                    if r["file"] in (a, b):
                        r["flags"].append(f"near-duplicate of {Path(b if r['file'] == a else a).name} (dHash {d}/64)")
    # contact sheet: 360px-high thumbs in a row-wrapped grid, filename under each
    th, pad, label = 360, 16, 22
    thumbs = []
    for p in ps:
        with Image.open(p) as im:
            t = im.convert("RGB"); t.thumbnail((th * 2, th)); thumbs.append((p.name, t))
    cols = min(4, len(thumbs)) or 1
    cw = max(t.width for _, t in thumbs) + pad
    rows_n = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw + pad, rows_n * (th + label + pad) + pad), (24, 24, 26))
    d = ImageDraw.Draw(sheet)
    for i, (n, t) in enumerate(thumbs):
        x, y = pad + (i % cols) * cw, pad + (i // cols) * (th + label + pad)
        sheet.paste(t, (x, y)); d.text((x, y + th + 4), n[:60], fill=(220, 220, 220))
    out_p = Path(out).expanduser() if out else ps[0].parent / "contact-sheet.png"
    sheet.save(out_p)
    return {"contact_sheet": str(out_p), "images": rows,
            "reminder": "Open the contact sheet and LOOK: stray text/logos, does each image explain its section?"}


def optimise(path: str, widths: list[int] | None = None, formats: list[str] | None = None, out_dir: str | None = None,
             name: str | None = None, crop: list[int] | None = None, budget_kb: int | None = None,
             avif_q: int = 50, webp_q: int = 72) -> dict:
    """Responsive AVIF/WebP set. crop = [left, top, width, height] in source px. Never upscales."""
    from PIL import Image
    src = Path(path).expanduser()
    widths = sorted(widths or [640, 1024, 1536])
    formats = formats or ["avif", "webp"]
    od = Path(out_dir).expanduser() if out_dir else src.parent
    od.mkdir(parents=True, exist_ok=True)
    base = name or slugify(src.stem)
    files, warn = [], []
    with Image.open(src) as im0:
        im0 = im0.convert("RGB")
        if crop:
            l, t, w, h = crop
            im0 = im0.crop((l, t, l + w, t + h))
        for w in widths:
            if w > im0.width:
                warn.append(f"skip {w}w: source is only {im0.width}px wide (no upscaling)")
                continue
            im = im0.resize((w, round(im0.height * w / im0.width)), Image.LANCZOS)
            for fmt in formats:
                f = od / f"{base}-{w}.{fmt}"
                if fmt == "avif":
                    im.save(f, "AVIF", quality=avif_q, speed=4)
                elif fmt == "webp":
                    im.save(f, "WEBP", quality=webp_q, method=6)
                elif fmt == "jpg":
                    im.save(f, "JPEG", quality=80, optimize=True, progressive=True)
                else:
                    raise ValueError(f"format {fmt!r} not supported (avif, webp, jpg)")
                kb = f.stat().st_size // 1024
                files.append({"file": str(f), "w": w, "h": im.height, "kb": kb})
                if budget_kb and kb > budget_kb:
                    warn.append(f"{f.name} {kb}KB > budget {budget_kb}KB")
    srcset = {fmt: ", ".join(f"{Path(x['file']).name} {x['w']}w" for x in files if x["file"].endswith(fmt)) for fmt in formats}
    return {"files": files, "srcset": srcset, "warnings": warn}


# ---------------------------------------------------------------- CLI

COLOURS_HELP = "page tokens that replace the preset's default hexes, e.g. ground=#F2EFE8,accent=#2F4B6E,highlight=#14131A"


def _colours(spec: str | None) -> dict | None:
    return dict(kv.split("=", 1) for kv in spec.split(",")) if spec else None


def _cli(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="imagegen", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen"); g.add_argument("prompt"); g.add_argument("--aspect", default="1:1")
    g.add_argument("--out-dir", default="."); g.add_argument("--name"); g.add_argument("--provider", default="auto")
    g.add_argument("--variants", type=int, default=1); g.add_argument("--style-preset"); g.add_argument("--colours", help=COLOURS_HELP)
    a = sub.add_parser("art"); a.add_argument("brief"); a.add_argument("--slot", default="plate"); a.add_argument("--style-preset", default="dark-studio"); a.add_argument("--colours", help=COLOURS_HELP)
    sub.add_parser("providers")
    c = sub.add_parser("compare"); c.add_argument("paths", nargs="+"); c.add_argument("--out"); c.add_argument("--aspect")
    o = sub.add_parser("optimise"); o.add_argument("path"); o.add_argument("--widths", default="640,1024,1536")
    o.add_argument("--formats", default="avif,webp"); o.add_argument("--out-dir"); o.add_argument("--name")
    o.add_argument("--crop", help="left,top,width,height"); o.add_argument("--budget-kb", type=int)
    r = sub.add_parser("review"); r.add_argument("path"); r.add_argument("verdict"); r.add_argument("--note", default="")
    b = sub.add_parser("complete"); b.add_argument("job_id"); b.add_argument("path")
    x = ap.parse_args(argv)
    if x.cmd == "gen":
        res = generate_image(x.prompt, x.aspect, x.out_dir, x.name, x.provider, x.variants, x.style_preset, _colours(x.colours))
    elif x.cmd == "art":
        res = art_direct(x.brief, x.slot, x.style_preset, _colours(x.colours))
    elif x.cmd == "providers":
        res = list_providers()
    elif x.cmd == "compare":
        res = compare(x.paths, x.out, x.aspect)
    elif x.cmd == "optimise":
        res = optimise(x.path, [int(w) for w in x.widths.split(",")], x.formats.split(","), x.out_dir, x.name,
                       [int(v) for v in x.crop.split(",")] if x.crop else None, x.budget_kb)
    elif x.cmd == "review":
        res = record_review(x.path, x.verdict, x.note)
    else:
        res = complete_browser_job(x.job_id, x.path)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
