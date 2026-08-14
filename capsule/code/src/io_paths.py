"""
io_paths.py — resolve data/results roots for both Code Ocean and local runs.

On Code Ocean the capsule mounts /code, /data, /results. Locally the repository
root holds data/ and results/. This module returns absolute paths that work in
both, so every analysis script is location-independent.
"""
from pathlib import Path
import os


def _first_existing(*cands):
    for c in cands:
        if c and Path(c).exists():
            return Path(c)
    return None


def data_root() -> Path:
    env = os.environ.get("P10_DATA")
    root = _first_existing(env, "/data", Path(__file__).resolve().parents[2] / "data")
    if root is None:
        raise FileNotFoundError("data directory not found (looked for $P10_DATA, /data, ../../data)")
    return root


def results_root() -> Path:
    env = os.environ.get("P10_RESULTS")
    for c in (env, "/results"):
        if c and Path(c).exists():
            return Path(c)
    # local default: <repo>/results
    r = Path(__file__).resolve().parents[2] / "results"
    r.mkdir(parents=True, exist_ok=True)
    return r


def out_dir() -> Path:
    """Directory for this run's outputs (tables/, figures/, metrics_summary.md)."""
    od = os.environ.get("P10_OUT_DIR")
    d = Path(od) if od else results_root()
    (d / "tables").mkdir(parents=True, exist_ok=True)
    (d / "figures").mkdir(parents=True, exist_ok=True)
    return d
