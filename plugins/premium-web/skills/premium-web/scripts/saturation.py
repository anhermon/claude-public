#!/usr/bin/env python3
"""Saturation / restraint meter for screenshots: is the palette calm or a toy?

Usage: saturation.py <png|webp|dir> ...   -> per image: vivid share, strong share, chromatic hue count.
  vivid  = HSV S > VIVID_S and V > VIVID_V (a hot, full-strength colour: primaries, neon; muted colour blocks at
           S 0.55-0.70 do not count)
  strong = HSV S > STRONG_S and V > STRONG_V (anything clearly coloured, including dark saturated grounds)
Verdict per image:
  TOY   vivid > TOY_VIVID, or vivid > TOY_VIVID_MULTI_HUE with HUES_FOR_TOY or more hues
  LOUD  vivid > LOUD_VIVID
  ok    otherwise
Exit 1 when the MEAN vivid share of the inputs exceeds PAGE_MEAN_MAX (a page-level fail over a page's shots).

Provenance of the thresholds: set 2026-10 on 1440 px full-section screenshots of about nine builds that a human
reviewer had labelled. Approved quiet or filmic pages measured 0.00-0.01 vivid share; pages rejected as
"oversaturated, feels like a toy" measured 0.14-0.19 as a whole page and 0.35-0.64 in their worst sections.
Small sample (under ten pages): the numbers are heuristics, not laws. Recalibrate with `critic.py --calibrate DIR`
and your own labelled corpus before relying on them for a different style.
Photographic or filmic imagery (a sunset hero) can read vivid and still be premium; judge those by the critic.
"""
import sys
from pathlib import Path

from PIL import Image

VIVID_S, VIVID_V = 0.72, 0.50
STRONG_S, STRONG_V = 0.35, 0.25
TOY_VIVID = 0.20
TOY_VIVID_MULTI_HUE = 0.10
HUES_FOR_TOY = 3
LOUD_VIVID = 0.08
PAGE_MEAN_MAX = 0.12      # mean vivid share across a page's shots
SECTION_MAX = 0.20        # one section's 1440 shots
HUE_BUCKETS = 12
HUE_MIN_AREA = 0.03       # a hue counts when it covers more than this share of pixels
THUMB = 360               # measure on a thumbnail of this size
IMAGE_SUFFIXES = (".png", ".webp", ".jpg", ".jpeg")  # format support only; the plugin ships no images


def measure(p):
    im = Image.open(p).convert("RGB")
    im.thumbnail((THUMB, THUMB))
    raw = im.convert("HSV").tobytes()
    n = vivid = strong = 0
    hues = {}
    for h, s, v in zip(raw[0::3], raw[1::3], raw[2::3]):
        n += 1
        s, v = s / 255, v / 255
        if s > VIVID_S and v > VIVID_V:
            vivid += 1
        if s > STRONG_S and v > STRONG_V:
            strong += 1
            b = int(h / 255 * HUE_BUCKETS) % HUE_BUCKETS
            hues[b] = hues.get(b, 0) + 1
    nh = sum(c / n > HUE_MIN_AREA for c in hues.values())
    return vivid / n, strong / n, nh


LOUD_MIN_HUES = 2


def verdict(vivid, strong, nh):
    if vivid > TOY_VIVID or (vivid > TOY_VIVID_MULTI_HUE and nh >= HUES_FOR_TOY):
        return "TOY"
    return "LOUD" if vivid > LOUD_VIVID and nh >= LOUD_MIN_HUES else "ok"  # one dark ground + one glow hue is monochrome, not loud


def main(args):
    files = [f for a in args for f in (sorted(x for x in Path(a).rglob("*") if x.suffix.lower() in IMAGE_SUFFIXES)
                                       if Path(a).is_dir() else [Path(a)])]
    if not files:
        print(__doc__)
        return 2
    rows = []
    for f in files:
        v, s, nh = measure(f)
        rows.append(v)
        print(f"{verdict(v, s, nh):5} vivid={v:.2f} strong={s:.2f} hues={nh}  {f.name}")
    mean = sum(rows) / len(rows)
    print(f"mean vivid share {mean:.2f} (page limit {PAGE_MEAN_MAX})")
    return 1 if mean > PAGE_MEAN_MAX else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
