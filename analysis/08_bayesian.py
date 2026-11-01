"""Bayesian view of the same experiment: how likely is it that ads help,
and by how much? Beta-Binomial model, with a prior-sensitivity check."""
import duckdb
import numpy as np

DRAWS = 200_000
rng = np.random.default_rng(42)

con = duckdb.connect("data/criteo.duckdb", read_only=True)
rows = con.sql("""
    SELECT treatment, COUNT(*) AS n, SUM(visit) AS visits, SUM(conversion) AS conversions
    FROM criteo GROUP BY treatment ORDER BY treatment
""").fetchall()
groups = {t: {"n": n, "visit": v, "conversion": c} for t, n, v, c in rows}


def posterior(successes, n, prior_a, prior_b):
    """Draws from the Beta posterior of a conversion rate."""
    return rng.beta(prior_a + successes, prior_b + n - successes, DRAWS)


def summarize(metric, prior_name, prior):
    c, t = groups[0], groups[1]
    p_c = posterior(c[metric], c["n"], *prior(c[metric] / c["n"]))
    p_t = posterior(t[metric], t["n"], *prior(c[metric] / c["n"]))
    diff = p_t - p_c
    rel = p_t / p_c - 1
    # Expected loss: average shortfall if we ship ads and they are actually worse
    loss_ship = np.maximum(p_c - p_t, 0).mean()
    lo, hi = np.percentile(diff, [2.5, 97.5])
    rlo, rhi = np.percentile(rel, [2.5, 97.5])
    print(f"{metric:<10} {prior_name:<22} P(ads better) = {(diff > 0).mean():.4f}   "
          f"lift = {100 * diff.mean():.3f} pts [{100 * lo:.3f}, {100 * hi:.3f}]   "
          f"relative = {100 * rel.mean():.1f}% [{100 * rlo:.1f}, {100 * rhi:.1f}]   "
          f"expected loss if shipped = {loss_ship:.2e}")
    return rel


PRIORS = {
    # Flat: every rate between 0 and 1 equally likely before seeing data
    "flat Beta(1,1)": lambda base: (1, 1),
    # Skeptical: centred on the control rate, worth 100,000 users of evidence,
    # i.e. we start out believing ads probably do nothing
    "skeptical (100k users)": lambda base: (base * 100_000, (1 - base) * 100_000),
}

print("=== Bayesian A/B results (intent-to-treat) ===")
results = {}
for metric in ("visit", "conversion"):
    for name, prior in PRIORS.items():
        results[(metric, name)] = summarize(metric, name, prior)

# Decision-relevant question: how likely is the relative lift above a threshold?
print("\n=== Probability the relative conversion lift exceeds a threshold ===")
rel = results[("conversion", "flat Beta(1,1)")]
for threshold in (0.25, 0.50, 0.60):
    print(f"P(lift > {threshold:.0%}) = {(rel > threshold).mean():.3f}")
