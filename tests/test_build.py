import tomllib
import unittest
from pathlib import Path

from tools import build

ROOT = Path(__file__).resolve().parent.parent


class Catalog(unittest.TestCase):
    def setUp(self):
        self.c = build.load_all()

    def test_catalog_has_no_errors(self):
        self.assertEqual(build.check_all(self.c), [])

    def test_generated_pages_are_current(self):
        for path, text in build.generated_pages(self.c).items():
            self.assertTrue(path.exists(), f"{path} missing; run python tools/build.py tables")
            self.assertEqual(path.read_text(), text.rstrip("\n") + "\n", f"{path.name} is stale")

    def test_injected_blocks_are_current(self):
        self.assertTrue(build.apply_injections(self.c, only_check=True),
                        "a generated block is stale; run python tools/build.py tables")

    def test_bad_entries_are_caught(self):
        p = self.c["projects"][0]
        bad = [dict(p, evidence="L9", repro="maybe", layer="nowhere", orders="maybe")]
        errs = build.check(self.c["papers"], bad, self.c["layers"])
        for needle in ("unknown evidence", "unknown repro", "unknown layer", "orders must be one of"):
            self.assertTrue(any(needle in e for e in errs), needle)

    def entry(self, **kw):
        p = next(p for p in self.c["projects"] if p["id"] == "alpaca-mcp-server")
        return dict(p, **kw)

    def errs(self, *projects):
        return build.check(self.c["papers"], list(projects), self.c["layers"])

    def test_order_authority_needs_pinned_evidence(self):
        self.assertTrue(any("needs a pinned 'orders' source" in e for e in self.errs(self.entry(sources=[]))))
        moved = [dict(s, url=s["url"].replace(self.entry()["last_sha"], "f" * 40)) for s in self.entry()["sources"]]
        self.assertTrue(any("not pinned to last_sha" in e for e in self.errs(self.entry(sources=moved))))
        self.assertTrue(any("orders must be one of" in e for e in self.errs(self.entry(orders=None))))

    def test_commit_must_be_a_full_hash(self):
        self.assertTrue(any("full 40-character" in e for e in self.errs(self.entry(last_sha="d8dac43"))))

    def test_license_status_rules(self):
        self.assertTrue(any("needs the license_file" in e for e in self.errs(self.entry(license_file=""))))
        self.assertTrue(any("declared-only license needs" in e
                            for e in self.errs(self.entry(license_status="declared"))))
        self.assertTrue(any("unknown license_status" in e for e in self.errs(self.entry(license_status="maybe"))))

    def test_declared_maintenance_needs_a_source(self):
        self.assertTrue(any("needs a pinned 'maintenance' source" in e
                            for e in self.errs(self.entry(maintenance="unmaintained"))))

    def test_headline_license_groups_add_up(self):
        listed = build.listed(self.c["projects"])
        self.assertEqual(sum(build.license_groups(self.c["projects"])), len(listed))
        self.assertIn(f"{len(listed)} repositories (", build.headline(self.c))

    def test_live_and_paper_marks_link_to_evidence(self):
        for p in build.listed(self.c["projects"]):
            line = build.readme_entry(p, zh=False)
            if p["orders"] in ("live", "paper"):
                self.assertIn(f"]({build.source(p, 'orders')})", line, p["id"])
            self.assertIn(build.tree_url(p), line)

    def test_category_must_belong_to_layer(self):
        p = next(p for p in self.c["projects"] if p.get("layer") == "data")
        errs = build.check(self.c["papers"], [dict(p, category="agent-multi")], self.c["layers"])
        self.assertTrue(any("is not in layer" in e for e in errs))

    def test_duplicate_repository_is_caught(self):
        p = next(p for p in self.c["projects"] if p.get("layer"))
        errs = build.check(self.c["papers"], [p, dict(p, id=p["id"] + "-copy", repo=p["repo"].upper())], self.c["layers"])
        self.assertTrue(any("already catalogued" in e for e in errs))

    def test_private_links_are_refused(self):
        c = dict(self.c, articles=[{"title": "t", "author": "a", "url": "https://x." + "slack.com/archives/1", "source": "blog",
                                    "date": "2026-01-01", "layer": "data", "why": "w", "checked": "2026-01-01"}])
        self.assertTrue(any("private workspace" in e for e in build.check_all(c)))

    def test_every_teardown_listed_in_catalog(self):
        ids = {p["id"] for p in self.c["projects"] if p["read"] == "teardown"}
        files = {f.stem for f in (ROOT / "docs" / "teardowns").glob("*.md")}
        self.assertEqual(ids, files)

    def test_every_layer_has_a_page_and_both_readmes_list_it(self):
        en, zh = (ROOT / "README.md").read_text(), (ROOT / "README.zh-CN.md").read_text()
        for lay in self.c["layers"]:
            self.assertTrue((ROOT / "layers" / f"{lay['id']}.md").exists())
            self.assertIn(f"## {lay['num']}. {lay['title']}:", en)
            self.assertIn(f"## {lay['num']}. {lay['title_zh']}：", zh)

    def test_readmes_list_the_same_repositories(self):
        import re
        pat = re.compile(r"^- \[[^\]]+\]\((https://github\.com/[^)]+)\)", re.M)
        en = pat.findall((ROOT / "README.md").read_text())
        zh = pat.findall((ROOT / "README.zh-CN.md").read_text())
        self.assertEqual(en, zh)

    def test_no_project_reaches_l3(self):
        # docs/02-evidence-ladder.md states that none does; this fails when the claim stops being true.
        self.assertEqual([p["id"] for p in self.c["projects"] if p["evidence"] == "L3"], [])

    def test_exclusions_are_valid_and_disjoint_from_catalog(self):
        with open(ROOT / "catalog" / "excluded.toml", "rb") as f:
            excluded = tomllib.load(f)["excluded"]
        repos = {p["repo"].lower() for p in self.c["projects"]}
        for e in excluded:
            self.assertIn(e["reason"], {"general-list", "quant-library"})
            self.assertNotIn(e["repo"].lower(), repos)


if __name__ == "__main__":
    unittest.main()
