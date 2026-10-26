"""Documentation hygiene: every relative link and anchor resolves."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)|!\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"^```.*?^```", re.S | re.M)


def slug(heading: str) -> str:
    h = re.sub(r"`|\*|\[|\]", "", heading.strip().lower())
    h = re.sub(r"\([^)]*\)", lambda m: m.group(0)[1:-1], h)  # keep parenthesised words, drop the brackets
    h = re.sub(r"[^\w\- ]", "", h)
    return h.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    text = FENCE.sub("", path.read_text())
    return {slug(m.group(1)) for m in re.finditer(r"^#{1,6}\s+(.*)$", text, re.M)}


def markdown_files():
    skip = {"node_modules", ".git", ".venv", "data"}
    return [p for p in ROOT.rglob("*.md") if not skip & set(p.relative_to(ROOT).parts)]


class Links(unittest.TestCase):
    def test_relative_links_and_anchors_resolve(self):
        problems = []
        for md in markdown_files():
            text = FENCE.sub("", md.read_text())
            for m in LINK.finditer(text):
                target = m.group(1) or m.group(2)
                if re.match(r"^(https?:|mailto:|#|cursor:)", target) and not target.startswith("#"):
                    continue
                path_part, _, anchor = target.partition("#")
                dest = md if not path_part else (md.parent / path_part).resolve()
                rel = md.relative_to(ROOT)
                if not dest.exists():
                    problems.append(f"{rel}: missing file {target}")
                elif anchor and dest.suffix == ".md" and anchor not in anchors(dest):
                    problems.append(f"{rel}: no heading for #{anchor} in {dest.name}")
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
