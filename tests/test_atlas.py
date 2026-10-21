import tomllib
import unittest
from pathlib import Path

from tools import atlas

ROOT = Path(__file__).resolve().parent.parent


class Catalog(unittest.TestCase):
    def setUp(self):
        self.papers, self.projects = atlas.load()

    def test_catalog_has_no_errors(self):
        self.assertEqual(atlas.check(self.papers, self.projects), [])

    def test_generated_tables_are_current(self):
        for name, text in (("papers.md", atlas.render_papers(self.papers)),
                           ("projects.md", atlas.render_projects(self.projects))):
            path = ROOT / "docs" / "catalog" / name
            self.assertTrue(path.exists(), f"{path} missing; run python tools/atlas.py tables")
            self.assertEqual(path.read_text(), text.rstrip("\n") + "\n", f"{name} is stale")

    def test_bad_entries_are_caught(self):
        bad = [dict(self.projects[0], evidence="L9", repro="maybe")]
        errs = atlas.check(self.papers, bad)
        self.assertTrue(any("unknown evidence" in e for e in errs))
        self.assertTrue(any("unknown repro" in e for e in errs))

    def test_every_teardown_listed_in_catalog(self):
        ids = {p["id"] for p in self.projects if p["read"] == "teardown"}
        files = {f.stem for f in (ROOT / "docs" / "teardowns").glob("*.md")}
        self.assertEqual(ids, files)

    def test_every_catalogued_paper_with_a_project_resolves(self):
        arxiv = {p["arxiv"] for p in self.papers}
        for p in self.projects:
            if p.get("paper"):
                self.assertIn(p["paper"], arxiv)

    def test_injected_blocks_are_current(self):
        self.assertTrue(atlas.apply_injections(self.papers, self.projects, only_check=True),
                        "a generated block in the docs is stale; run python tools/atlas.py tables")

    def test_no_project_reaches_l3(self):
        # docs/02-evidence-ladder.md states that none does; this fails when the claim stops being true.
        self.assertEqual([p["id"] for p in self.projects if p["evidence"] == "L3"], [])

    def test_exclusions_are_valid_and_disjoint_from_catalog(self):
        with open(ROOT / "catalog" / "excluded.toml", "rb") as f:
            excluded = tomllib.load(f)["excluded"]
        repos = {p["repo"].lower() for p in self.projects}
        for e in excluded:
            self.assertIn(e["reason"], {"general-list", "quant-library"})
            self.assertNotIn(e["repo"].lower(), repos)


if __name__ == "__main__":
    unittest.main()
