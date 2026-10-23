import contextlib
import io
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

from tools.extract import client as cl
from tools.extract import sources
from tools.extract import __main__ as cli
from tools.extract.schema import FIELDS, SCHEMA, SYSTEM, verify_card

try:
    import anthropic  # noqa: F401
    HAVE_SDK = True
except ImportError:
    HAVE_SDK = False

PAPER = (
    "FinThing: A Trading Agent\n\n"
    "We evaluate on US equities from January 2, 2024 to March 29, 2024 using a daily decision loop.\n"
    "Table 1: Results\n| Ticker | Model | Cumulative Return (%) | Sharpe |\n| AAPL | FinThing | 26.62 | 8.21 |\n"
    "The agent uses GPT-4o as its backbone model and a transaction cost of 0.1% per trade is assumed.\n"
)
FAKE_KEY = "test-key-0000-not-a-credential"


class HtmlToText(unittest.TestCase):
    def test_tables_math_and_skips(self):
        raw = ("<html><head><title>x</title></head><body><script>var secret=1</script>"
               "<p>Intro  text\nwrapped.</p>"
               "<table><tr><td><p>A</p></td><td>B</td></tr><tr><td>C</td><td>D\n</td></tr></table>"
               "<p>Let <math alttext=\"x^2\"><mi>x</mi></math> be.</p>"
               "<section class=\"ltx_bibliography\"><p>Ref one</p></section><p>After.</p></body></html>")
        t = sources.html_to_text(raw)
        self.assertIn("Intro text wrapped.", t)
        self.assertIn("| A | B", t)
        self.assertIn("| C | D", t)
        self.assertIn("x^2", t)
        self.assertNotIn("secret", t)
        self.assertNotIn("Ref one", t)
        self.assertIn("After.", t)
        self.assertEqual(t.count("| A"), 1)

    def test_latexml_span_tables_keep_rows(self):
        raw = ('<span class="ltx_tabular"><span class="ltx_tr"><span class="ltx_td">a</span><span class="ltx_td">b</span></span>'
               '<span class="ltx_tr"><span class="ltx_td">c</span><span class="ltx_td">d</span></span></span>')
        lines = [l for l in sources.html_to_text(raw).splitlines() if l.strip()]
        self.assertEqual(len(lines), 2)


class QuoteMatching(unittest.TestCase):
    def test_exact_loose_and_rejected(self):
        self.assertEqual(sources.find_quote("from January 2, 2024 to March 29, 2024", PAPER), "exact")
        self.assertEqual(sources.find_quote("“the agent uses GPT-4o as its backbone model”", PAPER), "exact")
        self.assertEqual(sources.find_quote("AAPL FinThing 26.62 8.21", PAPER), "loose")  # table separators dropped
        self.assertIsNone(sources.find_quote("a transaction cost of 0.5% per trade is assumed", PAPER))  # changed number
        self.assertIsNone(sources.find_quote("hello", PAPER))  # too short to count

    def test_hyphenation_and_typography(self):
        src = "The strat-\negy uses “quotes” and a long—dash and café data over the sample."
        self.assertEqual(sources.find_quote('strategy uses "quotes" and a long-dash', src), "exact")


class VerifyCard(unittest.TestCase):
    def fields(self, **over):
        f = {k: {"status": "not_found", "value": "", "quote": ""} for k in FIELDS}
        f["window"] = {"status": "stated", "value": "Jan-Mar 2024", "quote": "from January 2, 2024 to March 29, 2024"}
        f["costs"] = {"status": "stated", "value": "0.1% per trade", "quote": "transaction cost of 0.1% per trade"}
        f.update(over)
        return f

    def test_counts(self):
        v = verify_card(self.fields(), PAPER)
        self.assertEqual((v["verified"], v["failed"], v["not_found"]), (2, 0, 10))

    def test_fabricated_quote_fails_the_field(self):
        v = verify_card(self.fields(costs={"status": "stated", "value": "0.5%", "quote": "transaction cost of 0.5% per trade"}), PAPER)
        self.assertEqual(v["detail"]["costs"], "failed")
        self.assertEqual(v["failed"], 1)

    def test_stated_without_quote_is_malformed(self):
        v = verify_card(self.fields(costs={"status": "stated", "value": "0.1%", "quote": ""}), PAPER)
        self.assertEqual(v["detail"]["costs"], "malformed")

    def test_schema_is_closed(self):
        self.assertFalse(SCHEMA["additionalProperties"])
        self.assertEqual(set(SCHEMA["required"]), set(FIELDS))


