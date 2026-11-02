"""premium-web imagegen MCP server (stdio). Thin wrapper over core.py.

HARD RULE: nothing here writes to stdout (it is the JSON-RPC transport). Logging goes to stderr;
child processes write to per-image .log files (see core.py).

Register (user scope), from any directory:
  claude mcp add premium-web-imagegen -- uv run --with mcp==1.29.0 --with pillow==12.3.0 \
    python ~/.claude/skills/premium-web/mcp/imagegen/server.py
"""
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # run as a file, not a package

from mcp.server.fastmcp import FastMCP  # noqa: E402

import core  # noqa: E402

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
mcp = FastMCP("premium-web-imagegen")


@mcp.tool()
def list_providers() -> list:
    """Which image providers are usable right now, and why not. codex = `codex exec` image tool (ChatGPT plan quota);
    openai/fal/gemini-api/together/replicate = API, usable only when the key exists in secrets runner (never read here);
    gemini-web/higgsfield = browser handoff (returns needs_browser_agent + a job file for a claude-in-chrome agent)."""
    return core.list_providers()


@mcp.tool()
def art_direct(brief: str, slot: str = "plate", style_preset: str = "dark-studio", colours: dict | None = None) -> dict:
    """Expand a one-line subject brief into a full prompt: shared look (light, material, palette, grain), slot
    composition (hero, hero-mobile, plate, card, backdrop, og, texture) and the negative list (no text, logos,
    people, UI, cliches). Presets: dark-studio, paper-editorial, neutral-product, material-texture.
    The brief must say what the image COMMUNICATES for its section, not just what it looks like.
    colours={ground, accent, highlight} hex values replace the preset defaults: pass the PAGE's tokens, or a light/muted brief
    gets the dark-blue defaults baked in."""
    return core.art_direct(brief, slot, style_preset, colours)


@mcp.tool()
def generate_image(prompt: str, aspect: str = "1:1", out_dir: str = ".", name: str = "", provider: str = "auto",
                   variants: int = 1, style_preset: str = "", colours: dict | None = None) -> list:
    """Generate 1-4 images. Output names are idempotent (<name>-<hash>.png): an existing file is returned with
    status 'exists' and nothing is regenerated. Each image gets a MANIFEST.md row in out_dir. Aspects: 1:1 3:2 2:3
    4:5 5:4 16:9 9:16 21:9. If style_preset is set, prompt is treated as a brief and art-directed first.
    Status per image: generated | exists | failed | needs_browser_agent (then follow the job file and call
    complete_browser_job). A global limiter spaces requests and caps them per hour."""
    return core.generate_image(prompt, aspect, out_dir, name or None, provider, variants, style_preset or None, colours)


@mcp.tool()
def complete_browser_job(job_id: str, path: str) -> dict:
    """Register the file a browser agent captured for a needs_browser_agent job (copies/converts it to the job's
    expected output path and adds a MANIFEST row marked as a browser capture)."""
    return core.complete_browser_job(job_id, path)


@mcp.tool()
def compare(paths: list[str], out: str = "", target_aspect: str = "") -> dict:
    """Contact sheet PNG + checks per image: dimensions, aspect drift vs target, file size, near-duplicates (dHash).
    Does NOT detect stray text (no reliable cheap heuristic): open the contact sheet and look."""
    return core.compare(paths, out or None, target_aspect or None)


@mcp.tool()
def optimise(path: str, widths: list[int] = [640, 1024, 1536], formats: list[str] = ["avif", "webp"],  # noqa: B006
             out_dir: str = "", name: str = "", crop: list[int] = [], budget_kb: int = 0) -> dict:  # noqa: B006
    """Responsive AVIF/WebP set (Pillow), never upscales. crop=[left,top,width,height]. Returns files with sizes,
    ready-to-paste srcset strings and budget warnings (suggested budgets: hero <=180KB desktop / <=90KB mobile,
    section plates <=160KB / <=70KB)."""
    return core.optimise(path, widths, formats, out_dir or None, name or None, crop or None, budget_kb or None)


@mcp.tool()
def record_review(path: str, verdict: str, note: str = "") -> dict:
    """Write the review verdict (keep / cut / redo + short reason) into the image's MANIFEST.md row.
    Judge by communication, not prettiness: an image that does not explain its section is cut."""
    return core.record_review(path, verdict, note)


if __name__ == "__main__":
    mcp.run(transport="stdio")
