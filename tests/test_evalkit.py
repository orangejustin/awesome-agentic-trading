import copy
import math
import random
import unittest

from tools.evalkit import budget, ratings, report_card, stats


def gauss_series(n, mu, sigma, rng):
    return [rng.gauss(mu, sigma) for _ in range(n)]


class SharpeBasics(unittest.TestCase):
    def test_annualization(self):
        r = [0.001, 0.002, -0.001, 0.0015, 0.0005] * 50
        daily = stats.mean(r) / stats.stdev(r)
        self.assertAlmostEqual(stats.sharpe(r), daily * math.sqrt(252))

    def test_zero_vol_raises(self):
        with self.assertRaises(ValueError):
            stats.sharpe([0.01] * 10)

    def test_known_documentation_numbers(self):
        # These are the figures quoted in docs/06-reading-a-backtest.md and the teardowns.
        self.assertAlmostEqual(stats.sharpe_se_annual(5.6, 0.25), 2.06, places=2)
        self.assertAlmostEqual(stats.sharpe_se_annual(3.12, 0.5), 1.43, places=2)
        self.assertAlmostEqual(stats.sharpe_se_annual(1.0, 1.0), 1.0, places=2)
        self.assertAlmostEqual(stats.min_track_record_years(1.96), 0.71, places=1)
        self.assertAlmostEqual(stats.years_to_resolve_sharpe_diff(0.5, 0.5, 0.9), 3.1, places=1)


class MinTrackRecord(unittest.TestCase):
    def test_infinite_when_not_better(self):
        self.assertEqual(stats.min_track_record_periods(0.05, 0.05), math.inf)

    def test_skew_and_kurtosis_lengthen_the_record(self):
        base = stats.min_track_record_years(1.0)
        fat = stats.min_track_record_years(1.0, skew=-1.0, kurt=8.0)
        self.assertGreater(fat, base)

    def test_larger_benchmark_needs_longer(self):
        self.assertGreater(stats.min_track_record_years(1.5, 1.0), stats.min_track_record_years(1.5, 0.0))


class SharpeStandardError(unittest.TestCase):
    def test_se_matches_simulation(self):
        """Monte Carlo: the spread of annualized Sharpe estimates should match sharpe_se_annual."""
        rng = random.Random(11)
        t, reps, mu, sigma = 252, 2000, 0.0008, 0.01   # one year of daily data, true annual Sharpe ~1.27
        ests = [stats.sharpe(gauss_series(t, mu, sigma, rng)) for _ in range(reps)]
        m = stats.mean(ests)
        sim_se = math.sqrt(sum((e - m) ** 2 for e in ests) / (reps - 1))
        formula = stats.sharpe_se_annual(mu / sigma * math.sqrt(252), years=1.0)
        self.assertAlmostEqual(sim_se / formula, 1.0, delta=0.06)

    def test_se_shrinks_with_the_square_root_of_time(self):
        self.assertAlmostEqual(stats.sharpe_se_annual(1.0, 1.0) / stats.sharpe_se_annual(1.0, 4.0), 2.0, places=2)


class SharpeDifference(unittest.TestCase):
    def test_se_formula_matches_simulation(self):
        """Monte Carlo: the closed form for Var(SR1 - SR2) should match the sampling spread."""
        rng = random.Random(7)
        rho, t, reps = 0.9, 500, 1500
        mu1, mu2, sigma = 0.0006, 0.0003, 0.01
        diffs = []
        for _ in range(reps):
            a, b = [], []
            for _ in range(t):
                z1, z2 = rng.gauss(0, 1), rng.gauss(0, 1)
                x = mu1 + sigma * z1
                y = mu2 + sigma * (rho * z1 + math.sqrt(1 - rho ** 2) * z2)
                a.append(x)
                b.append(y)
            diffs.append(stats.sharpe(a) - stats.sharpe(b))
        m = stats.mean(diffs)
        sim_se = math.sqrt(sum((d - m) ** 2 for d in diffs) / (reps - 1))
        sr1 = mu1 / sigma * math.sqrt(252)
        sr2 = mu2 / sigma * math.sqrt(252)
        formula = stats.sharpe_diff_se_annual(sr1, sr2, rho, years=t / 252)
        self.assertAlmostEqual(sim_se / formula, 1.0, delta=0.08)

    def test_years_to_resolve_round_trips_with_se(self):
        years = stats.years_to_resolve_sharpe_diff(0.5, 0.5, 0.9)
        se = stats.sharpe_diff_se_annual(1.0, 0.5, 0.9, years)
        self.assertAlmostEqual(1.959964 * se, 0.5, places=3)

    def test_correlation_matters_a_lot(self):
        hi = stats.years_to_resolve_sharpe_diff(0.5, 0.5, 0.9)
        lo = stats.years_to_resolve_sharpe_diff(0.5, 0.5, 0.0)
        self.assertGreater(lo, 5 * hi)

    def test_bootstrap_detects_a_real_difference_and_not_a_null(self):
        rng = random.Random(3)
        n = 1500
        base = gauss_series(n, 0.0, 0.01, rng)
        better = [x + 0.0008 + rng.gauss(0, 0.002) for x in base]
        res = stats.bootstrap_sharpe_diff(better, base, n_boot=400, seed=1)
        self.assertGreater(res["lo"], 0.0)
        same = [x + rng.gauss(0, 0.002) for x in base]
        null = stats.bootstrap_sharpe_diff(same, base, n_boot=400, seed=1)
        self.assertLess(null["lo"], 0.0 + 1e-9)
        self.assertGreater(null["hi"], 0.0 - 1e-9)

    def test_bootstrap_rejects_misaligned_series(self):
        with self.assertRaises(ValueError):
            stats.bootstrap_sharpe_diff([0.0] * 30, [0.0] * 31)