class Keys(unittest.TestCase):
    def test_env_wins(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": FAKE_KEY}):
            self.assertEqual(cl.get_api_key(), FAKE_KEY)

    def test_key_command_and_no_stderr_leak(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {}, clear=False):
            for name in cl.KEY_ENVS:
                os.environ.pop(name, None)
            ok = Path(d) / "ok.toml"
            ok.write_text('key_command = ["python3", "-c", "print(\'k-from-command\')"]\n')
            with mock.patch.object(cl, "LOCAL", ok):
                self.assertEqual(cl.get_api_key(), "k-from-command")
            bad = Path(d) / "bad.toml"
            bad.write_text('key_command = ["python3", "-c", "import sys; sys.stderr.write(\'SECRET-STORE-NAME\'); sys.exit(3)"]\n')
            with mock.patch.object(cl, "LOCAL", bad), self.assertRaises(RuntimeError) as cm:
                cl.get_api_key()
            self.assertNotIn("SECRET-STORE-NAME", str(cm.exception))

    def test_missing_key_message_names_no_service(self):
        with mock.patch.dict(os.environ, {}, clear=False), mock.patch.object(cl, "LOCAL", Path("/nonexistent/local.toml")):
            for name in cl.KEY_ENVS:
                os.environ.pop(name, None)
            with self.assertRaises(RuntimeError):
                cl.get_api_key()


class Ledger(unittest.TestCase):
    def test_cap_stops_new_work(self):
        led = cl.Ledger(max_usd=0.01)
        led.check()
        led.add(100_000, 0)  # $0.40
        with self.assertRaises(cl.BudgetExceeded):
            led.check()

    def test_cost_arithmetic(self):
        self.assertAlmostEqual(cl.cost(1_000_000, 1_000_000), 24.0)


class Promote(unittest.TestCase):
    def test_only_abstract_papers_with_passing_cards_flip(self):
        text = ('[[paper]]\narxiv = "2401.00001"\nread = "abstract"\nsummary = "a"\n\n'
                '[[paper]]\narxiv = "2401.00002"\nread = "abstract"\nsummary = "b"\n\n'
                '[[paper]]\narxiv = "2401.00003"\nread = "full"\nsummary = "c"\n')
        new, n = cli.promote_text(text, {"2401.00001", "2401.00003"})
        self.assertEqual(n, 1)
        self.assertIn('arxiv = "2401.00001"\nread = "card"', new)
        self.assertIn('arxiv = "2401.00002"\nread = "abstract"', new)
        self.assertIn('arxiv = "2401.00003"\nread = "full"', new)


def make_fields(paper_text):
    f = {k: {"status": "not_found", "value": "", "quote": ""} for k in FIELDS}
    f["window"] = {"status": "stated", "value": "Jan-Mar 2024", "quote": "from January 2, 2024 to March 29, 2024"}
    f["models"] = {"status": "stated", "value": "GPT-4o", "quote": "The agent uses GPT-4o as its backbone model"}
    f["costs"] = {"status": "stated", "value": "0.5% per trade", "quote": "a transaction cost of 0.5% per trade is assumed"}  # fabricated
    return f


class FakeApi(BaseHTTPRequestHandler):
    mode = "ok"
    seen: list = []

    def log_message(self, *a):
        pass

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["content-length"])))
        FakeApi.seen.append((self.path, req, dict(self.headers)))
        if self.path.endswith("/count_tokens"):
            return self._send({"input_tokens": 12345})
        stop = {"refusal": "refusal", "max_tokens": "max_tokens"}.get(FakeApi.mode, "end_turn")
        text = json.dumps(make_fields(req["messages"][0]["content"]))
        self._send({
            "id": "msg_test", "type": "message", "role": "assistant", "model": req["model"], "stop_reason": stop,
            "stop_sequence": None, "content": [{"type": "text", "text": text}],
            "usage": {"input_tokens": 20_000, "output_tokens": 5_000},
        })


