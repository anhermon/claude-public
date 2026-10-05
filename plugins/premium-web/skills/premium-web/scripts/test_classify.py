"""Self-check for the step 0 classification gate: python3 scripts/test_classify.py (no browser, no model calls; the shell part runs chrome-shot only when Chrome exists)"""
import importlib.util as u, os, subprocess, sys, tempfile, pathlib, shutil
here = pathlib.Path(__file__).resolve().parent
s = u.spec_from_file_location("classify", here / "classify.py"); c = u.module_from_spec(s); s.loader.exec_module(c)
READ = "## Step 0 classification\nmode: marketing\nclassification: READ\nusers: prospects arriving from search\nfrequency: first visit\nevidence: the page sells the product; nobody operates it\n"
APP = ("## Step 0 classification\nmode: app\nclassification: WORK\nusers: on-call engineers\nfrequency: daily, 30 opens each\nevidence: they find, compare, trigger and approve deploys\n"
       "density_target: 20 rows at 1440x900\nprimary_tasks:\n- find last night's deploy\n- compare two runs\n")
ok = lambda t, m: c.check(t, m)[1] == []
bad = lambda t, m, frag: any(frag in p for p in c.check(t, m)[1])
assert ok(READ, "marketing") and ok(APP, "app") and ok(APP, "tool")                          # tool is an alias of app
f, p = c.check("# Notes\nnothing here\n", "marketing"); assert f is None and "no '## Step 0" in p[0]   # missing section
assert bad(READ, "app", "NOTES.md says mode: marketing")                                      # mode must match the run
assert bad(APP, "marketing", "NOTES.md says mode: app")
assert bad(READ.replace("READ", "WORK"), "marketing", "cannot have mode")                    # WORK with marketing
assert bad(READ.replace("classification: READ", "classification: maybe"), "marketing", "READ, WORK or MIXED")
assert bad(READ.replace("users: prospects arriving from search", "users: on-call SREs and admins"), "marketing", "operators")  # never default to marketing when users operate it
assert bad(READ.replace("evidence: the page sells the product; nobody operates it", "evidence: short"), "marketing", "evidence")
assert bad(READ.replace("frequency: first visit", "frequency:"), "marketing", "frequency")
mixed = READ.replace("READ", "MIXED")
assert bad(mixed, "marketing", "scope"); assert ok(mixed + "scope: the public docs landing page only\n", "marketing")   # MIXED: one scoped deliverable per mode
assert ok(APP.replace("WORK", "MIXED") + "scope: the signed-in console only\n", "app")
assert bad(APP.replace("- find last night's deploy\n- compare two runs\n", ""), "app", "primary_tasks")                  # app requires the task list
assert bad(APP.replace("density_target: 20 rows at 1440x900\n", ""), "app", "density_target")
assert ok(READ.replace("mode: marketing", "mode: marketing") , "marketing") and not bad(READ, "marketing", "primary_tasks")  # marketing needs no task list
assert ok("## Intro\nx\n\n" + APP + "\n## Later\nmode: bogus\n", "app")                          # section ends at the next heading
# gate(): file discovery. PW_NOTES wins; else NOTES.md in an ancestor of the --from dir
d = pathlib.Path(tempfile.mkdtemp()); (d / "shots" / "x").mkdir(parents=True)
old = os.environ.pop("PW_NOTES", None); cwd = os.getcwd(); os.chdir(tempfile.mkdtemp())
f, msg = c.gate("marketing", [d / "shots"]); assert f is None and "CLASSIFICATION REQUIRED (exit 4)" in msg and "## Step 0 classification" in msg   # message prints the header to paste
(d / "NOTES.md").write_text(READ); f, msg = c.gate("marketing", [d / "shots" / "x"]); assert f and f["notes"] == str((d / "NOTES.md").resolve()), msg
f, msg = c.gate("app", [d / "shots"]); assert f is None and "NOTES.md says mode: marketing" in msg
(d / "alt.md").write_text(APP); os.environ["PW_NOTES"] = str(d / "alt.md"); f, msg = c.gate("tool", [d]); assert f and f["primary_tasks"][0].startswith("find"), msg
os.environ.pop("PW_NOTES")
assert c.main(["--mode", "marketing", "--from", str(d / "shots")]) == 0 and c.main(["--mode", "app", "--from", str(d / "shots")]) == 4 and c.main([]) == 2
os.chdir(cwd)
print("classify unit ok")
# critic.py and chrome-shot.mjs refuse with exit 4 (no model call, no Chrome needed: the gate runs first)
env = {k: v for k, v in os.environ.items() if k != "PW_NOTES"}
empty = pathlib.Path(tempfile.mkdtemp()); (empty / "sections" / "01").mkdir(parents=True)
r = subprocess.run([sys.executable, str(here / "critic.py"), str(empty / "sections"), "--wow", "01"], capture_output=True, text=True, env=env, cwd=empty)
assert r.returncode == 4 and "CLASSIFICATION REQUIRED" in r.stdout, (r.returncode, r.stdout, r.stderr)
r = subprocess.run([sys.executable, str(here / "critic.py"), str(empty / "sections"), "--mode", "app", "--signature", "01"], capture_output=True, text=True, env=env, cwd=empty)
assert r.returncode == 4, (r.returncode, r.stdout)
if shutil.which("node"):
    r = subprocess.run(["node", str(here / "chrome-shot.mjs"), "http://127.0.0.1:9/", str(empty / "out")], capture_output=True, text=True, env=env, cwd=empty)
    assert r.returncode == 4 and "CLASSIFICATION REQUIRED" in r.stderr, (r.returncode, r.stderr)
    (empty / "NOTES.md").write_text(READ)   # a marketing run with an APP-mode request is refused too
    r = subprocess.run(["node", str(here / "chrome-shot.mjs"), "http://127.0.0.1:9/", str(empty / "out")], capture_output=True, text=True, env={**env, "MODE": "tool"}, cwd=empty)
    assert r.returncode == 4 and "mode: marketing but this run is app" in r.stderr, (r.returncode, r.stderr)
print("scripts refuse without classification (exit 4) ok")
