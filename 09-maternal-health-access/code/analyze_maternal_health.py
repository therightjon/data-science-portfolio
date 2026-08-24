"""Reproducible county-level maternal health analysis for DSC680.

Inputs:
  * CDC WONDER Natality extracts for 2020-2024 in data/raw/*.json
  * HRSA AHRF 2024-2025 county CSV files in data/raw/ahrf/

Outputs:
  * analysis-ready county data, data dictionary, model metrics, coefficients,
    ranked county table, and four publication-ready figures.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "output" / "figures"
TABLES = ROOT / "output" / "tables"
AHRF = RAW / "ahrf" / "NCHWA-2024-2025+AHRF+COUNTY+CSV"

SEED = 680
TARGET = "low_birth_weight_pct"

# Keep the candidate feature list in one place so the model inputs, descriptive
# statistics, and feature-importance output always use the same definitions.
FEATURES = [
    "late_or_no_prenatal_pct",
    "tobacco_use_pct",
    "maternal_age_15_19_pct",
    "maternal_age_35_plus_pct",
    "poverty_pct",
    "uninsured_under65_pct",
    "obgyn_per_100k",
    "midwives_per_100k",
    "obstetric_hospitals_per_100k",
    "log_population_density",
    "primary_care_hpsa",
]


def read_json(name: str) -> pd.DataFrame:
    """Load one browser-exported CDC WONDER aggregate into a DataFrame."""
    with (RAW / name).open(encoding="utf-8") as handle:
        return pd.DataFrame(json.load(handle))


def load_cdc() -> pd.DataFrame:
    """Combine the four CDC extracts and calculate county-level percentages."""
    bw = read_json("cdc_natality_birthweight_2020_2024.json")
    prenatal = read_json("cdc_natality_prenatal_2020_2024.json")
    tobacco = read_json("cdc_natality_tobacco_2020_2024.json")
    age = read_json("cdc_natality_maternal_age_2020_2024.json")
    # Each source should contain one pooled record per reported county. The
    # validation option fails early if a malformed extract introduces duplicates.
    out = bw.merge(prenatal, on=["fips", "county"], validate="one_to_one")
    out = out.merge(tobacco, on=["fips", "county"], validate="one_to_one")
    out = out.merge(age, on=["fips", "county"], validate="one_to_one")
    # FIPS codes ending in 999 are CDC's state-level groups of smaller,
    # unidentified counties. They cannot be joined to one HRSA county.
    out = out.loc[~out["fips"].str.endswith("999")].copy()

    # Use records with known values as the denominator for each indicator. This
    # avoids treating unknown or unreported values as if they were negative cases.
    out[TARGET] = 100 * out["low_birth_weight"] / out["births_known"]
    out["late_or_no_prenatal_pct"] = 100 * out["late_or_no_prenatal"] / out["prenatal_known"]
    out["tobacco_use_pct"] = 100 * out["tobacco_yes"] / out["tobacco_known"]
    out["maternal_age_15_19_pct"] = 100 * out["age_15_19"] / out["age_known"]
    out["maternal_age_35_plus_pct"] = 100 * out["age_35_plus"] / out["age_known"]
    return out


def load_ahrf() -> pd.DataFrame:
    """Load selected AHRF fields and engineer comparable access measures."""
    # Reading only the required columns keeps memory use manageable because the
    # complete AHRF release contains several thousand variables.
    geo_cols = ["fips_st_cnty", "cnty_name_st_abbrev", "st_name_abbrev", "rural_urban_contnm_23", "hpsa_prim_care_25"]
    pop_cols = ["fips_st_cnty", "popn_est_24", "pers_lt_fpl_pct_23", "pers_noins_lt65_pct_22", "medn_hhi_acs_23"]
    hp_cols = ["fips_st_cnty", "md_nf_obgyn_gen_all_pc_23", "apn_midwvs_npi_24"]
    hf_cols = ["fips_st_cnty", "stgh_obstetrc_care_23"]
    env_cols = ["fips_st_cnty", "popn_densty_per_squr_mi_20"]
    frames = [
        pd.read_csv(AHRF / "AHRF2025geo.csv", usecols=geo_cols),
        pd.read_csv(AHRF / "AHRF2025pop.csv", usecols=pop_cols),
        pd.read_csv(AHRF / "AHRF2025hp.csv", usecols=hp_cols),
        pd.read_csv(AHRF / "AHRF2025hf.csv", usecols=hf_cols),
        pd.read_csv(AHRF / "AHRF2025env.csv", usecols=env_cols),
    ]
    out = frames[0]
    for frame in frames[1:]:
        # AHRF component files should each have one record per county.
        out = out.merge(frame, on="fips_st_cnty", validate="one_to_one")

    # Preserve leading zeroes so the key matches CDC's five-character FIPS code.
    out["fips"] = out["fips_st_cnty"].astype(str).str.zfill(5)
    out = out.rename(
        columns={
            "cnty_name_st_abbrev": "ahrf_county",
            "popn_est_24": "population_2024",
            "pers_lt_fpl_pct_23": "poverty_pct",
            "pers_noins_lt65_pct_22": "uninsured_under65_pct",
            "medn_hhi_acs_23": "median_household_income",
            "rural_urban_contnm_23": "rural_urban_continuum_code",
            "hpsa_prim_care_25": "primary_care_hpsa",
            "md_nf_obgyn_gen_all_pc_23": "obgyn_count",
            "apn_midwvs_npi_24": "midwife_count",
            "stgh_obstetrc_care_23": "obstetric_hospital_count",
            "popn_densty_per_squr_mi_20": "population_density",
        }
    )
    # Convert raw workforce and facility counts to rates so counties of different
    # population sizes can be compared on a common scale.
    denom = out["population_2024"] / 100_000
    out["obgyn_per_100k"] = out["obgyn_count"] / denom
    out["midwives_per_100k"] = out["midwife_count"] / denom
    out["obstetric_hospitals_per_100k"] = out["obstetric_hospital_count"] / denom
    # The log transform reduces the influence of extremely dense urban counties.
    out["log_population_density"] = np.log1p(out["population_density"])

    # AHRF uses codes for whole- and partial-county shortage designations. The
    # model only needs to distinguish any designation from no designation.
    out["primary_care_hpsa"] = out["primary_care_hpsa"].fillna(0).gt(0).astype(int)
    return out


def model_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compare two models and return predictions, metrics, and interpretation."""
    x, y = df[FEATURES], df[TARGET]

    # Shuffling prevents the input file's geographic order from determining the
    # folds. The fixed seed makes every run use the same validation splits.
    cv = KFold(n_splits=10, shuffle=True, random_state=SEED)

    # Imputation occurs inside each pipeline. During cross-validation, missing
    # values are therefore filled using only the training portion of each fold.
    ridge = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", RidgeCV(alphas=np.logspace(-3, 3, 61))),
    ])
    forest = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        # A minimum leaf size of five limits overly specific county-level splits.
        ("model", RandomForestRegressor(n_estimators=500, min_samples_leaf=5, max_features=0.8, random_state=SEED, n_jobs=1)),
    ])
    predictions = {}
    metrics = []
    for name, model in [("Ridge regression", ridge), ("Random forest", forest)]:
        # cross_val_predict gives every county a prediction from a model that was
        # not trained on that county, producing honest comparison metrics.
        pred = cross_val_predict(model, x, y, cv=cv, n_jobs=1)
        predictions[name] = pred
        metrics.append({"model": name, "cv_r2": r2_score(y, pred), "cv_mae_percentage_points": mean_absolute_error(y, pred)})
    metrics_df = pd.DataFrame(metrics).sort_values("cv_r2", ascending=False)
    best_name = metrics_df.iloc[0]["model"]
    best = ridge if best_name == "Ridge regression" else forest

    # Refit the selected model on all counties for final interpretation. The
    # stored county predictions remain the out-of-fold values calculated above.
    best.fit(x, y)
    df = df.copy()
    df["cross_validated_prediction"] = predictions[best_name]
    df["cross_validated_residual"] = y - df["cross_validated_prediction"]
    # Permutation importance asks how much fitted R-squared declines when one
    # feature is scrambled. It measures predictive contribution, not causality.
    perm = permutation_importance(best, x, y, n_repeats=30, random_state=SEED, scoring="r2", n_jobs=1)
    importance = pd.DataFrame({"feature": FEATURES, "importance": perm.importances_mean, "importance_sd": perm.importances_std}).sort_values("importance", ascending=False)
    # Standardized ridge coefficients provide a directional linear benchmark,
    # even when the random forest is the better-performing model.
    ridge.fit(x, y)
    coefs = pd.DataFrame({"feature": FEATURES, "standardized_coefficient": ridge.named_steps["model"].coef_}).sort_values("standardized_coefficient", key=abs, ascending=False)
    return df, metrics_df, importance.merge(coefs, on="feature", how="left")


