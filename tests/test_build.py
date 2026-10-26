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
        for needle in ("unknown evidence", "unknown repro", "unknown layer", "unknown orders"):
            self.assertTrue(any(needle in e for e in errs), needle)

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
