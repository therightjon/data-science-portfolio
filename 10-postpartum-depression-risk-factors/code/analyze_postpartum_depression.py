"""Reproducible analysis for the DSC680 postpartum depression project.

The binary outcome is EPDS high risk (score >= 13). All EPDS fields,
contemporaneous PHQ-9 fields, identifiers, and selected postpartum symptom
proxies are excluded from the predictors before any model is fitted.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, plot_tree


SEED = 680
ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data/raw/PPD_dataset_v3.csv"
OUTPUT = ROOT / "output/postpartum_depression"
FIGURES = OUTPUT / "figures"
TABLES = OUTPUT / "tables"

TARGET_SOURCE = "EPDS Result"
TARGET_LABEL = "epds_high_risk"

# Direct target components and current depression screen results.
SCREENING_LEAKAGE = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself or that you are a failure or have let yourself or your family down",
    "rouble concentrating on things",
    "Moving or speaking or restlessness",
    "Thoughts that you would be better off dead, or of hurting yourself",
    "PHQ9 Score",
    "PHQ9 Result",
    "You have been able to laugh and see the funny side of things",
    "You have looked forward with enjoyment to things",
    "You have blamed myself unnecessarily when things went wrong",
    "You have been anxious or worried for no good reason",
    "You have felt scared or panicky for no good reason",
    "Things have been getting to you",
    "You have been so unhappy that you have had difficulty sleeping",
    "You have felt sad or miserable",
    "You have been so unhappy that you have been crying",
    "The thought of harming yourself has occurred ",
    "EPDS Score",
    "EPDS Result",
]

# These fields were collected postpartum and closely reflect current mood,
# bonding, sleep, anxiety, irritability, or functional impairment.
POSTPARTUM_PROXY_FIELDS = [
    "Relationship with the newborn",
    "Relationship between father and newborn",
    "Feeling about motherhood",
    "Worry about newborn",
    "Relax/sleep when newborn is tended ",
    "Relax/sleep when the newborn is asleep",
    "Angry after latest child birth",
    "Feeling for regular activities",
]

ID_FIELDS = ["sr"]
EXCLUDED_FIELDS = ID_FIELDS + SCREENING_LEAKAGE + POSTPARTUM_PROXY_FIELDS

# The data dictionary explicitly includes "None" for these fields, while the
# CSV represents that response as a blank. Preserve the documented meaning
# instead of assigning the most frequent observed condition.
DOCUMENTED_NONE_FIELDS = [
    "Addiction",
    "Disease before pregnancy",
    "History of pregnancy loss",
    "Monthly income before latest pregnancy",
    "Current monthly income",
    "Husband’s monthly income",
    "Education Level",
    "Husband's education level",
    "Diseases during pregnancy",
]

# Category normalization is limited to clear spelling, capitalization, or
# dictionary-alignment corrections. It does not combine substantively distinct
# answers.
CATEGORY_NORMALIZATION = {
    "Occupation before latest pregnancy": {"House wife": "Housewife"},
    "Occupation After Your Latest Childbirth": {"House wife": "Housewife"},
    "Education Level": {
        "Primary school": "Primary School",
        "High school": "High School",
    },
    "Husband's education level": {
        "Primary school": "Primary School",
        "High school": "High School",
    },
    "Total children": {"More than Two": "More than two"},
    "History of pregnancy loss": {
        "Still-born Delivery": "Stillbirth",
        "Still-born delivery": "Stillbirth",
    },
    "Diseases during pregnancy": {
        "Chronic disease": "Chronic Disease",
        "Non-chronic disease": "Non-Chronic Disease",
    },
    "Addiction": {"Drinking": "Alcohol"},
}

INVALID_VALUES = {
    "Disease before pregnancy": {"1.2"},
}


class RareCategoryOneHotEncoder(BaseEstimator, TransformerMixin):
    """Group rare and unseen values before one-hot encoding.

    Frequency rules are learned on each training fold. Categories absent from a
    fold are mapped to an explicit Other / infrequent level instead of the
    dropped reference category.
    """

    def __init__(self, min_frequency: int = 5, drop: str | None = "first"):
        self.min_frequency = min_frequency
        self.drop = drop

    def fit(self, X, y=None):
        frame = pd.DataFrame(X).astype(str)
        self.frequent_categories_ = []
        categories = []
        preferred_references = ["No", "None", "Negative"]
        for column in frame.columns:
            counts = frame[column].value_counts(dropna=False)
            frequent = sorted(counts[counts >= self.min_frequency].index.astype(str).tolist())
            self.frequent_categories_.append(set(frequent))
            reference = next((value for value in preferred_references if value in frequent), None)
            ordered = ([reference] if reference else []) + [value for value in frequent if value != reference]
            categories.append(ordered + ["Other / infrequent"])
        mapped = self._map(frame)
        self.encoder_ = OneHotEncoder(
            categories=categories,
            handle_unknown="ignore",
            drop=self.drop,
            sparse_output=True,
        )
        self.encoder_.fit(mapped)
        return self

    def transform(self, X):
        return self.encoder_.transform(self._map(pd.DataFrame(X).astype(str)))

    def _map(self, frame: pd.DataFrame) -> pd.DataFrame:
        mapped = frame.copy()
        for position, column in enumerate(mapped.columns):
            frequent = self.frequent_categories_[position]
            mapped[column] = mapped[column].where(
                mapped[column].isin(frequent), "Other / infrequent"
            )
        return mapped

    def get_feature_names_out(self, input_features=None):
        if input_features is None:
            input_features = [f"x{i}" for i in range(len(self.frequent_categories_))]
        return self.encoder_.get_feature_names_out(input_features)


def clean_predictor_categories(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply documented missing semantics and conservative category cleanup."""
    cleaned = df.copy()
    audit_rows = []

    for column in cleaned.select_dtypes(include="object").columns:
        cleaned[column] = cleaned[column].str.strip().replace("", np.nan)

    for column, invalid in INVALID_VALUES.items():
        if column in cleaned:
            count = int(cleaned[column].isin(invalid).sum())
            cleaned.loc[cleaned[column].isin(invalid), column] = np.nan
            audit_rows.append({
                "column": column,
                "action": "Invalid value recoded as missing",
                "records_affected": count,
                "detail": ", ".join(sorted(invalid)),
            })

    for column, replacements in CATEGORY_NORMALIZATION.items():
        if column in cleaned:
            for old, new in replacements.items():
                count = int(cleaned[column].eq(old).sum())
                cleaned[column] = cleaned[column].replace(old, new)
                audit_rows.append({
                    "column": column,
                    "action": "Category normalized",
                    "records_affected": count,
                    "detail": f"{old} -> {new}",
                })

    for column in DOCUMENTED_NONE_FIELDS:
        if column in cleaned:
            count = int(cleaned[column].isna().sum())
            cleaned[column] = cleaned[column].fillna("None")
            audit_rows.append({
                "column": column,
                "action": "Blank mapped to documented response",
                "records_affected": count,
                "detail": "None",
            })

    older_child = "Age of immediate older children"
    if older_child in cleaned:
        count = int(cleaned[older_child].isna().sum())
        cleaned[older_child] = cleaned[older_child].fillna("Not available or not applicable")
        audit_rows.append({
            "column": older_child,
            "action": "Structural or unavailable blank labeled",
            "records_affected": count,
            "detail": "Not available or not applicable",
        })

    return cleaned, pd.DataFrame(audit_rows)