class MultipleTesting(unittest.TestCase):
    def test_expected_max_grows_with_trials(self):
        v = 0.01 ** 2
        self.assertLess(stats.expected_max_sharpe(10, v), stats.expected_max_sharpe(1000, v))
        self.assertEqual(stats.expected_max_sharpe(1, v), 0.0)

    def test_deflated_is_lower_than_probabilistic(self):
        s, n = 0.08, 750
        plain = stats.psr(s, 0.0, n)
        deflated = stats.dsr(s, n, n_trials=100, var_of_trial_sharpes=0.05 ** 2)
        self.assertLess(deflated, plain)

    def test_psr_half_at_the_benchmark(self):
        self.assertAlmostEqual(stats.psr(0.05, 0.05, 500), 0.5)


class RatingsAndCosts(unittest.TestCase):
    def test_unreadable_rating_raises_not_hold(self):
        with self.assertRaises(ValueError):
            ratings.normalize_rating("maybe")

    def test_markdown_wrapped_rating(self):
        self.assertEqual(ratings.normalize_rating("**Overweight**"), "Overweight")

    def test_weights_respect_gross_cap(self):
        w = ratings.weights_from_ratings({"A": "Buy", "B": "Sell"}, max_gross=0.5)
        self.assertAlmostEqual(sum(abs(x) for x in w.values()), 0.5)

    def test_long_only_never_shorts(self):
        w = ratings.weights_from_ratings({"A": "Sell", "B": "Underweight"}, ratings.LONG_ONLY)
        self.assertTrue(all(x >= 0 for x in w.values()))

    def test_costs_charge_turnover_only(self):
        w = [{"A": 1.0}, {"A": 1.0}, {"A": 0.0}]
        r = [{"A": 0.0}, {"A": 0.0}, {"A": 0.0}]
        out = ratings.net_returns(w, r, cost_bps=10)
        self.assertAlmostEqual(out[0], -0.001)   # buy from cash
        self.assertAlmostEqual(out[1], 0.0)      # no trade
        self.assertAlmostEqual(out[2], -0.001)   # sell to cash

    def test_misaligned_inputs_raise(self):
        with self.assertRaises(ValueError):
            ratings.net_returns([{}], [{}, {}])


class Budget(unittest.TestCase):
    def test_dollars_from_tokens(self):
        b = budget.BudgetLedger(budget.Caps(), price_in_per_mtok=4.0, price_out_per_mtok=20.0)
        b.record_model_call(1_000_000, 100_000)
        self.assertAlmostEqual(b.dollars, 4.0 + 2.0)

    def test_cap_raises(self):
        b = budget.BudgetLedger(budget.Caps(model_calls=2), 1.0, 1.0)
        b.record_model_call(10, 10)
        b.record_model_call(10, 10)
        with self.assertRaises(budget.BudgetExceeded):
            b.record_model_call(10, 10)

    def test_tool_call_cap(self):
        b = budget.BudgetLedger(budget.Caps(tool_calls=1), 1.0, 1.0)
        b.record_tool_call()
        with self.assertRaises(budget.BudgetExceeded):
            b.record_tool_call()

    def test_scale_caps(self):
        c = budget.scale_caps(budget.Caps(input_tokens=1000, dollars=0.02), 5)
        self.assertEqual(c.input_tokens, 5000)
        self.assertAlmostEqual(c.dollars, 0.10)
        self.assertIsNone(c.tool_calls)


def filled_card():
    card = copy.deepcopy(report_card.TEMPLATE)
    card["universe"]["description"] = "20 large-cap US stocks"
    card["data"]["vendors"] = ["vendor-a"]
    card["models"]["list"] = [{"name": "model-x", "snapshot_id": "model-x-2026-01-01", "stated_cutoff": "2025-06"}]
    return card


class ReportCard(unittest.TestCase):
    def test_blank_template_is_rejected(self):
        problems = report_card.validate(copy.deepcopy(report_card.TEMPLATE))
        self.assertIn("missing field: universe.description", problems)
        self.assertIn("models.list[0] missing snapshot_id", problems)

    def test_filled_card_passes(self):
        self.assertEqual(report_card.validate(filled_card()), [])

    def test_missing_sections_are_named(self):
        problems = report_card.validate({"window": {"start": "2025-01-01"}})
        self.assertIn("missing field: window.end", problems)
        self.assertIn("missing section: budget", problems)

    def test_requires_single_call_and_passive_baselines(self):
        card = filled_card()
        card["baselines"] = {"list": [{"kind": "rule"}]}
        problems = report_card.validate(card)
        self.assertTrue(any("single_call" in p for p in problems))
        self.assertTrue(any("passive" in p for p in problems))

    def test_model_snapshot_and_cutoff_required(self):
        card = filled_card()
        card["models"] = {"list": [{"name": "m"}]}
        problems = report_card.validate(card)
        self.assertIn("models.list[0] missing snapshot_id", problems)
        self.assertIn("models.list[0] missing stated_cutoff", problems)


if __name__ == "__main__":
    unittest.main()
