import unittest

from tools import privacy_lint as pl


class Patterns(unittest.TestCase):
    def hits(self, text):
        return pl.scan_text(text, pl.GENERIC, "x")

    def test_flags_what_must_not_be_published(self):
        bad = {
            "email address": "contact me at someone@company.org",  # privacy-lint: allow
            "API key (sk-...)": "key = sk-" + "a1b2c3d4" * 4,
            "GitHub token": "token ghp_" + "A" * 36,
            "Slack token": "xoxb-" + "1" * 12,
            "Slack workspace URL": "see https://myteam.slack.com/archives/C1",  # privacy-lint: allow
            "AWS access key": "AKIA" + "ABCDEFGHIJKLMNOP",
            "private key block": "-----BEGIN RSA PRIVATE KEY-----",  # privacy-lint: allow
            "home directory path": "cd /Users/someone/project",  # privacy-lint: allow
            "named secret-store lookup": 'key_command = ["security", "find-generic-password", "-s", "my-real-item", "-w"]',  # privacy-lint: allow
        }
        for label, text in bad.items():
            self.assertTrue(any(label in h for h in self.hits(text)), label)

    def test_accepts_harmless_text(self):
        ok = ["noreply@users.noreply.github.com", "git@github.com:org/repo.git", "see you@example.com",
              'key_command = ["security", "find-generic-password", "-s", "YOUR-SERVICE-NAME", "-w"]',
              "Sharpe 2.06 at 252 periods per year", "https://arxiv.org/abs/2412.20138"]
        for text in ok:
            self.assertEqual(self.hits(text), [], text)

    def test_denylist_is_case_insensitive(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "deny.txt"
            f.write_text("# comment\nsecretword\n")
            pats = pl.load_denylist(f)
            self.assertEqual(len(pl.scan_text("A SecretWord here", pats, "x")), 1)

    def test_repository_is_clean(self):
        self.assertEqual(pl.lint_files(pl.GENERIC), [])


if __name__ == "__main__":
    unittest.main()
