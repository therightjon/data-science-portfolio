# Maternal Health Access and Risk Patterns Across U.S. Counties

**Status: in progress — currently at proposal stage.**

A county-level analysis linking maternal and birth outcome indicators to local health resource
conditions, identifying where access gaps and elevated risk factors suggest a need for targeted
outreach and resource planning.

## Problem

Maternal health outcomes in the United States vary sharply by geography, demographics, and access
to care. Health systems and public health agencies need clearer evidence about where maternal risk
is elevated and which county-level factors are most associated with poor birth-related outcomes.

Research questions:

- Which county characteristics are most associated with adverse maternal or infant indicators?
- Are there patterns in prenatal care, maternal age, rurality, workforce availability, or
  socioeconomic conditions that align with worse outcomes?
- How can those patterns support more targeted outreach, planning, and intervention?

## Data (planned)

| Source | Contribution |
|---|---|
| **CDC WONDER Natality** | County-level birth records: maternal age, race, prenatal care timing, gestation, tobacco use, delivery method, birth weight, geography |
| **HRSA Area Health Resources Files** | Provider supply, facilities, population characteristics, and local economic measures |
| **HRSA shortage designations** (if needed) | Primary Care HPSA and Maternity Care Target Area indicators to represent access constraints |

This pairing links birth outcomes directly to local health resource conditions, which a single
composite source would not support.

## Approach (planned)

1. Clean, select variables, and merge at the county level on common geographic identifiers.
2. Exploratory analysis for distributions, outliers, regional patterns, and missingness.
3. Correlation analysis and comparative visualizations relating outcome indicators to potential
   drivers, including access to care.
4. Modeling — the project follows the full end-to-end process rather than stopping at EDA.
5. Plain-language white paper with recommendations, plus a recorded presentation.

## Planned deliverables

```
code/            Analysis notebook
data/            Merged county-level dataset and source documentation
deliverables/    White paper, recorded presentation, audience Q&A
figures/         Exported charts
```

## Ethical considerations

County-level aggregation means every finding describes places, not people — conclusions must not be
read as statements about individuals. Maternal health data touches on sensitive outcomes, so the
analysis will report associations rather than implied causes, and will state clearly where the data
cannot support a claim.

---

*This README will be replaced with the completed project write-up.*
