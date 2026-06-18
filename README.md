# Cyber DNA: A Human-Centered Behavioral Similarity Assessment Framework

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/frontend-React--Vite-cyan.svg)](https://react.dev/)
[![Dataset](https://img.shields.io/badge/dataset-CMU%20CERT%20r4.2-green.svg)](https://doi.org/10.1184/R1/12841247.v1)

Cyber DNA is a human-centered behavioral similarity assessment framework designed to continuously model user behavior in enterprise networks. Instead of relying on volatile technical indicators (like IP addresses, MAC addresses, or credentials) which are easily spoofed or obfuscated, Cyber DNA constructs weekly **Digital Behavioral Signatures (DBS)** to capture persistent, human-centric characteristics across activity patterns, communication styles, and organizational interaction networks.

The framework integrates concepts from **Cyber Anthropology** to quantify behavioral continuity and role consistency, and introduces **Behavioral Drift Analysis** to track how digital identities evolve over time.

---

## 🚀 Key Features

*   **Multi-Dimensional Behavioral Signatures (DBS)**: Constructs weekly 8D profiles from logons, stylometric email footprints (vocabulary diversity, reply lag), and network interaction networks.
*   **Behavioral Similarity Index (BSI)**: Measures alignment between distinct user profiles or users and organizational centroids using Cosine Similarity.
*   **Behavioral Drift Score (BDS)**: Tracks weekly self-drift relative to baseline weeks using Euclidean distance ($L_2$ norm).
*   **Cyber Anthropology Consistency Guardrails**: Computes static stability scores for Identity Persistence ($IDP$), Behavioral Continuity ($BC$), and Social Role Consistency ($SRC$), boosting classifier precision.
*   **Adaptive Z-Score Departmental Filter**: Suppresses false-positive alerts caused by legitimate departmental transitions (transfers or promotions) by matching drift signatures to target department centroids.
*   **Interactive React Analytics Dashboard**: A premium user interface featuring Overview statistics, Anthropology gauges, BDS drift timelines, BSI heatmaps, and Research sweeps.

---

## 📐 Mathematical Formulation

### 1. Digital Behavioral Signature (DBS)
For user $U$ and week $W$, the normalized feature vector is defined as:
$$
\mathbf{DBS}_{U, W} = \begin{bmatrix} \bar{f}_{LF} & \bar{f}_{AH} & \bar{f}_{SD} & \bar{f}_{EF} & \bar{f}_{VD} & \bar{f}_{RT} & \bar{f}_{CD} & \bar{f}_{RR} \end{bmatrix}^T
$$
*Where: LF = Logon Frequency, AH = Active Hour Ratio, SD = Session Duration, EF = Email Frequency, VD = Vocabulary Diversity, RT = Inverted Response Time, CD = Contact Diversity, RR = Reciprocity Ratio.*

### 2. Behavioral Similarity Index (BSI)
Calculates profile alignment between two signatures via Cosine Similarity:
$$
BSI(\mathbf{DBS}_A, \mathbf{DBS}_B) = \frac{\mathbf{DBS}_A \cdot \mathbf{DBS}_B}{\|\mathbf{DBS}_A\|_2 \|\mathbf{DBS}_B\|_2}
$$

### 3. Behavioral Drift Score (BDS)
Measures weekly behavioral shift relative to baseline week $T_{\text{base}}$ via Euclidean distance:
$$
BDS(U, T_{\text{base}}, W) = \|\mathbf{DBS}_{U, W} - \mathbf{DBS}_{U, T_{\text{base}}}\|_2
$$

### 4. Cyber Anthropology stability metrics
- **Identity Persistence ($IDP$)**: Transition stability:
  $$IDP_U = e^{-\frac{1}{W-1}\sum_{t=1}^{W-1} \|\mathbf{DBS}_{U, T_{t+1}} - \mathbf{DBS}_{U, T_t}\|_2}$$
- **Behavioral Continuity ($BC$)**: Smoothness of weekly drift step variations:
  $$BC_U = e^{-\text{std}\left(\left\{\|\mathbf{DBS}_{U, T_{t+1}} - \mathbf{DBS}_{U, T_t}\|_2 \;\mid\; t \in [1, W-1]\right\}\right)}$$
- **Social Role Consistency ($SRC$)**: Footprint stability:
  $$SRC_U = 1.0 - \frac{1}{W-1}\sum_{t=1}^{W-1} |IPS_{U, T_t} - IPS_{U, T_{t+1}}|$$

---

## 🛠️ Project Structure

```text
Cyber-DNA/
│
├── .gitignore                  # Git exclude configurations
├── README.md                   # Project documentation
├── cyber_dna_prototype.py      # Entry point for baseline data generation
├── final_project_proposal.md   # Full academic proposal document
│
├── src/                        # Python Core Pipeline
│   ├── preprocess.py           # Ingestion and normalization logic
│   ├── signature.py            # DBS builder and anthropology calculators
│   ├── engine.py               # BSI, BDS, and Department Centroid filter
│   ├── models.py               # XGBoost & Random Forest classifier training
│   ├── mock_generator.py       # Synthetic cohort generator (Alice, Bob, etc.)
│   └── calibrate_dept_filter.py # Calibration scripts for Z-Score filters
│
├── results/                    # Saved Evaluation Metrics & Plots
│   └── formulas/               # High-res formula PNGs for reports
│
├── screenshots/                # Dashboard interface screenshots
│
└── web_app/                    # Vite + React Analytics Dashboard UI
    ├── src/
    │   ├── App.jsx             # Core React dashboard components
    │   ├── index.css           # Dashboard styling
    │   └── cyber_dna_data.json # Visualized cohort JSON dataset
    ├── index.html
    └── vite.config.js
```

---

## 📦 Getting Started

### Prerequisites
- Python 3.8+
- Node.js (v16+) & npm

### 1. Ingesting & Running Python Pipeline
Clone the repository and install the Python dependencies:
```bash
git clone https://github.com/spoorthi2615/Cyber-DNA.git
cd Cyber-DNA
pip install pandas numpy scikit-learn xgboost matplotlib
```

To run the pipeline and perform features calibration on the cohort:
```bash
python src/run_sweep_diagnostic.py
```

### 2. Launching React Analytics Dashboard
Navigate to the web dashboard directory, install Node packages, and start the local development server:
```bash
cd web_app
npm install
npm run dev
```
Open [http://localhost:5173/](http://localhost:5173/) in your browser to view the interactive interface.

---

## 📊 Evaluation & Gaps Bridged

Typical insider threat systems perform static user-week evaluations. Cyber DNA's primary contributions include:
1. **Dynamic Timelines**: Employs rolling $BDS$ timelines instead of static audits.
2. **Anthropology Fusion**: Incorporates $IDP$, $BC$, and $SRC$ stability metrics into classifiers, which significantly suppresses false-alarm alerts and increases precision.
3. **Legitimate Suppression**: Utilizes the Z-score Departmental Filter to suppress false-positive alarms triggered by legitimate employee transfers.

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
