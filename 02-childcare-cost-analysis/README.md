# Childcare Cost Analysis: Where Families Pay the Most

A multi-format data storytelling project that turns a county-level childcare pricing dataset into
an interactive dashboard, a one-page infographic, and an executive slide deck — one message
delivered three ways for three different reading contexts.

## Problem

Childcare is one of the largest line items in a working family's budget, but published price data
sits in a technical government dataset that most parents will never open. The goal was to make
county-level childcare costs legible to the people actually paying them: how price changes as a
child ages, how provider type affects cost, and how much of the difference is simply geography.

## Data

**National Database of Childcare Prices (NDCP)** — U.S. Department of Labor, Women's Bureau.
County-level weekly price estimates spanning 2008–2018, broken out by four child age groups
(infant, toddler, preschool, school-age) and two provider types (center-based and family childcare).
2018 is used as the primary story year.

> The source workbook (~35 MB) is not committed here. Download it from the Women's Bureau NDCP
> release, along with its technical guide, to reproduce the dashboard inputs.

## Approach

1. Cleaned and reshaped the county-level price file, retaining the dataset's own imputed values as
   documented in the technical guide rather than silently dropping or re-imputing them.
2. Computed medians and percentile spreads by age group, provider type, and county.
3. Estimated budget burden as a share of county median household income (MHI) for local context.
4. Designed three deliverables around one shared visual system — a restrained blue palette,
   consistent hierarchy, and chart types chosen for clarity over novelty — so the message stays
   identical while the format adapts to how each medium is consumed.

## Key findings

- **The early years cost the most.** In 2018, median center-based infant care ran **\$153.60/week**
  versus **\$106.22** for school-age care — roughly a **31% premium** in the earliest years.
  Family childcare followed the same downward curve at a lower level (\$120.00 → \$98.77).
- **Provider type matters, most of all for infants.** Center-based care exceeded family childcare
  at every age group, with the gap widest for infants at **\$33.60/week**.
- **Geography is the biggest single driver.** For center-based infant care in 2018, county prices
  ranged from **\$108 at the 10th percentile to \$236 at the 90th** — a \$128 weekly spread. Where
  you live shapes what you pay as much as what you choose.
- At the median county, center-based infant care consumed roughly **16.1%** of estimated weekly
  household income; family infant care, about **12.5%**.

## What's in this folder

```
code/          Self-contained interactive dashboard (single HTML file, no build step —
               open it directly in a browser)
deliverables/  Slide deck (pptx/pdf), one-page infographic, written summary of findings,
               and the design rationale explaining the medium choices
figures/       Dashboard screenshots for counties with different cost profiles
process/       Project proposal, audience and design plan, draft deliverables,
               and the original dashboard wireframe
```

## Tools

Python · pandas · HTML/CSS/JavaScript (self-contained dashboard) · PowerPoint

## Notes and limitations

- The dataset measures **prices, not availability** — it says nothing about whether slots exist.
- Informal care from relatives, friends, or neighbors is not captured.
- Budget-burden figures use county MHI as a proxy; the dataset has no household-level income, so
  these are contextual estimates rather than family-specific affordability calculations.
- Data ends at 2018, so pandemic-era disruption and recent price movement are out of scope.
- The 2018 snapshot is not inflation-adjusted.
