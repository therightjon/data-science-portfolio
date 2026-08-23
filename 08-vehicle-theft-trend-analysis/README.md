# Vehicle Theft Trend Analysis: A Targeted Problem or a General Rise?

A municipal public safety briefing that separates a specific, targeted theft phenomenon from
background growth in auto theft — and turns that distinction into a concrete resourcing
recommendation.

## Problem

When any crime category rises, the first question a city official has to answer is whether it
reflects a distinct, targetable problem or general drift in the overall rate. The two call for
completely different responses. This analysis tested whether the surge in Kia and Hyundai thefts
was a targeted vulnerability warranting focused intervention, or simply auto theft rising across
the board.

## Data

| File | Description |
|---|---|
| `data/vice-news-kia-hyundai-theft-data.xlsx` | Multi-city Kia/Hyundai theft dataset compiled by VICE News / Motherboard |
| `data/kia_hyundai_thefts.csv` | Kia/Hyundai theft counts |
| `data/kia_hyundai_milwaukee.csv` | Milwaukee-specific series |
| `data/car_thefts_map.csv` | Geographic theft distribution |

Coverage spans 2019–2022, which brackets the onset of the trend.

## Approach

Analysis and all visualization were done in **R** — the only R-based project in this portfolio.

1. Reshaped the multi-city dataset and normalized city and date fields.
2. Separated Kia/Hyundai thefts from all other vehicle thefts so the two series could be compared
   directly rather than inferred from a single total.
3. Built six chart types deliberately matched to different comparison tasks: stacked area for
   composition over time, donut for a single share, treemap for cross-city magnitude, stacked bar
   for per-city composition, and line for a focused local trend.
4. Framed the output as a policy briefing with a specific, costed ask.

## Key findings

- The rise in Kia/Hyundai thefts is **distinguishable from the general auto theft baseline** — the
  affected models grew as a share of total thefts rather than rising proportionally with everything
  else. This is what makes the problem targetable.
- Impact is **geographically concentrated**, with Milwaukee showing a pronounced local trend
  against the multi-city backdrop.
- Recommendation delivered: approve focused prevention measures — steering-wheel lock distribution,
  adjusted patrol allocation, and localized public awareness campaigns in high-impact jurisdictions.

## What's in this folder

```
code/          R analysis and visualization script (+ its exported output PDF)
data/          Multi-city theft dataset, city-level series, and geographic distribution
deliverables/  Public safety briefing deck (pptx/pdf) and written summary
figures/       Six exported charts
```

## Tools

R · ggplot2 · PowerPoint

## Notes and limitations

- Reported theft counts reflect **reporting practices as well as actual incidence**, and reporting
  standards vary by jurisdiction.
- No normalization by registered vehicle counts, so cities with more Kia/Hyundai vehicles on the
  road will show higher absolute numbers regardless of targeting.
- City coverage is limited to what the source dataset compiled; absence from the data is not
  evidence of absence of the problem.
