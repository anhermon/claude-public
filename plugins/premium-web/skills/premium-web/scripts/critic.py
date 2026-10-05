#!/usr/bin/env python3
"""Section critic: scores every section screenshot against references/rubric.md with a vision model.

Usage:
  critic.py <sections-dir>            # one subdir per section (from SECTIONS=1 chrome-shot.mjs); writes critic.json
  critic.py <sections-dir> --wow <id> [--wow-test "<acceptance test>"]  # REQUIRED: score the page's signature moment against its declared test; wow < 4 fails the page
  critic.py --calibrate               # judge the gallery anchors; exit 1 if the critic misjudges any

Each section is shown to a FRESH critic with one PASS anchor and one FAIL anchor from references/gallery, because
an uncalibrated critic called the Meridian method section "visually rich" (2026-10-01). Pass/fail is computed here
from the scores, never taken from the model. Exit code 1 = at least one section fails; 3 = critic unavailable (quota/session limit), verdict unknown.
Mode: default marketing (unchanged). `--mode app` (alias `tool`) or env MODE=app judges an APP/TOOL people operate, by references/rubric-app.md, never by the marketing rubric:
  critic.py <screens-dir> --mode app --signature <screen-id> --signature-test "<sentence>" [--walkthrough walkthrough.json]
  <screens-dir> has one subdir per SCREEN (SECTIONS="[data-screen]" chrome-shot). Scored per SCREEN (task clarity, information hierarchy, density, state coverage,
  interaction quality, distinctiveness) and per FLOW (one per primary_tasks line of the step 0 classification, from walkthrough.json:
  {"tasks":[{"task","steps","result","shot","screens":[screen-dir,...]}]}, the same fields as candidates.json tasks[]), then SIGNATURE CLARITY (replaces wow) and a whole-app
  generic-template verdict. --wow/--wow-test are accepted as aliases of --signature/--signature-test. The tells.js scan must have run with the same mode (mismatch = UNVERIFIED).
Step 0 gate: both modes refuse to run (exit 4, nothing judged) unless NOTES.md holds a valid "## Step 0 classification" whose mode equals this mode (scripts/classify.py; PW_NOTES=<path>).
Exit codes: 0 all pass, 1 something failed, 2 usage, 3 UNVERIFIED (gate could not run), 4 classification missing/invalid.
NOT RUN != PASS: a missing/unrunnable gate prints `UNVERIFIED: <reason>` and exits 3 (no claude/codex binary, quota/limit, tells.js not run
or not scanned at >= 1000px, mode mismatch); it never exits 0. If something else already failed for real, exit is 1.
env: CRITIC=claude|codex (default claude: `claude -p --allowedTools Read`), CRITIC_MODEL (default sonnet),
     CRITIC_JOBS=4 parallel critics.
Progress: per-section "[critic +Ns] start/done <label>: PASS|FAIL" lines on STDERR (stdout keeps only the verdict lines).
Runtime (estimate, not a benchmark): each critic is one model call of ~1-4 min with a 600s cap and one retry. Sections run CRITIC_JOBS at a time,
then wow, then page: expect ~5-20 min for 3-8 sections, and ~10-15 min for --calibrate. Run it in the background (or with a >= 20 min tool
timeout) and tail stderr; silence is not a hang. Budget this inside the time box (SKILL.md "Time box").
"""
import json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import saturation  # noqa: E402  (pixel share of hot colours per screenshot; owns PAGE_MAX / SECTION_MAX)
PAGE_MAX, SECTION_MAX = saturation.PAGE_MAX, saturation.SECTION_MAX
import classify  # noqa: E402  (step 0 gate: NOTES.md classification)
MODE = os.environ.get("MODE", "marketing")
MODE = "app" if MODE == "tool" else MODE  # tool is the old name of app
GALLERY = SKILL / "references" / "gallery"
RUBRIC = (SKILL / "references" / "rubric.md").read_text()
CRIT = ["distinctiveness", "explanatory_visual", "density_detail", "hierarchy", "polish"]
PASS_REFS = ["accept-anhermon-v4-guard-codedrawn.webp", "approved-pebble-jar-maths.webp", "approved-halcyon-instrument.webp"]
FAIL_REFS = ["reject-meridian-method.webp", "reject-ember-v3-toy-hero.webp", "reject-ember-principles-cards.webp", "reject-thin-line-art.webp"]  # judge_section shows the first two
APPROVED = ["approved-pebble-hero.webp", "approved-pebble-jar-maths.webp", "approved-halcyon-hero.webp", "approved-halcyon-instrument.webp"]
REJECTED = ["reject-ember-hero-terminal.webp", "reject-ember-principles-cards.webp", "reject-meridian-method.webp", "nice-not-wow-meridian-logpanel.webp", "reject-ember-v3-toy-hero.webp", "reject-ember-v3-toy-fullbleed.webp"]
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
doesn't give a premium feeling or a wow factor": {rejected}
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
                             shots="\n".join(f"- {s}" for s in shots), tells=tells, sat=f"{hot_share(shots):.2f} (toy above {PAGE_MAX:.2f})") + "\n\nRUBRIC:\n" + RUBRIC, ("could_be_20_others", "closest_to"))
    j["saturation"] = round(hot_share(shots), 3)
    j["pass"] = page_pass(j) and j["saturation"] <= PAGE_MAX  # measured, not model-judged: ember v3 0.19, approved pages 0.00-0.01
    if j["saturation"] > PAGE_MAX:
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
        try:
            r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=600)
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:  # no binary / hung critic: unknown, not a design verdict
            return {"error": f"UNVERIFIED: critic could not run ({cmd[0]}: {type(e).__name__} {e})", "raw": ""}
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
    j = ask(SECTION_TASK.format(pass_ref=pass_ref, fail_ref=fail_ref, name=name, sat=f"{sat:.2f} (toy above {SECTION_MAX:.2f})",
                                shots="\n".join(f"- {s}" for s in shots)) + "\n\nRUBRIC:\n" + RUBRIC, ("scores", "ban_hits", "explanatory_visual_present"))
    ok, why = verdict(j)
    j["saturation"] = round(sat, 3)
    if sat > SECTION_MAX:  # measured: ember v3 drift/access/revisions 0.35-0.64; approved pages 0.00-0.01
        ok, why = False, why + [f"saturation: {sat:.2f} of the section's pixels are full-strength colour (toy palette; limit {SECTION_MAX:.2f})"]
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
    errs = [n for n, j in [*res.items(), *wows.items(), *pres.items()] if "error" in j]
    if errs:
        print(f"UNVERIFIED: critic could not judge {', '.join(errs)}: {next(j['error'] for j in [*res.values(), *wows.values(), *pres.values()] if 'error' in j).strip()[-160:]}"); return 3
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


