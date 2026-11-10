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


# ---------------------------------------------------------------- raw HTML in Markdown

from html.parser import HTMLParser  # noqa: E402

INLINE_CODE = re.compile(r"`[^`\n]*`")
HTML_REF = re.compile(r"""<(?:a|img|source)\b[^>]*?\b(?:href|src|srcset)\s*=\s*["']([^"']+)["']""", re.I)
# a tag that starts and never closes before the line ends or the next tag starts, e.g. "</b" or "<a href=...".
# Only real HTML tag names count, so prose such as "<5 trades" or "<name>" is left alone.
TAGS = ("a|b|i|p|em|strong|code|kbd|sub|sup|span|div|center|img|br|hr|picture|source|details|summary|"
        "table|thead|tbody|tr|td|th|ul|ol|li|h1|h2|h3|h4|h5|h6|blockquote|pre")
BROKEN_TAG = re.compile(rf"</?(?:{TAGS})\b[^<>\n]*(?=<|\n|$)", re.I)
VOID = {"img", "br", "hr", "source", "meta", "link", "input", "wbr", "col"}


def prose(text: str) -> str:
    """Markdown without fenced code and inline code spans, where HTML is rendered as HTML."""
    return INLINE_CODE.sub("", FENCE.sub("", text))


class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, int]] = []
        self.problems: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1][0] != tag:
            self.problems.append(f"line {self.getpos()[0]}: </{tag}> does not close "
                                 f"{'<' + self.stack[-1][0] + '>' if self.stack else 'anything'}")
            return
        self.stack.pop()


def html_problems(text: str) -> list[str]:
    body = prose(text)
    out = [f"line {body.count(chr(10), 0, m.start()) + 1}: unfinished tag {m.group(0)[:30]!r}"
           for m in BROKEN_TAG.finditer(body)]
    p = Balance()
    p.feed(body)
    p.close()
    out += p.problems + [f"line {line}: <{tag}> is never closed" for tag, line in p.stack]
    return out


class Html(unittest.TestCase):
    def test_the_checker_catches_what_broke_the_home_page(self):
        broken = '<p align="center"><b>English</b\n> A curated guide.\n'
        self.assertTrue(any("unfinished tag" in x for x in html_problems(broken)))
        self.assertTrue(html_problems("<p>one <b>two</p>"))
        self.assertTrue(html_problems('<a href="x.md">never closed'))
        self.assertEqual(html_problems('<p align="center"><b>English</b> | <a href="README.zh-CN.md">简体中文</a></p>'), [])
        self.assertEqual(html_problems("Fewer than <5 trades; see `<p>` and\n```\n<b>\n```\n"), [])

    def test_html_tags_are_complete_and_balanced(self):
        problems = []
        for md in markdown_files():
            problems += [f"{md.relative_to(ROOT)}: {x}" for x in html_problems(md.read_text())]
        self.assertEqual(problems, [])

    def test_html_links_and_images_resolve(self):
        problems = []
        for md in markdown_files():
            for m in HTML_REF.finditer(prose(md.read_text())):
                for target in m.group(1).split(","):
                    target = target.strip().split(" ")[0]
                    if re.match(r"^(https?:|mailto:|data:)", target):
                        continue
                    path_part, _, anchor = target.partition("#")
                    dest = md if not path_part else (md.parent / path_part).resolve()
                    if not dest.exists():
                        problems.append(f"{md.relative_to(ROOT)}: missing file {target}")
                    elif anchor and dest.suffix == ".md" and anchor not in anchors(dest):
                        problems.append(f"{md.relative_to(ROOT)}: no heading for #{anchor} in {dest.name}")
        self.assertEqual(problems, [])


class Bilingual(unittest.TestCase):
    """The two home pages are one page in two languages."""

    def setUp(self):
        self.en = (ROOT / "README.md").read_text()
        self.zh = (ROOT / "README.zh-CN.md").read_text()
        self.tw = (ROOT / "README.zh-TW.md").read_text()

    def test_each_home_page_links_to_the_other_near_the_top(self):
        pages = {"README.md": ("English", self.en), "README.zh-CN.md": ("简体中文", self.zh), "README.zh-TW.md": ("繁體中文", self.tw)}
        for name, (label, text) in pages.items():
            top = "\n".join(text.splitlines()[:8])
            self.assertIn(f"<b>{label}</b>", top, name)  # the page you are on is shown, not linked
            for other, (other_label, _) in pages.items():
                if other != name:
                    self.assertIn(f'<a href="{other}">{other_label}</a>', top, f"{name} -> {other}")

    def test_both_have_a_text_title_not_only_the_banner_image(self):
        for text in (self.en, self.zh, self.tw):
            self.assertRegex(text, r"<h1[^>]*>Awesome Agentic Trading</h1>")

    def test_same_structure(self):
        def shape(text):
            body = FENCE.sub("", text)
            return [len(m.group(1)) for m in re.finditer(r"^(#{1,6})\s", body, re.M)]

        def blocks(text):
            return re.findall(r"<!-- gen:([\w-]+) -->", text)

        def rows(text):
            return len(re.findall(r"^\|", prose(text), re.M)), len(re.findall(r"^- ", prose(text), re.M))

        self.assertEqual(shape(self.en), shape(self.zh))
        self.assertEqual(blocks(self.en), blocks(self.zh))
        self.assertEqual(rows(self.en), rows(self.zh))
        self.assertEqual((shape(self.zh), blocks(self.zh), rows(self.zh)), (shape(self.tw), blocks(self.tw), rows(self.tw)))

    def test_same_counts_in_the_headline(self):
        def numbers(text):
            return re.findall(r"\d+", re.search(r"<!-- gen:headline -->(.*?)<!-- /gen:headline -->", text, re.S).group(1))

        self.assertEqual(numbers(self.en), numbers(self.zh))
        self.assertEqual(numbers(self.en), numbers(self.tw))

    def test_traditional_page_has_no_simplified_text_left(self):
        body = self.tw.replace('<a href="README.zh-CN.md">简体中文</a>', "")
        for ch in "这个仓库论文许可证实盘数据层执行应用开验":
            if ch in "个仓库论许证实盘数据层执应开验" and ch in body:
                self.fail(f"simplified character {ch!r} left in README.zh-TW.md")
        self.assertIn("assets/stack.zh-TW.svg", self.tw)
        self.assertIn("docs/milestones.zh-TW.md", self.tw)

    def test_neither_page_calls_the_whole_list_open_source(self):
        intro_en = self.en.split("## Contents")[0]
        intro_zh = self.zh.split("## 目录")[0]
        self.assertNotRegex(re.sub(r"<!-- gen:headline -->.*?<!-- /gen:headline -->", "", intro_en, flags=re.S), r"(?i)open[- ]source")
        self.assertNotIn("开源", re.sub(r"<!-- gen:headline -->.*?<!-- /gen:headline -->", "", intro_zh, flags=re.S))
        banner = (ROOT / "assets" / "banner.svg").read_text()
        self.assertNotRegex(banner, r"(?i)open[- ]source")
