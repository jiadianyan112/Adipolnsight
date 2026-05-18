"""
GWAS data harmonization — allele alignment, palindromic SNP handling, strand flipping.

Ensures exposure and outcome datasets are aligned before MR analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


COMPLEMENT = str.maketrans("ACGTacgt", "TGCAtgca")


@dataclass
class HarmonizationResult:
    """Output of harmonize()."""
    data: pd.DataFrame
    n_original: int
    n_after: int
    n_removed_palindromic: int
    n_removed_missing: int
    n_flipped: int
    warnings: List[str] = field(default_factory=list)

    @property
    def n_removed(self) -> int:
        return self.n_original - self.n_after


def reverse_complement(seq: str) -> str:
    return seq.translate(COMPLEMENT)[::-1]


def is_palindromic(a1: str, a2: str) -> bool:
    """Check if allele pair is palindromic (A/T or C/G)."""
    pair = {a1.upper(), a2.upper()}
    return pair in ({"A", "T"}, {"C", "G"})


def harmonize(
    exposure: pd.DataFrame,
    outcome: pd.DataFrame,
    on: str = "SNP",
    ea_col: str = "effect_allele",
    oa_col: str = "other_allele",
    beta_col: str = "beta",
    se_col: str = "se",
    eaf_col: str = "eaf",
) -> HarmonizationResult:
    """
    Harmonize exposure and outcome GWAS data.

    Steps:
    1. Intersect by SNP
    2. Align effect alleles — flip beta sign and EAF when needed
    3. Remove palindromic SNPs with ambiguous strand
    4. Return aligned DataFrame

    Returns aligned exposure columns prefixed with `exposure_` and outcome with `outcome_`.
    """
    exp = exposure.copy()
    out = outcome.copy()
    n_original = len(exp)
    n_flipped = 0
    n_removed_palindromic = 0
    n_removed_missing = 0
    warnings = []

    # Normalize column access
    if "SNP" not in exp.columns and on in exp.columns:
        exp = exp.rename(columns={on: "SNP"})
    if "SNP" not in out.columns and on in out.columns:
        out = out.rename(columns={on: "SNP"})

    required_exp = {"SNP", ea_col, oa_col, beta_col, se_col}
    required_out = {"SNP", ea_col, oa_col, beta_col, se_col}
    missing_exp = required_exp - set(exp.columns)
    missing_out = required_out - set(out.columns)
    if missing_exp:
        raise ValueError(f"Exposure missing columns: {missing_exp}")
    if missing_out:
        raise ValueError(f"Outcome missing columns: {missing_out}")

    # Deduplicate
    exp = exp.drop_duplicates(subset="SNP")
    out = out.drop_duplicates(subset="SNP")

    # Intersect
    merged = pd.merge(exp, out, on="SNP", suffixes=("_exp", "_out"), how="inner")
    n_removed_missing = n_original - len(merged)

    # Allele alignment
    flip_mask = np.zeros(len(merged), dtype=bool)
    drop_mask = np.zeros(len(merged), dtype=bool)

    for i, row in merged.iterrows():
        ea_exp = str(row[f"{ea_col}_exp"]).upper()
        oa_exp = str(row[f"{oa_col}_exp"]).upper()
        ea_out = str(row[f"{ea_col}_out"]).upper()
        oa_out = str(row[f"{oa_col}_out"]).upper()

        if ea_exp == ea_out and oa_exp == oa_out:
            continue  # aligned
        elif ea_exp == oa_out and oa_exp == ea_out:
            flip_mask[i] = True  # strand flip needed
        elif ea_exp == reverse_complement(ea_out):
            flip_mask[i] = True  # strand flip via complement
        elif is_palindromic(ea_exp, oa_exp):
            drop_mask[i] = True  # ambiguous palindromic
            n_removed_palindromic += 1
        else:
            drop_mask[i] = True  # can't align
            n_removed_palindromic += 1

    merged = merged[~drop_mask].copy()
    n_removed_palindromic = int(drop_mask.sum())

    # Apply flips
    flip_idx = merged.index[flip_mask[~drop_mask]]
    if len(flip_idx) > 0:
        n_flipped = len(flip_idx)
        merged.loc[flip_idx, f"{beta_col}_out"] = -merged.loc[flip_idx, f"{beta_col}_out"]
        # swap alleles
        ea_tmp = merged.loc[flip_idx, f"{ea_col}_out"].copy()
        merged.loc[flip_idx, f"{ea_col}_out"] = merged.loc[flip_idx, f"{oa_col}_out"]
        merged.loc[flip_idx, f"{oa_col}_out"] = ea_tmp
        if eaf_col in merged.columns:
            merged.loc[flip_idx, f"{eaf_col}_out"] = 1.0 - merged.loc[flip_idx, f"{eaf_col}_out"]

    if n_removed_palindromic > 0:
        warnings.append(f"Removed {n_removed_palindromic} palindromic/unmatchable SNPs")
    if n_flipped > 0:
        warnings.append(f"Flipped {n_flipped} SNPs to align effect alleles")

    # Rename columns for MR engine
    result = merged.rename(columns={
        f"{beta_col}_exp": "beta_exposure",
        f"{se_col}_exp": "se_exposure",
        f"{beta_col}_out": "beta_outcome",
        f"{se_col}_out": "se_outcome",
        f"{ea_col}_exp": "effect_allele_exposure",
        f"{oa_col}_exp": "other_allele_exposure",
        f"{ea_col}_out": "effect_allele_outcome",
        f"{oa_col}_out": "other_allele_outcome",
    })

    return HarmonizationResult(
        data=result,
        n_original=n_original,
        n_after=len(result),
        n_removed_palindromic=int(round(n_removed_palindromic)),
        n_removed_missing=n_removed_missing,
        n_flipped=n_flipped,
        warnings=warnings,
    )