_T0 = time.time()


def timed(label, fn, *args):
    """Progress to stderr (stdout stays the verdict lines): one fresh critic is a 1-4 min model call, so a silent run looks hung."""
    print(f"[critic +{time.time() - _T0:.0f}s] start {label}", file=sys.stderr, flush=True)
    j = fn(*args)
    print(f"[critic +{time.time() - _T0:.0f}s] done  {label}: " + ("ERROR (critic unavailable)" if "error" in j else "PASS" if j.get("pass") else "FAIL"), file=sys.stderr, flush=True)
    return j


# ---------------------------------------------------------------- app mode (MODE=app): screens, flows, signature clarity
# Scored per SCREEN and per FLOW against references/rubric-app.md. No "explanatory visual per section", no marketing section framing, no "could be 20 others" page question.
APP_AXES = ["task_clarity", "information_hierarchy", "density", "state_coverage", "interaction_quality", "distinctiveness"]
FLOW_AXES = ["task_clarity", "interaction_quality", "information_hierarchy"]
APPROVED_APP = ["approved-tool-axiom-stream.webp", "approved-tool-linear-hero.webp", "approved-tool-openai-status.webp", "approved-tool-vercel-status.webp"]
REJECTED_APP = ["reject-tool-generic-a.webp", "reject-tool-generic-b.webp"]
_RA = SKILL / "references" / "rubric-app.md"
APP_RUBRIC = _RA.read_text() if _RA.exists() else (  # fallback only; rubric-app.md is the standard
    "Axes (1-5): task_clarity (answer/next action visible on arrival, few steps), information_hierarchy (act-on, state, detail), density (meets the stated target, "
    "12-14px legible, tabular numerals), state_coverage (empty/loading/error/partial designed), interaction_quality (keyboard, focus, filters at volume, URL state), "
    "distinctiveness (one truthful signature way of making the product's data legible; the generic AI dashboard is 1-2). Pass: task_clarity >= 4, distinctiveness >= 4, none < 3, at most two 3s.\n"
    "Bans: marketing structure on an app screen (hero, eyebrows, closing CTA, footer columns), data-wow or decorative numerals added for a gate, KPI card grid as the content, "
    "uppercase micro-label overload, pastel pill soup, invented metrics.")
