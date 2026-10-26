"""Assigned vs actually exposed: intent-to-treat and the effect on exposed users.

Only some users in the treatment group actually saw an ad. That gives three
different numbers:
  1) ITT  - effect of ASSIGNING users to ads (what launching the campaign does)
  2) CACE - effect on users who would actually see an ad (ITT / exposure rate),
            valid because control users can never be exposed (assignment is
            random and only affects outcomes through exposure)
  3) Naive exposed-vs-unexposed comparison - biased, because users who end up
            seeing ads differ from users who don't (selection bias)
"""
import duckdb
import numpy as np

con = duckdb.connect("data/criteo.duckdb", read_only=True)

print("=== Exposure by group ===")
print(con.sql("""
    SELECT treatment, COUNT(*) AS users, SUM(exposure) AS exposed,
           ROUND(100.0 * AVG(exposure), 3) AS exposure_rate_pct
    FROM criteo GROUP BY treatment ORDER BY treatment
"""))

stats_by_group = {
    t: (n, e, v, c) for t, n, e, v, c in con.execute("""
        SELECT treatment, COUNT(*), AVG(exposure), AVG(visit), AVG(conversion)
        FROM criteo GROUP BY treatment
    """).fetchall()
}
n_c, e_c, *_ = stats_by_group[0]
n_t, e_t, *_ = stats_by_group[1]
first_stage = e_t - e_c                                  # share made exposed by assignment
se_fs = np.sqrt(e_t * (1 - e_t) / n_t + e_c * (1 - e_c) / n_c)

for i, metric in ((2, "visit"), (3, "conversion")):
    p_c, p_t = stats_by_group[0][i], stats_by_group[1][i]
    itt = p_t - p_c
    se_itt = np.sqrt(p_t * (1 - p_t) / n_t + p_c * (1 - p_c) / n_c)
    cace = itt / first_stage
    # delta method (ignores the small covariance between ITT and first stage)
    se_cace = np.sqrt(se_itt**2 / first_stage**2 + itt**2 * se_fs**2 / first_stage**4)
    print(f"\n{metric.upper()}")
    print(f"  ITT  (assigned to ads):        {100 * itt:+.3f} pts  "
          f"95% CI [{100 * (itt - 1.96 * se_itt):+.3f}, {100 * (itt + 1.96 * se_itt):+.3f}]")
    print(f"  CACE (effect on exposed users): {100 * cace:+.2f} pts  "
          f"95% CI [{100 * (cace - 1.96 * se_cace):+.2f}, {100 * (cace + 1.96 * se_cace):+.2f}]")

print("\n=== Why NOT to compare exposed vs unexposed directly (selection bias) ===")
print(con.sql("""
    SELECT CASE WHEN treatment = 0 THEN 'control (never exposed)'
                WHEN exposure = 1 THEN 'treatment, exposed'
                ELSE 'treatment, not exposed' END AS segment,
           COUNT(*) AS users,
           ROUND(100.0 * AVG(visit), 3)      AS visit_rate_pct,
           ROUND(100.0 * AVG(conversion), 4) AS conversion_rate_pct,
           ROUND(AVG(f3), 3) AS avg_f3, ROUND(AVG(f6), 3) AS avg_f6
    FROM criteo GROUP BY segment ORDER BY segment
"""))
