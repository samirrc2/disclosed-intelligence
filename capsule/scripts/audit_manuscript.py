#!/usr/bin/env python3
"""Manuscript-wide numerical consistency audit (source of truth).

Recomputes every headline value from the frozen inputs and asserts it equals the
value stated in the manuscript. Fails loudly on any mismatch so the paper, tables,
figures, and code cannot drift apart. Run: python3 scripts/audit_manuscript.py

Frozen inputs (pseudonymized) live under the Code Ocean capsule's data/ directory;
set P10_DATA or run from the capsule root.
"""
import csv
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def find_data():
    for c in (os.environ.get("P10_DATA"), ROOT / "codeocean" / "data",
              ROOT / "data", Path("/data")):
        if c and Path(c).exists() and (Path(c) / "labels_primary.csv").exists():
            return Path(c)
    sys.exit("ERROR: data directory not found (set P10_DATA to the capsule's data/).")


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * p, 1), round(100 * (c - h), 1), round(100 * (c + h), 1)


def kappa_pabak(tp, fp, fn, tn):
    n = tp + fp + fn + tn
    po = (tp + tn) / n
    pe = ((tp + fp) / n) * ((tp + fn) / n) + ((fn + tn) / n) * ((fp + tn) / n)
    return round((po - pe) / (1 - pe), 3)


DATA = find_data()
key = "fid" if "fid" in next(iter(csv.DictReader(open(DATA / "labels_primary.csv")))) else "crd"

prim = {r[key]: {c: int(r[c]) for c in "abcde"} for r in csv.DictReader(open(DATA / "labels_primary.csv"))}
ind = {r[key]: {c: int(r[c]) for c in "abcde"} for r in csv.DictReader(open(DATA / "labels_independent.csv"))}

N = len(prim)
anyuse = sum(1 for v in prim.values() if v["a"] or v["b"] or v["e"])
mention = sum(1 for v in prim.values() if any(v[c] for c in "abcde"))
risk = sum(v["c"] for v in prim.values())

# --- design-weighted any-use validation (two-phase verification sample) ---
ment = {k: int(any(prim[k][c] for c in "abcde")) for k in prim}
n_neg_pop = sum(1 for k in ment if ment[k] == 0)
keys = [k for k in ind if k in prim]
n_neg_samp = sum(1 for k in keys if ment[k] == 0)
wneg = n_neg_pop / n_neg_samp
w = {k: (1.0 if ment[k] else wneg) for k in keys}
au = lambda d: 1 if (d["a"] or d["b"] or d["e"]) else 0
tp = sum(w[k] for k in keys if au(prim[k]) and au(ind[k]))
fp = sum(w[k] for k in keys if au(prim[k]) and not au(ind[k]))
fn = sum(w[k] for k in keys if not au(prim[k]) and au(ind[k]))
tn = sum(w[k] for k in keys if not au(prim[k]) and not au(ind[k]))
val_prec = round(tp / (tp + fp), 3)
val_rec = round(tp / (tp + fn), 3)
val_kappa = kappa_pabak(tp, fp, fn, tn)

facts = {
    "N classified": N,
    "any-use rate% (Wilson)": wilson(anyuse, N),
    "any-mention rate% (Wilson)": wilson(mention, N),
    "risk-factor rate% (Wilson)": wilson(risk, N),
    "validation any-use precision": val_prec,
    "validation any-use recall": val_rec,
    "validation any-use kappa": val_kappa,
    "validation n": len(keys),
}

# What the MANUSCRIPT states (single source of truth to keep in sync)
manuscript = {
    "N classified": 388,
    "any-use rate% (Wilson)": (23.7, 19.7, 28.2),
    "any-mention rate% (Wilson)": (31.7, 27.3, 36.5),
    "risk-factor rate% (Wilson)": (27.6, 23.4, 32.2),
    "validation any-use precision": 0.761,
    "validation any-use recall": 0.837,
    "validation any-use kappa": 0.738,
    "validation n": 180,
}

print(f"{'FACT':32s} {'RECOMPUTED':>20s}  {'MANUSCRIPT':>20s}  OK")
print("-" * 80)
ok = True
for k, mval in manuscript.items():
    fval = facts[k]
    match = fval == mval
    ok &= match
    print(f"{k:32s} {str(fval):>20s}  {str(mval):>20s}  {'OK' if match else 'FAIL'}")

print("\n" + ("AUDIT PASS — manuscript numbers match the frozen data."
              if ok else "AUDIT FAIL — mismatch(es) above."))
sys.exit(0 if ok else 1)
