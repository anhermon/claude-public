#!/usr/bin/env python3
"""Step 0 classification gate (SKILL.md "Step 0"). Scripts that judge or shoot a page refuse to run without it.

Usage: classify.py --mode marketing|app|tool [--from <dir>]... [--json]     (tool = alias of app)
Finds NOTES.md: $PW_NOTES, else walks up from each --from dir (chrome-shot passes its out dir, critic its sections dir) and from cwd.
The NOTES.md must contain this section (key: value lines until the next heading; primary_tasks is a "- " list):

    ## Step 0 classification
    mode: marketing | app
    classification: READ | WORK | MIXED
    scope: <MIXED only: the deliverable this mode covers>
    users: <who uses it>
    frequency: <how often, with a number>
    evidence: <what in the request/product shows this: task verbs find/compare/trigger/approve/edit, usage numbers; >= 20 chars>
    density_target: <app only: rows/items visible at 1440x900, integer>
    primary_tasks:
    - <app only: verb phrase, 1-8 of them>

Rules: marketing <- READ (or MIXED with scope); app <- WORK (or MIXED with scope). READ with operators named in `users` is refused
(never default to marketing when users operate the thing). The mode given by the caller must equal `mode:`.
Exit codes (shared by chrome-shot.mjs and critic.py): 0 ok, 4 classification missing/invalid/mismatched (nothing was run). 2 = usage.
"""
import json, os, re, sys
from pathlib import Path

OPERATE = re.compile(r"\b(operators?|operations|ops|on-?call|sres?|admins?|administrators?|internal|support agents?)\b", re.I)
HEADER = re.compile(r"^#{1,4}\s*step\s*0\b.*$", re.I | re.M)


def norm(mode):
    return "app" if mode == "tool" else mode


def parse(text):
    """Return the classification fields from NOTES.md text, or None when the section is absent."""
    m = HEADER.search(text)
    if not m:
        return None
    body = re.split(r"^#{1,4}\s", text[m.end():], maxsplit=1, flags=re.M)[0]
    f, tasks, in_tasks = {}, [], False
    for ln in body.splitlines():
        if in_tasks and re.match(r"^\s*[-*]\s+\S", ln):
            tasks.append(re.sub(r"^\s*[-*]\s+", "", ln).strip()); continue
        k = re.match(r"^\s*([a-z_]+)\s*:\s*(.*?)\s*$", ln)
        if k:
            in_tasks = k.group(1) == "primary_tasks"
            if not in_tasks:
                f[k.group(1)] = k.group(2)
        elif ln.strip():
            in_tasks = False
    f["primary_tasks"] = tasks
    return f


def check(text, mode):
    """-> (fields | None, [problems]). Pure: the tests drive this."""
    mode = norm(mode)
    f = parse(text)
    if f is None:
        return None, ["no '## Step 0 classification' section in NOTES.md"]
    p = []
    cls, fm = f.get("classification", "").upper(), norm(f.get("mode", ""))
    if fm not in ("marketing", "app"):
        p.append(f"mode: must be marketing or app (got {f.get('mode', '')!r})")
    if cls not in ("READ", "WORK", "MIXED"):
        p.append(f"classification: must be READ, WORK or MIXED (got {f.get('classification', '')!r})")
    if fm and fm in ("marketing", "app") and fm != mode:
        p.append(f"NOTES.md says mode: {fm} but this run is {mode} (set MODE={mode if mode == 'app' else 'marketing'} to match, or fix the classification honestly)")
    if cls == "READ" and fm == "app" or cls == "WORK" and fm == "marketing":
        p.append(f"classification {cls} cannot have mode: {fm} (READ -> marketing, WORK -> app, MIXED -> one scoped deliverable per mode)")
    if cls == "MIXED" and len(f.get("scope", "")) < 8:
        p.append("classification MIXED needs scope: naming the deliverable this mode covers (two scoped deliverables, each its own mode)")
    for k in ("users", "frequency"):
        if len(f.get(k, "")) < 3:
            p.append(f"{k}: is empty")
    if len(f.get("evidence", "")) < 20:
        p.append("evidence: needs >= 20 characters (the request's own words, task verbs find/compare/trigger/approve/edit, usage numbers)")
    if cls == "READ" and OPERATE.search(f.get("users", "")):
        p.append(f"classification READ but users names operators ({OPERATE.search(f['users']).group(0)!r}): people who operate the thing make it WORK or MIXED")
    if fm == "app":
        t = f["primary_tasks"]
        if not 1 <= len(t) <= 8 or any(len(x) < 6 for x in t):
            p.append("primary_tasks: app mode needs 1-8 '- <verb phrase>' lines (the daily jobs; screens and flows are judged against them)")
        if not re.fullmatch(r"\d{1,4}", f.get("density_target", "").split()[0] if f.get("density_target") else ""):
            p.append("density_target: app mode needs an integer (items/rows visible at 1440x900, e.g. '20 rows at 1440x900')")
    return (None if p else f), p


def find_notes(roots):
    if os.environ.get("PW_NOTES"):
        return [Path(os.environ["PW_NOTES"])]
    seen, out = set(), []
    for r in [*roots, Path.cwd()]:
        d = Path(r).resolve()
        for q in [d, *d.parents]:
            n = q / "NOTES.md"
            if n.exists() and n not in seen:
                seen.add(n); out.append(n)
    return out


def gate(mode, roots=()):
    """-> (fields | None, message). message is the full user-facing error when fields is None."""
    mode = norm(mode)
    if mode not in ("marketing", "app"):
        return None, f"unknown mode {mode!r} (use marketing or app; tool is an alias of app)"
    cands = find_notes(roots)
    errs = []
    for n in cands:
        f, p = check(n.read_text(errors="replace"), mode)
        if f is not None:
            f["notes"] = str(n); return f, ""
        errs.append(f"  {n}: " + "; ".join(p))
    where = "\n".join(errs) or "  (no NOTES.md found: set PW_NOTES=<path>, or create NOTES.md in the project or an ancestor of the output dir)"
    return None, ("CLASSIFICATION REQUIRED (exit 4): nothing was run. Write step 0 into NOTES.md first (SKILL.md Step 0):\n" + where +
                  "\nHeader to paste:\n## Step 0 classification\nmode: " + mode + "\nclassification: " + ("WORK" if mode == "app" else "READ") +
                  "\nusers: <who>\nfrequency: <how often>\nevidence: <request words / task verbs / usage numbers, >= 20 chars>" +
                  ("\ndensity_target: <rows visible at 1440x900>\nprimary_tasks:\n- <verb phrase>" if mode == "app" else ""))


def main(a):
    if "--mode" not in a:
        print(__doc__); return 2
    mode = a[a.index("--mode") + 1]
    roots = [a[i + 1] for i, x in enumerate(a) if x == "--from"]
    f, msg = gate(mode, roots)
    if f is None:
        print(msg, file=sys.stderr); return 4
    print(json.dumps(f) if "--json" in a else f"classification ok: {f['classification']} -> {f['mode']} ({f['notes']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
