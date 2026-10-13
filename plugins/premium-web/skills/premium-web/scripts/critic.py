#!/usr/bin/env python3
"""Section critic: scores every section screenshot against references/rubric.md with a vision model.

Usage:
  critic.py <sections-dir>            # one subdir per section (from SECTIONS=1 chrome-shot.mjs); writes critic.json
  critic.py <sections-dir> --wow <id> [--wow-test "<acceptance test>"]  # REQUIRED: score the page's signature moment against its declared test; wow < 4 fails the page
  critic.py --calibrate               # judge the gallery anchors; exit 1 if the critic misjudges any

Each section is shown to a FRESH critic with one PASS anchor and one FAIL anchor from references/gallery, because
an uncalibrated critic called the Meridian method section "visually rich" (2026-10-01). Pass/fail is computed here
from the scores, never taken from the model. Exit code 1 = at least one section fails; 3 = critic unavailable (quota/session limit), verdict unknown.
env: CRITIC=claude|codex (default claude: `claude -p --allowedTools Read`), CRITIC_MODEL (default sonnet),
     CRITIC_JOBS=4 parallel critics.
"""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import saturation  # noqa: E402  (pixel share of hot colours per screenshot)
GALLERY = SKILL / "references" / "gallery"
RUBRIC = (SKILL / "references" / "rubric.md").read_text()
CRIT = ["distinctiveness", "explanatory_visual", "density_detail", "hierarchy", "polish"]
PASS_REFS = ["accept-anhermon-v4-guard-codedrawn.webp", "approved-pebble-jar-maths.webp", "approved-halcyon-instrument.webp"]
FAIL_REFS = ["reject-meridian-method.webp", "reject-ember-v3-toy-hero.webp", "reject-ember-principles-cards.webp", "reject-thin-line-art.webp"]  # judge_section shows the first two
APPROVED = ["approved-pebble-hero.webp", "approved-pebble-jar-maths.webp", "approved-halcyon-hero.webp", "approved-halcyon-instrument.webp"]
REJECTED = ["reject-ember-hero-terminal.webp", "reject-ember-principles-cards.webp", "reject-meridian-method.webp", "nice-not-wow-meridian-logpanel.webp", "reject-ember-v3-toy-hero.webp", "reject-ember-v3-toy-fullbleed.webp", "reject-provenant-gold-plate.webp", "reject-provenant-v2-beige-boxes.webp"]
IMG = (".png", ".webp", ".jpg", ".jpeg")

