# Should we keep running these ads? An A/B test analysis on 14M users

Analysis of a **real randomized advertising experiment** (Criteo's public uplift dataset,
13,979,592 users) from raw data to a ship/no-ship recommendation: SQL in DuckDB,
validity checks, confidence intervals, power analysis, CUPED variance reduction,
intent-to-treat vs effect-on-exposed, and a break-even decision under stated assumptions.

## Key results

| | Control (no ads) | Treatment (ads) | Absolute lift [95% CI] | Relative lift [95% CI] |
|---|---|---|---|---|
| Users | 2,096,937 (15%) | 11,882,655 (85%) | | |
| **Visit rate** | 3.82% | 4.85% | **+1.03 pts** [+1.01, +1.06] | **+27.1%** [+26.2%, +28.0%] |
| **Conversion rate** | 0.194% | 0.309% | **+0.115 pts** [+0.109, +0.122] | **+59.4%** [+54.4%, +64.7%] |

- **Validity:** sample ratio mismatch check passed (85.000% vs 85% design, χ² p = 0.999).
- **Power:** the test could detect lifts as small as **1.05%** (visits) and **4.76%** (conversions) relative; observed effects are 12–26× larger.
- **Effect on users who actually saw an ad** (only 3.6% of the treatment group): **+28.7 pts** visits, **+3.20 pts** conversions.
- **Decision:** the campaign pays for itself when a conversion is worth more than roughly **31–39× the cost of showing ads to one user** (see [decision memo](docs/decision_memo.md)).

## What I checked, and what I found

| Step | Script | Finding |
|---|---|---|
| 1. Load + compare groups (SQL) | `analysis/01_load.py` | 14M rows into DuckDB; group rates with window functions |
| 2. SRM + lifts with CIs | `analysis/02_effects.py` | Valid split; delta-method CI for relative lift |
| 3. Power / MDE | `analysis/03_power.py` | Conversions need ~20× more users than visits for the same relative lift; the 85/15 split costs ~2× the users of 50/50 |
| 4. CUPED (cross-fitted) | `analysis/04_cuped.py` | Variance −25% (visits), −11% (conversions), **but the point estimate moved** (+1.03 → +0.70 pts visits) |
| 5. Covariate balance | `analysis/05_balance.py` | 9 of 12 pre-experiment features differ (max SMD 0.049 vs ~0.0008 expected by chance) |
| 6. Exposure: ITT vs CACE | `analysis/06_exposure.py` | Naive exposed-vs-unexposed comparison overstates the visit effect by about a third (selection bias) |
| 7. Break-even decision | `analysis/07_decision.py` | Break-even conversion value under labelled cost assumptions |

### The most important finding: an imbalance that a single number would hide
In a clean randomized test, CUPED should shrink the confidence interval **without moving the estimate**.
Here it moved the visit lift by about a third, so I checked covariate balance and found small but
systematic differences between groups. The dataset's authors assembled it from several experiments and
re-sampled them to a common 85% treatment ratio to remove a test-level confounder found in v1; a residual
imbalance from that process, or features influenced by the ads, are both possible explanations. I therefore
report the unadjusted intent-to-treat estimate as primary and the adjusted estimate as a sensitivity check:
**the effect is clearly positive under both; its exact size is less certain.**

## Limitations
- This is an analysis of public experimental data; I did not design or run the experiment.
- The data has no costs or revenues; the decision uses **explicitly labelled assumptions**.
- Features are anonymized, so the source of the covariate imbalance cannot be identified.
- The effect on exposed users (CACE) assumes assignment affects outcomes only through ad exposure.

## Run it
```bash
pip install -r requirements.txt
mkdir -p data && curl -L -o data/criteo-uplift-v2.1.csv.gz \
  "https://huggingface.co/datasets/criteo/criteo-uplift/resolve/main/criteo-research-uplift-v2.1.csv.gz"
for s in analysis/0*.py; do python "$s"; done
```

## Data and credit
Criteo Uplift Prediction Dataset v2.1 (Diemert et al., *A Large Scale Benchmark for Individual Treatment
Effect Prediction and Uplift Modeling*). The raw data is not stored in this repository.

Built by **Shirisha Gajendra** · MS Data Science, Stony Brook University
