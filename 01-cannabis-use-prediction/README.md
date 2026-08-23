# Predicting Cannabis Use from National Health Survey Data

A binary classification project that predicts self-reported cannabis use from demographic,
behavioral, and psychosocial survey responses, and identifies which factors carry the most
predictive signal.

## Problem

Public health agencies plan outreach with limited budgets and need to know which population
characteristics are most associated with substance use. This project asks two questions: can
cannabis use be predicted from routinely collected health survey variables, and which of those
variables actually drive the prediction?

## Data

**Canadian Community Health Survey (CCHS)** — 108,252 respondent records across 50 variables
covering demographics, general and mental health, chronic conditions, physical activity,
substance use, employment, income, food security, and insurance coverage.

The target variable (`Cannabis_use`) is imbalanced, which drove much of the modeling strategy.

| File | Description |
|---|---|
| `data/health_dataset.csv` | Survey extract used for the analysis |
| `data/health_dataset_data_dictionary.txt` | Variable definitions |
| `data/health_dataset_decoding_and_mapping_dictionary.docx` | Coded-value decoding reference |

## Approach

1. **Cleaning** — standardized column names, corrected source typos, and dropped identifier and
   leakage-prone fields.
2. **Encoding** — one-hot encoding for categorical variables and scaling for continuous ones,
   assembled into a `ColumnTransformer` / `Pipeline` so preprocessing is fit only on training folds.
3. **Class imbalance** — random oversampling of the minority class, evaluated against an
   unbalanced baseline rather than assumed to be an improvement.
4. **Models** — Logistic Regression and a Decision Tree classifier, compared on precision, recall,
   and ROC AUC.
5. **Interpretation** — coefficient magnitudes for the logistic model and impurity-based feature
   importance for the tree.

## Key findings

- Oversampling raised recall for cannabis users from **17% to 64%** (logistic regression) and from
  **34% to 62%** (decision tree), at a modest cost in overall accuracy. For a screening use case
  where missing a user is worse than a false positive, this is the right trade.
- **Logistic regression outperformed the decision tree** on precision, recall, and ROC AUC. The
  tree performed only marginally better than chance on the ROC curve.
- The strongest predictors were a mix of **demographic** (age, gender), **behavioral** (tobacco use),
  and **psychosocial** factors (life satisfaction, mental health state, sense of belonging, food
  security). Health region also ranked highly in the tree model, indicating meaningful regional
  variation.
- The takeaway for a public health audience: substance use here is not explained by demographics
  alone. Psychosocial and regional context carries real predictive weight, which argues for
  place-based and wellbeing-oriented outreach rather than purely demographic targeting.

## What's in this folder

```
code/          Full analysis notebook (load, clean, model, evaluate, interpret)
data/          Survey extract and data dictionaries
deliverables/  White paper (docx/pdf), slide deck, and a recorded audio walkthrough
figures/       Exported charts: target distribution, subgroup breakdowns,
               ROC comparison, and top-15 feature importance for both models
```

## Tools

Python · pandas · NumPy · scikit-learn (Pipeline, ColumnTransformer, LogisticRegression,
DecisionTreeClassifier) · matplotlib · seaborn

## Notes and limitations

- Survey self-reporting introduces response bias, particularly for a substance-use target.
- The models identify **association, not causation** — nothing here supports a causal claim about
  what leads to cannabis use.
- Results reflect a Canadian survey population and should not be extrapolated to other countries
  without revalidation.
