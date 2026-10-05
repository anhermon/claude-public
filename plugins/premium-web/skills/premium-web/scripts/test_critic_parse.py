"""Self-check for critic.parse_reply: python3 scripts/test_critic_parse.py"""
import importlib.util as u, sys
s = u.spec_from_file_location("c", __import__("pathlib").Path(__file__).with_name("critic.py")); m = u.module_from_spec(s); s.loader.exec_module(m)
t = 'Here is {the plan} then:\n{"a": "line1\nline2 it\\\'s", "b": {"c": 1}}\ntrailing }'
r = m.parse_reply(t); print(r)
assert r == {"a": "line1\nline2 it's", "b": {"c": 1}}
assert m.parse_reply("no json") is None
assert m.parse_reply('```json\n{"score": 4}\n```') == {"score": 4}
print("ok")
# the verdict object is the one carrying the required key, not just the largest dict (sealref r8 wow KeyError)
two = '{"example": {"x": 1, "y": 2, "z": 3, "w": 4}}\n{"wow": {"score": 4}}'
assert m.parse_reply(two, ("wow",)) == {"wow": {"score": 4}}
assert m.parse_reply('{"other": 1}', ("wow",)) is None
print("need ok")
assert m.parse_reply('{"wow": {"score": 3}, "fixes": ["a"]\n', ("wow",)) == {"wow": {"score": 3}, "fixes": ["a"]}
print("brace ok")
assert m.parse_reply('{"wow": {"score": 4}, "motion_polish": {"score": 4}}', ("wow", "fallback", "motion_polish")) is None  # truncated: no fallback
print("required keys ok")
assert m.parse_reply('{"wow": {"score": 3, "fixes": ["a"]\n', ("wow",)) == {"wow": {"score": 3, "fixes": ["a"]}}
print("two braces ok")
nested = '{"wow": {"score": 4}, "motion_polish": {"score": 3, "fallback": {"score": 4}, "fixes": []}'
assert m.parse_reply(nested, ("wow", "fallback", "motion_polish"))["fallback"] == {"score": 4}
print("nested ok")
assert m.parse_reply(r'{"a": "path \\' + "' and it\\'s"  + '"}') == {"a": "path \\' and it's"}  # \\' is a real backslash; \' is the model's bad escape
print("escape ok")
# --- UNVERIFIED / mode behaviour (no model calls: judges are stubbed) ---
import io, json, tempfile, contextlib, pathlib, subprocess
assert (m.PAGE_MAX, m.SECTION_MAX) == (0.12, 0.20) and m.PAGE_MAX is m.saturation.PAGE_MAX  # one copy of the saturation limits
real = m.subprocess.run
def nobin(*a, **k): raise FileNotFoundError("claude")
m.subprocess.run = nobin
r = m.ask("x", ("wow",)); assert r["error"].startswith("UNVERIFIED") and not m.judge_wow(["a.png"])["pass"]
m.subprocess.run = real
m.judge_section = lambda n, s, exclude="": {"pass": True, "scores": {c: {"score": 4} for c in m.CRIT}}
m.judge_wow = lambda s, test=None: {"pass": True, "wow": {"score": 4}}
m.judge_page = lambda s, t="", exclude=(): {"pass": True}
NOTES = {"marketing": "## Step 0 classification\nmode: marketing\nclassification: READ\nusers: prospects from search\nfrequency: first visit\nevidence: the page sells the product; nobody operates it\n",
         "app": "## Step 0 classification\nmode: app\nclassification: WORK\nusers: on-call engineers\nfrequency: daily, 30 opens each\nevidence: they find, compare and trigger deploys\ndensity_target: 20 rows\nprimary_tasks:\n- find last night's deploy\n- compare two runs\n"}
WALK = {"tasks": [{"task": "Find last night's deploy", "steps": "2 clicks, 3 keys", "result": "row highlighted", "screens": ["01"]}, {"task": "compare two runs", "steps": 4, "result": "diff visible", "screens": ["01"]}]}
def run(tells, mode, argv=(), notes=None, walk=WALK):
    d = pathlib.Path(tempfile.mkdtemp()); (d / "sections" / "01").mkdir(parents=True); (d / "sections" / "wow").mkdir()
    (d / "sections" / "01" / "1440.png").write_bytes(b""); (d / "sections" / "wow" / "1440-t1.png").write_bytes(b"")
    if tells is not None: (d / "report.json").write_text(json.dumps({"1440": {"eval": tells}}))
    if notes != "": (d / "NOTES.md").write_text(NOTES["app" if mode in ("app", "tool") else "marketing"] if notes is None else notes)
    if walk is not None and mode in ("app", "tool"): (d / "walkthrough.json").write_text(json.dumps(walk))
    m.MODE = "marketing"; buf = io.StringIO(); os.environ.pop("PW_NOTES", None)
    with contextlib.redirect_stdout(buf):
        rc = m.main([str(d / "sections"), *(["--wow", "wow"] if mode not in ("app", "tool") else []), "--mode", mode, *argv])
    return rc, buf.getvalue()
