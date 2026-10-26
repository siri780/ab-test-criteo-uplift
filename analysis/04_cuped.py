"""CUPED-style variance reduction using the 12 pre-experiment features (f0-f11).

Idea: part of each user's outcome is predictable from features measured BEFORE
the experiment. Subtracting that predictable part leaves the treatment effect
unchanged (randomization makes features independent of treatment) but removes
noise, so confidence intervals shrink. We predict with a linear model fitted by
2-fold cross-fitting, so no user's prediction uses their own outcome.
"""
import duckdb
import numpy as np

FEATURES = [f"f{i}" for i in range(12)]
con = duckdb.connect("data/criteo.duckdb", read_only=True)
df = con.execute(f"""
    SELECT {", ".join(f"CAST({f} AS FLOAT) AS {f}" for f in FEATURES)},
           CAST(treatment AS TINYINT) AS treatment,
           CAST(visit AS FLOAT) AS visit,
           CAST(conversion AS FLOAT) AS conversion
    FROM criteo
""").df()
X = df[FEATURES].to_numpy(dtype=np.float32)
t = df["treatment"].to_numpy() == 1
rng = np.random.default_rng(42)
fold = rng.integers(0, 2, len(df))          # random 2-fold split


def fit_linear(X, y, rows, chunk=1_000_000):
    """Least squares via chunked normal equations (memory friendly)."""
    k = X.shape[1] + 1
    xtx, xty = np.zeros((k, k)), np.zeros(k)
    idx = np.flatnonzero(rows)
    for s in range(0, len(idx), chunk):
        part = idx[s:s + chunk]
        A = np.hstack([np.ones((len(part), 1)), X[part].astype(np.float64)])
        xtx += A.T @ A
        xty += A.T @ y[part]
    return np.linalg.solve(xtx, xty)


def predict(X, beta, chunk=1_000_000):
    out = np.empty(len(X))
    for s in range(0, len(X), chunk):
        out[s:s + chunk] = beta[0] + X[s:s + chunk].astype(np.float64) @ beta[1:]
    return out


def diff_and_se(y):
    a, b = y[~t], y[t]
    return b.mean() - a.mean(), np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


for metric in ("visit", "conversion"):
    y = df[metric].to_numpy(dtype=np.float64)
    pred = np.empty(len(y))
    for k in (0, 1):                           # cross-fitting
        beta = fit_linear(X, y, fold != k)
        pred[fold == k] = predict(X[fold == k], beta)
    theta = np.cov(y, pred)[0, 1] / pred.var(ddof=1)
    y_cuped = y - theta * (pred - pred.mean())

    d0, se0 = diff_and_se(y)
    d1, se1 = diff_and_se(y_cuped)
    reduction = 1 - (se1 / se0) ** 2
    print(f"\n{metric.upper()}")
    print(f"  plain : lift {100 * d0:+.4f} pts, 95% CI ±{100 * 1.96 * se0:.4f}")
    print(f"  CUPED : lift {100 * d1:+.4f} pts, 95% CI ±{100 * 1.96 * se1:.4f}")
    print(f"  variance reduced by {100 * reduction:.1f}%  ->  same precision with "
          f"{100 * reduction:.1f}% fewer users")
