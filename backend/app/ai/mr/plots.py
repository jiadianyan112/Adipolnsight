"""
MR visualization — scatter, forest, leave-one-out, and funnel plots.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# Style defaults
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "figure.dpi": 150,
})


def _save_or_bytes(fig: plt.Figure, path: Optional[str] = None) -> Optional[bytes]:
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, bbox_inches="tight", dpi=150)
        plt.close(fig)
        return None
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    return buf.getvalue()


# ---- Scatter Plot ----

def plot_scatter(
    beta_exposure: List[float],
    beta_outcome: List[float],
    se_exposure: List[float],
    se_outcome: List[float],
    ivw_beta: float,
    output_dir: str,
) -> str:
    """SNP-exposure vs SNP-outcome scatter with IVW line. Returns file path."""
    fig, ax = plt.subplots(figsize=(7, 6))

    bx = np.array(beta_exposure)
    by = np.array(beta_outcome)
    sx = np.array(se_exposure)
    sy = np.array(se_outcome)

    ax.errorbar(bx, by, xerr=sx, yerr=sy, fmt="o", color="#2c3e50",
                ecolor="#7f8c8d", elinewidth=0.8, capsize=2, markersize=5, alpha=0.8)
    ax.axline((0, 0), slope=ivw_beta, color="#c0392b", linewidth=1.5, linestyle="--",
              label=f"IVW (β={ivw_beta:.3f})")

    ax.axhline(0, color="#bdc3c7", linewidth=0.5)
    ax.axvline(0, color="#bdc3c7", linewidth=0.5)
    ax.set_xlabel("SNP effect on exposure")
    ax.set_ylabel("SNP effect on outcome")
    ax.set_title("MR Scatter Plot")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.2)

    path = os.path.join(output_dir, "scatter_plot.png")
    _save_or_bytes(fig, path)
    return path


# ---- Forest Plot ----

def plot_forest(
    estimates: List[Dict],
    output_dir: str,
) -> str:
    """Forest plot of MR method estimates. Returns file path."""
    methods = [e["method"] for e in estimates]
    betas = [e["beta"] for e in estimates]
    cis = [(e["ci_lower"], e["ci_upper"]) for e in estimates]

    fig, ax = plt.subplots(figsize=(8, 0.5 * len(methods) + 2))

    y_pos = range(len(methods))
    for i, (method, beta, (lo, hi)) in enumerate(zip(methods, betas, cis)):
        color = "#2c3e50" if method == "IVW" else "#7f8c8d"
        ax.plot([lo, hi], [i, i], color=color, linewidth=2)
        ax.plot(beta, i, "o", color="#c0392b" if method == "IVW" else color, markersize=6)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(methods)
    ax.axvline(0, color="#bdc3c7", linewidth=0.5)
    ax.set_xlabel("Causal effect (β)")
    ax.set_title("MR Forest Plot")
    ax.grid(True, alpha=0.2, axis="x")

    path = os.path.join(output_dir, "forest_plot.png")
    _save_or_bytes(fig, path)
    return path


# ---- Leave-One-Out Plot ----

def plot_leave_one_out(
    loo_results: List[Dict],
    output_dir: str,
) -> str:
    """Leave-one-out analysis plot. Returns file path."""
    if not loo_results:
        path = os.path.join(output_dir, "leave_one_out.png")
        _save_or_bytes(plt.figure(), path)
        return path

    snps = [r.get("snp", f"SNP{i}") for i, r in enumerate(loo_results)]
    betas = [r["beta"] for r in loo_results]
    cis = [(r["ci_lower"], r["ci_upper"]) for r in loo_results]

    fig, ax = plt.subplots(figsize=(8, max(4, 0.3 * len(snps))))

    y_pos = range(len(snps))
    for i, (snp, beta, (lo, hi)) in enumerate(zip(snps, betas, cis)):
        ax.plot([lo, hi], [i, i], color="#2c3e50", linewidth=1.5)
        ax.plot(beta, i, "o", color="#2c3e50", markersize=4)

    ax.axvline(np.mean(betas), color="#c0392b", linewidth=1, linestyle="--", label=f"Mean: {np.mean(betas):.3f}")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(snps, fontsize=7)
    ax.set_xlabel("Causal effect (β)")
    ax.set_title("Leave-One-Out Analysis")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.2, axis="x")

    path = os.path.join(output_dir, "leave_one_out.png")
    _save_or_bytes(fig, path)
    return path


# ---- Funnel Plot ----

def plot_funnel(
    beta_outcome: List[float],
    se_outcome: List[float],
    output_dir: str,
) -> str:
    """Funnel plot: individual SNP estimates vs precision (1/SE). Returns file path."""
    by = np.array(beta_outcome)
    se = np.array(se_outcome)

    fig, ax = plt.subplots(figsize=(7, 5))

    precision = 1.0 / se
    ax.scatter(by, precision, color="#2c3e50", alpha=0.7, s=30)
    ax.axvline(np.median(by), color="#c0392b", linewidth=1, linestyle="--",
               label=f"Median: {np.median(by):.3f}")

    ax.set_xlabel("Individual SNP estimate (β)")
    ax.set_ylabel("Precision (1/SE)")
    ax.set_title("MR Funnel Plot")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.2)

    path = os.path.join(output_dir, "funnel_plot.png")
    _save_or_bytes(fig, path)
    return path