APP_SCREEN_TASK = """You are a demanding product designer reviewing ONE SCREEN of a working app that people operate (not a landing page; never ask for a hero, a section visual or a wow).
Judge it as the person who uses it daily for these PRIMARY TASKS: {tasks}
Calibration (judged already): APPROVED work tools {pass_ref}; REJECTED generic AI dashboards {fail_ref}.
Screen under review "{name}" (same screen at different widths / states; read every file):
{shots}
Measured hot-pixel share of this screen's 1440 shots: {sat} (toy palette above {lim}).
Judge only what is visible; every score needs evidence you can point to. A clean sidebar + KPI tiles + table is a 3 at best on distinctiveness.
Reply with ONLY this JSON: {{"screen":"{name}","what_it_shows":"<one sentence: what this screen is for>",
"app_scores":{{"task_clarity":{{"score":1-5,"evidence":"..."}},"information_hierarchy":{{"score":1-5,"evidence":"..."}},"density":{{"score":1-5,"evidence":"..."}},
"state_coverage":{{"score":1-5,"evidence":"..."}},"interaction_quality":{{"score":1-5,"evidence":"..."}},"distinctiveness":{{"score":1-5,"evidence":"..."}}}},
"ban_hits":[{{"rule":"<ban>","evidence":"..."}}],"fixes":["<concrete change to this screen>"]}}
"""
APP_FLOW_TASK = """You are judging ONE FLOW of a working app: the primary task "{task}". The builder recorded this walk-through (steps and result are claims; check them against the screenshots):
{entry}
Screens/end state of the flow, in order (read every file):
{shots}
Question 1: is the task completed in the end-state shot, with the result visible? Question 2: could a first-time user do it without being told, in about the recorded number of steps?
Question 3: is state kept (filters, selection, drafts) and recoverable on error, as far as the shots show? Score the FLOW, not the prettiness of a screen.
Reply with ONLY this JSON: {{"flow_scores":{{"task_clarity":{{"score":1-5,"evidence":"..."}},"interaction_quality":{{"score":1-5,"evidence":"..."}},"information_hierarchy":{{"score":1-5,"evidence":"..."}}}},
"completed":true|false,"friction":["<where a user stalls>"],"fixes":["..."]}}
"""
APP_SIGNATURE_TASK = """You are judging the SIGNATURE CLARITY of a working app (this replaces the marketing "wow"): one distinctive, TRUTHFUL way the screen makes the product's own data legible
(all items on one field, a timeline that is the filter, a diff drawn as the thing itself), validated by the primary-task walk-through, not by spectacle.
Frames of the screen (read every file): {shots}
The builder declared this acceptance sentence: "{test}" (if empty, intake failed). Walk-through results (claims): {walk}
Score 1-5: 5 = a user sees what a table would hide and the walk-through shows a shorter task; 4 = real, truthful, small gain; 3 = a competent chart/panel/table every tool has (the "nice" ceiling); 1-2 = decoration, invented data, or nothing.
"truthful" is false if any mark is not a real record or sample data is not labelled "sample". Never reward size, motion or beauty by themselves.
Reply with ONLY this JSON: {{"signature":{{"score":1-5,"evidence":"...","legible_because":"<what is now easy to read, and the task it shortens>"}},"truthful":true|false,"fixes":["..."]}}
"""
APP_PAGE_TASK = """You are judging a WHOLE working app from one screenshot per screen. APPROVED work tools: {approved}. REJECTED as the generic AI dashboard: {rejected}.
Screens (read every file): {shots}
DOM scan (tells.js app profile): {tells}
Question: is this the generic admin/dashboard template (greeting or hero card, KPI tile row with deltas, sidebar + topbar chrome, donut/line cards, pastel pills) or a tool built around its own data and tasks?
Also: do the screens form one coherent app (same shell, same object model) rather than separate pages?
Reply with ONLY this JSON: {{"generic_template":true|false,"flows_coherent":true|false,"closest_to":"approved"|"rejected","verdict":"<one sentence>","tells_seen":[{{"tell":"...","evidence":"..."}}],"fixes":["..."]}}
"""
SCHEMAS.update({
    "app_scores": {"type": "object", "required": ["screen", "app_scores", "ban_hits", "fixes"], "properties": {
        "screen": {"type": "string"}, "what_it_shows": {"type": "string"}, "app_scores": {"type": "object", "required": APP_AXES, "properties": {c: _S for c in APP_AXES}},
        "ban_hits": SCHEMAS["scores"]["properties"]["ban_hits"], "fixes": _FIX}},
    "flow_scores": {"type": "object", "required": ["flow_scores", "completed", "friction", "fixes"], "properties": {
        "flow_scores": {"type": "object", "required": FLOW_AXES, "properties": {c: _S for c in FLOW_AXES}}, "completed": {"type": "boolean"},
        "friction": _FIX, "fixes": _FIX}},
    "signature": {"type": "object", "required": ["signature", "truthful", "fixes"], "properties": {
        "signature": {**_S, "properties": {**_S["properties"], "legible_because": {"type": "string"}}}, "truthful": {"type": "boolean"}, "fixes": _FIX}},
    "generic_template": {"type": "object", "required": ["generic_template", "flows_coherent", "closest_to", "verdict"], "properties": {
        "generic_template": {"type": "boolean"}, "flows_coherent": {"type": "boolean"}, "closest_to": {"type": "string", "enum": ["approved", "rejected"]},
        "verdict": {"type": "string"}, "tells_seen": SCHEMAS["could_be_20_others"]["properties"]["tells_seen"], "fixes": _FIX}},
})


