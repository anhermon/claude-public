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
def run(tells, mode, argv=()):
    d = pathlib.Path(tempfile.mkdtemp()); (d / "sections" / "01").mkdir(parents=True); (d / "sections" / "wow").mkdir()
    (d / "sections" / "01" / "1440.png").write_bytes(b""); (d / "sections" / "wow" / "1440-t1.png").write_bytes(b"")
    if tells is not None: (d / "report.json").write_text(json.dumps({"1440": {"eval": tells}}))
    m.MODE = "marketing"; buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = m.main([str(d / "sections"), "--wow", "wow", "--mode", mode, *argv])
    return rc, buf.getvalue()
ok_t = {"mode": "marketing", "desktop_gates": True, "tells": {}, "hits": [], "templaty": False, "craft_fail": []}
rc, out = run(None, "marketing");                       assert rc == 3 and "UNVERIFIED: tells.js was not run" in out, out   # was: silent PASS
rc, out = run(ok_t, "marketing");                       assert rc == 0, out                                                  # marketing unchanged
rc, out = run({**ok_t, "desktop_gates": False}, "marketing"); assert rc == 3 and "< 1000px" in out
rc, out = run(ok_t, "tool");                            assert rc == 3 and "mode but critic is in tool" in out              # mode mismatch
rc, out = run({**ok_t, "mode": "tool"}, "tool");        assert rc == 0, out
rc, out = run({**ok_t, "mode": "tool", "craft_fail": ["wow_visible"]}, "tool"); assert rc == 1 and "CRAFT GATE FAIL" in out and "tool mode" in out, out
rc, out = run(ok_t, "bogus");                           assert rc == 3 and "UNVERIFIED: unknown mode" in out
print("unverified/mode ok")
