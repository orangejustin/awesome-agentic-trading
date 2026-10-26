import unittest

from tools import make_assets


class Assets(unittest.TestCase):
    def test_assets_are_current(self):
        for name, text in make_assets.render_all().items():
            path = make_assets.OUT / name
            self.assertTrue(path.exists(), f"{path} missing; run python tools/make_assets.py")
            self.assertEqual(path.read_text(), text, f"{name} is stale; run python tools/make_assets.py")

    def test_svgs_are_well_formed(self):
        import xml.etree.ElementTree as ET
        for text in make_assets.render_all().values():
            ET.fromstring(text)


if __name__ == "__main__":
    unittest.main()