SECTION_TASK = """You are a demanding design director reviewing ONE section of a marketing web page against the rubric
below. Default to skepticism: a clean layout with hairlines, small sketches and grey text is a FAIL, not "minimal".
Calibration (read these first; they are judged already):
- PASS anchors: {pass_ref}
- FAIL anchors (stick-figure / template / "generic AI templaty"): {fail_ref}
Section under review "{name}" (same section at different widths / moments; read every file):
{shots}
Restraint check (Angel rejected ember v3 as "oversaturated, feels like a game / toy"; anchors reject-ember-v3-toy-*):
big fields must be neutral or low-chroma, at most one or two saturated colours at small area. Full-strength primaries
across large areas, rainbow overprint, sticker/pill colour everywhere = ban rule "Toy palette". Measured share of
pixels at hot saturation in this section's 1440 shots: {sat}.
Judge only what is visible. Every score needs evidence you can point to in the screenshots.
Reply with ONLY this JSON, no prose:
{{"section":"{name}","what_it_shows":"<one sentence>","explanatory_visual_present":true|false,
"scores":{{"distinctiveness":{{"score":1-5,"evidence":"..."}},"explanatory_visual":{{"score":1-5,"evidence":"..."}},
"density_detail":{{"score":1-5,"evidence":"..."}},"hierarchy":{{"score":1-5,"evidence":"..."}},"polish":{{"score":1-5,"evidence":"..."}}}},
"ban_hits":[{{"rule":"<ban list item>","evidence":"..."}}],
"fixes":["<concrete change: what visual to build, with what real data/labels>"]}}
"""
WOW_TEST = ""
WOW_TASK = """You are judging the SIGNATURE moment of a web page (rubric's "Wow" section below).
Calibration: {wow_pass} scores 4-5 (subject-derived, replayable WebGL); {wow_nice} scores 3 (competent but every
product in the category has one). Frames of the moment under review (t1..tN are MID-ANIMATION frames, time-spaced
or one per scroll position, then rm-* reduced-motion / poster fallback frames if present; read every file):
{shots}
The page declared this ACCEPTANCE TEST for its wow (judge against it literally; if it is empty, the page failed intake): "{wow_test}"
A wow below 4 fails the whole page regardless of every other score. Anchors: a 4 = a stranger would screenshot it unprompted and the
product's own substance is what you are looking at (Stripe's live checkout beside a gradient wedge, Linear's real product UI at full width,
a rendered object); 3 = a competent panel/chart/diagram of the kind every product in the category has; a table, a list, bordered boxes = 1-2.
Question 1: would someone screenshot this and send it to a colleague? Be honest; "nice" is a 3.
Question 2, motion polish, judged on the MIDDLE frames, not only the last (Angel on ember r2's signature: "nice,
the animation needs a bit more polish"): easing and settle (nothing half-faded into a smear, no stop-start), particle
budget (points are information, no ambient dust), no particles or trails over text, glow never muddies labels,
half-drawn states look intentional, one focal motion at a time. Cite the frame file for each problem.
Reply with ONLY this JSON: {{"wow":{{"score":1-5,"evidence":"...","would_share_because":"... or why not"}},
"motion_polish":{{"score":1-5,"evidence":"<frame file: problem>"}},
"fallback":{{"score":1-5,"evidence":"..."}},"fixes":["..."]}}
"""
PAGE_TASK = """You are Angel, a demanding client, judging a WHOLE landing page from its section screenshots.
APPROVED pages by Angel (pebble: tactile fintech; halcyon: cinematic instrument): {approved}
REJECTED by Angel, in his words: ember "not good, generic AI templaty"; meridian "nice, but it's missing a wow factor"
and its method section "a template with stick-figure placeholders"; ember v3 "oversaturated and feels like a game / toy,
doesn't give a premium feeling or a wow factor"; provenant (luxury store) "looks terrible - you don't create a luxurious
feeling by writing 'luxury' or putting the price at the front, or covering everything with gold", "show real products, not concept"; provenant v2 (warm paper, small packshots in big beige boxes) "it still doesn't look good": {rejected}
Page under review, section by section (read every file):
{shots}
DOM scan of structural tells (heuristic, from scripts/tells.js): {tells}
1. Distinctiveness test: cover the brand name. Could this page belong to 20 other products in its category? Name
   two real or typical competitors whose page it could be, or say why it could not.
2. Templaty tells (rubric list): which are visible? Evidence for each.
3. Do sections change shape and meaning, or could they swap places without changing anything?
4. Restraint: does the page hold to one or two saturated colours at small area with large neutral fields, or does it
   read as a toy / game (primaries at full saturation over big areas, rainbow)? Measured hot-pixel share across the
   wide shots: {sat}. A toy-reading page is closest_to "rejected" whatever else it does well.
Reply with ONLY this JSON: {{"could_be_20_others":true|false,"lookalikes":["..."],"distinctive_because":"...",
"tells_seen":[{{"tell":"...","evidence":"..."}}],"sections_interchangeable":true|false,
"closest_to":"approved"|"rejected","verdict_in_angels_words":"<one sentence>","fixes":["..."]}}
"""


def page_pass(j):
    # tells_seen count dropped: the approved pages drew 5+ critic-listed tells in the 2026-10-01 reachability run (a
    # count double-counts what closest_to already weighs). The DOM scan (tells.js) still forces a fail when templaty.
    return "error" not in j and not j.get("could_be_20_others") and j.get("closest_to") == "approved"


def hot_share(paths):
    v = [saturation.measure(p)[0] for p in paths if Path(p).exists()]
    return sum(v) / len(v) if v else 0.0


