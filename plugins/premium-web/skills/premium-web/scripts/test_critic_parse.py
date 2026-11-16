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