def app_verdict(j):
    """Screen pass rule (rubric-app.md): task_clarity >= 4, distinctiveness >= 4, none < 3, at most two 3s, no ban hit. Computed here, never taken from the model."""
    if "error" in j:
        return False, ["critic error"]
    sc = {c: int(j["app_scores"][c]["score"]) for c in APP_AXES}
    why = [f"{c}={v}" for c, v in sc.items() if v < 3]
    why += [f"{c}={sc[c]} (needs 4)" for c in ("task_clarity", "distinctiveness") if sc[c] == 3]
    if sum(v == 3 for v in sc.values()) > 2:
        why.append("three or more axes at 3: " + ", ".join(f"{c}={v}" for c, v in sc.items() if v == 3))
    why += ["ban: " + b["rule"] for b in j.get("ban_hits", [])]
    return not why, why


def flow_verdict(j, entry):
    """Flow pass: the walk-through names steps and a result (script-checked), the critic sees the task completed, task clarity >= 4, interaction >= 3, at most one 3."""
    if "error" in j:
        return False, ["critic error"]
    sc = {c: int(j["flow_scores"][c]["score"]) for c in FLOW_AXES}
    why = [f"{c}={v}" for c, v in sc.items() if v < 3]
    if sc["task_clarity"] < 4:
        why.append(f"task_clarity={sc['task_clarity']} (needs 4)")
    if sum(v == 3 for v in sc.values()) > 1:
        why.append("two or more flow axes at 3")
    if not j.get("completed"):
        why.append("critic does not see the task completed in the end-state shot")
    if entry.get("steps") in (None, "") or not str(entry.get("result", "")).strip():
        why.append("walk-through entry lacks steps or result")
    return not why, why


def _same(a, b):
    a, b = (re.sub(r"\W+", " ", re.sub(r"['\u2019]", "", x.lower())).strip() for x in (a, b))
    return bool(a and b) and (a == b or a in b or b in a)


def judge_screen(name, shots, tasks):
    wide = [p for p in shots if Path(p).name.startswith("1440")] or shots
    sat = hot_share(wide)
    j = ask(APP_SCREEN_TASK.format(tasks="; ".join(tasks), pass_ref=", ".join(str(GALLERY / p) for p in APPROVED_APP[:2]), fail_ref=", ".join(str(GALLERY / p) for p in REJECTED_APP),
                                   name=name, sat=f"{sat:.2f}", lim=f"{SECTION_MAX:.2f}", shots="\n".join(f"- {s}" for s in shots)) + "\n\nRUBRIC:\n" + APP_RUBRIC, ("app_scores", "ban_hits"))
    ok, why = app_verdict(j)
    j["saturation"] = round(sat, 3)
    if sat > SECTION_MAX:
        ok, why = False, why + [f"saturation: {sat:.2f} of the screen's pixels are full-strength colour (limit {SECTION_MAX:.2f})"]
    j["pass"], j["fail_reasons"] = ok, why
    return j


