# Identifying Risk Factors for Postpartum Depression

A binary classification study testing whether routinely collected maternal, socioeconomic, family,
and obstetric characteristics can identify elevated postpartum depression screening risk — built
with deliberate leakage controls, because the easy version of this problem is also the useless one.

## Problem

Postpartum depression affects maternal health, family functioning, and infant wellbeing, and care
teams need ways to recognize risk early enough to support timely screening and follow-up. Where
staff and behavioral health resources are limited, a risk model could help prioritize outreach.

The business question is narrower and harder than it first appears: can *routinely available*
characteristics identify elevated screening risk **without using the symptoms that define the
outcome**?

## The leakage problem — and why it defines this project

The raw dataset contains EPDS and PHQ-9 screening items. A model trained on those would score
beautifully and mean nothing: it would be predicting a depression score from the depression
questions that compute it. To make the question real, the following were removed before modeling:

- All EPDS items, EPDS score, and EPDS category
- All current PHQ-9 items, PHQ-9 score, and PHQ-9 category
- Eight contemporaneous postpartum symptom proxies (bonding with the newborn, feelings about
  motherhood, ability to relax when the newborn sleeps, anger since childbirth, and similar)
- The row identifier

**32 fields excluded in total**, leaving 38 predictor columns. The moderate performance below is
the honest number that remains once the shortcuts are gone.

## Data

**Data for Postpartum Depression Prediction in Bangladesh, version 3** — Mendeley Data, CC BY 4.0.
Raisa, J. F., & Kaiser, M. S. (2026). https://doi.org/10.17632/4nznnrk8cg.3

- **800 respondents** who had given birth within the prior 24 months, 70 raw columns
- Outcome: **EPDS ≥ 13** — **349 participants (43.6%)** met the high-risk threshold
- Coverage: demographics, income, family relationships, health history, pregnancy and delivery,
  newborn health, and postpartum experience

## Data quality work

The raw file carried 4,312 missing cells, 4,089 of them in retained predictor fields. Rather than
dropping rows or blanket-imputing, each pattern was resolved against the data dictionary and logged
to a record-level audit (`results/data_cleaning_audit.csv`):

- **Documented "None" responses assigned** where the dictionary supported it — 789 addiction blanks,
  613 pregnancy-loss blanks, 589 pre-existing-disease blanks, and others. These were never missing;
  they were unticked checkboxes.
- **517 structural blanks** for age of older children labeled *not available or not applicable*.
- **206 genuinely ambiguous blanks** labeled *Missing / not reported* within each training fold.
- Spelling and capitalization variants normalized (`House wife` → `Housewife`, `Still-born
  Delivery` → `Stillbirth`, and 11 more patterns).
- The invalid disease value `1.2` recoded as missing.
- One row labeled High with an EPDS score of 12 was resolved by the documented numeric rule.
- Rare categories (fewer than five occurrences in a training fold) grouped as *Other / infrequent*,
  **within each fold** rather than globally.

That last detail matters: fold-wise grouping, fold-wise imputation, and fold-wise rare-level
handling are what keep the cross-validated score honest.

## Approach

Regularized logistic regression and a shallow decision tree, evaluated with repeated stratified
cross-validation on 600 training rows and a held-out 200-row test set. Random seed 680 throughout.
Categorical predictors one-hot encoded; numeric predictors median-imputed and standardized.

## Key findings

**Model performance**

| Model | CV ROC-AUC | Test ROC-AUC (95% CI) | Test recall | Test precision |
|---|---|---|---|---|
| **Logistic regression** | 0.774 ± 0.032 | **0.760** (0.690–0.826) | 0.598 | 0.650 |
| Decision tree | 0.729 ± 0.040 | 0.731 (0.662–0.800) | **0.736** | 0.552 |

**Moderate discrimination, and that is the finding.** Logistic regression is the better ranker; the
decision tree catches more true cases at the cost of more false positives. For an outreach
prioritization use case, the tree's higher recall may be the more useful trade — missing an at-risk
parent costs more than an unnecessary check-in.

**The strongest signals** (logistic regression odds ratios, `results/logistic_regression_terms.csv`)

| Factor | Odds ratio | Direction |
|---|---|---|
| Depression before pregnancy (PHQ-2 positive) | 1.90 | ↑ risk |
| Depression during pregnancy (PHQ-2 positive) | 1.75 | ↑ risk |
| Fear of pregnancy | 1.71 | ↑ risk |
| Low support received | 1.68 | ↑ risk |
| Good relationship with husband | 0.54 | ↓ risk |
| Good relationship with in-laws | 0.55 | ↓ risk |
| Able to trust and share feelings | 0.61 | ↓ risk |

Observed high-risk rates track the same story: **69.1%** among those reporting depression before
pregnancy versus 40.8% without; **57.1%** among those reporting low support versus 27.0% with high
support.

These align with the published literature — prior depression, poor social support, and unintended
pregnancy recur across meta-analyses — which is a credibility check on the model rather than a novel
finding.

## What's in this folder

```
code/          Standalone analysis script, executed notebook, pinned requirements
data/raw/      Mendeley dataset v3 and its data dictionary
deliverables/  White paper (docx/pdf), presentation (pptx/pdf), recording script
figures/       EPDS distribution, selected risk factors, ROC curves, logistic terms,
               supplemental decision tree
results/       Model metrics, permutation importance, logistic terms, holdout predictions,
               dataset summary, and the record-level cleaning audit
process/       Proposal and draft white paper
```

## Reproducing it

```bash
pip install -r code/requirements.txt
python code/analyze_postpartum_depression.py
```

Seed 680; writes to `figures/` and `results/`.

## Tools

Python · scikit-learn (LogisticRegression, DecisionTreeClassifier, permutation importance,
stratified CV) · pandas · NumPy · matplotlib · Jupyter

## Notes and limitations

**This model must never substitute for EPDS screening, clinical diagnosis, or professional
judgment.** Its only appropriate use is exploratory risk stratification that directs attention
toward validated screening and follow-up.

- **Population specificity.** 800 respondents in Bangladesh. Family structure, income bands, and
  support norms in this sample do not transfer to other settings without revalidation. The CDC
  figure that roughly one in eight U.S. women with a recent live birth report postpartum depression
  symptoms is context, not a benchmark for this sample.
- **Self-reported, cross-sectional data.** Predictors and outcome were collected at the same time,
  so nothing here establishes temporal ordering, let alone causation.
- **A 0.76 AUC is moderate.** Roughly a quarter of ranked pairs are ordered wrong. Reported with its
  confidence interval precisely because a single point estimate would oversell it.
- **Never validated prospectively.** The recommendation in the white paper is to retain logistic
  regression as the analytical baseline and validate it in the intended population before any
  operational use.