import os
ok_t = {"mode": "marketing", "desktop_gates": True, "tells": {}, "hits": [], "templaty": False, "craft_fail": []}
rc, out = run(None, "marketing");                       assert rc == 3 and "UNVERIFIED: tells.js was not run" in out, out   # was: silent PASS
rc, out = run(ok_t, "marketing");                       assert rc == 0, out                                                  # marketing unchanged
rc, out = run({**ok_t, "desktop_gates": False}, "marketing"); assert rc == 3 and "< 1000px" in out
rc, out = run(ok_t, "bogus");                           assert rc == 3 and "UNVERIFIED: unknown mode" in out
print("unverified/mode ok")
# --- step 0 gate: nothing is judged without a classification of the same mode ---
rc, out = run(ok_t, "marketing", notes="");             assert rc == 4 and "CLASSIFICATION REQUIRED (exit 4)" in out, out
rc, out = run(ok_t, "marketing", notes=NOTES["app"]);   assert rc == 4 and "mode: app but this run is marketing" in out, out
rc, out = run(ok_t, "marketing", notes=NOTES["marketing"].replace("first visit", "daily")); assert rc == 4 and "return and operate" in out, out
print("classification gate ok")
# --- app mode: screens + flows + signature clarity (judges stubbed) ---
A = ["task_clarity", "information_hierarchy", "density", "state_coverage", "interaction_quality", "distinctiveness"]
sc = lambda **o: {"app_scores": {c: {"score": o.get(c, 4)} for c in A}, "ban_hits": []}
assert m.app_verdict(sc())[0] and m.app_verdict(sc(density=3, state_coverage=3))[0]
assert not m.app_verdict(sc(distinctiveness=3))[0] and not m.app_verdict(sc(task_clarity=3))[0]          # generic-but-clean AI dashboard cannot pass
assert not m.app_verdict(sc(density=2))[0] and not m.app_verdict(sc(density=3, state_coverage=3, interaction_quality=3))[0]
assert not m.app_verdict({**sc(), "ban_hits": [{"rule": "marketing structure"}]})[0]
fl = lambda **o: {"flow_scores": {c: {"score": o.get(c, 4)} for c in ("task_clarity", "interaction_quality", "information_hierarchy")}, "completed": o.get("done", True)}
e = {"steps": 3, "result": "x"}
assert m.flow_verdict(fl(), e)[0] and not m.flow_verdict(fl(done=False), e)[0] and not m.flow_verdict(fl(task_clarity=3), e)[0] and not m.flow_verdict(fl(), {"result": "x"})[0]
assert m._same("Find last night's deploy", "find last nights deploy") and not m._same("find", "")
m.judge_screen = lambda n, s, t: {"pass": True, "app_scores": {c: {"score": 4} for c in A}}
m.judge_flow = lambda t, e, s: {"pass": True, "flow_scores": {"task_clarity": {"score": 4}, "interaction_quality": {"score": 4}, "information_hierarchy": {"score": 4}}}
m.judge_signature = lambda s, t, w, ok: {"pass": ok, "signature": {"score": 4}}
m.judge_app_page = lambda s, t="": {"pass": True}
app_t = {**ok_t, "mode": "app", "craft_fail": []}
SIG = ["--signature", "01", "--signature-test", "x"]
rc, out = run(app_t, "app", SIG);                       assert rc == 0, out
rc, out = run({**app_t, "mode": "tool"}, "app", SIG);   assert rc == 0, out                                          # tool-mode scan + app critic: aliases agree
rc, out = run(app_t, "tool", SIG);                      assert rc == 0, out                                          # ... and the reverse
rc, out = run(ok_t, "app", SIG);                        assert rc == 3 and "ran in marketing mode but critic is in app mode" in out, out
rc, out = run(None, "app", SIG);                        assert rc == 3 and "tells.js was not run" in out
rc, out = run(app_t, "app", SIG, walk=None);            assert rc == 3 and "walk-through missing" in out, out
rc, out = run(app_t, "app");                            assert rc == 2 and "--signature" in out
rc, out = run({**app_t, "craft_fail": ["page_shaped_mismatch"]}, "app", SIG); assert rc == 1 and "CRAFT GATE FAIL (tells.js, app): page_shaped_mismatch" in out, out
rc, out = run(app_t, "app", SIG, walk={"tasks": WALK["tasks"][:1]}); assert rc == 1 and "primary task not walked" in out, out   # a task without a walk-through entry fails
rc, out = run(app_t, "app", ["--wow", "01", "--wow-test", "x"]); assert rc == 0, out                                 # --wow is an alias of --signature
print("app mode ok")
