# Decision memo: keep running the ad campaign?

**To:** Marketing leadership · **From:** Shirisha Gajendra, Data Science · **Data:** randomized test, 13,979,592 users

## Recommendation
**Keep the campaign running, provided an average conversion is worth more than about 31–39× what it costs
to show ads to one user.** At $0.25 per exposed user that is roughly **$8–10 per conversion**.
Before scaling spend further, confirm the conversion value with finance and re-run a clean test to
narrow the effect size (see "Open risk").

## Evidence
- Users assigned to ads converted at **0.309% vs 0.194%** without ads: **+0.115 percentage points**
  (95% CI +0.109 to +0.122), a **59% relative increase**. Visits rose **27%**.
- The test was valid (no sample ratio mismatch) and far larger than needed to detect effects this size.
- Only **3.6%** of assigned users actually saw an ad; among them the conversion effect is about
  **+3.2 percentage points**. The campaign's value depends on reaching more of the right users.

## What it is worth (per 1,000,000 users assigned)
36,037 users see an ad and the campaign generates **about 1,150 extra conversions**
(916 under the most conservative estimate).

| Cost per exposed user (assumption) | $0.10 | $0.25 | $0.50 | $1.00 |
|---|---|---|---|---|
| Break-even value per conversion (main estimate) | $3.13 | $7.82 | $15.64 | $31.29 |
| Break-even value (conservative, CUPED-adjusted) | $3.93 | $9.84 | $19.67 | $39.34 |

If the true conversion value is above the break-even figure for your actual cost, the campaign is profitable.

## Open risk
The pre-experiment user features are slightly imbalanced between groups. Adjusting for them lowers the
estimated effect by about 20–33%, though it stays clearly positive. The recommendation above holds under
both estimates, but the size of the return is uncertain within that range.

## Next steps
1. Get the actual cost per exposed user and average conversion value, and plug them into the table.
2. Run a fresh randomized test with pre-registered balance checks to pin down the effect size.
3. Investigate targeting: exposed users behave very differently, so better targeting may raise the return.
