"""The weekly source check: its decisions are tested offline with recorded observations."""
import unittest

from tools import verify

OLD, NEW = "a" * 40, "b" * 40
PROJECT = {"id": "x", "repo": "o/x", "last_sha": OLD, "last_commit": "2026-10-01", "license_file": "LICENSE",
           "license_status": "open"}


class Projects(unittest.TestCase):
    def levels(self, found):
        return sorted((f["level"], f["message"]) for f in found)

    def test_unreachable_fails(self):
        self.assertEqual(verify.compare_project(PROJECT, None, {}, None)[0]["level"], "fail")

    def test_unchanged_is_silent(self):
        self.assertEqual(verify.compare_project(PROJECT, OLD, {}, None), [])

    def test_moved_head_is_a_recheck_with_both_commits(self):
        facts = {OLD: {"date": "2026-10-01", "license_blob": "l1"}, NEW: {"date": "2026-10-20", "license_blob": "l1"}}
        found = verify.compare_project(PROJECT, NEW, facts, None)
        self.assertEqual([f["level"] for f in found], ["recheck"])
        self.assertEqual((found[0]["old_sha"], found[0]["new_sha"], found[0]["new_date"]), (OLD, NEW, "2026-10-20"))

    def test_changed_or_missing_license_file_fails(self):
        changed = {OLD: {"date": "d", "license_blob": "l1"}, NEW: {"date": "d", "license_blob": "l2"}}
        gone = {OLD: {"date": "d", "license_blob": "l1"}, NEW: {"date": "d", "license_blob": ""}}
        for facts, word in ((changed, "changed"), (gone, "gone")):
            fails = [f for f in verify.compare_project(PROJECT, NEW, facts, None) if f["level"] == "fail"]
            self.assertEqual(len(fails), 1)
            self.assertIn(word, fails[0]["message"])

    def test_newly_archived_fails_unless_marked(self):
        api = {"archived": True, "spdx": "MIT", "pushed_at": ""}
        self.assertEqual(verify.compare_project(PROJECT, OLD, {}, api)[0]["level"], "fail")
        self.assertEqual(verify.compare_project(dict(PROJECT, maintenance="archived"), OLD, {}, api), [])

    def test_detected_license_where_catalog_has_none_is_a_recheck(self):
        p = dict(PROJECT, license_file="", license_status="declared")
        found = verify.compare_project(p, OLD, {}, {"archived": False, "spdx": "MIT", "pushed_at": ""})
        self.assertEqual([f["level"] for f in found], ["recheck"])

    def test_unfetchable_checked_commit_is_reported(self):
        facts = {OLD: {"error": "commit not fetchable"}, NEW: {"date": "d", "license_blob": "l1"}}
        msgs = [f["message"] for f in verify.compare_project(PROJECT, NEW, facts, None)]
        self.assertTrue(any("can no longer be fetched" in m for m in msgs))


class PapersAndLinks(unittest.TestCase):
    def test_paper_changes(self):
        p = {"arxiv": "2401.00001", "title": "A Title", "published": "2024-01-01", "updated": "2024-01-01"}
        self.assertEqual(verify.compare_paper(p, None)[0]["level"], "fail")
        retitled = verify.compare_paper(p, {"title": "Another", "published": "2024-01-01", "updated": "2024-01-01"})
        self.assertEqual([f["level"] for f in retitled], ["fail"])
        newer = verify.compare_paper(p, {"title": " a  title ", "published": "2024-01-01", "updated": "2024-05-01"})
        self.assertEqual([f["level"] for f in newer], ["recheck"])

    def test_http_classification(self):
        self.assertEqual([verify.classify_http(s) for s in (200, 301, 404, 410, 403, 429, 500, None)],
                         ["ok", "ok", "fail", "fail", "unverifiable", "unverifiable", "unverifiable", "unverifiable"])

    def test_pinned_github_links_are_recognised(self):
        m = verify.GH_PINNED.match(f"https://github.com/o/x/blob/{OLD}/docs/a%20b.md?plain=1#L3-L5")
        self.assertEqual((m.group(1), m.group(2), m.group(3)), ("o/x", OLD, "docs/a%20b.md"))
        self.assertIsNone(verify.GH_PINNED.match("https://github.com/o/x"))
        self.assertTrue(verify.X_POST.match("https://x.com/user/status/123"))


class Report(unittest.TestCase):
    def test_report_lists_failures_moves_and_unverifiable(self):
        found = [
            verify.finding("repo", "x", "fail", "license file LICENSE changed since the checked commit", repo="o/x"),
            verify.finding("repo", "y", "recheck", "HEAD moved since the checked commit", repo="o/y", old_sha=OLD,
                           new_sha=NEW, old_date="2026-10-01", new_date="2026-10-20", archived="no"),
            verify.finding("article", "https://e.example/a", "unverifiable", "could not be checked",
                           url="https://e.example/a", how="HTTP 403"),
            verify.finding("paper", "2401.00001", "ok", "unchanged"),
        ]
        md = verify.render_report(found, "2026-10-26 00:00 UTC")
        self.assertIn("**1 failures · 1 to re-check · 1 unverifiable.**", md)
        self.assertIn("## Failures", md)
        self.assertIn(f"https://github.com/o/y/compare/{OLD[:12]}...{NEW[:12]}", md)
        self.assertIn("HTTP 403", md)


if __name__ == "__main__":
    unittest.main()
