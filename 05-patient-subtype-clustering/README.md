# Patient Subtype Clustering in ALS Progression Data

An unsupervised learning project that groups ALS patients by clinical progression profile without
using any outcome label, then validates and visualizes the resulting structure.

## Problem

ALS presents and progresses differently across patients, and those differences matter for trial
design and care planning. Supervised methods need a label defining what you are looking for. The
value of clustering here is that it does not — it asks whether patients fall into natural groups
based on clinical measurements alone, letting the structure emerge instead of imposing it.

## Data

**ALS clinical dataset** — patient-level records aggregated into summary statistics (max, median,
min, range, and slope) across a wide panel of clinical measures.

Features selected for clustering cover disease progression and motor function:

- **ALSFRS** functional rating scores, including total scores and progression slope
- **Motor function measures** — hand, leg, and respiratory function
- **Lab values** — albumin and liver enzyme panels
- **Demographics** — age and gender

| File | Description |
|---|---|
| `data/als_patient_data.csv` | Patient-level clinical summary statistics |

## Approach

1. **Feature selection with a clinical rationale.** Rather than dumping every column into the
   model, selected features tied to ALS progression, motor function, and disease onset — because in
   distance-based clustering, irrelevant features are not neutral, they actively distort the
   geometry.
2. **Standard scaling.** K-Means minimizes Euclidean distance, so unscaled features let whichever
   variable has the largest raw units dominate the result. Scaling is mandatory here, not optional.
3. **Choose k with silhouette analysis.** Plotted silhouette scores across candidate values of k
   rather than picking a number by eye.
4. **Fit K-Means** at the selected k.
5. **PCA to two components** purely for visualization, then a scatterplot colored by cluster
   assignment to visually confirm separation.

## Key findings

- **Silhouette scores were strong at both k=2 and k=3.** Chose **k=3** to preserve finer distinctions
  in how the disease affects patients that two clusters would collapse — a judgment call trading a
  small amount of cluster cohesion for interpretive resolution, documented as such in the notebook.
- The PCA projection showed **reasonably distinct groupings**, confirming that K-Means found real
  structure rather than partitioning noise.
- The clusters reflect genuine variation in ALS progression profiles, which is the practical
  takeaway: patient subtypes are visible in routine clinical measurements without needing an
  outcome label.

## What's in this folder

```
code/          Clustering notebook (feature selection → scaling → silhouette → K-Means → PCA)
data/          ALS patient clinical summary data
deliverables/  Exported notebook PDF
```

## Tools

Python · scikit-learn (KMeans, StandardScaler, PCA, silhouette_score) · pandas · matplotlib

## Notes and limitations

- **K-Means assumes roughly spherical, similarly-sized clusters.** Clinical data often violates
  this. DBSCAN or Gaussian mixture models would be the right comparison to run next.
- Cluster assignments are **descriptive, not diagnostic**. Nothing here should inform individual
  patient care, and no clinical validation of the subtypes was performed.
- PCA is used only to make the result visible in two dimensions; clustering was performed in the
  full scaled feature space, so the plot understates true separation.
- Choosing k=3 over k=2 was a deliberate trade. A different analyst could reasonably choose k=2.
