"""Turn the effect into a business decision: break-even value of a conversion.

The data has no costs or revenues, so we use clearly LABELLED ASSUMPTIONS for
the cost of showing ads to one user, and solve for the conversion value at
which the campaign breaks even. Results are per 1,000,000 users assigned.
"""
from pathlib import Path

import duckdb
import numpy as np

PER = 1_000_000
COST_PER_EXPOSED_USER = [0.10, 0.25, 0.50, 1.00]   # assumption, in dollars
CUPED_CONVERSION_LIFT = 0.000916                   # from 04_cuped.py (sensitivity)

con = duckdb.connect("data/criteo.duckdb", read_only=True)
(n_c, p_c), (n_t, p_t) = con.execute("""
    SELECT COUNT(*), AVG(conversion) FROM criteo GROUP BY treatment ORDER BY treatment
""").fetchall()
exposure_rate = con.execute(
    "SELECT AVG(exposure) FROM criteo WHERE treatment = 1").fetchone()[0]

itt = p_t - p_c
se = np.sqrt(p_t * (1 - p_t) / n_t + p_c * (1 - p_c) / n_c)
scenarios = {
    "ITT estimate": itt,
    "ITT lower 95% bound": itt - 1.96 * se,
    "CUPED estimate (conservative)": CUPED_CONVERSION_LIFT,
}
exposed = exposure_rate * PER

lines = [
    f"Per {PER:,} users assigned to ads: {exposed:,.0f} actually see an ad.",
    "",
    "| Lift estimate | Extra conversions | " + " | ".join(
        f"Break-even @ ${c:.2f}/exposed user" for c in COST_PER_EXPOSED_USER) + " |",
    "|---|---|" + "---|" * len(COST_PER_EXPOSED_USER),
]
for name, lift in scenarios.items():
    extra = lift * PER
    cells = [f"${c * exposed / extra:,.2f}" for c in COST_PER_EXPOSED_USER]
    lines.append(f"| {name} | {extra:,.0f} | " + " | ".join(cells) + " |")

table = "\n".join(lines)
print(table)
Path("results").mkdir(exist_ok=True)
Path("results/decision_table.md").write_text(table + "\n")
print("\nSaved to results/decision_table.md")