def judge_page(shots, tells="(not run)", exclude=()):
    j = ask(PAGE_TASK.format(approved=", ".join(str(GALLERY / a) for a in APPROVED if a not in exclude),
                             rejected=", ".join(str(GALLERY / a) for a in REJECTED if a not in exclude),
                             shots="\n".join(f"- {s}" for s in shots), tells=tells, sat=f"{hot_share(shots):.2f} (toy above 0.12)") + "\n\nRUBRIC:\n" + RUBRIC, ("could_be_20_others", "closest_to"))
    j["saturation"] = round(hot_share(shots), 3)
    j["pass"] = page_pass(j) and j["saturation"] <= 0.12  # measured, not model-judged: ember v3 0.19, approved pages 0.00-0.01
    if j["saturation"] > 0.12:
        j.setdefault("fixes", []).append(f"saturation: {j['saturation']} of pixels at hot colour; neutral large fields, one small spot colour")
    return j


_S = {"type": "object", "required": ["score", "evidence"],
      "properties": {"score": {"type": "integer", "minimum": 1, "maximum": 5}, "evidence": {"type": "string"}}}
_FIX = {"type": "array", "items": {"type": "string"}}
SCHEMAS = {  # structured output per judge, keyed by its first required key (typed: untyped props came back as strings)
    "scores": {"type": "object", "required": ["section", "explanatory_visual_present", "scores", "ban_hits", "fixes"], "properties": {
        "section": {"type": "string"}, "what_it_shows": {"type": "string"}, "explanatory_visual_present": {"type": "boolean"},
        "scores": {"type": "object", "required": list(CRIT), "properties": {c: _S for c in CRIT}},
        "ban_hits": {"type": "array", "items": {"type": "object", "required": ["rule", "evidence"],
                                                 "properties": {"rule": {"type": "string"}, "evidence": {"type": "string"}}}},
        "fixes": _FIX}},
    "wow": {"type": "object", "required": ["wow", "motion_polish", "fallback", "fixes"], "properties": {
        "wow": {**_S, "properties": {**_S["properties"], "would_share_because": {"type": "string"}}},
        "motion_polish": _S, "fallback": _S, "fixes": _FIX}},
    "could_be_20_others": {"type": "object", "required": ["could_be_20_others", "closest_to", "verdict_in_angels_words"], "properties": {
        "could_be_20_others": {"type": "boolean"}, "lookalikes": {"type": "array", "items": {"type": "string"}},
        "distinctive_because": {"type": "string"}, "sections_interchangeable": {"type": "boolean"},
        "tells_seen": {"type": "array", "items": {"type": "object", "properties": {"tell": {"type": "string"}, "evidence": {"type": "string"}}}},
        "closest_to": {"type": "string", "enum": ["approved", "rejected"]}, "verdict_in_angels_words": {"type": "string"}, "fixes": _FIX}},
}


def parse_reply(text, need=()):
    """Needs every key in `need` (a truncated reply that lost ban_hits or fallback is a parse failure, not a pass). Largest JSON object in a model reply. Tolerates prose braces before it, raw newlines in strings and \\' escapes
    (sealref r8: verdicts lost to a greedy regex, strict json.loads and a dropped final brace)."""
    text, dec, best = re.sub(r"(?<!\\)((?:\\\\)*)\\'", r"\1'", text), json.JSONDecoder(strict=False), None
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                obj, end = dec.raw_decode(text, i)
            except json.JSONDecodeError:
                continue
            for v in list(obj.values()) if isinstance(obj, dict) else []:  # a misplaced brace nests the next key one level down
                if isinstance(v, dict):
                    obj.update({k: v.pop(k) for k in need if k in v and k not in obj})
            if isinstance(obj, dict) and (not need or all(k in obj for k in need)) and (best is None or end - i > best[0]):
                best = (end - i, obj)
    if best is None and not text.endswith("\0"):  # replies drop 1-2 closing braces (sealref r8 wow, twice): retry closed
        for k in (1, 2, 3):
            j = parse_reply(text.rstrip() + "}" * k + "\0", need)
            if j is not None:
                return j
    return best and best[1]