def judge_flow(task, entry, shots):
    if not shots:
        return {"pass": False, "fail_reasons": ["no end-state shot / screens for this flow"], "flow_scores": {}}
    j = ask(APP_FLOW_TASK.format(task=task, entry=json.dumps(entry, ensure_ascii=False), shots="\n".join(f"- {s}" for s in shots)) + "\n\nRUBRIC:\n" + APP_RUBRIC, ("flow_scores", "completed"))
    j["pass"], j["fail_reasons"] = flow_verdict(j, entry)
    return j


def judge_signature(shots, test, walk, flows_ok):
    j = ask(APP_SIGNATURE_TASK.format(shots="\n".join(f"- {s}" for s in shots), test=test or "(none declared)", walk=json.dumps(walk, ensure_ascii=False)[:2500]) + "\n\nRUBRIC:\n" + APP_RUBRIC, ("signature", "truthful"))
    if "error" in j:
        j["pass"] = False
        return j
    why = []
    if int(j["signature"]["score"]) < 4:
        why.append(f"signature clarity={j['signature']['score']} (needs 4)")
    if not j.get("truthful"):
        why.append("not truthful: a mark is not a real record or sample data is unlabelled")
    if not flows_ok:
        why.append("the primary-task walk-through does not validate it (a flow failed)")
    j["pass"], j["fail_reasons"] = not why, why
    return j


def app_page_pass(j):
    return "error" not in j and not j.get("generic_template") and j.get("flows_coherent") and j.get("closest_to") == "approved"


def judge_app_page(shots, tells="(not run)"):
    j = ask(APP_PAGE_TASK.format(approved=", ".join(str(GALLERY / a) for a in APPROVED_APP), rejected=", ".join(str(GALLERY / a) for a in REJECTED_APP),
                                 shots="\n".join(f"- {s}" for s in shots), tells=tells) + "\n\nRUBRIC:\n" + APP_RUBRIC, ("generic_template", "flows_coherent", "closest_to"))
    j["saturation"] = round(hot_share(shots), 3)
    j["pass"] = app_page_pass(j) and j["saturation"] <= PAGE_MAX
    return j


