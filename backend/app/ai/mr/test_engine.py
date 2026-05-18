"""
Tests for MR engine — IVW, MR-Egger, Weighted Median, Weighted Mode.

Uses known datasets with predictable results to verify correctness.
"""

import math
import pytest
from backend.app.ai.mr.engine import (
    mr_ivw,
    mr_egger,
    mr_weighted_median,
    mr_weighted_mode,
    cochran_q,
    mr_egger_intercept_test,
    MREstimate,
)


# ---- Fixtures: simulated-but-deterministic GWAS data ----

@pytest.fixture
def simple_data():
    """8 SNPs with known effects. IVW beta ~0.30."""
    return {
        "beta_exposure": [0.12, 0.08, 0.05, 0.15, 0.10, 0.18, 0.07, 0.09],
        "se_exposure":    [0.03, 0.02, 0.04, 0.03, 0.02, 0.04, 0.03, 0.02],
        "beta_outcome":   [0.042, 0.028, 0.019, 0.051, 0.035, 0.058, 0.025, 0.031],
        "se_outcome":     [0.05, 0.04, 0.06, 0.05, 0.04, 0.05, 0.05, 0.04],
    }


@pytest.fixture
def perfect_data():
    """Perfect ratio: every SNP has beta_outcome = 0.3 * beta_exposure."""
    betas = [0.05, 0.10, 0.08, 0.12, 0.06, 0.15]
    ses =   [0.02, 0.03, 0.02, 0.04, 0.02, 0.03]
    return {
        "beta_exposure": betas,
        "se_exposure": ses,
        "beta_outcome": [b * 0.3 for b in betas],
        "se_outcome": ses,  # same SEs for simplicity
    }


# ---- IVW ----

def test_ivw_returns_positive_beta(simple_data):
    """IVW on simple data yields positive causal estimate."""
    result = mr_ivw(simple_data["beta_exposure"], simple_data["se_outcome"],
                    simple_data["beta_outcome"])
    assert result.beta > 0
    assert result.se > 0
    assert result.p_value < 0.05
    assert result.method == "IVW"


def test_ivw_perfect_ratio(perfect_data):
    """IVW with perfect ratio data recovers true beta=0.3 within tolerance."""
    result = mr_ivw(perfect_data["beta_exposure"], perfect_data["se_outcome"],
                    perfect_data["beta_outcome"])
    assert abs(result.beta - 0.3) < 0.01
    assert result.p_value < 0.05  # 6 SNPs, large SE => p≈0.009 is correct


def test_ivw_single_snp():
    """IVW with one SNP is just the ratio estimate."""
    result = mr_ivw([0.1], [0.05], [0.04])
    assert result.beta == pytest.approx(0.4, abs=0.01)
    assert result.se > 0


def test_ivw_insufficient_snps():
    """IVW with 0 SNPs raises ValueError."""
    with pytest.raises(ValueError):
        mr_ivw([], [], [])


# ---- MR-Egger ----

def test_egger_returns_intercept_and_beta(simple_data):
    """MR-Egger returns both beta and intercept."""
    result = mr_egger(simple_data["beta_exposure"], simple_data["se_outcome"],
                      simple_data["beta_outcome"])
    assert result.beta > 0
    assert result.intercept is not None
    assert result.method == "MR-Egger"


def test_egger_perfect_data_no_intercept(perfect_data):
    """With no pleiotropy (perfect data), MR-Egger intercept ~0."""
    result = mr_egger(perfect_data["beta_exposure"], perfect_data["se_outcome"],
                      perfect_data["beta_outcome"])
    assert abs(result.intercept) < 0.05  # near zero
    assert abs(result.beta - 0.3) < 0.05  # close to true


def test_egger_intercept_test():
    """mr_egger_intercept_test returns p-value for directional pleiotropy."""
    pval, intercept, se = mr_egger_intercept_test(
        [0.12, 0.08, 0.05, 0.15, 0.10, 0.18],
        [0.05, 0.04, 0.06, 0.05, 0.04, 0.05],
        [0.042, 0.028, 0.019, 0.051, 0.035, 0.058],
    )
    assert 0 <= pval <= 1
    assert se > 0


# ---- Weighted Median ----

def test_weighted_median_returns_estimate(simple_data):
    """Weighted Median returns a valid estimate."""
    result = mr_weighted_median(simple_data["beta_exposure"],
                                simple_data["se_outcome"],
                                simple_data["beta_outcome"])
    assert result.beta > 0
    assert result.se > 0
    assert result.method == "Weighted Median"


def test_weighted_median_consistent(simple_data):
    """Weighted Median gives consistent results on repeated calls."""
    d = simple_data
    r1 = mr_weighted_median(d["beta_exposure"], d["se_outcome"], d["beta_outcome"])
    r2 = mr_weighted_median(d["beta_exposure"], d["se_outcome"], d["beta_outcome"])
    assert r1.beta == pytest.approx(r2.beta)


# ---- Weighted Mode ----

def test_weighted_mode_returns_estimate(simple_data):
    """Weighted Mode returns a valid estimate."""
    result = mr_weighted_mode(simple_data["beta_exposure"],
                              simple_data["se_outcome"],
                              simple_data["beta_outcome"])
    assert result.beta > 0
    assert result.se > 0
    assert result.method == "Weighted Mode"


# ---- Cochran's Q ----

def test_cochran_q_returns_dict(simple_data):
    """Cochran's Q returns a dict with statistic, df, pval."""
    result = cochran_q(simple_data["beta_outcome"], simple_data["se_outcome"],
                       ivw_beta=0.35)
    assert "q_statistic" in result
    assert "q_df" in result
    assert "q_pval" in result
    assert result["q_df"] == len(simple_data["beta_outcome"]) - 1
    assert 0 <= result["q_pval"] <= 1
