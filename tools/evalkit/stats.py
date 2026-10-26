"""Sharpe-ratio statistics that decide whether a backtest can say anything.

Everything here assumes returns are *excess* returns per period (day, week, ...)
unless a function says "annual". Formulas follow Lo (2002), Jobson and Korkie
(1981) with Memmel's (2003) correction, and Bailey and Lopez de Prado (2012,
2014). The closed forms assume independent, identically distributed returns;
use the block bootstrap when that is doubtful, which for daily trading returns
it usually is.
"""
from __future__ import annotations

import math
import random
from statistics import NormalDist

_N = NormalDist()
EULER_GAMMA = 0.5772156649015329


def mean(xs: list[float]) -> float:
    return math.fsum(xs) / len(xs)  # exact summation: sum() rounds differently across Python versions


def stdev(xs: list[float]) -> float:
    """Sample standard deviation (n - 1)."""
    if len(xs) < 2:
        raise ValueError("need at least two observations")
    m = mean(xs)
    return math.sqrt(math.fsum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def sharpe(returns: list[float], periods_per_year: int = 252) -> float:
    """Annualized Sharpe ratio of per-period excess returns."""
    s = stdev(returns)
    if s <= 1e-12 * abs(mean(returns)):  # a constant series: float noise, not volatility
        raise ValueError("zero volatility: Sharpe is undefined")
    return mean(returns) / s * math.sqrt(periods_per_year)


def skew_kurtosis(returns: list[float]) -> tuple[float, float]:
    """Sample skewness and (non-excess) kurtosis; a normal has kurtosis 3."""
    n = len(returns)
    m = mean(returns)
    s2 = sum((x - m) ** 2 for x in returns) / n
    if s2 == 0:
        raise ValueError("zero variance")
    s = math.sqrt(s2)
    g3 = sum((x - m) ** 3 for x in returns) / n / s ** 3
    g4 = sum((x - m) ** 4 for x in returns) / n / s ** 4
    return g3, g4


def sharpe_se_annual(sr_annual: float, years: float, periods_per_year: int = 252) -> float:
    """Standard error of an annualized Sharpe ratio measured over `years` (iid normal, Lo 2002).

    Lo's result is Var(SR_hat) = (1 + SR^2 / 2) / N for a *per-period* Sharpe ratio SR measured over
    N periods. Annualizing multiplies the estimator by sqrt(periods_per_year), which gives
    Var(SR_annual_hat) = (1 + SR_annual^2 / (2 * periods_per_year)) / years. For daily data the second
    term is tiny, so the standard error is close to 1 / sqrt(years) at any plausible Sharpe ratio.
    """
    if years <= 0:
        raise ValueError("years must be positive")
    return math.sqrt((1 + 0.5 * sr_annual ** 2 / periods_per_year) / years)


def min_track_record_periods(sr_per_period: float, sr0_per_period: float = 0.0,
                             skew: float = 0.0, kurt: float = 3.0, confidence: float = 0.95) -> float:
    """Minimum number of periods before a Sharpe ratio is distinguishable from `sr0` (Bailey and Lopez de Prado 2012).

    `confidence` is one-sided. Returns inf when the observed Sharpe does not exceed sr0.
    """
    if sr_per_period <= sr0_per_period:
        return math.inf
    z = _N.inv_cdf(confidence)
    var_term = 1 - skew * sr_per_period + (kurt - 1) / 4 * sr_per_period ** 2
    return 1 + var_term * (z / (sr_per_period - sr0_per_period)) ** 2


def min_track_record_years(sr_annual: float, sr0_annual: float = 0.0, periods_per_year: int = 252,
                           skew: float = 0.0, kurt: float = 3.0, confidence: float = 0.95) -> float:
    """Same as `min_track_record_periods`, with annual inputs and a result in years."""
    m = math.sqrt(periods_per_year)
    n = min_track_record_periods(sr_annual / m, sr0_annual / m, skew, kurt, confidence)
    return n / periods_per_year


def sharpe_diff_var_per_period(sr1: float, sr2: float, rho: float) -> float:
    """T * Var(SR1 - SR2) for per-period Sharpe ratios and return correlation `rho` (Jobson-Korkie, Memmel)."""
    return 2 * (1 - rho) + 0.5 * (sr1 ** 2 + sr2 ** 2 - 2 * sr1 * sr2 * rho ** 2)


def sharpe_diff_se_annual(sr1_annual: float, sr2_annual: float, rho: float, years: float,
                          periods_per_year: int = 252) -> float:
    """Standard error of an annualized Sharpe-ratio difference over `years` (iid bivariate normal)."""
    m = periods_per_year
    s1, s2 = sr1_annual / math.sqrt(m), sr2_annual / math.sqrt(m)
    var_per_period_total = sharpe_diff_var_per_period(s1, s2, rho)  # = T * Var, per-period units
    t_periods = years * m
    return math.sqrt(var_per_period_total / t_periods * m)


def years_to_resolve_sharpe_diff(delta_annual: float, sr_low_annual: float, rho: float,
                                 confidence: float = 0.95, two_sided: bool = True,
                                 periods_per_year: int = 252) -> float:
    """Years of data needed for a Sharpe difference `delta_annual` to clear its own standard error.

    `sr_low_annual` is the lower of the two Sharpe ratios; the higher one is sr_low + delta.
    """
    if delta_annual <= 0:
        raise ValueError("delta must be positive")
    z = _N.inv_cdf(1 - (1 - confidence) / (2 if two_sided else 1))
    m = periods_per_year
    s1 = (sr_low_annual + delta_annual) / math.sqrt(m)
    s2 = sr_low_annual / math.sqrt(m)
    var_total = sharpe_diff_var_per_period(s1, s2, rho)  # per-period units, times T
    # z * sqrt(var_total / T_periods * m) = delta  ->  T_periods = z^2 * var_total * m / delta^2
    t_periods = z ** 2 * var_total * m / delta_annual ** 2
    return t_periods / m


def psr(sr_per_period: float, sr0_per_period: float, n: int, skew: float = 0.0, kurt: float = 3.0) -> float:
    """Probabilistic Sharpe ratio: P(true Sharpe > sr0) given n observations (Bailey and Lopez de Prado 2012)."""
    if n < 2:
        raise ValueError("need at least two observations")
    denom = math.sqrt(1 - skew * sr_per_period + (kurt - 1) / 4 * sr_per_period ** 2)
    return _N.cdf((sr_per_period - sr0_per_period) * math.sqrt(n - 1) / denom)


def expected_max_sharpe(n_trials: int, var_of_trial_sharpes: float) -> float:
    """Expected maximum per-period Sharpe among `n_trials` unskilled trials (Bailey and Lopez de Prado 2014)."""
    if n_trials < 2:
        return 0.0
    sd = math.sqrt(var_of_trial_sharpes)
    return sd * ((1 - EULER_GAMMA) * _N.inv_cdf(1 - 1 / n_trials)
                 + EULER_GAMMA * _N.inv_cdf(1 - 1 / (n_trials * math.e)))


def dsr(sr_per_period: float, n: int, n_trials: int, var_of_trial_sharpes: float,
        skew: float = 0.0, kurt: float = 3.0) -> float:
    """Deflated Sharpe ratio: the PSR against the best Sharpe luck alone would give after `n_trials` tries."""
    return psr(sr_per_period, expected_max_sharpe(n_trials, var_of_trial_sharpes), n, skew, kurt)


def _circular_block_indices(n: int, block: int, rng: random.Random) -> list[int]:
    idx: list[int] = []
    while len(idx) < n:
        start = rng.randrange(n)
        idx.extend((start + k) % n for k in range(block))
    return idx[:n]


def bootstrap_sharpe_diff(a: list[float], b: list[float], periods_per_year: int = 252,
                          block: int | None = None, n_boot: int = 2000, seed: int = 0,
                          alpha: float = 0.05) -> dict:
    """Paired circular block bootstrap of Sharpe(a) - Sharpe(b).

    Both series are resampled with the same block indices so their correlation is kept.
    Returns the point estimate, a percentile interval, and the fraction of resamples with a
    non-positive difference (a one-sided bootstrap p-value for "a is better than b").
    """
    if len(a) != len(b):
        raise ValueError("series must be the same length and aligned on dates")
    n = len(a)
    if n < 20:
        raise ValueError("too few observations to bootstrap")
    block = block or max(1, round(n ** (1 / 3)))
    rng = random.Random(seed)
    diffs = []
    for _ in range(n_boot):
        idx = _circular_block_indices(n, block, rng)
        ra, rb = [a[i] for i in idx], [b[i] for i in idx]
        try:
            diffs.append(sharpe(ra, periods_per_year) - sharpe(rb, periods_per_year))
        except ValueError:
            continue
    diffs.sort()
    k = len(diffs)
    lo = diffs[int(k * alpha / 2)]
    hi = diffs[min(k - 1, int(k * (1 - alpha / 2)))]
    return {
        "diff": sharpe(a, periods_per_year) - sharpe(b, periods_per_year),
        "lo": lo,
        "hi": hi,
        "p_a_not_better": sum(1 for d in diffs if d <= 0) / k,
        "block": block,
        "n_boot": k,
    }
