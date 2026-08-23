# U.S. Retail Sales Forecasting

A time series project forecasting national monthly retail sales 12 months ahead using Facebook
Prophet, validated against a held-out year that happens to contain a major demand shock.

## Problem

Retail planning — inventory, staffing, capital allocation — runs on a forward view of demand.
Monthly national retail sales carry both a long-run trend and strong annual seasonality, which
makes them a good test of whether a model captures structure or just fits noise. The question here
was whether a decomposition-based forecaster could produce a usable 12-month view, and how badly it
degrades when the test window contains a period nothing in the training data resembles.

## Data

**U.S. monthly retail sales, 1992–2021** — 30 years of national totals, published in wide format
(one row per year, one column per month).

| File | Description |
|---|---|
| `data/us_retail_sales.csv` | Monthly retail sales, wide format as published |

## Approach

1. **Reshape.** The source arrives wide (`YEAR` + twelve month columns). Melted it to long format
   and constructed a proper datetime from the year and month-abbreviation columns, giving one row
   per month — the shape every time series library expects.
2. **Inspect.** Plotted the full 1992–2021 series to confirm the trend and the year-end seasonal
   peaks before modeling anything.
3. **Split by time, not at random.** Training on everything before July 2020, testing on
   July 2020 – June 2021. A random split would leak future information into training and produce a
   meaningless score.
4. **Model.** Fit Prophet, which decomposes the series into trend plus seasonality, then generated
   a 12-month forward forecast with uncertainty intervals.
5. **Evaluate.** RMSE on the held-out year, plus an actual-vs-predicted plot for the test window.
6. **Baseline.** A separate notebook fits a simple linear regression on the same series as a
   sanity check — a forecast is only interesting if it beats the trivial alternative.

## Key findings

- Prophet achieved **RMSE of $57,238** on the held-out year against a series running in the
  hundreds of thousands, and reproduced both the long-run upward trend and the annual seasonal
  shape.
- **The test window is the interesting part.** July 2020 – June 2021 covers pandemic-era retail
  behavior — a demand pattern with no analogue in 28 years of training data. The error is
  concentrated there, which is the honest story: the model captures structure well and cannot
  anticipate a regime change. That is a property of forecasting, not a bug in this model.
- Time-based splitting and the wide-to-long reshape are the two steps that matter most here.
  Both are easy to get wrong, and both invalidate everything downstream when you do.

## What's in this folder

```
code/          Prophet forecasting notebook, plus a linear regression baseline
data/          30 years of monthly national retail sales
deliverables/  Exported notebook PDF
```

## Tools

Python · Prophet · pandas · NumPy · scikit-learn (metrics) · matplotlib

## Notes and limitations

- Single national series — no category, region, or channel breakdown, so it says nothing about
  *which* retail segments drive the movement.
- Prophet's uncertainty intervals assume future volatility resembles past volatility, which the
  test window itself demonstrates is not always true.
- No exogenous regressors (holidays beyond Prophet's defaults, promotions, macro indicators).
  Adding them is the obvious next iteration.
