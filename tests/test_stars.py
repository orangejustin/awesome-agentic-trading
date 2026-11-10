import unittest

from tools import stars

TEXT = '''[[project]]
id = "a"
repo = "o/a"
stars = "507"
stars_asof = "2026-10-21"
last_commit = "2026-01-01"

[[project]]
id = "b"
repo = "o/b"
stars = "1.2k"
stars_asof = "2026-10-21"
'''


class Stars(unittest.TestCase):
    def test_short_form(self):
        self.assertEqual([stars.short(n) for n in (507, 1000, 1349, 13650, 69400)], ["507", "1k", "1.3k", "13.7k", "69.4k"])

    def test_refresh_updates_each_entry_and_reports_renames(self):
        api = {"o/a": {"stars": 2900, "full_name": "o/a2"}, "o/b": None}
        projects = [{"id": "a", "repo": "o/a", "stars": "507"}, {"id": "b", "repo": "o/b", "stars": "1.2k"}]
        text, changes, renames = stars.refresh(TEXT, projects, api.get, "2026-11-10")
        self.assertIn('id = "a"\nrepo = "o/a"\nstars = "2.9k"\nstars_asof = "2026-11-10"', text)
        self.assertIn('stars = "1.2k"\nstars_asof = "2026-10-21"', text)  # no answer: untouched
        self.assertEqual(changes, ["a: 507 -> 2.9k", "b: no answer, left as is"])
        self.assertEqual(renames, ["a: o/a is now o/a2"])


if __name__ == "__main__":
    unittest.main()
