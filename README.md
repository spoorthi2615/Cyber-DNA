# Cyber DNA

Cyber DNA is a continuous behavioral authentication and insider threat detection framework. It addresses the limitations of standard point-in-time perimeter defenses by building longitudinal models of user behavior using enterprise logs.

This repository contains the verified Phase 11 expanded model and the React visualization dashboard. All ML evaluation metrics are leakage-free. Dashboard visualizations for Temporal Drift and BSI Similarity are computed directly from the Phase 11 feature pipeline — not illustrative or synthetic data.

---

## Final Verified Results (Phase 11 — Full Feature Set)

| Metric | Baseline | Full Phase 11 |
|---|---|---|
| **F1 Score** | 44.44% | **48.41%** |
| **Recall** | 34.15% | **46.34%** |
| **Precision** | 63.64% | **50.67%** |
| **AUPRC** | 0.4059 | **0.4490** |
| **True Positives** | 28 | **38** |
| **False Positives** | 16 | **37** |
| **False Negatives** | 54 | **44** |
| **Threshold** | 0.50 | **0.30** |
| **Features** | 16 | **29** |

* **Ground truth** — CERT r4.2 `insiders.csv` (70 malicious users, 1,069 malicious user-weeks)
* **Chronological split** — Weeks 1–52 train, Weeks 53–72 test
* **Test support (malicious)** — 82 user-weeks

All experiments are strictly leakage-free. `MinMaxScaler` normalization and threshold selection are confined to the training subset only.

---

## Repository Structure

```
cyber_dna_phase11_ablation.py   # Core leakage-free evaluation pipeline (FROZEN — do not modify)
src/
  export_to_web.py              # Exports verified ablation metrics → cyber_dna_data.json
  export_dashboard_metrics.py   # Computes real BDS curves and BSI distributions → cyber_dna_data.json
web_app/                        # React dashboard source code
results/
  phase11_ablation_metrics.csv          # Verified Phase 11 ablation table
  phase11_feature_importance.csv        # XGBoost feature importance
  phase11_run_summary.json              # Best configuration summary
  dashboard_temporal_drift.csv          # Computed weekly cohort BDS curves
  dashboard_bsi_distribution.csv        # Computed pairwise cosine BSI histogram
  dashboard_metrics_summary.json        # Full computed dashboard metrics export
data/                           # CMU CERT r4.2 dataset (not included — see below)
final_project_report.md         # Comprehensive academic report
legacy_archive/                 # Old prototype scripts (historical reference only)
```

---

## Dashboard Tabs

| Tab | Data Source | Status |
|---|---|---|
| **Overview** | `phase11_ablation_metrics.csv` | ✅ Verified Phase 11 results |
| **Ablation Study** | `phase11_ablation_metrics.csv` | ✅ Verified Phase 11 results |
| **Feature Importance** | `phase11_feature_importance.csv` | ✅ Verified Phase 11 results |
| **Research Results** | `final_project_report.md` / `phase11_run_summary.json` | ✅ Verified Phase 11 results |
| **Cyber Anthropology** | Documented benchmark interpretation thresholds | ✅ Verified Benchmark Interpretation |
| **Temporal Drift** | `dashboard_computed_metrics.temporal_drift` | ✅ Computed from pipeline (real BDS curves) |
| **BSI Similarity** | `dashboard_computed_metrics.bsi_distribution` | ✅ Computed from pipeline (real cosine BSI) |

> **Temporal Drift** shows the weekly cohort-average BDS (euclidean distance from user baseline) for benign vs. malicious user populations across Weeks 1–72. `malicious_bds=0.0` in early weeks means no ground-truth malicious user-weeks existed in those weeks, not that drift was zero.
>
> **BSI Similarity** shows the pairwise cosine similarity distribution across 499,500 user pairs (N=1000, B=930, M=70) using training-period mean DBS vectors (Weeks 1–52) to honor the leakage-free philosophy.

---

## Reproducing the Project

### 1. Prerequisites

Download the CMU CERT r4.2 dataset and extract it into:
```
data/cert_r4.2/r4.2/         # logon.csv, email.csv, device.csv, etc.
data/cert_r4.2/answers/       # insiders.csv
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### 2. Execution Order

Run the three scripts in this exact order:

**Step 1 — Run the ML Evaluation Pipeline**
```bash
python cyber_dna_phase11_ablation.py
```
Extracts features, runs the leakage-free chronological ML evaluation, and writes verified results to `results/`.

**Step 2 — Export Verified Ablation Metrics to Dashboard**
```bash
python src/export_to_web.py
```
Converts Phase 11 CSV metrics into the `web_app/src/cyber_dna_data.json` file.

**Step 3 — Compute Real Dashboard Visualization Metrics**
```bash
python src/export_dashboard_metrics.py
```
Computes the actual BDS cohort curves (Temporal Drift) and pairwise cosine BSI distribution from the pipeline feature outputs, and injects them into `cyber_dna_data.json` as `dashboard_computed_metrics`. Also exports auditable CSVs to `results/`.

**Step 4 — Launch the Dashboard**
```bash
cd web_app
npm install
npm run dev
```
Launches the React dashboard at `http://localhost:5173`.

---

## Academic Notes

* `cyber_dna_phase11_ablation.py` is the frozen evaluation engine. Do not modify it.
* `src/export_dashboard_metrics.py` is the presentation/export layer. It reads from the same feature pipeline functions but does not alter ML training or evaluation.
* The `dashboard_computed_metrics` JSON node contains auditable metadata including user counts, pair counts, vector basis definition, and a mathematical pair-count consistency check (`B*M = 65,100`).
