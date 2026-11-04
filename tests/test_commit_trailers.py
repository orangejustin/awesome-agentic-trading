import os
import subprocess
import tempfile
import unittest

from tools import commit_trailers

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BODY = "Add a card\n\nWhy it matters.\n"


class StripTest(unittest.TestCase):
    def test_removes_claude_trailers(self):
        msg = BODY + "\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_x\n"
        self.assertEqual(commit_trailers.strip(msg), BODY)

    def test_keeps_human_co_authors(self):
        msg = BODY + "\nCo-Authored-By: Ada <ada@example.com>\n"
        self.assertEqual(commit_trailers.strip(msg), msg)

    def test_message_without_trailers_is_untouched(self):
        self.assertEqual(commit_trailers.strip("no newline at end"), "no newline at end")


class HookTest(unittest.TestCase):
    def test_commit_msg_hook_cleans_a_real_commit(self):
        with tempfile.TemporaryDirectory() as repo:
            def git(*args):
                return subprocess.run(["git", "-C", repo, *args], check=True,
                                      capture_output=True, text=True).stdout
            git("init", "-q")
            os.makedirs(os.path.join(repo, "tools"))
            os.symlink(os.path.join(ROOT, "tools", "commit_trailers.py"),
                       os.path.join(repo, "tools", "commit_trailers.py"))
            git("config", "core.hooksPath", os.path.join(ROOT, ".githooks"))
            git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q",
                "--allow-empty", "-m", "Subject\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
            self.assertEqual(git("log", "-1", "--format=%B").strip(), "Subject")
            self.assertEqual(commit_trailers.offenders("HEAD"), [])


if __name__ == "__main__":
    unittest.main()
