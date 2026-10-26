"""Is the split valid (SRM), and how big is the lift, with confidence intervals?"""
import duckdb
import numpy as np
from scipy import stats

EXPECTED_TREATMENT_SHARE = 0.85   # the design ratio Criteo published
con = duckdb.connect("data/criteo.duckdb", read_only=True)

# One row per group: users, visits, conversions (all counted in SQL)
rows = con.sql("""
    SELECT treatment, COUNT(*) AS n, SUM(visit) AS visits, SUM(conversion) AS conversions
    FROM criteo GROUP BY treatment ORDER BY treatment
""").fetchall()
groups = {t: {"n": n, "visit": v, "conversion": c} for t, n, v, c in rows}
n_c, n_t = groups[0]["n"], groups[1]["n"]

# 1) Sample ratio mismatch: chi-square test of the observed split vs 85/15
total = n_c + n_t
expected = [total * (1 - EXPECTED_TREATMENT_SHARE), total * EXPECTED_TREATMENT_SHARE]
chi2, p_srm = stats.chisquare([n_c, n_t], f_exp=expected)
print("=== Sample ratio mismatch (SRM) check ===")
print(f"Treatment share: {n_t / total:.5f} (expected {EXPECTED_TREATMENT_SHARE})")
print(f"Chi-square = {chi2:.2f}, p = {p_srm:.4f} ->",
      "OK, split looks valid" if p_srm >= 0.001 else "SRM! Do not trust results")

# 2) Effect of ads on each metric
print("\n=== Effect of showing ads (intent-to-treat) ===")
for metric in ("visit", "conversion"):
    p_c = groups[0][metric] / n_c
    p_t = groups[1][metric] / n_t
    diff = p_t - p_c
    se = np.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    lo, hi = diff - 1.96 * se, diff + 1.96 * se
    # two-proportion z-test (pooled standard error under "no effect")
    p_pool = (groups[0][metric] + groups[1][metric]) / total
    se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_t))
    z = diff / se_pool
    p_value = 2 * stats.norm.sf(abs(z))
    # relative lift with a delta-method interval on the log ratio
    log_ratio = np.log(p_t / p_c)
    se_log = np.sqrt((1 - p_t) / (n_t * p_t) + (1 - p_c) / (n_c * p_c))
    rel_lo, rel_hi = np.exp(log_ratio - 1.96 * se_log) - 1, np.exp(log_ratio + 1.96 * se_log) - 1
    print(f"\n{metric.upper()}")
    print(f"  control {100 * p_c:.4f}%  vs  treatment {100 * p_t:.4f}%")
    print(f"  absolute lift: {100 * diff:+.4f} pts   95% CI [{100 * lo:+.4f}, {100 * hi:+.4f}]")
    print(f"  relative lift: {100 * (p_t / p_c - 1):+.1f}%   95% CI [{100 * rel_lo:+.1f}%, {100 * rel_hi:+.1f}%]")
    print(f"  z = {z:.1f}, p-value = {p_value:.2e}")