def ask(prompt, need=()):
    """Run one fresh critic; return parsed JSON (one retry on a parse failure). claude uses structured output
    (--json-schema): free-text JSON lost 4 of ~40 verdicts on sealref r8 (bad escapes, raw quotes, dropped braces)."""
    codex = os.environ.get("CRITIC", "claude") == "codex"
    if codex:
        imgs = re.findall(r"(/\S+\.(?:png|webp|jpe?g))", prompt)
        cmd = ["codex", "exec", "--skip-git-repo-check", "--sandbox", "read-only"] + sum((["-i", p] for p in imgs), []) + ["-"]
    else:
        schema = SCHEMAS.get(need[0] if need else None, {"type": "object"})
        cmd = ["claude", "-p", "--allowedTools", "Read", "--model", os.environ.get("CRITIC_MODEL", "sonnet"),
               "--output-format", "json", "--json-schema", json.dumps(schema)]
    for _ in range(2):
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=600)
        out = r.stdout
        if not codex:
            try:
                ev = json.loads(out)
                res = next(e for e in (ev if isinstance(ev, list) else [ev]) if e.get("type") == "result")
                if isinstance(res.get("structured_output"), dict) and all(k in res["structured_output"] for k in need):
                    return res["structured_output"]
                out = str(res.get("result", out))  # quota/limit text, or a reply to salvage below
            except (json.JSONDecodeError, StopIteration, AttributeError):
                pass
        j = parse_reply(out, need)
        if j is not None:
            return j
    return {"error": (out + r.stderr)[-400:], "raw": out}  # full reply kept in critic.json for diagnosis


def verdict(j):
    if "error" in j:
        return False, ["critic error"]
    sc = {c: int(j["scores"][c]["score"]) for c in CRIT}
    # Calibrated 2026-10-01 against Angel-approved pages (reachability check): "all five >= 4" failed pebble's approved
    # hero (polish 3) and 5/6 pebble sections, so the bar was unreachable. Rule now: the explaining visual scores >= 4,
    # nothing below 3, and at most two 3s. Meridian method / ember principles still fail (explanatory 1-2, ban hits).
    why = [f"{c}={v}" for c, v in sc.items() if v < 3]
    if sc["explanatory_visual"] < 4:
        why.append(f"explanatory_visual={sc['explanatory_visual']} (needs 4)")
    if sum(v == 3 for v in sc.values()) > 2:
        why.append("three or more scores at 3: " + ", ".join(f"{c}={v}" for c, v in sc.items() if v == 3))
    if not j.get("explanatory_visual_present"):
        why.append("no explanatory visual")
    why += ["ban: " + b["rule"] for b in j.get("ban_hits", [])]
    return not why, why


def judge_section(name, shots, exclude=""):
    pass_ref = ", ".join(str(GALLERY / p) for p in [p for p in PASS_REFS if p != exclude][:2])
    fail_ref = ", ".join(str(GALLERY / p) for p in [p for p in FAIL_REFS if p != exclude][:2])
    wide = [p for p in shots if Path(p).name.startswith("1440")] or shots
    sat = hot_share(wide)
    j = ask(SECTION_TASK.format(pass_ref=pass_ref, fail_ref=fail_ref, name=name, sat=f"{sat:.2f} (toy above 0.20)",
                                shots="\n".join(f"- {s}" for s in shots)) + "\n\nRUBRIC:\n" + RUBRIC, ("scores", "ban_hits", "explanatory_visual_present"))
    ok, why = verdict(j)
    j["saturation"] = round(sat, 3)
    if sat > 0.20:  # measured: ember v3 drift/access/revisions 0.35-0.64; approved pages 0.00-0.01
        ok, why = False, why + [f"saturation: {sat:.2f} of the section's pixels are full-strength colour (toy palette; limit 0.20)"]
    j["pass"], j["fail_reasons"] = ok, why
    return j


def judge_wow(shots, test=None):
    j = ask(WOW_TASK.format(wow_pass=GALLERY / "accept-anhermon-v4-hero.webp",
                            wow_nice=GALLERY / "nice-not-wow-meridian-logpanel.webp", wow_test=(test if test is not None else WOW_TEST) or "(none declared)",
                            shots="\n".join(f"- {s}" for s in shots)) + "\n\nRUBRIC:\n" + RUBRIC, ("wow", "fallback", "motion_polish"))
    if "error" not in j:
        mid = [x for x in shots if "-t" in Path(x).name and "-rm-" not in Path(x).name]  # motion polish counts only with a real frame sequence
        j["pass"] = (int(j["wow"]["score"]) >= 4 and int(j.get("fallback", {}).get("score", 0)) >= 3  # missing = not judged, never a pass
                     and (len(mid) < 6 or int(j.get("motion_polish", {}).get("score", 0)) >= 4))
    else:
        j["pass"] = False
    return j


