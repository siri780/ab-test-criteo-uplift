"""Covariate balance: are the 12 pre-experiment features the same in both groups?

In a clean randomized test, standardized mean differences (SMD) should be
tiny (well under 0.01 with millions of users). A larger gap means the groups
differ before treatment, which would bias simple comparisons, or that a
feature is affected by the treatment itself.
"""
import duckdb

FEATURES = [f"f{i}" for i in range(12)]
con = duckdb.connect("data/criteo.duckdb", read_only=True)

parts = []
for f in FEATURES:
    parts.append(f"""
        SELECT '{f}' AS feature,
               AVG({f}) FILTER (WHERE treatment = 0)        AS mean_control,
               AVG({f}) FILTER (WHERE treatment = 1)        AS mean_treatment,
               STDDEV_SAMP({f}) FILTER (WHERE treatment = 0) AS sd_control,
               STDDEV_SAMP({f}) FILTER (WHERE treatment = 1) AS sd_treatment
        FROM criteo""")
balance = con.execute(" UNION ALL ".join(parts)).df()
balance["smd"] = (balance.mean_treatment - balance.mean_control) / (
    ((balance.sd_control**2 + balance.sd_treatment**2) / 2) ** 0.5)
balance["flag"] = balance.smd.abs().map(
    lambda s: "IMBALANCED" if s >= 0.05 else ("check" if s >= 0.01 else "ok"))
print(balance.round(4).to_string(index=False))
print(f"\nLargest |SMD|: {balance.smd.abs().max():.4f}")
