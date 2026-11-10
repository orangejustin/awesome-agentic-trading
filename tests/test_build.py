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
        # the commit each entry was checked at is on its layer page
        pages = {lay["id"]: build.render_layer_page(self.c, lay) for lay in self.c["layers"]}
        for p in build.listed(self.c["projects"]):
            self.assertIn(build.tree_url(p), pages[p["layer"]], p["id"])

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
            self.assertIn(e["reason"], {"general-list", "quant-library", "token", "referral", "duplicate", "no-code"})
            self.assertNotIn(e["repo"].lower(), repos)


if __name__ == "__main__":
    unittest.main()


class Evidence(unittest.TestCase):
    """What the component matrix and the recipes claim must be cited, and every cited link must be checked."""

    def setUp(self):
        import copy
        self.c = copy.deepcopy(build.load_all())

    def errors(self):
        return build.check_components(self.c)

    def test_component_needs_a_source_for_each_core_fact(self):
        self.c["components"][0]["sources"] = []
        errs = self.errors()
        for what in build.COMPONENT_MUST_CITE:
            self.assertTrue(any(f"no pinned source for {what}" in e for e in errs), what)

    def test_installed_or_run_needs_the_full_record(self):
        m = self.c["components"][0]
        m.update(verification="run", verify_cmd="pip install x", verify_date="2026-11-10")
        errs = self.errors()
        self.assertTrue(any("needs verify_env" in e for e in errs))
        self.assertTrue(any("needs verify_result" in e for e in errs))
        m.update(verify_env="Ubuntu 24.04, Python 3.12", verify_result="imported")
        self.assertEqual(self.errors(), [])

    def test_recipe_marked_run_needs_a_run_record(self):
        r = self.c["recipes"][0]
        r["status"] = "run"
        errs = self.errors()
        for k in build.RUN_PROOF:
            self.assertTrue(any(f"needs run.{k}" in e for e in errs), k)
        r["run"] = {"date": "2026-11-10", "env": "Ubuntu 24.04", "commits": "qlib abc1234", "cmd": "make demo",
                    "result": "one factor evaluated", "log": "https://example.org/log"}
        self.assertEqual(self.errors(), [])
        r["status"] = "design"
        self.assertTrue(any("only for status = run" in e for e in self.errors()))

    def test_recipe_links_must_be_pinned(self):
        self.c["recipes"][0]["links"] = [{"label": "docs", "url": "https://github.com/microsoft/qlib/blob/main/README.md"}]
        self.assertTrue(any("must be pinned" in e for e in self.errors()))

    def test_every_cited_link_is_a_check_target(self):
        links = build.evidence_links(self.c)
        urls = {u for _, _, u in links}
        cited = {s["url"] for p in self.c["projects"] for s in p.get("sources", [])}
        for m in self.c["components"]:
            cited |= {s["url"] for s in m.get("sources", [])} | {g["url"] for g in m.get("integrations", []) if g.get("url")}
        for r in self.c["recipes"]:
            cited |= {x["url"] for x in r.get("links", [])}
        self.assertEqual(urls, cited)
        self.assertEqual({k for k, _, _ in links}, {"source", "component", "integration", "recipe"})
