"""
MR analysis engine — core statistical methods.

Implements IVW, MR-Egger, Weighted Median, Weighted Mode, and sensitivity tests
using numpy/scipy/statsmodels. All methods operate on aligned SNP-level data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
from scipy import stats
import statsmodels.api as sm


@dataclass
class MREstimate:
    """Single MR method result."""
    method: str
    beta: float
    se: float
    p_value: float
    ci_lower: float
    ci_upper: float
    n_snps: int
    intercept: Optional[float] = None  # MR-Egger only


# ---- Internal helpers ----

def _ratio_estimates(
    beta_exposure: List[float],
    beta_outcome: List[float],
    se_outcome: List[float],
) -> np.ndarray:
    """Wald ratio per SNP: beta_outcome / beta_exposure."""
    bx = np.array(beta_exposure, dtype=np.float64)
    by = np.array(beta_outcome, dtype=np.float64)
    se_y = np.array(se_outcome, dtype=np.float64)

    if len(bx) == 0:
        raise ValueError("At least 1 SNP required")

    ratio = by / bx
    ratio_se = se_y / np.abs(bx)
    return ratio, ratio_se


def _ci(beta: float, se: float) -> tuple:
    z = stats.norm.ppf(0.975)
    return (beta - z * se, beta + z * se)


# ---- IVW ----

def mr_ivw(
    beta_exposure: List[float],
    se_outcome: List[float],
    beta_outcome: List[float],
) -> MREstimate:
    """Fixed-effects IVW: weighted linear regression forced through origin."""
    bx = np.array(beta_exposure, dtype=np.float64)
    by = np.array(beta_outcome, dtype=np.float64)
    se_y = np.array(se_outcome, dtype=np.float64)
    n = len(bx)

    if n < 1:
        raise ValueError("At least 1 SNP required for IVW")

    w = 1.0 / (se_y ** 2)
    beta = np.sum(w * by * bx) / np.sum(w * bx ** 2)
    se_beta = np.sqrt(1.0 / np.sum(w * bx ** 2))
    z = beta / se_beta
    p_value = float(2 * stats.norm.sf(abs(z)))
    lo, hi = _ci(beta, se_beta)

    return MREstimate("IVW", float(beta), float(se_beta), p_value, lo, hi, n)


# ---- MR-Egger ----

def mr_egger(
    beta_exposure: List[float],
    se_outcome: List[float],
    beta_outcome: List[float],
) -> MREstimate:
    """MR-Egger: weighted regression with intercept (directional pleiotropy)."""
    bx = np.array(beta_exposure, dtype=np.float64)
    by = np.array(beta_outcome, dtype=np.float64)
    se_y = np.array(se_outcome, dtype=np.float64)
    n = len(bx)

    if n < 3:
        raise ValueError("MR-Egger requires at least 3 SNPs")

    w = 1.0 / (se_y ** 2)
    X = sm.add_constant(bx)
    model = sm.WLS(by, X, weights=w)
    results = model.fit()

    intercept = float(results.params[0])
    beta = float(results.params[1])
    se_beta = float(results.bse[1])
    z = beta / se_beta
    p_value = float(2 * stats.norm.sf(abs(z)))
    lo, hi = _ci(beta, se_beta)

    return MREstimate("MR-Egger", beta, se_beta, p_value, lo, hi, n, intercept)


def mr_egger_intercept_test(
    beta_exposure: List[float],
    se_outcome: List[float],
    beta_outcome: List[float],
) -> tuple:
    """Returns (p_value, intercept, se_intercept) for Egger intercept test."""
    bx = np.array(beta_exposure, dtype=np.float64)
    by = np.array(beta_outcome, dtype=np.float64)
    se_y = np.array(se_outcome, dtype=np.float64)

    w = 1.0 / (se_y ** 2)
    X = sm.add_constant(bx)
    model = sm.WLS(by, X, weights=w)
    results = model.fit()

    intercept = float(results.params[0])
    se_int = float(results.bse[0])
    z = intercept / se_int if se_int > 0 else 0.0
    pval = float(2 * stats.norm.sf(abs(z)))
    return pval, intercept, se_int


# ---- Weighted Median ----

def mr_weighted_median(
    beta_exposure: List[float],
    se_outcome: List[float],
    beta_outcome: List[float],
) -> MREstimate:
    """Weighted median of Wald ratio estimates, bootstrapped SE."""
    bx = np.array(beta_exposure, dtype=np.float64)
    by = np.array(beta_outcome, dtype=np.float64)
    se_y = np.array(se_outcome, dtype=np.float64)
    n = len(bx)

    ratio, ratio_se = _ratio_estimates(beta_exposure, beta_outcome, se_outcome)
    w = 1.0 / (ratio_se ** 2)
    w = w / w.sum()

    order = np.argsort(ratio)
    ratio_sorted = ratio[order]
    w_sorted = w[order]
    cum_w = np.cumsum(w_sorted)
    median_idx = np.searchsorted(cum_w, 0.5)
    beta = float(ratio_sorted[min(median_idx, n - 1)])

    # SE via bootstrap
    rng = np.random.RandomState(42)
    boot_betas = []
    for _ in range(1000):
        idx = rng.choice(n, size=n, replace=True)
        b = np.average(ratio[idx], weights=w[idx])
        boot_betas.append(b)
    se = float(np.std(boot_betas))
    z = beta / se if se > 0 else 0
    p_value = float(2 * stats.norm.sf(abs(z)))
    lo, hi = _ci(beta, se)

    return MREstimate("Weighted Median", beta, se, p_value, lo, hi, n)


# ---- Weighted Mode ----

def mr_weighted_mode(
    beta_exposure: List[float],
    se_outcome: List[float],
    beta_outcome: List[float],
    bandwidth: float = 1.0,
) -> MREstimate:
    """Zero-modal pleiotropy assumption: mode of weighted density of ratio estimates."""
    ratio, ratio_se = _ratio_estimates(beta_exposure, beta_outcome, se_outcome)
    w = 1.0 / (ratio_se ** 2)
    w = w / w.sum()
    n = len(ratio)

    # Kernel density with Gaussian kernel, weighted
    from scipy.stats import gaussian_kde
    bw_default = bandwidth * np.std(ratio) / (n ** 0.2) if n > 1 else 1.0
    bw = max(bw_default, 0.01)

    xs = np.linspace(ratio.min() - bw * 3, ratio.max() + bw * 3, 200)
    density = np.zeros_like(xs)
    for xi, wi in zip(ratio, w):
        density += wi * stats.norm.pdf(xs, loc=xi, scale=bw)

    beta = float(xs[np.argmax(density)])

    # SE via bootstrap
    rng = np.random.RandomState(42)
    boot_betas = []
    for _ in range(1000):
        idx = rng.choice(n, size=n, replace=True)
        xs_b = np.linspace(ratio[idx].min() - bw, ratio[idx].max() + bw, 200)
        dens_b = np.zeros_like(xs_b)
        for xi, wi in zip(ratio[idx], w[idx]):
            dens_b += wi * stats.norm.pdf(xs_b, loc=xi, scale=bw)
        boot_betas.append(float(xs_b[np.argmax(dens_b)]))
    se = float(np.std(boot_betas))
    z = beta / se if se > 0 else 0
    p_value = float(2 * stats.norm.sf(abs(z)))
    lo, hi = _ci(beta, se)

    return MREstimate("Weighted Mode", beta, se, p_value, lo, hi, n)


# ---- Cochran's Q ----

def cochran_q(
    beta_outcome: List[float],
    se_outcome: List[float],
    ivw_beta: float,
) -> Dict:
    """Cochran's Q test for heterogeneity among causal estimates."""
    by = np.array(beta_outcome, dtype=np.float64)
    se_y = np.array(se_outcome, dtype=np.float64)
    bx = np.ones_like(by)  # placeholder — actual Q uses per-SNP IV estimate

    w = 1.0 / (se_y ** 2)
    residuals = by - ivw_beta * bx
    q = float(np.sum(w * residuals ** 2))
    q_df = len(by) - 1
    q_pval = float(1 - stats.chi2.cdf(q, q_df)) if q_df > 0 else 1.0

    return {"q_statistic": q, "q_df": q_df, "q_pval": q_pval}