def line(name, j):
    s = " ".join(f"{c[:4]}={j['scores'][c]['score']}" for c in CRIT) if "scores" in j else j.get("error", "")[:80]
    return f"{'PASS' if j['pass'] else 'FAIL'}  {name:28} {s}  {'; '.join(j.get('fail_reasons', []))[:120]}"


def calibrate():
    cases = {  # anchor -> expected section pass
        "reject-meridian-method.webp": False, "reject-thin-line-art.webp": False,
        "reject-provenant-gold-plate.webp": False, "reject-provenant-v2-beige-boxes.webp": False,
        "reject-anhermon-03364e9-serif-mono.webp": False,
        "accept-anhermon-v4-guard-codedrawn.webp": True,
        "reject-ember-v3-toy-fullbleed.webp": False,  # toy palette: measured saturation alone fails it
        # informational (None): the critic is stricter than what shipped here; observed 2026-10-01 it fails the
        # observe plate on whitespace (expl=3) and the log panel crop on polish/hierarchy (3). Kept to watch drift.
        "accept-anhermon-v4-observe-plate.webp": None, "nice-not-wow-meridian-logpanel.webp": None,
    }
    with ThreadPoolExecutor(int(os.environ.get("CRITIC_JOBS", 4))) as ex:
        res = dict(zip(cases, ex.map(lambda a: judge_section(a, [str(GALLERY / a)], exclude=a), cases)))
        wows = dict(zip(["accept-anhermon-v4-hero.webp", "nice-not-wow-meridian-logpanel.webp"],
                        ex.map(lambda a: judge_wow([str(GALLERY / a)], {"accept-anhermon-v4-hero.webp": "A stranger would say: that agent run is drawn as light strands, one per span, and I can replay it", "nice-not-wow-meridian-logpanel.webp": "A stranger would say: a log search that narrows to the culprit line"}[a]), ["accept-anhermon-v4-hero.webp", "nice-not-wow-meridian-logpanel.webp"])))
        pages = {"ember": ["reject-ember-hero-terminal.webp", "reject-ember-principles-cards.webp"],
                 "pebble": ["approved-pebble-hero.webp", "approved-pebble-jar-maths.webp"],
                 "halcyon": ["approved-halcyon-hero.webp", "approved-halcyon-instrument.webp"],
                 "meridian": ["nice-not-wow-meridian-logpanel.webp", "reject-meridian-method.webp"],
                 "ember-v3": ["reject-ember-v3-toy-hero.webp", "reject-ember-v3-toy-fullbleed.webp"]}
        pres = dict(zip(pages, ex.map(lambda k: judge_page([str(GALLERY / f) for f in pages[k]], exclude=pages[k]), pages)))
    bad = 0
    for k, want in {"ember": False, "pebble": True, "halcyon": True, "meridian": False, "ember-v3": False}.items():
        ok = pres[k]["pass"] == want; bad += not ok
        print(("ok    " if ok else "WRONG ") + f"page {k}: {'PASS' if pres[k]['pass'] else 'FAIL'} 20-others={pres[k].get('could_be_20_others')} closest={pres[k].get('closest_to')} tells={len(pres[k].get('tells_seen', []))} | {pres[k].get('verdict_in_angels_words', pres[k].get('error', ''))[:110]}")
    for a, want in cases.items():
        ok = want is None or res[a]["pass"] == want; bad += not ok
        print(("info  " if want is None else "ok    " if ok else "WRONG ") + line(a, res[a]))
    for a, want in {"accept-anhermon-v4-hero.webp": True, "nice-not-wow-meridian-logpanel.webp": False}.items():
        ok = wows[a]["pass"] == want; bad += not ok
        print(("ok    " if ok else "WRONG ") + f"wow {a}: {wows[a].get('wow', wows[a])}")
    out = Path(os.environ.get("TMPDIR", "/tmp")) / "premium-web-calibration.json"
    out.write_text(json.dumps({"sections": res, "wow": wows, "pages": pres}, indent=1))
    print(f"{'CALIBRATED' if not bad else f'{bad} MISJUDGED'}; details {out}")
    return 1 if bad else 0


