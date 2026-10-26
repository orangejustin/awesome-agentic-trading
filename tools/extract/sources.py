"""Fetch a paper's text from arXiv and clean it for extraction. Standard library only.

Order of attempts: arxiv.org/html (LaTeXML), ar5iv, then the PDF through `pdftotext` when it is installed.
The cleaned text is cached under data/extract/sources/ (git-ignored: this repository stores short quotes and
hashes, never a redistributed copy of a paper).
"""
from __future__ import annotations

import hashlib
import html.parser
import json
import re
import shutil
import subprocess
import time
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CACHE = ROOT / "data" / "extract" / "sources"
UA = "awesome-agentic-trading-extract/1.0 (research; contact via repository issues)"
MAX_CHARS = 600_000  # a long paper is ~250k characters; beyond this we truncate and say so

BLOCK = {"p", "div", "section", "article", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol", "tr",
         "table", "caption", "figcaption", "br", "blockquote", "dd", "dt"}
CELL = {"td", "th"}
SKIP = {"script", "style", "svg", "nav", "button", "noscript", "head", "img"}
SKIP_CLASS = ("ltx_bibliography", "ltx_page_footer", "ltx_page_logo", "ltx_pagination")


class _Text(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.stack: list[tuple[str, bool]] = []  # (tag, skipping)
        self.skip_depth = 0
        self.table_depth = 0

    def _is_break(self, tag: str) -> bool:
        # inside a table only rows and captions break lines, so a row stays on one line
        if self.table_depth:
            return tag in {"tr", "table", "caption", "figcaption"}
        return tag in BLOCK

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        skipping = tag in SKIP or any(c in (a.get("class") or "") for c in SKIP_CLASS)
        if tag == "math":
            alt = a.get("alttext")
            if alt and not self.skip_depth:
                self.out.append(" " + alt.strip() + " ")
            skipping = True
        if tag not in {"br", "img", "meta", "link", "input", "hr"}:
            self.stack.append((tag, skipping))
            if skipping:
                self.skip_depth += 1
        if tag == "table":
            self.table_depth += 1
        tokens = (a.get("class") or "").split()
        if not self.skip_depth:
            if self._is_break(tag) or "ltx_tr" in tokens:  # LaTeXML also builds tables from spans
                self.out.append("\n")
            elif tag in CELL or "ltx_td" in tokens or "ltx_th" in tokens:
                self.out.append(" | ")

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                for _, sk in self.stack[i:]:
                    if sk:
                        self.skip_depth -= 1
                del self.stack[i:]
                break
        if tag == "table" and self.table_depth:
            self.table_depth -= 1
        if not self.skip_depth and self._is_break(tag):
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip_depth:
            self.out.append(re.sub(r"\s+", " ", data))  # source line breaks are not line breaks


def html_to_text(raw: str) -> str:
    p = _Text()
    p.feed(raw)
    text = "".join(p.out)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _get(url: str, binary: bool = False, timeout: int = 90):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", errors="replace")


def fetch(arxiv_id: str, refresh: bool = False) -> dict:
    """Return {'text', 'kind', 'url', 'sha256', 'chars', 'truncated', 'fetched'} for one paper, using the cache."""
    CACHE.mkdir(parents=True, exist_ok=True)
    meta_path, text_path = CACHE / f"{arxiv_id}.json", CACHE / f"{arxiv_id}.txt"
    if not refresh and meta_path.exists() and text_path.exists():
        meta = json.loads(meta_path.read_text())
        meta["text"] = text_path.read_text()
        return meta
    time.sleep(1.0)  # be polite to arxiv.org: one uncached fetch per second at most
    errors = []
    # a few papers 404 without a version suffix, so the newest versioned page is tried last
    attempts = [("html", f"https://arxiv.org/html/{arxiv_id}"), ("ar5iv", f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}")]
    attempts += [(f"html-v{v}", f"https://arxiv.org/html/{arxiv_id}v{v}") for v in (4, 3, 2, 1)]
    text = kind = url = None
    for kind_, url_ in attempts:
        try:
            t = html_to_text(_get(url_))
            if len(t) > 4000:  # an error page or a stub is shorter than any paper
                text, kind, url = t, kind_, url_
                break
            errors.append(f"{kind_}: too short ({len(t)} chars)")
        except Exception as e:  # network or HTTP error: try the next source
            errors.append(f"{kind_}: {type(e).__name__}")
    if text is None and shutil.which("pdftotext"):
        try:
            pdf = _get(f"https://arxiv.org/pdf/{arxiv_id}", binary=True, timeout=180)
            r = subprocess.run(["pdftotext", "-layout", "-", "-"], input=pdf, capture_output=True, timeout=180)
            t = r.stdout.decode("utf-8", errors="replace")
            if r.returncode == 0 and len(t) > 4000:
                text, kind, url = re.sub(r"\n{3,}", "\n\n", t).strip(), "pdf", f"https://arxiv.org/pdf/{arxiv_id}"
        except Exception as e:
            errors.append(f"pdf: {type(e).__name__}")
    if text is None:
        raise RuntimeError(f"{arxiv_id}: no usable source ({'; '.join(errors)})")
    truncated = len(text) > MAX_CHARS
    text = text[:MAX_CHARS]
    meta = {
        "kind": kind, "url": url, "chars": len(text), "truncated": truncated,
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "fetched": time.strftime("%Y-%m-%d", time.gmtime()),
    }
    text_path.write_text(text)
    meta_path.write_text(json.dumps(meta, indent=1))
    meta["text"] = text
    return meta


def norm(s: str) -> str:
    """Normalise for quote matching: NFKC, ASCII punctuation, joined hyphenation, collapsed whitespace, lower case."""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("­", "").replace("​", "")
    s = re.sub(r"[‘’‚′]", "'", s)
    s = re.sub(r"[“”„″]", '"', s)
    s = re.sub(r"[‐-―−]", "-", s)
    s = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def alnum(s: str) -> str:
    """Letters and digits only: tolerant of spacing, table separators and punctuation, strict about content."""
    return re.sub(r"[^0-9a-z]+", "", norm(s))


def find_quote(quote: str, source: str) -> str | None:
    """Return 'exact' if the quote is a substring after normalisation, 'loose' if only letters and digits match, else None."""
    quote = quote.strip().strip("\"'\u201c\u201d\u2018\u2019").strip()  # a model may wrap the passage in quote marks
    if len(alnum(quote)) < 12:  # too short to mean anything
        return None
    if norm(quote) in norm(source):
        return "exact"
    if alnum(quote) in alnum(source):
        return "loose"
    return None
