"""Was the test big enough? Minimum detectable effect and required sample sizes."""
import duckdb
import numpy as np
from scipy import stats
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

ALPHA, POWER = 0.05, 0.80
Z = stats.norm.ppf(1 - ALPHA / 2) + stats.norm.ppf(POWER)   # about 2.80

con = duckdb.connect("data/criteo.duckdb", read_only=True)
n_c, n_t, visit_c, conv_c = con.execute("""
    SELECT SUM(1 - treatment), SUM(treatment),
           AVG(visit) FILTER (WHERE treatment = 0),
           AVG(conversion) FILTER (WHERE treatment = 0)
    FROM criteo
""").fetchone()
n_c, n_t = int(n_c), int(n_t)
baselines = {"visit": visit_c, "conversion": conv_c}


def mde(p, n_c, n_t):
    """Smallest absolute lift this test could reliably detect."""
    return Z * np.sqrt(p * (1 - p) * (1 / n_c + 1 / n_t))


def users_needed(p, rel_lift, treat_share):
    """Total users needed to detect a relative lift with a given split."""
    delta = p * rel_lift
    return Z**2 * p * (1 - p) * (1 / treat_share + 1 / (1 - treat_share)) / delta**2


print(f"Alpha = {ALPHA}, power = {POWER}; control n = {n_c:,}, treatment n = {n_t:,}\n")
print("=== 1) Minimum detectable effect (MDE) of THIS test ===")
for metric, p in baselines.items():
    m = mde(p, n_c, n_t)
    print(f"{metric:>10}: baseline {100 * p:.4f}%  ->  MDE {100 * m:.4f} pts "
          f"({100 * m / p:.2f}% relative)")

print("\n=== 2) Users needed to detect a given relative lift ===")
print(f"{'metric':>10} {'lift':>6} {'85/15 split':>14} {'50/50 split':>14}")
for metric, p in baselines.items():
    for lift in (0.05, 0.10, 0.20):
        a = users_needed(p, lift, 0.85)
        b = users_needed(p, lift, 0.50)
        print(f"{metric:>10} {lift:>6.0%} {a:>14,.0f} {b:>14,.0f}")

# Cross-check one number with statsmodels (Cohen's h effect size)
p = baselines["conversion"]
h = proportion_effectsize(p * 1.10, p)
n1 = NormalIndPower().solve_power(effect_size=h, alpha=ALPHA, power=POWER, ratio=1.0)
print(f"\nCheck (statsmodels, conversion +10%, 50/50): {2 * n1:,.0f} users in total")
