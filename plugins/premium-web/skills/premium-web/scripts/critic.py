#!/usr/bin/env python3
"""Independent section / wow / page critic. Judges screenshots from the written rubric and, optionally, run-time anchors.

Usage:
  critic.py <sections-dir> --wow <id> [--wow-test "<acceptance test>"] [--pass-refs DIR] [--fail-refs DIR]
      <sections-dir> has one subdir of screenshots per section (from `SECTIONS=1 chrome-shot.mjs`); writes critic.json.
      --wow <id>        REQUIRED: the section dir holding the signature-moment frames (or --wow-exempt REASON for sub-pages)
      --pass-refs DIR   optional folder (outside the repo) with 1-2 images per section type that the owner judged good
      --fail-refs DIR   optional folder with images judged bad or "nice but not wow"
  critic.py --calibrate DIR   DIR holds pass/ and fail/ section images; reports where the critic disagrees
  critic.py --calibrate       prints how to build such a corpus (exit 2)

Rubric = references/section-craft.md + references/wow.md + references/failure-modes.md (read at run time; no
screenshots ship with the skill). A FRESH critic judges each section; pass/fail is computed here from the scores and
never taken from the model. Exit: 0 all pass, 1 something fails, 2 usage, 3 critic unavailable (quota: verdict unknown).
Known calibration issue: a rubric-only critic scores strictly (a pilot corpus had no section above 4). Set the bar
from external references: see references/qa-loop.md "Calibration" and the CRITIC_* env below.
env: CRITIC=claude|codex (default claude: `claude -p --allowedTools Read`), CRITIC_MODEL (default sonnet), CRITIC_JOBS
     (parallel critics, default 4), CRITIC_FOCAL_MIN (default 4), CRITIC_MAX_THREES (default 2), CRITIC_MAX_ROUNDS (3).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import saturation  # noqa: E402  (pixel share of hot colours per screenshot)

RUBRIC_FILES = ("section-craft.md", "wow.md", "failure-modes.md")
CRIT = ["distinctiveness", "focal_visual", "finish", "hierarchy", "polish"]
IMG = saturation.IMAGE_SUFFIXES
EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_UNAVAILABLE = 0, 1, 2, 3
SCORE_MIN, SCORE_MAX = 1, 5
SCORE_FLOOR = 3                                   # no criterion may score below this
FOCAL_MIN = int(os.environ.get("CRITIC_FOCAL_MIN", 4))
MAX_THREES = int(os.environ.get("CRITIC_MAX_THREES", 2))
MAX_ROUNDS = int(os.environ.get("CRITIC_MAX_ROUNDS", 3))  # consecutive failing runs of one section before "replace it"
WOW_MIN, FALLBACK_MIN, MOTION_MIN = 4, 3, 4
MIN_MID_FRAMES = 6                                # motion polish counts only with a real frame sequence
REFS_PER_SECTION = 2
PAGE_SHOT_LIMIT = 10                              # wide shots shown to the page critic
WIDE_PREFIX = "1440"
CRITIC_TIMEOUT_S = 600
ASK_ATTEMPTS = 2
HISTORY_FILE = "critic-history.json"
CORPUS_HOWTO = """No calibration corpus given. Build one outside the repo:
  <DIR>/pass/*.png   6-12 section screenshots at 1440 px that the owner judged good (premium)
  <DIR>/fail/*.png   6-12 judged bad, plus a few 'nice but not wow' ones
Then run: critic.py --calibrate <DIR>. Mismatches show where the bar (CRITIC_FOCAL_MIN, ban list) needs adjusting."""


def load_rubric():
    parts = []
    for f in RUBRIC_FILES:
        p = SKILL / "references" / f
        parts.append(p.read_text() if p.exists() else f"(missing rubric file {f})")
    return "\n\n".join(parts)


RUBRIC = load_rubric()
WOW_TEST = ""

SECTION_TASK = """You are a demanding design director reviewing ONE section of a marketing web page against the rubric
below. Default to skepticism: a clean layout with hairlines, small sketches and grey text is a FAIL, not "minimal".
{refs}Section under review "{name}" (the same section at different widths / moments; read every file):
{shots}
Restraint check: big fields must be neutral or low-chroma, with at most one or two saturated colours at small area.
Full-strength primaries across large areas, rainbow overprint, sticker or pill colour everywhere is the ban "Toy
palette". Measured share of pixels at hot saturation in this section's 1440 shots: {sat}.
Judge only what is visible. Every score needs evidence you can point to in the screenshots. `focal_visual` asks:
does ONE designed focal moment (the persistent subject's state, a type moment, a media band, real UI in code, a
micro-demo, or a diagram when the section explains a mechanism) carry this section's message? `finish` asks: light,
material, grain and precise detail, or flat fills and default shadows?
Reply with ONLY this JSON, no prose:
{{"section":"{name}","what_it_shows":"<one sentence>","explanatory_visual_present":true|false,
"scores":{{"distinctiveness":{{"score":1-5,"evidence":"..."}},"focal_visual":{{"score":1-5,"evidence":"..."}},
"finish":{{"score":1-5,"evidence":"..."}},"hierarchy":{{"score":1-5,"evidence":"..."}},"polish":{{"score":1-5,"evidence":"..."}}}},
"ban_hits":[{{"rule":"<ban list item>","evidence":"..."}}],
"fixes":["<concrete change: what to build, with what real data or material>"]}}
(`explanatory_visual_present` means: a designed focal moment is present.)
"""

WOW_TASK = """You are judging the SIGNATURE moment of a web page (see the rubric's wow section below).
{refs}Frames of the moment under review (t1..tN are MID-ANIMATION frames, time-spaced or one per scroll position,
then rm-* reduced-motion / poster fallback frames if present; read every file):
{shots}
The page declared this ACCEPTANCE TEST for its wow (judge against it literally; if empty, intake failed): "{wow_test}"
A wow below {wow_min} fails the whole page regardless of every other score. A 4 = a stranger would screenshot it
unprompted and the subject's own substance is what you are looking at; 3 = a competent panel, chart or diagram of the
kind every product in the category has; a table, list or bordered boxes = 1-2.
Question 1: would someone screenshot this and send it to a colleague? Be honest; "nice" is a 3.
Question 2, motion polish, judged on the MIDDLE frames, not only the last: easing and settle (nothing half-faded into
a smear, no stop-start), points are information (no ambient dust), no particles or trails over text, glow never
muddies labels, half-drawn states look intentional, one focal motion at a time, no ghosted double headlines. Cite the
frame file for each problem.
Reply with ONLY this JSON: {{"wow":{{"score":1-5,"evidence":"...","would_share_because":"... or why not"}},
"motion_polish":{{"score":1-5,"evidence":"<frame file: problem>"}},
"fallback":{{"score":1-5,"evidence":"..."}},"fixes":["..."]}}
"""

PAGE_TASK = """You are a demanding client judging a WHOLE landing page from its section screenshots.
{refs}Page under review, section by section (read every file):
{shots}
DOM scan of structural tells (heuristic, from scripts/tells.js): {tells}
1. Distinctiveness test: cover the brand name. Could this page belong to 20 other products in its category? Name two
   real or typical competitors whose page it could be, or say why it could not.
2. Templaty tells (rubric list): which are visible? Evidence for each.
3. Do sections change shape and meaning, or could they swap places without changing anything? Does one persistent
   subject carry through the chapters?
4. Restraint: one or two saturated colours at small area with large neutral fields, or a toy/game look? Measured
   hot-pixel share across the wide shots: {sat}.
{closest}Reply with ONLY this JSON: {{"could_be_20_others":true|false,"lookalikes":["..."],"distinctive_because":"...",
"tells_seen":[{{"tell":"...","evidence":"..."}}],"sections_interchangeable":true|false,{closest_key}
"verdict":"<one sentence>","fixes":["..."]}}
"""
CLOSEST_Q = "5. Is the page closer to the PASS references or the FAIL references? Answer closest_to.\n"
CLOSEST_KEY = '"closest_to":"pass_refs"|"fail_refs",'


def ref_files(folder):
    if not folder:
        return []
    return sorted(str(p) for p in Path(folder).iterdir() if p.suffix.lower() in IMG)[:REFS_PER_SECTION] if Path(folder).is_dir() else []


def refs_text(pass_refs, fail_refs):
    out = []
    if pass_refs:
        out.append("PASS anchors (judged good by the owner; use them to calibrate what a 4-5 looks like): " + ", ".join(pass_refs))
    if fail_refs:
        out.append("FAIL anchors (judged bad or 'nice but not wow'; what a 1-3 looks like): " + ", ".join(fail_refs))
    return ("Calibration (read these first; they are already judged):\n- " + "\n- ".join(out) + "\n") if out else \
           "No external anchors were supplied: judge from the rubric alone, and remember rubric-only critics tend to be strict.\n"


def hot_share(paths):
    v = [saturation.measure(p)[0] for p in paths if Path(p).exists()]
    return sum(v) / len(v) if v else 0.0


def page_pass(j, have_refs=False):
    ok = "error" not in j and not j.get("could_be_20_others")
    return ok and (not have_refs or j.get("closest_to") == "pass_refs")


_S = {"type": "object", "required": ["score", "evidence"],
      "properties": {"score": {"type": "integer", "minimum": SCORE_MIN, "maximum": SCORE_MAX}, "evidence": {"type": "string"}}}
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
    "could_be_20_others": {"type": "object", "required": ["could_be_20_others", "verdict"], "properties": {
        "could_be_20_others": {"type": "boolean"}, "lookalikes": {"type": "array", "items": {"type": "string"}},
        "distinctive_because": {"type": "string"}, "sections_interchangeable": {"type": "boolean"},
        "tells_seen": {"type": "array", "items": {"type": "object", "properties": {"tell": {"type": "string"}, "evidence": {"type": "string"}}}},
        "closest_to": {"type": "string", "enum": ["pass_refs", "fail_refs"]}, "verdict": {"type": "string"}, "fixes": _FIX}},
}


def parse_reply(text, need=()):
    """Largest JSON object in a model reply that has every key in `need` (a truncated reply that lost ban_hits or
    fallback is a parse failure, not a pass). Tolerates prose braces before it, raw newlines in strings, \\' escapes
    and 1-3 dropped closing braces."""
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
    if best is None and not text.endswith("\0"):  # replies drop 1-2 closing braces: retry closed
        for k in (1, 2, 3):
            j = parse_reply(text.rstrip() + "}" * k + "\0", need)
            if j is not None:
                return j
    return best and best[1]


def ask(prompt, need=()):
    """Run one fresh critic; return parsed JSON (one retry on a parse failure). claude uses structured output
    (--json-schema): free-text JSON lost verdicts to bad escapes, raw quotes and dropped braces."""
    codex = os.environ.get("CRITIC", "claude") == "codex"
    if codex:
        imgs = re.findall(r"(/\S+\.(?:png|webp|jpe?g))", prompt)
        cmd = ["codex", "exec", "--skip-git-repo-check", "--sandbox", "read-only"] + sum((["-i", p] for p in imgs), []) + ["-"]
    else:
        schema = SCHEMAS.get(need[0] if need else None, {"type": "object"})
        cmd = ["claude", "-p", "--allowedTools", "Read", "--model", os.environ.get("CRITIC_MODEL", "sonnet"),
               "--output-format", "json", "--json-schema", json.dumps(schema)]
    out = err = ""
    for _ in range(ASK_ATTEMPTS):
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=CRITIC_TIMEOUT_S)
        out, err = r.stdout, r.stderr
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
    return {"error": (out + err)[-400:], "raw": out}  # full reply kept in critic.json for diagnosis


def verdict(j):
    """Section pass rule: focal_visual >= FOCAL_MIN, no score below SCORE_FLOOR, at most MAX_THREES scores at 3, no ban hits."""
    if "error" in j:
        return False, ["critic error"]
    sc = {c: int(j["scores"][c]["score"]) for c in CRIT}
    why = [f"{c}={v}" for c, v in sc.items() if v < SCORE_FLOOR]
    if sc["focal_visual"] < FOCAL_MIN:
        why.append(f"focal_visual={sc['focal_visual']} (needs {FOCAL_MIN})")
    if sum(v == SCORE_FLOOR for v in sc.values()) > MAX_THREES:
        why.append("too many scores at 3: " + ", ".join(f"{c}={v}" for c, v in sc.items() if v == SCORE_FLOOR))
    if not j.get("explanatory_visual_present"):
        why.append("no designed focal moment")
    why += ["ban: " + b["rule"] for b in j.get("ban_hits", [])]
    return not why, why


def judge_section(name, shots, pass_refs=(), fail_refs=()):
    wide = [p for p in shots if Path(p).name.startswith(WIDE_PREFIX)] or shots
    sat = hot_share(wide)
    j = ask(SECTION_TASK.format(refs=refs_text(list(pass_refs), list(fail_refs)), name=name,
                                sat=f"{sat:.2f} (toy above {saturation.SECTION_MAX})",
                                shots="\n".join(f"- {s}" for s in shots)) + "\n\nRUBRIC:\n" + RUBRIC,
            ("scores", "ban_hits", "explanatory_visual_present"))
    ok, why = verdict(j)
    j["saturation"] = round(sat, 3)
    if sat > saturation.SECTION_MAX:
        ok, why = False, why + [f"saturation: {sat:.2f} of the section's pixels are full-strength colour (limit {saturation.SECTION_MAX})"]
    j["pass"], j["fail_reasons"] = ok, why
    return j


def judge_wow(shots, test=None, pass_refs=(), fail_refs=()):
    j = ask(WOW_TASK.format(refs=refs_text(list(pass_refs), list(fail_refs)), wow_min=WOW_MIN,
                            wow_test=(test if test is not None else WOW_TEST) or "(none declared)",
                            shots="\n".join(f"- {s}" for s in shots)) + "\n\nRUBRIC:\n" + RUBRIC, ("wow", "fallback", "motion_polish"))
    if "error" in j:
        j["pass"] = False
        return j
    mid = [x for x in shots if "-t" in Path(x).name and "-rm-" not in Path(x).name]
    j["pass"] = (int(j["wow"]["score"]) >= WOW_MIN and int(j.get("fallback", {}).get("score", 0)) >= FALLBACK_MIN  # missing = not judged
                 and (len(mid) < MIN_MID_FRAMES or int(j.get("motion_polish", {}).get("score", 0)) >= MOTION_MIN))
    return j


def judge_page(shots, tells="(not run)", pass_refs=(), fail_refs=()):
    have = bool(pass_refs and fail_refs)
    j = ask(PAGE_TASK.format(refs=refs_text(list(pass_refs), list(fail_refs)), shots="\n".join(f"- {s}" for s in shots), tells=tells,
                             sat=f"{hot_share(shots):.2f} (toy above {saturation.PAGE_MEAN_MAX})",
                             closest=CLOSEST_Q if have else "", closest_key=CLOSEST_KEY if have else "") + "\n\nRUBRIC:\n" + RUBRIC,
            ("could_be_20_others", "verdict"))
    j["saturation"] = round(hot_share(shots), 3)
    j["pass"] = page_pass(j, have) and j["saturation"] <= saturation.PAGE_MEAN_MAX
    if j["saturation"] > saturation.PAGE_MEAN_MAX:
        j.setdefault("fixes", []).append(f"saturation: {j['saturation']} of pixels at hot colour; neutral large fields, one small spot colour")
    return j


def line(name, j):
    s = " ".join(f"{c[:4]}={j['scores'][c]['score']}" for c in CRIT) if "scores" in j else j.get("error", "")[:80]
    return f"{'PASS' if j['pass'] else 'FAIL'}  {name:28} {s}  {'; '.join(j.get('fail_reasons', []))[:120]}"


def calibrate(corpus):
    """Judge each image in CORPUS/pass and CORPUS/fail alone; report disagreements with the labels."""
    if not corpus or not Path(corpus, "pass").is_dir() or not Path(corpus, "fail").is_dir():
        print(CORPUS_HOWTO)
        return EXIT_USAGE
    labelled = [(p, True) for p in sorted(Path(corpus, "pass").iterdir()) if p.suffix.lower() in IMG] + \
               [(p, False) for p in sorted(Path(corpus, "fail").iterdir()) if p.suffix.lower() in IMG]
    if not labelled:
        print(CORPUS_HOWTO)
        return EXIT_USAGE
    with ThreadPoolExecutor(int(os.environ.get("CRITIC_JOBS", 4))) as ex:
        res = list(ex.map(lambda pw: judge_section(pw[0].name, [str(pw[0])]), labelled))
    bad = 0
    for (p, want), j in zip(labelled, res):
        ok = j["pass"] == want
        bad += not ok
        print(("ok    " if ok else "WRONG ") + f"[{'pass' if want else 'fail'}] " + line(p.name, j))
    print(f"{'CALIBRATED' if not bad else f'{bad} of {len(labelled)} MISJUDGED'} (corpus {len(labelled)} images, focal min {FOCAL_MIN})")
    return EXIT_FAIL if bad else EXIT_OK


def update_history(root, results):
    """Count consecutive failing runs per section; at MAX_ROUNDS tell the builder to replace the concept."""
    f = root / HISTORY_FILE
    try:
        hist = json.loads(f.read_text())
    except (OSError, json.JSONDecodeError):
        hist = {}
    for k, j in results.items():
        hist[k] = 0 if j.get("pass") else hist.get(k, 0) + 1
        if hist[k] >= MAX_ROUNDS:
            j.setdefault("fixes", []).insert(0, f"ROUND BUDGET USED ({hist[k]} failing runs): replace this section's focal moment, do not polish it")
    f.write_text(json.dumps(hist, indent=1))
    return hist


def build_parser():
    ap = argparse.ArgumentParser(description="Independent section / wow / page critic", add_help=True)
    ap.add_argument("dir", nargs="?", help="sections dir (one subdir of screenshots per section)")
    ap.add_argument("--wow", help="id of the section dir holding the signature-moment frames")
    ap.add_argument("--wow-test", default="", help="the written acceptance test for the wow")
    ap.add_argument("--wow-exempt", help="sub-pages only: reason the page inherits its site's wow")
    ap.add_argument("--pass-refs", help="folder of images the owner judged good")
    ap.add_argument("--fail-refs", help="folder of images the owner judged bad")
    ap.add_argument("--calibrate", nargs="?", const="", metavar="DIR", help="judge a labelled corpus DIR/pass, DIR/fail")
    return ap


def main(argv):
    global WOW_TEST
    a = build_parser().parse_args(argv)
    if a.calibrate is not None:
        return calibrate(a.calibrate)
    if not a.dir:
        print(__doc__)
        return EXIT_USAGE
    if not a.wow and not a.wow_exempt:
        print("--wow <section-id> (or --wow-exempt REASON for sub-pages) is REQUIRED: a page with no judged signature moment cannot pass (references/wow.md)")
        return EXIT_USAGE
    if a.wow_exempt:
        print(f"WOW EXEMPT (sub-page): {a.wow_exempt}")
    WOW_TEST = a.wow_test
    root = Path(a.dir).resolve()
    pass_refs, fail_refs = ref_files(a.pass_refs), ref_files(a.fail_refs)
    secs = {d.name: sorted(str(p) for p in d.iterdir() if p.suffix.lower() in IMG)
            for d in sorted(root.iterdir()) if d.is_dir() and not d.name.endswith("footer")}  # footer = chrome, judged at page level
    secs = {k: v for k, v in secs.items() if v}
    if a.wow and a.wow not in secs:
        print(f"no frames for --wow {a.wow}")
        return EXIT_USAGE
    w = None
    with ThreadPoolExecutor(int(os.environ.get("CRITIC_JOBS", 4))) as ex:
        names = [k for k in secs if k != a.wow]
        res = dict(zip(names, ex.map(lambda k: judge_section(k, secs[k], pass_refs, fail_refs), names)))
        if a.wow:
            w = judge_wow(secs[a.wow], pass_refs=pass_refs, fail_refs=fail_refs)
        rep = root.parent / "report.json"
        tells = None
        if rep.exists():
            tells = next((v["eval"] for v in json.loads(rep.read_text()).values() if isinstance(v.get("eval"), dict) and "tells" in v["eval"]), None)
        w14 = {k: [p for p in secs[k] if Path(p).name.startswith(WIDE_PREFIX)] for k in names}
        wide = [v[0] for v in w14.values() if v] + [p for v in w14.values() for p in v[1:]]  # one shot from EVERY section first, then fill
        page = judge_page(wide[:PAGE_SHOT_LIMIT], json.dumps({"hits": tells["hits"], "templaty": tells["templaty"]}) if tells else
                          "(not run: add EVAL=scripts/tells.js)", pass_refs, fail_refs)
        if tells and tells.get("craft_fail"):
            page["pass"], page["craft_fail"] = False, tells["craft_fail"]
            print("CRAFT GATE FAIL (tells.js): " + ", ".join(tells["craft_fail"]) + "  [panel_run | scale_change | type_scale | wow not above the fold]")
        if tells and tells["templaty"]:
            page["pass"], page["dom_templaty"] = False, tells["hits"]
    update_history(root, res)
    for k, j in res.items():
        print(line(k, j))
        for f in j.get("fixes", [])[:3]:
            print("      fix:", f[:160])
    if w:
        print(f"{'PASS' if w['pass'] else 'FAIL'}  WOW {a.wow}: {w.get('wow', w)}  fallback={w.get('fallback')}")
    print(f"{'PASS' if page['pass'] else 'FAIL'}  PAGE could_be_20_others={page.get('could_be_20_others')} closest={page.get('closest_to', '-')} "
          f"tells={[t.get('tell') for t in page.get('tells_seen', [])]} dom={page.get('dom_templaty', '-')}\n      {page.get('verdict', page.get('error', ''))}")
    (root / "critic.json").write_text(json.dumps({"sections": res, "wow": w, "page": page}, indent=1))
    ok = all(j["pass"] for j in res.values()) and (bool(a.wow_exempt) if w is None else w["pass"]) and page["pass"]
    errs = {k: v["error"] for k, v in list(res.items()) + [("wow", w or {}), ("page", page)] if "error" in v}
    if errs:  # a quota/session limit is not a verdict: those parts are unknown, never reported as failed designs
        print(f"CRITIC UNAVAILABLE for {', '.join(errs)}: {next(iter(errs.values())).strip()[-160:]}")
        print("Re-run when the limit resets (or CRITIC=codex); exit 3 = unknown, not failed.")
        return EXIT_UNAVAILABLE
    print(f"{'ALL SECTIONS PASS' if ok else 'NOT DONE: fix the failing sections and re-shoot'}; {root / 'critic.json'}")
    return EXIT_OK if ok else EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
