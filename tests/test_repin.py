import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools import repin

OLD_README = "# Tool\n\nIntro.\n\n## Orders\n\nPaper trading only.\nNo live orders.\n\n## Install\n\npip install tool\n"
NEW_README = "# Tool\n\nIntro.\nA new paragraph.\n\n## Orders\n\nPaper trading only.\nNo live orders.\n\n## Install\n\nuv pip install tool\n"


class Relocate(unittest.TestCase):
    def test_unchanged_block_is_found_at_its_new_lines(self):
        self.assertEqual(repin.relocate(OLD_README.splitlines(), NEW_README.splitlines(), 7, 8), (8, 9))

    def test_changed_block_is_not_relocated(self):
        self.assertIsNone(repin.relocate(OLD_README.splitlines(), NEW_README.splitlines(), 12, 12))

    def test_nearest_duplicate_wins(self):
        old = ["a", "x", "b", "x"]
        self.assertEqual(repin.relocate(old, ["a", "x", "b", "c", "x"], 4, 4), (5, 5))


class EndToEnd(unittest.TestCase):
    """A local upstream repository with two commits, and a catalog that cites the first."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.up = t / "up"
        self.up.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "uploadpack.allowAnySHA1InWant", "true")
        self.git("config", "uploadpack.allowFilter", "true")
        (self.up / "README.md").write_text(OLD_README)
        (self.up / "LICENSE").write_text("MIT License\n")
        self.old = self.commit("first")
        (self.up / "README.md").write_text(NEW_README)
        self.new = self.commit("second")
        self.root = t / "cat"
        (self.root / "catalog").mkdir(parents=True)
        base = f"https://github.com/o/tool/blob/{self.old}/README.md?plain=1"
        (self.root / "catalog/projects.toml").write_text(
            f'[[project]]\nid = "tool"\nlast_commit = "2026-01-01"\nlast_sha = "{self.old}"\nchecked = "2026-01-02"\n'
            f'sources = [\n  {{ what = "orders", url = "{base}#L7-L8" }},\n  {{ what = "install", url = "{base}#L12" }},\n]\n')
        (self.root / "catalog/components.toml").write_text(f'x = "https://github.com/o/tool/tree/{self.old}"\n')
        self.p = {"id": "tool", "repo": "o/tool", "last_sha": self.old, "license_file": "LICENSE"}

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
        return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=self.up, check=True,
                              capture_output=True, text=True, env=env).stdout.strip()

    def commit(self, msg):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD")

    def test_diff_reports_same_and_changed_citations(self):
        r = repin.compare(self.p, root=self.root, out=self.root / "out", remote=str(self.up))
        self.assertTrue(r["moved"])
        self.assertEqual(r["license"], "same")
        self.assertEqual(r["readme"]["added"], 2)
        status = {c["url"].split("#")[-1] if "#" in c["url"] else "tree": c["status"] for c in r["citations"]}
        self.assertEqual(status, {"L7-L8": "same", "L12": "changed", "tree": "same"})
        self.assertTrue((self.root / "out/tool/README.diff").exists())
        self.assertEqual(len(repin.blockers(r)), 1)

    def test_apply_refuses_until_every_citation_is_settled(self):
        r = repin.compare(self.p, root=self.root, remote=str(self.up))
        before = (self.root / "catalog/projects.toml").read_text()
        self.assertEqual(repin.apply([r], "2026-02-02", root=self.root), ["tool"])
        self.assertEqual((self.root / "catalog/projects.toml").read_text(), before)

    def test_apply_repins_and_records_the_read_date(self):
        text = (self.root / "catalog/projects.toml").read_text().replace("#L12", "#L5")
        (self.root / "catalog/projects.toml").write_text(text)
        r = repin.compare(self.p, root=self.root, remote=str(self.up))
        self.assertEqual(repin.apply([r], "2026-02-02", root=self.root), [])
        out = (self.root / "catalog/projects.toml").read_text()
        self.assertIn(f"{self.new}/README.md?plain=1#L8-L9", out)
        self.assertIn(f"{self.new}/README.md?plain=1#L6", out)
        self.assertIn(f'last_sha = "{self.new}"\nchecked = "2026-02-02"', out)
        self.assertNotIn(self.old, out + (self.root / "catalog/components.toml").read_text())


if __name__ == "__main__":
    unittest.main()