def load_and_prepare(path: Path = RAW_PATH) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Load data, define the target, normalize blanks, and select predictors."""
    raw = pd.read_csv(path)
    raw.columns = [c.strip() for c in raw.columns]
    excluded = [c.strip() for c in EXCLUDED_FIELDS]

    # The publisher defines High as EPDS 13-30. Validate against the score.
    target_from_result = raw[TARGET_SOURCE].str.strip().str.casefold().eq("high").astype(int)
    target_from_score = raw["EPDS Score"].ge(13).astype(int)
    # One published row labels a score of 12 as High. Use the documented
    # threshold rather than the inconsistent categorical label.
    cleaned, cleaning_audit = clean_predictor_categories(raw)
    cleaned.attrs["target_label_disagreements"] = int((target_from_result != target_from_score).sum())
    cleaned.attrs["raw_missing_cells"] = int(raw.isna().sum().sum())
    raw_predictors = raw.drop(columns=[c for c in excluded if c in raw.columns])
    cleaned.attrs["raw_predictor_missing_cells"] = int(raw_predictors.isna().sum().sum())
    cleaned.attrs["cleaning_audit"] = cleaning_audit

    X = cleaned.drop(columns=[c for c in excluded if c in cleaned.columns]).copy()
    y = target_from_score.rename(TARGET_LABEL)
    return cleaned, X, y


def build_preprocessor(
    X: pd.DataFrame, *, drop: str | None = "first"
) -> tuple[ColumnTransformer, list[str], list[str]]:
    numeric = X.select_dtypes(include=np.number).columns.tolist()
    categorical = [c for c in X.columns if c not in numeric]
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                    ("scaler", StandardScaler()),
                ]),
                numeric,
            ),
            (
                "categorical",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="constant", fill_value="Missing / not reported")),
                    ("onehot", RareCategoryOneHotEncoder(min_frequency=5, drop=drop)),
                ]),
                categorical,
            ),
        ],
        verbose_feature_names_out=False,
    )
    return preprocessor, numeric, categorical


def make_models(X: pd.DataFrame) -> dict[str, Pipeline]:
    logistic_preprocessor, _, _ = build_preprocessor(X, drop="first")
    tree_preprocessor, _, _ = build_preprocessor(X, drop=None)
    return {
        "Logistic regression": Pipeline([
            ("preprocessor", logistic_preprocessor),
            ("model", LogisticRegression(C=0.25, class_weight="balanced", max_iter=5000, random_state=SEED)),
        ]),
        "Decision tree": Pipeline([
            ("preprocessor", tree_preprocessor),
            ("model", DecisionTreeClassifier(
                max_depth=4,
                min_samples_leaf=25,
                class_weight="balanced",
                random_state=SEED,
            )),
        ]),
    }


def evaluate_models(X: pd.DataFrame, y: pd.Series):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=SEED
    )
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=5, random_state=SEED)
    scoring = {
        "roc_auc": "roc_auc",
        "average_precision": "average_precision",
        "recall": "recall",
        "precision": "precision",
        "f1": "f1",
        "balanced_accuracy": "balanced_accuracy",
    }
    fitted = {}
    metric_rows = []
    predictions = {}
    for name, model in make_models(X).items():
        scores = cross_validate(model, X_train, y_train, cv=cv, scoring=scoring, n_jobs=-1)
        model.fit(X_train, y_train)
        prob = model.predict_proba(X_test)[:, 1]
        pred = (prob >= 0.5).astype(int)
        predictions[name] = {"prob": prob, "pred": pred}
        fitted[name] = model
        row = {"model": name}
        for metric in scoring:
            values = scores[f"test_{metric}"]
            row[f"cv_{metric}_mean"] = values.mean()
            row[f"cv_{metric}_sd"] = values.std(ddof=1)
        row.update({
            "test_roc_auc": roc_auc_score(y_test, prob),
            "test_average_precision": average_precision_score(y_test, prob),
            "test_recall": recall_score(y_test, pred),
            "test_precision": precision_score(y_test, pred),
            "test_f1": f1_score(y_test, pred),
            "test_accuracy": accuracy_score(y_test, pred),
            "test_balanced_accuracy": balanced_accuracy_score(y_test, pred),
            "test_brier_score": brier_score_loss(y_test, prob),
            "test_tn": confusion_matrix(y_test, pred).ravel()[0],
            "test_fp": confusion_matrix(y_test, pred).ravel()[1],
            "test_fn": confusion_matrix(y_test, pred).ravel()[2],
            "test_tp": confusion_matrix(y_test, pred).ravel()[3],
        })
        metric_rows.append(row)
    return pd.DataFrame(metric_rows), fitted, predictions, X_train, X_test, y_train, y_test


def bootstrap_auc(y_true, probability, n_boot=2000):
    rng = np.random.default_rng(SEED)
    values = []
    y_array = np.asarray(y_true)
    p_array = np.asarray(probability)
    for _ in range(n_boot):
        idx = rng.integers(0, len(y_array), len(y_array))
        if np.unique(y_array[idx]).size == 2:
            values.append(roc_auc_score(y_array[idx], p_array[idx]))
    return np.percentile(values, [2.5, 97.5])


def risk_factor_summary(df: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    selected = {
        "Depression during pregnancy (PHQ2)": "Depression during pregnancy",
        "Depression before pregnancy (PHQ2)": "Depression before pregnancy",
        "Abuse": "Abuse reported",
        "Trust and share feelings": "Ability to confide",
        "Pregnancy plan": "Unplanned pregnancy",
        "Recieved Support": "Support received",
    }
    rows = []
    working = df.copy()
    working[TARGET_LABEL] = y
    for col, label in selected.items():
        for level, group in working.groupby(col, dropna=False):
            if len(group) >= 20:
                rows.append({
                    "factor": label,
                    "level": "Missing" if pd.isna(level) else str(level),
                    "n": len(group),
                    "high_risk_rate": group[TARGET_LABEL].mean(),
                })
    return pd.DataFrame(rows)


def logistic_terms(model: Pipeline) -> pd.DataFrame:
    names = model.named_steps["preprocessor"].get_feature_names_out()
    coefficients = model.named_steps["model"].coef_[0]
    terms = pd.DataFrame({"term": names, "coefficient": coefficients})
    terms["odds_ratio_per_encoded_unit"] = np.exp(terms["coefficient"])
    terms["absolute_coefficient"] = terms["coefficient"].abs()
    return terms.sort_values("absolute_coefficient", ascending=False)


def create_figures(df, X, y, metrics, fitted, predictions, X_test, y_test, risk_summary):
    plt.style.use("seaborn-v0_8-whitegrid")
    palette = {0: "#7A9E9F", 1: "#C65D4B"}

    # Figure 1: target distribution.
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    counts = y.value_counts().sort_index()
    bars = ax.bar(["Low or medium", "High"], counts.values, color=[palette[0], palette[1]])
    for bar, count in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, count + 8, f"{count}\n({count/len(y):.1%})", ha="center")
    ax.set(title="EPDS screening risk distribution", ylabel="Participants", xlabel="EPDS category")
    ax.set_ylim(0, max(counts) * 1.18)
    fig.tight_layout()
    fig.savefig(FIGURES / "figure_1_epds_distribution.png", dpi=220)
    plt.close(fig)

    # Figure 2: selected descriptive relationships.
    plot_df = risk_summary[risk_summary["factor"].isin([
        "Depression during pregnancy", "Depression before pregnancy", "Ability to confide", "Unplanned pregnancy"
    ])].copy()
    plot_df["label"] = plot_df["factor"] + ": " + plot_df["level"]
    plot_df = plot_df.sort_values("high_risk_rate")
    fig, ax = plt.subplots(figsize=(8.2, 6.0))
    ax.barh(plot_df["label"], plot_df["high_risk_rate"], color="#52796F")
    ax.set(xlabel="Share classified as EPDS high risk", ylabel="", title="High-risk prevalence in selected subgroups")
    ax.xaxis.set_major_formatter(lambda x, pos: f"{x:.0%}")
    fig.tight_layout()
    fig.savefig(FIGURES / "figure_2_selected_risk_factors.png", dpi=220)
    plt.close(fig)

    # Figure 3: holdout ROC curves.
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    for name, values in predictions.items():
        fpr, tpr, _ = roc_curve(y_test, values["prob"])
        auc = roc_auc_score(y_test, values["prob"])
        ax.plot(fpr, tpr, linewidth=2, label=f"{name} (AUC={auc:.3f})")
    ax.plot([0, 1], [0, 1], linestyle="--", color="#666666", label="Chance")
    ax.set(xlabel="False-positive rate", ylabel="True-positive rate", title="Holdout ROC performance")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(FIGURES / "figure_3_roc_curves.png", dpi=220)
    plt.close(fig)

    # Figure 4: strongest logistic regression terms.
    terms = logistic_terms(fitted["Logistic regression"])
    technical_level = terms["term"].str.contains(
        r"Missing / not reported|Other / infrequent|missingindicator", regex=True
    )
    terms = terms.loc[~technical_level].head(15).sort_values("coefficient")
    colors = np.where(terms["coefficient"] >= 0, "#C65D4B", "#52796F")
    fig, ax = plt.subplots(figsize=(8.5, 6.2))
    ax.barh(terms["term"], terms["coefficient"], color=colors)
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set(xlabel="Standardized / encoded coefficient", ylabel="", title="Strongest logistic regression terms")
    fig.tight_layout()
    fig.savefig(FIGURES / "figure_4_logistic_terms.png", dpi=220)
    plt.close(fig)

    # Supplemental interpretable tree diagram.
    tree_pipe = fitted["Decision tree"]
    feature_names = tree_pipe.named_steps["preprocessor"].get_feature_names_out()
    fig, ax = plt.subplots(figsize=(18, 9))
    plot_tree(
        tree_pipe.named_steps["model"], feature_names=feature_names,
        class_names=["Lower", "High"], filled=True, rounded=True,
        proportion=True, precision=2, fontsize=7, ax=ax,
    )
    fig.tight_layout()
    fig.savefig(FIGURES / "supplemental_decision_tree.png", dpi=180)
    plt.close(fig)


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    df, X, y = load_and_prepare()
    metrics, fitted, predictions, X_train, X_test, y_train, y_test = evaluate_models(X, y)
    risk_summary = risk_factor_summary(df, y)
    terms = logistic_terms(fitted["Logistic regression"])

    for name, values in predictions.items():
        lo, hi = bootstrap_auc(y_test, values["prob"])
        metrics.loc[metrics["model"].eq(name), "test_auc_ci_low"] = lo
        metrics.loc[metrics["model"].eq(name), "test_auc_ci_high"] = hi

    # Model-agnostic raw-feature importance on the holdout set.
    for name, model in fitted.items():
        result = permutation_importance(
            model, X_test, y_test, scoring="roc_auc", n_repeats=30, random_state=SEED, n_jobs=-1
        )
        pd.DataFrame({
            "feature": X.columns,
            "importance_mean": result.importances_mean,
            "importance_sd": result.importances_std,
        }).sort_values("importance_mean", ascending=False).to_csv(
            TABLES / f"{name.lower().replace(' ', '_')}_permutation_importance.csv", index=False
        )

    dataset_summary = {
        "rows": len(df),
        "raw_columns": df.shape[1],
        "predictor_columns": X.shape[1],
        "high_risk_n": int(y.sum()),
        "high_risk_rate": float(y.mean()),
        "raw_missing_cells": int(df.attrs.get("raw_missing_cells", df.isna().sum().sum())),
        "raw_predictor_missing_cells": int(df.attrs.get("raw_predictor_missing_cells", 0)),
        "predictor_missing_cells": int(X.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "target_label_disagreements": int(df.attrs.get("target_label_disagreements", 0)),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "excluded_fields": [c.strip() for c in EXCLUDED_FIELDS],
    }
    (TABLES / "dataset_summary.json").write_text(json.dumps(dataset_summary, indent=2))
    metrics.to_csv(TABLES / "model_metrics.csv", index=False)
    df.attrs["cleaning_audit"].to_csv(TABLES / "data_cleaning_audit.csv", index=False)
    risk_summary.to_csv(TABLES / "selected_risk_factor_summary.csv", index=False)
    terms.to_csv(TABLES / "logistic_regression_terms.csv", index=False)
    pd.DataFrame({
        "actual": y_test.to_numpy(),
        **{f"{name}_probability": values["prob"] for name, values in predictions.items()},
        **{f"{name}_prediction": values["pred"] for name, values in predictions.items()},
    }).to_csv(TABLES / "holdout_predictions.csv", index=False)
    create_figures(df, X, y, metrics, fitted, predictions, X_test, y_test, risk_summary)

    print(json.dumps(dataset_summary, indent=2))
    print("\nModel metrics\n", metrics.round(3).to_string(index=False))
    print("\nTop logistic terms\n", terms.head(12).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
