"""Unit tests with mocked providers. Run: python3 -m unittest test_core -v  (needs Pillow)
Fakes: a `codex` binary and a `secrets-runner` binary on PATH, and a local HTTP server standing in for all 5 image APIs."""
import base64
import http.server
import io
import json
import os
import stat
import sys
import tempfile
import threading
import unittest
from pathlib import Path

from PIL import Image

TMP = Path(tempfile.mkdtemp(prefix="imagegen-test-"))
os.environ["IMAGEGEN_STATE"] = str(TMP / "state")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import core  # noqa: E402

core.MIN_INTERVAL = 0


def png_bytes(colour=(40, 80, 160), size=(64, 48)):
    b = io.BytesIO(); Image.new("RGB", size, colour).save(b, "PNG"); return b.getvalue()


def write_exe(path: Path, body: str):
    path.write_text("#!" + sys.executable + "\n" + body)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


BIN = TMP / "bin"; BIN.mkdir()
COUNT = TMP / "codex-calls"
# Fake codex: reads the job from stdin, writes a PNG to the requested path (or, in MODE=gendir, only into the
# generated_images dir like real codex does when it forgets to copy; MODE=quota prints a quota error).
write_exe(BIN / "codex", f"""
import sys, re, os, io
from PIL import Image
open({str(COUNT)!r}, "a").write("x")
job = sys.stdin.read()
mode = os.environ.get("FAKE_CODEX_MODE", "copy")
if mode == "quota":  # real codex: prints the error, exits 0, and another session's image may be newest
    d = os.path.join(os.environ["CODEX_GENERATED_DIR"], "other-session"); os.makedirs(d, exist_ok=True)
    Image.new("RGB", (8, 8)).save(os.path.join(d, "exec-foreign.png"))
    print("ERROR: You've hit your usage limit. Upgrade to Pro, or try again at Oct 2nd, 2026 1:58 AM."); sys.exit(0)
out = re.search(r"save it as (\\S+\\.png)", job).group(1)
if mode == "gendir":
    d = os.path.join(os.environ["CODEX_GENERATED_DIR"], "sess"); os.makedirs(d, exist_ok=True); out = os.path.join(d, "exec-1.png")
    print("exec /bin/zsh -lc 'cp " + out + " somewhere'")
Image.new("RGB", (96, 64), (200, 120, 40)).save(out)
print("hook: PreToolUse Completed")
""")
# Fake secrets-runner: `keys <group>` lists names; `run --ref secrets://g/K=ENV -- cmd...` injects a fake secret.
write_exe(BIN / "secrets-runner", """
import os, sys
a = sys.argv[1:]
if a[0] == "keys":
    for k in os.environ.get("FAKE_VAULT_KEYS", "").split(","):
        if k: print(f"{k}  secrets://{a[1]}/{k}")
    sys.exit(0)
if a[0] == "run":
    env = dict(os.environ); i = a.index("--")
    ref = a[a.index("--ref") + 1]; env[ref.split("=")[1]] = "fake-secret-123"
    os.execvpe(a[i + 1], a[i + 1:], env)
""")
os.environ["PATH"] = f"{BIN}:{os.environ['PATH']}"
os.environ["CODEX_GENERATED_DIR"] = str(TMP / "generated")

SEEN = []


