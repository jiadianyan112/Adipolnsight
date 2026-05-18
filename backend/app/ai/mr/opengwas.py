"""
OpenGWAS API client (v4) for fetching GWAS metadata and summary statistics.

API documentation: https://api.opengwas.io/api/
Authentication: JWT Bearer token required (except /status, /batches).
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd

from backend.app.config import OPENGWAS_API_BASE, OPENGWAS_JWT

logger = logging.getLogger("adipoinsight.mr.opengwas")

DEFAULT_BASE = OPENGWAS_API_BASE.rstrip("/")
TIMEOUT = 30.0
BATCH_SIZE = 60  # API constraint: N(id)*N(variant) <= 64, so 60 is safe
MAX_RETRIES = 2


def _headers() -> Dict[str, str]:
    h = {"Accept": "application/json"}
    if OPENGWAS_JWT:
        h["Authorization"] = f"Bearer {OPENGWAS_JWT}"
    return h


def _client(timeout: float = TIMEOUT) -> httpx.Client:
    return httpx.Client(headers=_headers(), timeout=timeout, follow_redirects=True)


def _get_json(url: str, params: dict = None, timeout: float = TIMEOUT) -> dict:
    """Internal: GET and parse JSON, with error logging."""
    with _client(timeout=timeout) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


def _post_json(url: str, data: dict = None, timeout: float = TIMEOUT) -> dict:
    """Internal: POST JSON and parse response, with retry."""
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            with _client(timeout=timeout) as client:
                resp = client.post(url, json=data or {})
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            last_err = exc
            if attempt < MAX_RETRIES:
                import time
                time.sleep(1 * (attempt + 1))
    raise last_err  # type: ignore


# ---- Dataclasses ----

@dataclass
class GWASDataset:
    """Metadata for a GWAS dataset."""
    id: str
    trait: str = ""
    sample_size: int = 0
    ncase: int = 0
    ncontrol: int = 0
    ancestry: str = ""
    build: str = ""
    author: str = ""
    pmid: str = ""
    year: int = 0
    population: str = ""
    unit: str = ""
    nsnp: int = 0
    category: str = ""
    consortium: str = ""
    sex: str = ""
    note: str = ""


@dataclass
class SearchResult:
    datasets: List[GWASDataset] = field(default_factory=list)
    query: str = ""


# ---- Public API ----

def search(query: str, limit: int = 10) -> SearchResult:
    """
    Search OpenGWAS for datasets matching a trait name or ID.

    Uses /gwasinfo endpoint. Response is {id: metadata, ...} dict.
    Performs client-side filtering by trait name.
    """
    try:
        data = _get_json(f"{DEFAULT_BASE}/gwasinfo")

        if not isinstance(data, dict):
            return SearchResult(query=query)

        query_lower = query.lower().strip()
        datasets = []
        for dataset_id, item in data.items():
            if not isinstance(item, dict):
                continue
            trait = str(item.get("trait", ""))
            # Filter: match trait name or ID
            if query_lower in trait.lower() or query_lower in str(dataset_id).lower():
                datasets.append(_parse_dataset(dataset_id, item))
                if len(datasets) >= limit:
                    break

        return SearchResult(datasets=datasets, query=query)

    except Exception as exc:
        logger.warning("OpenGWAS search failed for '%s': %s", query, exc)
        return SearchResult(query=query)


def _parse_dataset(dataset_id: str, item: dict) -> GWASDataset:
    """Parse a single dataset entry from the gwasinfo response."""
    nsnp_val = int(item.get("nsnp", 0))
    ncase = int(item.get("ncase", 0))
    ncontrol = int(item.get("ncontrol", 0))
    return GWASDataset(
        id=str(dataset_id),
        trait=str(item.get("trait", "")),
        sample_size=ncase + ncontrol if (ncase + ncontrol) > 0 else nsnp_val,
        ncase=ncase,
        ncontrol=ncontrol,
        ancestry=str(item.get("population", "")),
        build=str(item.get("build", "")),
        author=str(item.get("author", "")),
        pmid=str(item.get("pmid", "")),
        year=int(item.get("year", 0)),
        population=str(item.get("population", "")),
        unit=str(item.get("unit", "")),
        nsnp=nsnp_val,
        category=str(item.get("category", "") or item.get("subcategory", "")),
        consortium=str(item.get("consortium", "")),
        sex=str(item.get("sex", "")),
        note=str(item.get("note", "")),
    )


def fetch_dataset_info(dataset_id: str) -> Optional[Dict[str, Any]]:
    """Get full metadata for a specific GWAS dataset by ID."""
    try:
        data = _get_json(f"{DEFAULT_BASE}/gwasinfo")
        if isinstance(data, dict):
            return data.get(dataset_id)
        return None
    except Exception as exc:
        logger.warning("gwasinfo failed for %s: %s", dataset_id, exc)
        return None


def fetch_tophits(
    dataset_id: str,
    pval_threshold: float = 5e-8,
    clump: bool = True,
    clump_r2: float = 0.001,
    clump_kb: int = 10000,
    pop: str = "EUR",
) -> pd.DataFrame:
    """
    Fetch top hits from a GWAS dataset with optional LD clumping.

    Uses /tophits endpoint (POST).
    """
    payload: Dict[str, Any] = {
        "id": dataset_id,
        "pval": pval_threshold,
        "clump": 1 if clump else 0,
        "r2": clump_r2,
        "kb": clump_kb,
        "pop": pop,
    }
    try:
        data = _post_json(f"{DEFAULT_BASE}/tophits", data=payload, timeout=60.0)
        if isinstance(data, dict) and "data" in data:
            return pd.DataFrame(data["data"])
        if isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame()
    except Exception as exc:
        logger.warning("tophits failed for %s: %s", dataset_id, exc)
        raise


def fetch_associations(
    dataset_id: str,
    variants: List[str],
    batch_size: int = 64,
) -> pd.DataFrame:
    """
    Fetch association statistics for specific variants from a GWAS.

    Uses /associations endpoint (POST). Batched: max 64 variants/request
    (API constraint: N(id) * N(variant) <= 64).
    """
    all_results = []
    for i in range(0, len(variants), batch_size):
        batch = variants[i:i + batch_size]
        try:
            data = _post_json(
                f"{DEFAULT_BASE}/associations",
                data={"id": dataset_id, "variant": batch},
                timeout=60.0,
            )
            if isinstance(data, list):
                all_results.extend(data)
            elif isinstance(data, dict) and "data" in data:
                all_results.extend(data["data"])
        except Exception as exc:
            logger.warning("associations batch %d failed for %s: %s", i // batch_size, dataset_id, exc)

    if not all_results:
        raise RuntimeError(f"No associations returned for {dataset_id}")

    logger.info("Fetched %d associations for %s in %d batches",
                len(all_results), dataset_id, (len(variants) + batch_size - 1) // batch_size)
    return pd.DataFrame(all_results)


def fetch_sumstats(dataset_id: str) -> pd.DataFrame:
    """
    Fetch full summary statistics for a dataset.

    For large datasets, this downloads via /gwasinfo/files endpoint.
    Falls back to tophits if full download is unavailable.
    """
    # Try getting file-level metadata first
    try:
        files_data = _get_json(
            f"{DEFAULT_BASE}/gwasinfo/files",
            params={"id": dataset_id},
        )
        if isinstance(files_data, list) and len(files_data) > 0:
            first = files_data[0]
            download_url = first.get("url") or first.get("download_url") or first.get("file_url", "")
            if download_url:
                logger.info("Downloading sumstats from: %s", download_url)
                with _client(timeout=120.0) as client:
                    resp = client.get(download_url)
                    resp.raise_for_status()
                    return pd.read_csv(
                        io.BytesIO(resp.content),
                        compression="infer" if download_url.endswith(".gz") else None,
                        sep=None,
                        engine="python",
                    )
    except Exception as exc:
        logger.warning("gwasinfo/files download failed: %s, falling back to tophits", exc)

    # Fallback: use tophits with lenient threshold to get many SNPs
    logger.info("Falling back to /tophits for dataset %s", dataset_id)
    return fetch_tophits(dataset_id, pval_threshold=1.0, clump=False)


def list_batches() -> List[Dict[str, Any]]:
    """List available data batches (no auth required)."""
    try:
        return _get_json(f"{DEFAULT_BASE}/batches")
    except Exception as exc:
        logger.warning("batches failed: %s", exc)
        return []


def find_best_match(
    trait: str,
    ancestry: str = "European",
    min_sample_size: int = 5000,
) -> Optional[GWASDataset]:
    """
    Find the best-matching GWAS dataset for a trait.
    Prioritizes: larger sample size, ancestry match, clearer phenotype definition.

    Loads all ~50k datasets and filters client-side.
    """
    result = search(trait, limit=50)
    if not result.datasets:
        return None

    scored = []
    for ds in result.datasets:
        if ds.sample_size < min_sample_size:
            continue
        ancestry_lower = ds.ancestry.lower() if ds.ancestry else ""
        ancestry_match = ancestry.lower() in ancestry_lower
        # Smart ancestry scoring: exact match > contains > different
        if ancestry_lower == ancestry.lower():
            ancestry_bonus = 2
        elif ancestry_match:
            ancestry_bonus = 1
        else:
            ancestry_bonus = 0
        score = (ancestry_bonus * 100_000_000) + ds.sample_size + ds.year
        scored.append((score, ds))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else None


def validate_token() -> Optional[Dict[str, Any]]:
    """Validate the JWT token and return user info (0 credits)."""
    try:
        return _get_json(f"{DEFAULT_BASE}/user")
    except Exception as exc:
        logger.warning("Token validation failed: %s", exc)
        return None
