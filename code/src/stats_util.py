"""
stats_util.py — small, dependency-light statistics used across the analysis.

All functions are pure and deterministic. Wilson intervals, Cohen's kappa,
PABAK, and a linear-by-linear (Cochran-Armitage-style) trend z are implemented
here so the results do not depend on library-version-specific defaults.
"""
import math


def wilson(k, n, z=1.96):
    """Wilson score interval for a binomial proportion. Returns (p, lo, hi)."""
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, centre - half, centre + half


def confusion(model, human, label):
    """2x2 counts treating the independent (human) code as reference.
    FP = model-positive/independent-negative; FN = model-negative/independent-positive."""
    tp = fp = fn = tn = 0
    for c in model:
        m = model[c][label]
        h = human[c][label]
        if m and h:
            tp += 1
        elif m and not h:
            fp += 1
        elif not m and h:
            fn += 1
        else:
            tn += 1
    return tp, fp, fn, tn


def prf(tp, fp, fn):
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    rec = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if (prec and rec and (prec + rec)) else float("nan")
    return prec, rec, f1


def kappa_pabak(tp, fp, fn, tn):
    """Cohen's kappa and PABAK from a 2x2 table."""
    n = tp + fp + fn + tn
    if n == 0:
        return float("nan"), float("nan")
    po = (tp + tn) / n
    pe = ((tp + fp) / n) * ((tp + fn) / n) + ((fn + tn) / n) * ((fp + tn) / n)
    kappa = (po - pe) / (1 - pe) if (1 - pe) else float("nan")
    pabak = 2 * po - 1
    return kappa, pabak


def linear_trend_z(x, y):
    """Linear-by-linear association z for an ordinal score x vs binary y."""
    n = len(y)
    xb = sum(x) / n
    yb = sum(y) / n
    sxy = sum((xi - xb) * (yi - yb) for xi, yi in zip(x, y))
    sxx = sum((xi - xb) ** 2 for xi in x)
    syy = sum((yi - yb) ** 2 for yi in y)
    if sxx == 0 or syy == 0:
        return float("nan")
    r = sxy / math.sqrt(sxx * syy)
    return r * math.sqrt(n - 1)