class Mock(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):  # image download for url-returning providers
        self.send_response(200); self.end_headers(); self.wfile.write(png_bytes((10, 200, 10)))

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        auth = self.headers.get("Authorization") or self.headers.get("x-goog-api-key")
        SEEN.append((self.path, auth, body))
        b64 = base64.b64encode(png_bytes()).decode()
        url = f"http://127.0.0.1:{self.server.server_port}/img.png"
        if "images/generations" in self.path:
            r = {"data": [{"b64_json": b64}]}
        elif "generateContent" in self.path:
            r = {"candidates": [{"content": {"parts": [{"text": "ok"}, {"inlineData": {"data": b64}}]}}]}
        elif "predictions" in self.path:
            r = {"status": "succeeded", "output": [url]}
        else:
            r = {"images": [{"url": url}]}
        out = json.dumps(r).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(out)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.HTTPServer(("127.0.0.1", 0), Mock)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        os.environ["IMAGEGEN_API_BASE"] = f"http://127.0.0.1:{cls.srv.server_port}"

    def setUp(self):
        self.out = Path(tempfile.mkdtemp(dir=TMP))
        os.environ.pop("FAKE_CODEX_MODE", None)
        COUNT.write_text("")

    def test_art_direct(self):
        a = core.art_direct("a glass block with a key inside", "hero", "paper-editorial")
        self.assertEqual(a["aspect"], "3:2")
        self.assertIn("no text", a["prompt"].lower())
        self.assertIn("left 40%", a["prompt"])
        with self.assertRaises(ValueError):
            core.art_direct("x", "banner")

    def test_art_direct_page_colours(self):
        a = core.art_direct("a sheet", "plate", "dark-studio", {"ground": "#F2EFE8"})["prompt"]
        self.assertIn("#F2EFE8", a)
        self.assertNotIn("#0E0F12", a)
        self.assertEqual(core._colours("ground=#111,accent=#222"), {"ground": "#111", "accent": "#222"})

    def test_names_idempotent(self):
        a = core.output_path(self.out, "Hero!", "p", "3:2", "codex", 0)
        self.assertEqual(a, core.output_path(self.out, "Hero!", "p", "3:2", "codex", 0))
        self.assertNotEqual(a, core.output_path(self.out, "Hero!", "p", "3:2", "codex", 1))
        self.assertTrue(a.name.startswith("hero-"))

    def test_codex_generates_then_skips(self):
        r = core.generate_image("brief", "3:2", str(self.out), "hero", "codex")
        self.assertEqual(r[0]["status"], "generated", r)
        self.assertTrue(Path(r[0]["path"]).exists())
        self.assertIn("| codex | 3:2 |", (self.out / "MANIFEST.md").read_text())
        r2 = core.generate_image("brief", "3:2", str(self.out), "hero", "codex")
        self.assertEqual(r2[0]["status"], "exists")
        self.assertEqual(len(COUNT.read_text()), 1, "second call must not invoke codex")
        self.assertEqual((self.out / "MANIFEST.md").read_text().count("hero-"), 1)

    def test_codex_fallback_to_generated_dir(self):
        os.environ["FAKE_CODEX_MODE"] = "gendir"
        r = core.generate_image("other brief", "1:1", str(self.out), "card", "codex")
        self.assertEqual(r[0]["status"], "generated", r)

    def test_codex_quota_failure(self):
        os.environ["FAKE_CODEX_MODE"] = "quota"
        r = core.generate_image("q brief", "1:1", str(self.out), None, "codex")
        self.assertEqual(r[0]["status"], "failed")
        self.assertIn("quota", r[0]["detail"])
        self.assertIn("try again at", r[0]["detail"])
        self.assertFalse(Path(r[0]["path"]).exists(), "must not adopt another session's image")

    def test_api_unavailable_without_key(self):
        os.environ["FAKE_VAULT_KEYS"] = ""
        ok, why = core.providers()["openai"].available()
        self.assertFalse(ok); self.assertIn("OPENAI_API_KEY", why)
        r = core.generate_image("x", "1:1", str(self.out), None, "openai")
        self.assertEqual(r[0]["status"], "failed")

    def test_all_api_adapters_via_secrets_runner(self):
        os.environ["FAKE_VAULT_KEYS"] = ",".join(core.API_PROVIDERS.values())
        for name in core.API_PROVIDERS:
            SEEN.clear()
            r = core.generate_image(f"brief for {name}", "16:9", str(self.out), name, name)
            self.assertEqual(r[0]["status"], "generated", (name, r))
            self.assertIn("fake-secret-123", SEEN[0][1], name)  # key reached the API via the child env
            log = Path(r[0]["path"]).with_suffix(".log").read_text()
            self.assertNotIn("fake-secret-123", log)
            Image.open(r[0]["path"]).verify()

    def test_auto_prefers_codex(self):
        r = core.generate_image("auto brief", "1:1", str(self.out), None, "auto")
        self.assertEqual(r[0]["provider"], "codex")

    def test_auto_falls_through_codex_quota_to_local(self):
        os.environ["FAKE_CODEX_MODE"] = "quota"
        fake = TMP / "localgen"
        write_exe(fake, "import sys\nfrom PIL import Image\n"
                        "a = sys.argv; Image.new('RGB', (8, 8)).save(a[a.index('--out') + 1])\n")
        old = core.LocalProvider.LG
        core.LocalProvider.LG = fake
        try:
            r = core.generate_image("fallthrough brief", "1:1", str(self.out), None, "auto")
        finally:
            core.LocalProvider.LG = old
        self.assertEqual(r[0]["status"], "generated", r)
        self.assertEqual(r[0]["provider"], "local")

    def test_auto_ends_at_browser_handoff(self):
        os.environ["FAKE_CODEX_MODE"] = "quota"
        old = core.LocalProvider.LG
        core.LocalProvider.LG = TMP / "nope"  # unavailable
        try:
            r = core.generate_image("fallthrough brief 2", "1:1", str(self.out), None, "auto")
        finally:
            core.LocalProvider.LG = old
        self.assertEqual(r[0]["status"], "needs_browser_agent")

    def test_browser_handoff(self):
        r = core.generate_image("web brief", "4:5", str(self.out), "plate", "gemini-web")
        self.assertEqual(r[0]["status"], "needs_browser_agent")
        job = json.loads((TMP / "state" / "browser-jobs" / f"{r[0]['job_id']}.json").read_text())
        self.assertTrue(any("FAILED" in s for s in job["steps"]))
        shot = self.out / "capture.jpg"; Image.new("RGB", (50, 60), (1, 2, 3)).save(shot)
        done = core.complete_browser_job(r[0]["job_id"], str(shot))
        self.assertTrue(Path(done["path"]).exists())
        self.assertIn("browser capture", (self.out / "MANIFEST.md").read_text())

    def test_limiter_cap(self):
        old = core.HOURLY_CAP; core.HOURLY_CAP = 2
        (TMP / "state" / "limiter.json").unlink(missing_ok=True)
        try:
            core.limiter_acquire(now=1000.0); core.limiter_acquire(now=1001.0)
            with self.assertRaises(core.RateLimited):
                core.limiter_acquire(now=1002.0)
            core.limiter_acquire(now=1000.0 + 3601)  # window rolled
        finally:
            core.HOURLY_CAP = old
            (TMP / "state" / "limiter.json").unlink(missing_ok=True)

    def test_compare_and_review(self):
        a, b, c = self.out / "a.png", self.out / "b.png", self.out / "c.png"
        g = Image.linear_gradient("L").resize((300, 200)).convert("RGB")
        g.save(a); g.save(b); Image.effect_noise((300, 200), 80).convert("RGB").save(c)
        r = core.compare([str(a), str(b), str(c)], target_aspect="3:2")
        flags = {Path(x["file"]).name: x["flags"] for x in r["images"]}
        self.assertTrue(any("near-duplicate" in f for f in flags["a.png"]))
        self.assertFalse(any("near-duplicate" in f for f in flags["c.png"]))
        self.assertTrue(Path(r["contact_sheet"]).exists())
        core.manifest_add(a, "p", "codex", "generated", "3:2")
        core.record_review(str(a), "cut", "does not explain the section")
        self.assertIn("| cut: does not explain the section |", (self.out / "MANIFEST.md").read_text())

    def test_optimise(self):
        src = self.out / "big.png"
        Image.effect_noise((1200, 800), 40).convert("RGB").save(src)
        r = core.optimise(str(src), [640, 1024, 2000], ["avif", "webp"], name="hero", budget_kb=1)
        names = sorted(Path(f["file"]).name for f in r["files"])
        self.assertEqual(names, ["hero-1024.avif", "hero-1024.webp", "hero-640.avif", "hero-640.webp"])
        self.assertTrue(any("no upscaling" in w for w in r["warnings"]))
        self.assertIn("hero-640.avif 640w", r["srcset"]["avif"])


if __name__ == "__main__":
    unittest.main()