def main(a):
    if a and a[0] == "--calibrate":
        return calibrate()
    if not a:
        print(__doc__); return 2
    root = Path(a[0]).resolve()
    wow = a[a.index("--wow") + 1] if "--wow" in a else None
    exempt = a[a.index("--wow-exempt") + 1] if "--wow-exempt" in a else None  # sub-pages only (a lib/fix page that inherits the site's wow); reason is printed
    if exempt: print(f"WOW EXEMPT (sub-page): {exempt}")
    if not wow and not exempt:  # 2026-10-04: wow was optional, so a page with no wow passed section scores. Now mandatory.
        print("--wow <section-id> (or --wow-exempt REASON for sub-pages) is REQUIRED: a page with no judged signature moment cannot pass (see references/wow.md)"); return 2
    global WOW_TEST
    WOW_TEST = a[a.index("--wow-test") + 1] if "--wow-test" in a else ""
    secs = {d.name: sorted(str(p) for p in d.iterdir() if p.suffix in IMG) for d in sorted(root.iterdir()) if d.is_dir() and not d.name.endswith("footer")}  # footer = chrome, judged at page level
    secs = {k: v for k, v in secs.items() if v}
    if not wow: wow = None
    if wow and wow not in secs:
        print(f"no frames for --wow {wow}"); return 2
    with ThreadPoolExecutor(int(os.environ.get("CRITIC_JOBS", 4))) as ex:
        res = dict(zip([k for k in secs if k != "wow"], ex.map(lambda k: judge_section(k, secs[k]), [k for k in secs if k != "wow"])))
        w = ex.submit(judge_wow, secs[wow]).result() if wow else None
        rep = root.parent / "report.json"
        tells = next((v["eval"] for v in json.loads(rep.read_text()).values() if isinstance(v.get("eval"), dict) and "tells" in v["eval"]), None) if rep.exists() else None
        w14 = {k: [p for p in v if Path(p).name.startswith("1440")] for k, v in secs.items() if k != "wow"}
        # one shot from EVERY section first, then fill to 10: the first 10 in order saw only the top half of sealref
        wide = [v[0] for v in w14.values() if v] + [p for v in w14.values() for p in v[1:]]
        wide = wide[:10]
        page = judge_page(wide, json.dumps({"hits": tells["hits"], "templaty": tells["templaty"]}) if tells else "(not run: add EVAL=scripts/tells.js)")
        if tells and tells.get("craft_fail"):
            page["pass"] = False
            page["craft_fail"] = tells["craft_fail"]
            print("CRAFT GATE FAIL (tells.js): " + ", ".join(tells["craft_fail"]) + "  [panel_run>3 consecutive boxed sections | scale_change<2 | type_scale<4x | wow not above the fold]")
        if tells and tells["templaty"]:
            page["pass"] = False
            page["dom_templaty"] = tells["hits"]
    for k, j in res.items():
        print(line(k, j))
        for f in j.get("fixes", [])[:3]:
            print("      fix:", f[:160])
    if w:
        print(f"{'PASS' if w['pass'] else 'FAIL'}  WOW {wow}: {w.get('wow', w)}  fallback={w.get('fallback')}")
    print(f"{'PASS' if page['pass'] else 'FAIL'}  PAGE could_be_20_others={page.get('could_be_20_others')} closest={page.get('closest_to')} "
          f"tells={[t.get('tell') for t in page.get('tells_seen', [])]} dom={page.get('dom_templaty', '-')}\n      {page.get('verdict_in_angels_words', page.get('error', ''))}")
    (root / "critic.json").write_text(json.dumps({"sections": res, "wow": w, "page": page}, indent=1))
    ok = all(j["pass"] for j in res.values()) and (w is None and bool(exempt) or (w is not None and w["pass"])) and page["pass"]
    errs = {k: v["error"] for k, v in list(res.items()) + [("wow", w or {}), ("page", page)] if "error" in v}
    if errs:  # a quota/session limit is not a verdict: those parts are unknown, never reported as failed designs
        print(f"CRITIC UNAVAILABLE for {', '.join(errs)}: {next(iter(errs.values())).strip()[-160:]}")
        print("Re-run when the limit resets (or CRITIC=codex); exit 3 = unknown, not failed.")
        return 3
    print(f"{'ALL SECTIONS PASS' if ok else 'NOT DONE: fix the failing sections and re-shoot'}; {root / 'critic.json'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