def main_app(a, root, cls):
    sig = a[a.index("--signature") + 1] if "--signature" in a else a[a.index("--wow") + 1] if "--wow" in a else None
    test = a[a.index("--signature-test") + 1] if "--signature-test" in a else a[a.index("--wow-test") + 1] if "--wow-test" in a else ""
    if not sig:
        print("--signature <screen-id> is REQUIRED in app mode (the screen whose signature clarity is judged; --wow is accepted as an alias)"); return 2
    wt = Path(a[a.index("--walkthrough") + 1]) if "--walkthrough" in a else next((p for p in (root / "walkthrough.json", root.parent / "walkthrough.json") if p.exists()), None)
    secs = {d.name: sorted(str(p) for p in d.iterdir() if p.suffix in IMG) for d in sorted(root.iterdir()) if d.is_dir()}
    secs = {k: v for k, v in secs.items() if v}
    if sig not in secs:
        print(f"no frames for --signature {sig}"); return 2
    unverified = []
    if not wt or not wt.exists():
        unverified.append("walk-through missing: write walkthrough.json ({\"tasks\":[{\"task\",\"steps\",\"result\",\"shot\",\"screens\"}]}) by performing each primary task in the real UI")
        walk = []
    else:
        try:
            walk = json.loads(wt.read_text()).get("tasks", [])
        except (json.JSONDecodeError, AttributeError) as e:
            walk = []; unverified.append(f"walk-through unreadable ({wt}): {e}")
    rep = root.parent / "report.json"
    evals = [v["eval"] for v in json.loads(rep.read_text()).values() if isinstance(v.get("eval"), dict) and "tells" in v["eval"]] if rep.exists() else []
    tells = next((e for e in evals if e.get("desktop_gates")), None)
    if not evals:
        unverified.append("tells.js was not run (no eval in report.json): MODE=app EVAL=scripts/tells.js, scan at 1440")
    elif not tells:
        unverified.append("tells.js only scanned at < 1000px: density and page_shaped_mismatch did not run; scan at 1440")
    elif ("app" if tells.get("mode") == "tool" else tells.get("mode", "marketing")) != "app":
        unverified.append(f"tells.js ran in {tells.get('mode', 'marketing')} mode but critic is in app mode (set MODE=app for both)"); tells = None
    if unverified:  # nothing is judged (and no model call is spent) when a precondition is missing
        for u in unverified:
            print("UNVERIFIED: " + u)
        return 3
    tasks = cls["primary_tasks"]
    print(f"[critic] app mode: {len(secs)} screens, {len(tasks)} flows -> signature -> app; typically 5-20 min", file=sys.stderr, flush=True)
    with ThreadPoolExecutor(int(os.environ.get("CRITIC_JOBS", 4))) as ex:
        res = dict(zip(secs, ex.map(lambda k: timed("screen " + k, judge_screen, k, secs[k], tasks), list(secs))))
        entries = [next((w for w in walk if isinstance(w, dict) and _same(str(w.get("task", "")), t)), None) for t in tasks]
        def flow_shots(e):
            ps = [str((root.parent / e["shot"]) if not Path(str(e.get("shot", ""))).is_absolute() else e["shot"])] if e.get("shot") else []
            ps = [p for p in ps if Path(p).exists()]
            return ps + [next((p for p in secs[s] if Path(p).name.startswith("1440")), secs[s][0]) for s in e.get("screens", []) if s in secs]
        flows = dict(zip(tasks, ex.map(lambda te: timed("flow " + te[0], judge_flow, te[0], te[1], flow_shots(te[1])) if te[1] else {"pass": False, "fail_reasons": ["primary task not walked: no walkthrough.json entry"], "flow_scores": {}}, zip(tasks, entries))))
        flows_ok = all(j["pass"] for j in flows.values())
        sg = timed("signature " + sig, judge_signature, secs[sig], test, walk, flows_ok)
        wide = [next((p for p in v if Path(p).name.startswith("1440")), v[0]) for v in secs.values()][:10]
        print(f"[critic +{time.time() - _T0:.0f}s] start page", file=sys.stderr, flush=True)
        page = judge_app_page(wide, json.dumps({"hits": tells["hits"], "craft_fail": tells["craft_fail"]}))
    if tells.get("craft_fail"):
        page["pass"], page["craft_fail"] = False, tells["craft_fail"]
        print("CRAFT GATE FAIL (tells.js, app): " + ", ".join(tells["craft_fail"]) + "  [density < stated target | pointer-looking control not focusable / nameless / < 24px | < 3 of empty/loading/error/partial | page-shaped structure (wrong mode) | data-wow | equal_card_grids | caps_micro_labels | palette]")
    if tells["templaty"]:
        page["pass"], page["dom_templaty"] = False, tells["hits"]
    for k, j in res.items():
        print(f"{'PASS' if j.get('pass') else 'FAIL'}  SCREEN {k:22} " + (" ".join(f"{c[:5]}={j['app_scores'][c]['score']}" for c in APP_AXES) if "app_scores" in j else j.get("error", "")[:80]) + "  " + "; ".join(j.get("fail_reasons", []))[:140])
        for f in j.get("fixes", [])[:3]:
            print("      fix:", f[:160])
    for k, j in flows.items():
        print(f"{'PASS' if j.get('pass') else 'FAIL'}  FLOW   {k[:22]:22} " + (" ".join(f"{c[:5]}={j['flow_scores'][c]['score']}" for c in FLOW_AXES) if j.get("flow_scores") else "") + "  " + "; ".join(j.get("fail_reasons", []))[:140])
    print(f"{'PASS' if sg.get('pass') else 'FAIL'}  SIGNATURE CLARITY {sig}: {sg.get('signature', sg.get('error', ''))}  {'; '.join(sg.get('fail_reasons', []))[:140]}")
    print(f"{'PASS' if page['pass'] else 'FAIL'}  APP generic_template={page.get('generic_template')} closest={page.get('closest_to')} dom={page.get('dom_templaty', '-')}\n      {page.get('verdict', page.get('error', ''))}")
    (root / "critic.json").write_text(json.dumps({"mode": "app", "screens": res, "flows": flows, "signature": sg, "page": page}, indent=1))
    ok = all(j["pass"] for j in res.values()) and flows_ok and sg["pass"] and page["pass"]
    errs = {k: v["error"] for k, v in [*res.items(), *flows.items(), ("signature", sg), ("page", page)] if "error" in v}
    if errs:
        print(f"CRITIC UNAVAILABLE for {', '.join(errs)}: {next(iter(errs.values())).strip()[-160:]}")
        print("UNVERIFIED: critic unavailable; re-run when the limit resets (or CRITIC=codex); exit 3 = unknown, not failed.")
        return 3
    print(f"{'ALL SCREENS AND FLOWS PASS' if ok else 'NOT DONE: fix the failing screens/flows and re-shoot'}; {root / 'critic.json'}")
    return 0 if ok else 1


