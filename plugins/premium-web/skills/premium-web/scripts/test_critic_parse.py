"""Self-check for critic.py without calling a model: python3 scripts/test_critic_parse.py
Covers reply parsing, the pass rule, usage errors, the no-corpus calibrate path, and one end-to-end run against a
fake `claude` on PATH over a tiny synthetic corpus (zero tokens)."""
import importlib.util as u
import io
import json
import os
import re
import stat
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
s = u.spec_from_file_location("c", HERE / "critic.py")
m = u.module_from_spec(s)
s.loader.exec_module(m)


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


# ---- reply parsing (kept from the original self-check)
t = 'Here is {the plan} then:\n{"a": "line1\nline2 it\\\'s", "b": {"c": 1}}\ntrailing }'
assert m.parse_reply(t) == {"a": "line1\nline2 it's", "b": {"c": 1}}
assert m.parse_reply("no json") is None
assert m.parse_reply('```json\n{"score": 4}\n```') == {"score": 4}
two = '{"example": {"x": 1, "y": 2, "z": 3, "w": 4}}\n{"wow": {"score": 4}}'
assert m.parse_reply(two, ("wow",)) == {"wow": {"score": 4}}
assert m.parse_reply('{"other": 1}', ("wow",)) is None
assert m.parse_reply('{"wow": {"score": 3}, "fixes": ["a"]\n', ("wow",)) == {"wow": {"score": 3}, "fixes": ["a"]}
assert m.parse_reply('{"wow": {"score": 4}, "motion_polish": {"score": 4}}', ("wow", "fallback", "motion_polish")) is None
assert m.parse_reply('{"wow": {"score": 3, "fixes": ["a"]\n', ("wow",)) == {"wow": {"score": 3, "fixes": ["a"]}}
nested = '{"wow": {"score": 4}, "motion_polish": {"score": 3, "fallback": {"score": 4}, "fixes": []}'
assert m.parse_reply(nested, ("wow", "fallback", "motion_polish"))["fallback"] == {"score": 4}
assert m.parse_reply(r'{"a": "path \\' + "' and it\\'s" + '"}') == {"a": "path \\' and it's"}
print("parse ok")


# ---- the pass rule
def sec(**over):
    sc = {c: 4 for c in m.CRIT}
    sc.update(over)
    return {"scores": {c: {"score": v, "evidence": "x"} for c, v in sc.items()}, "explanatory_visual_present": True, "ban_hits": []}


assert m.verdict(sec())[0]
assert not m.verdict(sec(focal_visual=3))[0]                        # focal moment needs FOCAL_MIN
assert not m.verdict(sec(polish=2))[0]                              # nothing below the floor
assert not m.verdict(sec(finish=3, hierarchy=3, polish=3))[0]       # too many 3s
assert m.verdict(sec(finish=3, hierarchy=3))[0]                     # two 3s are allowed
bad = sec()
bad["ban_hits"] = [{"rule": "Uniform panel grid", "evidence": "x"}]
assert not m.verdict(bad)[0]
assert not m.verdict({"error": "x"})[0]
assert m.page_pass({"could_be_20_others": False})                   # no refs: distinctiveness decides
assert not m.page_pass({"could_be_20_others": True})
assert not m.page_pass({"could_be_20_others": False, "closest_to": "fail_refs"}, have_refs=True)
assert m.page_pass({"could_be_20_others": False, "closest_to": "pass_refs"}, have_refs=True)
print("verdict ok")

# ---- no private anchors or gallery left in the scripts
for f in ("critic.py", "saturation.py"):
    body = (HERE / f).read_text().lower()
    for word in ("gallery", "users"):
        assert not re.search(rf"\b{word}\b", body), f"{f} still mentions {word}"
print("no leftovers ok")

# ---- usage errors and the no-corpus calibrate path
r, out = quiet(m.main, ["--calibrate"])
assert r == m.EXIT_USAGE and "Build one outside the repo" in out
r, out = quiet(m.main, [])
assert r == m.EXIT_USAGE
with tempfile.TemporaryDirectory() as d:
    r, out = quiet(m.main, [d])                                     # --wow is required
    assert r == m.EXIT_USAGE and "REQUIRED" in out
ap = m.build_parser().parse_args(["x", "--wow", "w", "--pass-refs", "/p", "--fail-refs", "/f", "--calibrate", "/c"])
assert (ap.pass_refs, ap.fail_refs, ap.calibrate) == ("/p", "/f", "/c")
print("usage ok")

# ---- end to end with a fake `claude` that answers by the schema it is given
FAKE = '''#!/usr/bin/env python3
import json, os, sys
sch = json.loads(sys.argv[sys.argv.index("--json-schema") + 1])
req = sch["required"]
sc = int(os.environ.get("FAKE_SCORE", "4"))
S = lambda: {"score": sc, "evidence": "fake"}
if "scores" in req:
    o = {"section": "s", "explanatory_visual_present": True, "ban_hits": [], "fixes": [],
         "scores": {c: S() for c in ["distinctiveness", "focal_visual", "finish", "hierarchy", "polish"]}}
elif "wow" in req:
    o = {"wow": S(), "motion_polish": S(), "fallback": S(), "fixes": []}
else:
    o = {"could_be_20_others": sc < 4, "verdict": "fake", "closest_to": "pass_refs" if sc >= 4 else "fail_refs"}
print(json.dumps([{"type": "result", "structured_output": o}]))
'''
from PIL import Image  # noqa: E402

with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    bindir = d / "bin"
    bindir.mkdir()
    fake = bindir / "claude"
    fake.write_text(FAKE)
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    os.environ["PATH"] = f"{bindir}{os.pathsep}{os.environ['PATH']}"

    def img(p, colour=(40, 40, 44)):
        p.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (64, 40), colour).save(p)

    out_dir = d / "shots" / "sections"
    for name in ("01-hero", "02-detail"):
        img(out_dir / name / "1440.png")
        img(out_dir / name / "390.png")
    for k in range(1, 3):
        img(out_dir / "wow" / f"1440-t{k}.png")
    img(out_dir / "wow" / "1440-rm-t1.png")
    img(d / "refs" / "pass" / "a.png")
    img(d / "refs" / "fail" / "b.png")

    os.environ["FAKE_SCORE"] = "4"
    r, out = quiet(m.main, [str(out_dir), "--wow", "wow", "--wow-test", "a stranger would say x",
                            "--pass-refs", str(d / "refs" / "pass"), "--fail-refs", str(d / "refs" / "fail")])
    assert r == m.EXIT_OK, out
    assert json.loads((out_dir / "critic.json").read_text())["page"]["pass"]
    os.environ["FAKE_SCORE"] = "2"
    for rnd in range(m.MAX_ROUNDS):
        r, out = quiet(m.main, [str(out_dir), "--wow", "wow"])
        assert r == m.EXIT_FAIL, out
    assert "ROUND BUDGET USED" in (out_dir / "critic.json").read_text()   # bounded rounds
    # calibrate with a labelled corpus: a critic that scores 4 everywhere misjudges the fail/ image
    os.environ["FAKE_SCORE"] = "4"
    r, out = quiet(m.main, ["--calibrate", str(d / "refs")])
    assert r == m.EXIT_FAIL and "WRONG" in out and "ok    [pass]" in out, out
print("end-to-end ok")
print("ok")