def make_figures(df: pd.DataFrame, importance: pd.DataFrame) -> None:
    """Create four report figures that answer distinct analytical questions."""
    sns.set_theme(style="whitegrid", context="notebook")
    palette = {"low": "#0B6E75", "high": "#C84C3A", "neutral": "#5B6573", "gold": "#D8A31A"}

    # Figure 1: show the overall distribution rather than only its average.
    fig, ax = plt.subplots(figsize=(8, 4.8))
    sns.histplot(df[TARGET], bins=24, color=palette["low"], edgecolor="white", ax=ax)
    med = df[TARGET].median()
    ax.axvline(med, color=palette["high"], lw=2, label=f"Median: {med:.1f}%")
    ax.set(title="Low birth weight prevalence varies across reported counties", xlabel="Births below 2,500 grams (%)", ylabel="Counties")
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(FIGURES / "figure_1_lbw_distribution.png", dpi=220); plt.close(fig)

    # Figure 2: compare both ends of the county distribution using equal groups.
    rank = pd.concat([df.nsmallest(8, TARGET), df.nlargest(8, TARGET)]).sort_values(TARGET)
    colors = [palette["low"]] * 8 + [palette["high"]] * 8
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(rank["county"], rank[TARGET], color=colors)
    ax.axvline(df[TARGET].median(), color=palette["neutral"], ls="--", lw=1.4)
    ax.set(title="The county range is wide even among larger counties", xlabel="Births below 2,500 grams (%)", ylabel="")
    fig.tight_layout(); fig.savefig(FIGURES / "figure_2_county_comparison.png", dpi=220); plt.close(fig)

    # Figure 3: display a key bivariate relationship and the unexplained spread.
    fig, ax = plt.subplots(figsize=(8, 5.2))
    sns.regplot(data=df, x="poverty_pct", y=TARGET, scatter_kws={"s": 30, "alpha": .55, "color": palette["neutral"]}, line_kws={"color": palette["high"], "lw": 2}, ax=ax)
    ax.set(title="County poverty and low birth weight move together, with substantial variation", xlabel="Population below poverty level (%)", ylabel="Births below 2,500 grams (%)")
    fig.tight_layout(); fig.savefig(FIGURES / "figure_3_poverty_relationship.png", dpi=220); plt.close(fig)

    # Figure 4: rank the ten strongest predictive signals from the fitted model.
    top = importance.head(10).sort_values("importance")
    labels = top["feature"].str.replace("_", " ").str.replace("pct", "%").str.title()
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.barh(labels, top["importance"], xerr=top["importance_sd"], color=palette["gold"], ecolor=palette["neutral"], capsize=3)
    ax.set(title="Permutation importance identifies the strongest predictive signals", xlabel="Decrease in fitted R² after feature permutation", ylabel="")
    fig.tight_layout(); fig.savefig(FIGURES / "figure_4_model_importance.png", dpi=220); plt.close(fig)


