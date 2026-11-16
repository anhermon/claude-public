"""Tests for scripts/sync-upstream.sh.

Run: python3 -m unittest discover -s plugins/skill-creator-plus/tests -v
"""
import os
import shutil
import subprocess
import tempfile
import unittest

PLUGIN = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def read(path):
    with open(path) as f:
        return f.read()


class ScriptModeTest(unittest.TestCase):
    def test_sync_script_is_executable(self):
        script = os.path.join(PLUGIN, "scripts", "sync-upstream.sh")
        self.assertTrue(os.access(script, os.X_OK))


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.plugin = os.path.join(self.tmp, "plugin")
        os.makedirs(os.path.join(self.plugin, "scripts"))
        shutil.copy(os.path.join(PLUGIN, "scripts", "sync-upstream.sh"),
                    os.path.join(self.plugin, "scripts"))
        self.up = os.path.join(self.plugin, "upstream", "skill-creator")
        self.loc = os.path.join(self.plugin, "skills", "skill-creator")
        self.src = os.path.join(self.tmp, "src", "skill-creator")
        self.base = {
            "SKILL.md": "".join(f"line {i}\n" for i in range(1, 21)),
            "scripts/a.py": "print('a')\n",
            "gone.txt": "to be deleted\n",
            "stay.txt": "unchanged\n",
        }
        for root in (self.up, self.loc, self.src):
            for name, text in self.base.items():
                write(os.path.join(root, name), text)

    def run_sync(self, *args):
        env = dict(os.environ, SYNC_DATE="2026-01-01")
        return subprocess.run(
            ["bash", os.path.join(self.plugin, "scripts", "sync-upstream.sh"), *args],
            capture_output=True, text=True, env=env)

    def test_merge_add_delete_preserve_local(self):
        write(os.path.join(self.loc, "SKILL.md"), "LOCAL PATCH\n" + self.base["SKILL.md"])
        write(os.path.join(self.src, "SKILL.md"),
              self.base["SKILL.md"].replace("line 18\n", "line 18 upstream\n"))
        write(os.path.join(self.src, "new.txt"), "added\n")
        os.remove(os.path.join(self.src, "gone.txt"))
        write(os.path.join(self.src, "__pycache__", "x.pyc"), "junk")
        write(os.path.join(self.src, ".DS_Store"), "junk")

        r = self.run_sync(self.src)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(read(os.path.join(self.up, "SKILL.md")),
                         read(os.path.join(self.src, "SKILL.md")))
        self.assertEqual(read(os.path.join(self.up, "new.txt")), "added\n")
        self.assertFalse(os.path.exists(os.path.join(self.up, "gone.txt")))
        self.assertFalse(os.path.exists(os.path.join(self.up, "__pycache__")))
        self.assertFalse(os.path.exists(os.path.join(self.up, ".DS_Store")))
        merged = read(os.path.join(self.loc, "SKILL.md"))
        self.assertTrue(merged.startswith("LOCAL PATCH\n"))
        self.assertIn("line 18 upstream\n", merged)
        self.assertEqual(read(os.path.join(self.loc, "new.txt")), "added\n")
        self.assertFalse(os.path.exists(os.path.join(self.loc, "gone.txt")))
        notes = read(os.path.join(self.plugin, "upstream", "UPSTREAM.md"))
        self.assertIn("2026-01-01", notes)
        self.assertIn("SKILL.md", notes)
        self.assertNotIn(self.tmp, notes)
        self.assertNotIn(os.path.expanduser("~"), notes)
        self.assertNotRegex(notes, r"/(Users|home)/")

    def test_conflict_exits_nonzero_with_markers(self):
        write(os.path.join(self.loc, "SKILL.md"),
              self.base["SKILL.md"].replace("line 10\n", "line 10 local\n"))
        write(os.path.join(self.src, "SKILL.md"),
              self.base["SKILL.md"].replace("line 10\n", "line 10 upstream\n"))
        r = self.run_sync(self.src)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("<<<<<<<", read(os.path.join(self.loc, "SKILL.md")))
        self.assertIn("SKILL.md", r.stderr)
        self.assertIn("line 10 upstream", read(os.path.join(self.up, "SKILL.md")))

    def test_deleted_upstream_but_modified_locally_conflicts(self):
        write(os.path.join(self.loc, "gone.txt"), "local edit\n")
        os.remove(os.path.join(self.src, "gone.txt"))
        r = self.run_sync(self.src)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(read(os.path.join(self.loc, "gone.txt")), "local edit\n")

    def test_noop_when_unchanged(self):
        r = self.run_sync(self.src)
        self.assertEqual(r.returncode, 0)
        self.assertIn("unchanged", r.stdout)
        self.assertIn("missing UPSTREAM.md", r.stdout)
        r = self.run_sync(self.src)
        self.assertIn("nothing to do", r.stdout)

    def test_dry_run_writes_nothing(self):
        write(os.path.join(self.src, "stay.txt"), "changed\n")
        r = self.run_sync("--dry-run", self.src)
        self.assertEqual(r.returncode, 0)
        self.assertIn("M stay.txt", r.stdout)
        self.assertEqual(read(os.path.join(self.up, "stay.txt")), "unchanged\n")
        self.assertEqual(read(os.path.join(self.loc, "stay.txt")), "unchanged\n")


if __name__ == "__main__":
    unittest.main()