@unittest.skipUnless(HAVE_SDK, "the anthropic package is not installed")
class EndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), FakeApi)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.srv.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        FakeApi.mode, FakeApi.seen = "ok", []
        self.env = mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": FAKE_KEY, "ANTHROPIC_BASE_URL": self.url})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_request_shape(self):
        led = cl.Ledger(max_usd=10)
        fields, usage = cl.extract_one(cl.make_client(), "FinThing", PAPER, led)
        path, req, headers = FakeApi.seen[-1]
        self.assertEqual(req["model"], "claude-opus-5-5")
        self.assertEqual(req["output_config"]["effort"], "medium")
        self.assertEqual(req["output_config"]["format"]["type"], "json_schema")
        self.assertNotIn("thinking", req)
        self.assertNotIn("temperature", req)
        self.assertEqual([m["role"] for m in req["messages"]], ["user"])  # no prefill
        self.assertIn("<paper>", req["messages"][0]["content"])
        self.assertEqual(req["system"], SYSTEM)
        self.assertEqual(usage, {"input_tokens": 20_000, "output_tokens": 5_000})
        self.assertAlmostEqual(led.spent, 0.18)
        self.assertEqual(fields["models"]["status"], "stated")

    def test_refusal_and_truncation_raise_but_are_billed(self):
        for mode, exc in (("refusal", cl.Refused), ("max_tokens", cl.Truncated)):
            FakeApi.mode = mode
            led = cl.Ledger(max_usd=10)
            with self.assertRaises(exc):
                cl.extract_one(cl.make_client(), "FinThing", PAPER, led)
            self.assertGreater(led.spent, 0)

    def test_count_tokens(self):
        self.assertEqual(cl.count_input_tokens(cl.make_client(), "FinThing", PAPER), 12345)

    def test_run_writes_a_verified_card_and_never_prints_the_key(self):
        paper = {"arxiv": "2401.00001", "title": "FinThing", "published": "2024-01-02", "updated": "2024-01-02", "read": "abstract"}
        src = {"kind": "html", "url": "u", "chars": len(PAPER), "truncated": False, "sha256": "ab" * 32, "fetched": "2026-10-21", "text": PAPER}
        with tempfile.TemporaryDirectory() as d:
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.object(cli, "CARDS", Path(d) / "cards"), mock.patch.object(cli, "DATA", Path(d) / "data"), \
                    mock.patch.object(cli, "select", return_value=[paper]), mock.patch.object(sources, "fetch", return_value=src), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = cli.main(["run", "--max-usd", "5", "--yes", "--workers", "1"])
            card = json.loads((Path(d) / "cards" / "2401.00001.json").read_text())
            ledger = (Path(d) / "data" / "ledger.jsonl").read_text()
            self.assertEqual(rc, 0)
            v = card["verification"]
            self.assertEqual((v["verified"], v["failed"]), (2, 1))  # the fabricated cost quote is rejected
            self.assertEqual(v["detail"]["costs"], "failed")
            md = cli.render_card(card)
            self.assertIn("The agent uses GPT-4o as its backbone model", md)
            self.assertNotIn("0.5% per trade", md)  # the unverifiable gloss is withheld
            self.assertIn("withheld", md)
            for blob in (out.getvalue(), err.getvalue(), json.dumps(card), ledger, md):
                self.assertNotIn(FAKE_KEY, blob)

    def test_run_without_yes_spends_nothing(self):
        with mock.patch.object(cli, "select", return_value=[{"arxiv": "2401.00001", "title": "t"}]), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["run", "--max-usd", "5"]), 2)
        self.assertEqual(FakeApi.seen, [])


if __name__ == "__main__":
    unittest.main()