def write_dictionary() -> None:
    """Write concise source-aware definitions for the modeled variables."""
    rows = [
        ("fips", "5-character county FIPS code", "CDC WONDER / HRSA AHRF"),
        (TARGET, "Births below 2,500 grams as a percent of births with known weight, pooled 2020-2024", "CDC WONDER"),
        ("late_or_no_prenatal_pct", "Prenatal care beginning after month 3 or no prenatal care, percent of known records", "CDC WONDER"),
        ("tobacco_use_pct", "Maternal tobacco use during pregnancy, percent of known records", "CDC WONDER"),
        ("maternal_age_15_19_pct", "Births to mothers age 15-19, percent of age-classified births", "CDC WONDER"),
        ("maternal_age_35_plus_pct", "Births to mothers age 35-54, percent of age-classified births", "CDC WONDER"),
        ("poverty_pct", "Persons below the federal poverty level, ACS 2019-2023 (%)", "HRSA AHRF"),
        ("uninsured_under65_pct", "Persons under 65 without health insurance, 2022 (%)", "HRSA AHRF"),
        ("obgyn_per_100k", "Nonfederal general OB-GYN physicians in patient care per 100,000 residents, 2023", "HRSA AHRF"),
        ("midwives_per_100k", "Advanced practice nurse midwives with an NPI per 100,000 residents, 2024", "HRSA AHRF"),
        ("obstetric_hospitals_per_100k", "Short-term general hospitals with obstetric care per 100,000 residents, 2023", "HRSA AHRF"),
        ("log_population_density", "Natural log of 1 plus population per square mile, 2020", "HRSA AHRF"),
        ("primary_care_hpsa", "Indicator that all or part of the county had a primary care HPSA code in 2025", "HRSA AHRF"),
    ]
    pd.DataFrame(rows, columns=["variable", "definition", "source"]).to_csv(TABLES / "data_dictionary.csv", index=False)


def main() -> None:
    """Run the end-to-end preparation, modeling, export, and chart workflow."""
    for folder in [PROCESSED, FIGURES, TABLES]:
        folder.mkdir(parents=True, exist_ok=True)
    cdc, ahrf = load_cdc(), load_ahrf()
    # The inner join restricts the analysis to named CDC counties with a matching
    # HRSA record. Counties with fewer than 500 known-weight births are excluded
    # to reduce instability in the pooled outcome rate.
    df = cdc.merge(ahrf, on="fips", how="inner", validate="one_to_one")
    df = df.loc[df["births_known"] >= 500].copy()
    modeled, metrics, importance = model_data(df)
    modeled.to_csv(PROCESSED / "maternal_health_county_analysis.csv", index=False)
    metrics.to_csv(TABLES / "model_metrics.csv", index=False)
    importance.to_csv(TABLES / "model_feature_results.csv", index=False)
    modeled.sort_values(TARGET, ascending=False)[["fips", "county", TARGET, "births_known", "late_or_no_prenatal_pct", "tobacco_use_pct", "poverty_pct", "obgyn_per_100k"]].to_csv(TABLES / "county_risk_summary.csv", index=False)
    summary = modeled[[TARGET] + FEATURES].describe().T
    summary.to_csv(TABLES / "descriptive_statistics.csv")
    write_dictionary()
    make_figures(modeled, importance)
    print(json.dumps({"rows": len(modeled), "states": modeled["st_name_abbrev"].nunique(), "births": int(modeled["births_known"].sum()), "metrics": metrics.to_dict("records")}, indent=2))


if __name__ == "__main__":
    main()
