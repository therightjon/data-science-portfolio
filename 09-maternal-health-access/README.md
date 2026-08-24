# Identifying Maternal Health Access and Risk Patterns Across U.S. Counties

A county-level predictive analysis of low birth weight across the United States, linking birth
outcomes to the local health resource conditions that surround them — built to help agencies decide
where to look first, not to claim what causes what.

## Problem

Maternal and infant health outcomes vary sharply across U.S. counties, and so does the capacity to
do anything about it. Health systems, public health agencies, and community partners need a
transparent method for identifying counties where adverse birth indicators and access constraints
overlap.

The question: which measured county characteristics are most associated with low birth weight, and
how can those patterns support targeted investigation, outreach, and resource planning?

## Data

Two federal sources joined on five-character county FIPS codes.

**CDC WONDER Natality (2020–2024)** — four separate county-of-residence extracts covering infant
birth weight, trimester prenatal care began, tobacco use, and maternal age. Counts were pooled
across five years to stabilize rates and reduce small-cell effects.

**HRSA Area Health Resources Files (2024–2025)** — county workforce, facility, population,
economic, and resource-scarcity measures.

**Final analytic file: 578 named counties across all 50 states, covering 14.4 million births.**

| Variable | Definition | Source |
|---|---|---|
| `low_birth_weight_pct` | Births below 2,500g as a percent of births with known weight | CDC WONDER |
| `late_or_no_prenatal_pct` | Prenatal care beginning after month 3, or none | CDC WONDER |
| `tobacco_use_pct` | Maternal tobacco use during pregnancy | CDC WONDER |
| `maternal_age_15_19_pct` / `maternal_age_35_plus_pct` | Maternal age composition | CDC WONDER |
| `poverty_pct` | Persons below the federal poverty level, ACS 2019–2023 | HRSA AHRF |
| `uninsured_under65_pct` | Persons under 65 without health insurance, 2022 | HRSA AHRF |
| `obgyn_per_100k` | Nonfederal OB-GYN physicians in patient care, 2023 | HRSA AHRF |
| `midwives_per_100k` | Advanced practice nurse midwives with an NPI, 2024 | HRSA AHRF |
| `obstetric_hospitals_per_100k` | Short-term general hospitals with obstetric care, 2023 | HRSA AHRF |
| `log_population_density` | Log of population per square mile, 2020 | HRSA AHRF |
| `primary_care_hpsa` | County had a primary care shortage designation in 2025 | HRSA AHRF |

## Approach

1. **Pooling and exclusion.** Five years of counts were pooled to stabilize county rates. Records
   labeled *Unidentified Counties* were removed — they combine several counties below CDC's
   identification threshold and cannot be linked to a single HRSA record.
2. **Rate construction.** Provider and hospital counts converted to rates per 100,000 residents.
   Population density log-transformed because its raw distribution is heavily right-skewed.
3. **Leakage control.** Median imputation happens *inside* each modeling pipeline, so no
   information crosses from validation folds into training. This is the detail that separates an
   honest cross-validated score from an inflated one.
4. **Two models, identical splits.** Ridge regression as a regularized linear benchmark, random
   forest to capture nonlinearity and interactions without a prespecified functional form. Both
   evaluated on the same 10-fold shuffled cross-validation.
5. **Permutation importance** measuring the drop in fitted R² after each feature is shuffled.

## Key findings

**Model performance**

| Model | Cross-validated R² | MAE (percentage points) |
|---|---|---|
| **Random forest** | **0.571** | **0.78** |
| Ridge regression | 0.542 | 0.81 |

The random forest explained **57.1% of out-of-sample county variation** with a mean absolute error
of **0.78 percentage points**. The modest gain over ridge suggests the relationships are mostly
close to linear, with some nonlinearity worth capturing.

**What actually predicts low birth weight**

| Feature | Permutation importance | Standardized coefficient |
|---|---|---|
| Maternal age 15–19 (%) | 0.613 | +0.74 |
| Poverty (%) | 0.235 | +0.25 |
| Log population density | 0.180 | +0.44 |
| OB-GYN per 100k | 0.157 | +0.42 |
| Late or no prenatal care (%) | 0.058 | +0.20 |

- **Teen birth share dominates**, with permutation importance more than 2.5× the next feature.
- Low birth weight averaged **8.44%** across counties (median 8.24%), ranging from **5.21% to
  15.77%** — a threefold spread between the healthiest and least healthy counties.
- **OB-GYN supply carries a positive coefficient**, which looks backwards until you consider that
  provider density tracks urbanization and referral patterns: counties with more OB-GYNs receive
  more high-risk transfers. This is a clear illustration of why importance is not effect.

## What's in this folder

```
code/          Analysis script, reproduction notes, pinned requirements
data/
  raw_cdc/       Four CDC WONDER natality extracts (JSON)
  raw_hrsa/      Official AHRF 2024-2025 county archives
  processed/     Merged county-level analytic file (578 rows)
deliverables/  White paper (docx/pdf), presentation (pptx/pdf), presentation script
figures/       Outcome distribution, county comparison, poverty relationship, feature importance
results/       Model metrics, feature results, descriptive statistics, county risk summary,
               and the analytic data dictionary
process/       Proposal and draft white paper
```

## Reproducing it

```bash
pip install -r code/requirements.txt
python code/analyze_maternal_health.py
```

The script expects the AHRF county CSV archive extracted under `data/raw/ahrf/` and the four CDC
extracts under `data/raw/`. **The CDC acquisition step cannot be automated** — CDC WONDER does not
permit automated location grouping through its public API, so the extracts must be regenerated
through the interactive request form using the 2016–2024 Expanded Natality form, years 2020–2024,
grouped by County of Residence. Everything downstream of acquisition is automated.

## Tools

Python · pandas · NumPy · scikit-learn (Ridge, RandomForestRegressor, permutation importance) ·
matplotlib · seaborn

## Notes and limitations

- **This is association, not causation.** Nothing here establishes that changing a county-level
  factor will produce a specific improvement in birth outcomes. Permutation importance measures
  predictive contribution within this dataset only.
- **Ecological inference.** Every finding describes counties, not individuals. County-level
  relationships do not transfer to people living in those counties.
- **578 of roughly 3,100 U.S. counties.** Counties below CDC's identification threshold are absent,
  which systematically excludes the smallest and most rural places — likely the ones with the
  sharpest access constraints. The analysis therefore understates rural risk.
- Maternal health disparities reflect care quality, access, clinical risk, and broader structural
  conditions. A model with eleven county-level features captures a narrow slice of that.
- Appropriate use is **screening and planning** — a starting point for investigation, not a
  conclusion about any county.
