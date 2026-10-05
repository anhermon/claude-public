#!/usr/bin/env python3
"""Saturation / restraint meter for screenshots (Angel on ember v3: "oversaturated, feels like a game / toy").
Usage: saturation.py <png|dir> ...   -> per image: vivid share, strong share, chromatic hues (>3% area each).
  vivid  = HSV S>0.72 and V>0.50 (a hot, full-strength colour: primaries, neon, brand pink; Pebble's approved clay blocks sit at S .60-.70 and do not count)
  strong = HSV S>0.35 and V>0.25 (anything clearly coloured, incl. dark saturated grounds)
Calibrated 2026-10-02 on the gallery (see rubric.md "Saturation and restraint"). Verdict per image:
  TOY   vivid > 0.20, or vivid > 0.10 with 3+ hues     (full-saturation fields across big areas)
  LOUD  vivid > 0.08
  ok    otherwise. Exit 1 when the MEAN vivid share of the inputs exceeds PAGE_MAX 0.12 (a page-level pass: a whole page of shots). Heuristic: the critic still looks.
  Exit 3 + `UNVERIFIED: ...` when it cannot run (no Pillow); exit 2 when given no images. These limits (PAGE_MAX, SECTION_MAX) are the single copy: critic.py imports them.
Photographic imagery (a sunset hero) can read vivid and still be premium; judge those by the critic, not this number."""
import sys
from pathlib import Path
try:
    from PIL import Image
except ImportError:  # not run != pass: say so, exit 3 (critic.py imports the constants below, so only fail when measuring)
    Image = None
PAGE_MAX = 0.12     # mean vivid share of a page's shots above this fails (critic.py page verdict, exit 1 here)
SECTION_MAX = 0.20  # one section's vivid share above this = toy palette (critic.py section verdict; also the TOY line below)


def measure(p):
    if Image is None:
        raise RuntimeError("Pillow missing: pip install pillow")
    im = Image.open(p).convert("RGB")
    im.thumbnail((360, 360))
    hsv = im.convert("HSV")
    n = vivid = strong = 0
    hues = {}
    b3 = hsv.tobytes()
    for h, s, v in zip(b3[0::3], b3[1::3], b3[2::3]):
        n += 1
        s, v = s / 255, v / 255
        if s > 0.72 and v > 0.50:
            vivid += 1
        if s > 0.35 and v > 0.25:
            strong += 1
            b = int(h / 255 * 12) % 12
            hues[b] = hues.get(b, 0) + 1
    nh = sum(c / n > 0.03 for c in hues.values())
    return vivid / n, strong / n, nh


def verdict(vivid, strong, nh):
    if vivid > SECTION_MAX or (vivid > 0.10 and nh >= 3):
        return "TOY"
    return "LOUD" if vivid > 0.08 else "ok"


def main(args):
    files = [f for a in args for f in (sorted(Path(a).rglob("*.png")) + sorted(Path(a).rglob("*.webp")) if Path(a).is_dir() else [Path(a)])]
    if not files:
        print(__doc__); return 2
    rows = []
    if Image is None:
        print("UNVERIFIED: Pillow is not installed, saturation not measured (pip install pillow)"); return 3
    for f in files:
        v, s, nh = measure(f)
        rows.append(v)
        print(f"{verdict(v, s, nh):5} vivid={v:.2f} strong={s:.2f} hues={nh}  {f.name}")
    mean = sum(rows) / len(rows)
    print(f"mean vivid share {mean:.2f}")
    return 1 if mean > PAGE_MAX else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
