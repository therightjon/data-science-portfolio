# Data Science Portfolio — Jonathan Steen

Ten end-to-end data science projects, built across a data science program and collected here as a
single portfolio. Each project folder is self-contained: problem framing, data, analysis code, and
the written deliverables that came out of it.

**Live site:** https://therightjon.github.io/data-science-portfolio/

## Projects

| # | Project | Focus | What it does |
|---|---|---|---|
| 01 | [Predicting Cannabis Use from Survey Data](01-cannabis-use-prediction) | Classification | Logistic regression and decision trees over 108,252 national health survey records. Correcting class imbalance lifted recall on cannabis users from 17% to 64%. |
| 02 | [Where Families Pay the Most for Childcare](02-childcare-cost-analysis) | Data storytelling | One county-level pricing story told three ways — interactive dashboard, infographic, and executive deck. Geography drives a $128 weekly spread between the 10th and 90th percentile counties. |
| 03 | [CodeType Trainer](03-codetype-trainer-llm-app) | Generative AI | A fine-tuned GPT-3.5 model that emits clean, executable Python, shipped as a Streamlit typing trainer. Dataset construction through fine-tuning to a working app. |
| 04 | [U.S. Retail Sales Forecasting](04-retail-sales-forecasting) | Time series | Prophet forecasting 12 months ahead across 30 years of national sales, with a held-out year that contains the pandemic demand shock. |
| 05 | [Patient Subtype Clustering in ALS](05-patient-subtype-clustering) | Unsupervised learning | K-Means over clinical progression measures, k chosen by silhouette analysis and validated in PCA space. Subtypes emerge without an outcome label. |
| 06 | [Handwritten Digit Recognition](06-handwritten-digit-cnn) | Deep learning | A convolutional network built from scratch in Keras, reaching 97% test accuracy on MNIST, evaluated per digit class. |
| 07 | [Content-Based Movie Recommender](07-movie-recommender) | Recommender systems | TF-IDF over genre tags and cosine similarity across 87,000 MovieLens titles, with fuzzy title matching and no cold-start problem. |
| 08 | [Vehicle Theft Trend Analysis](08-vehicle-theft-trend-analysis) | Analysis in R | Separating a targeted Kia/Hyundai theft surge from background growth in auto theft, then costing a prevention recommendation. |
| 09 | [Maternal Health Access Across U.S. Counties](09-maternal-health-access) | Regression | CDC WONDER natality joined to HRSA resource files across 578 counties and 14.4 million births. A random forest explained 57% of county variation in low birth weight. |
| 10 | [Identifying Risk Factors for Postpartum Depression](10-postpartum-depression-risk-factors) | Classification | Excluding 32 outcome-leaking screening fields leaves the honest problem: 0.76 test ROC-AUC from routine characteristics, with prior depression and low support the strongest signals. |

## How each project is organized

```
code/            Analysis notebook or script
data/            Source data and documentation (large files noted, not committed)
deliverables/    White paper, slides, and recorded presentation where produced
figures/         Exported charts
process/         Proposal and drafts, where the assignment produced them
```

Not every project has every folder — the structure follows what the work actually produced.

## Tools

**Python** — pandas, NumPy, scikit-learn, TensorFlow/Keras, Prophet, Streamlit, rapidfuzz,
matplotlib, seaborn, Jupyter
**R** — ggplot2
**Other** — OpenAI fine-tuning API, HTML/CSS/JavaScript, PowerPoint

## About the site

The portfolio front end is a static page — `index.html`, `styles.css`, and `script.js` with no build
step — published through GitHub Pages. Each project card links to that project's folder, where the
README renders as the case study.

## Contact

[Email](mailto:therightjon@gmail.com) · [GitHub](https://github.com/therightjon) ·
[LinkedIn](https://www.linkedin.com/in/jonsteen/)