def main(a):
    global MODE
    if "--mode" in a:
        MODE = a[a.index("--mode") + 1]
    MODE = "app" if MODE == "tool" else MODE
    if MODE not in ("marketing", "app"):
        print(f"UNVERIFIED: unknown mode {MODE!r} (use marketing or app; tool is an alias of app)"); return 3
    if a and a[0] == "--calibrate":
        if MODE == "app":
            print("UNVERIFIED: app-mode calibration anchors are not established yet (gallery approved-tool-* / reject-tool-generic-* are not asserted); only the marketing --calibrate exists"); return 3
        return calibrate()
    if not a:
        print(__doc__); return 2
    cls, msg = classify.gate(MODE, [Path(a[0])])  # step 0: no judging without a written classification of the same mode
    if cls is None:
        print(msg); return 4
    if MODE == "app":
        return main_app(a, Path(a[0]).resolve(), cls)
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
    unverified = []
    with ThreadPoolExecutor(int(os.environ.get("CRITIC_JOBS", 4))) as ex:
        names = [k for k in secs if k != "wow"]
        print(f"[critic] {len(names)} sections ({os.environ.get('CRITIC_JOBS', 4)} parallel) -> wow -> page; typically 5-20 min, see Usage", file=sys.stderr, flush=True)
        res = dict(zip(names, ex.map(lambda k: timed("section " + k, judge_section, k, secs[k]), names)))
        w = timed("wow " + wow, judge_wow, secs[wow]) if wow else None
        rep = root.parent / "report.json"
        evals = [v["eval"] for v in json.loads(rep.read_text()).values() if isinstance(v.get("eval"), dict) and "tells" in v["eval"]] if rep.exists() else []
        tells = next((e for e in evals if e.get("desktop_gates")), None)  # a 390 scan has the desktop craft gates switched off
        if not evals:
            unverified.append("tells.js was not run (no eval in report.json): add EVAL=scripts/tells.js to chrome-shot, scan at 1440")
        elif not tells:
            unverified.append("tells.js only scanned at < 1000px: type_scale, wow_visible, scale_change did not run; scan at 1440")
        elif ("app" if tells.get("mode") == "tool" else tells.get("mode", "marketing")) != MODE:
            unverified.append(f"tells.js ran in {tells.get('mode', 'marketing')} mode but critic is in {MODE} mode (set MODE={MODE} for both)"); tells = None
        w14 = {k: [p for p in v if Path(p).name.startswith("1440")] for k, v in secs.items() if k != "wow"}
        # one shot from EVERY section first, then fill to 10: the first 10 in order saw only the top half of sealref
        wide = [v[0] for v in w14.values() if v] + [p for v in w14.values() for p in v[1:]]
        wide = wide[:10]
        print(f"[critic +{time.time() - _T0:.0f}s] start page", file=sys.stderr, flush=True)
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
    for u in unverified:
        print("UNVERIFIED: " + u)
    if errs:  # a quota/session limit is not a verdict: those parts are unknown, never reported as failed designs
        print(f"CRITIC UNAVAILABLE for {', '.join(errs)}: {next(iter(errs.values())).strip()[-160:]}")
        print("UNVERIFIED: critic unavailable; re-run when the limit resets (or CRITIC=codex); exit 3 = unknown, not failed.")
        return 3
    if unverified and ok:  # nothing failed, but a gate did not run: unknown, never a pass
        print(f"NOT VERIFIED: sections pass, {len(unverified)} gate(s) did not run; {root / 'critic.json'}")
        return 3
    print(f"{'ALL SECTIONS PASS' if ok else 'NOT DONE: fix the failing sections and re-shoot'}; {root / 'critic.json'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
