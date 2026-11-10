"""Write a small synthetic file with the same columns as the Criteo data.
Used only by CI to check that the Docker image runs every step end to end."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(0)
n = 200_000
df = pd.DataFrame({f"f{i}": rng.normal(size=n) for i in range(12)})
df["treatment"] = (rng.random(n) < 0.85).astype(int)
df["exposure"] = np.where(df.treatment == 1, (rng.random(n) < 0.04).astype(int), 0)
df["visit"] = (rng.random(n) < 0.04 + 0.01 * df.exposure).astype(int)
df["conversion"] = ((rng.random(n) < 0.02 * df.exposure + 0.003) & (df.visit == 1)
                    | (rng.random(n) < 0.002)).astype(int)
df.to_csv("sample/criteo-uplift-v2.1.csv.gz", index=False, compression="gzip")
print(f"Wrote {n:,} synthetic rows to sample/")
