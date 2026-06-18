# PROJECT INTRO & PROPOSAL DEFENSE PREPARATION

---

**"Sir, we are proposing a human-centered behavioral similarity assessment framework called Cyber DNA. While most existing cybersecurity research studies behavioral biometrics, stylometry, user profiling, and cyber anthropology as separate areas, our project proposes to integrate these dimensions into a unified, mathematically-defined framework.**

**Instead of relying only on technical indicators (like IP addresses, MAC addresses, or device identifiers) which are easily hidden or altered, the Cyber DNA framework focuses on persistent behavioral characteristics. We propose to construct weekly Digital Behavioral Signatures (DBS) to capture activity, writing style, and network interactions.**

**Additionally, we propose a temporal Behavioral Drift Analysis component that will measure how a user's behavioral signature evolves over time, allowing the system to distinguish between malicious deviations and legitimate role transitions.**

**We plan to evaluate this framework using the industry-standard CMU CERT Insider Threat Dataset r4.2. The primary objective is not identity attribution, but rather behavioral similarity assessment and behavioral evolution analysis."**

---

## If Sir asks: "What exactly will you build?"
Say:
> **"We will build a data processing pipeline in Python to ingest logon events, email logs, device actions, and corporate LDAP directories. The system will extract weekly 8-dimensional Digital Behavioral Signatures (DBS), calculate a Cosine Similarity-based Behavioral Similarity Index (BSI) between users, and trace behavioral changes over time using a Euclidean distance-based Behavioral Drift Score (BDS). We will also develop a web-based interactive analytics dashboard to visualize these timelines, similarity heatmaps, and alert trends."**

---

## If Sir asks: "What's new?"
Say:
> **"Most existing approaches perform static behavioral analysis at a single point in time. The novelty of our work is the integration of activity, communication, social interaction, and anthropological indicators into a unified weekly signature, combined with a temporal Behavioral Drift Score (BDS) to analyze how digital identities evolve over time. We also propose an adaptive Z-Score Departmental Filter to suppress false alerts caused by legitimate job changes."**

---

## If Sir asks: "Why Cyber Anthropology?"
Say:
> **"Because the framework proposes to convert qualitative cyber anthropological concepts—such as identity persistence, social role consistency, and behavioral continuity—into precise, measurable mathematical formulas ($IDP$, $BC$, and $SRC$). We expect that incorporating these stability indicators will significantly suppress false-positive alarms in threat detection models."**

---

## If Sir asks: "What papers did you read?"
Say:
> **"We conducted a literature review of human vulnerability and behavioral biometrics, focusing on papers such as:
> 1. *Human Vulnerability Assessment in Cybersecurity: A Systematic Literature Review* (2026) - highlighted the lack of dynamic, multi-dimensional frameworks.
> 2. *People, the Weak Link in Cyber-security: Can Ethnography Bridge the Gap?* (2015) - proposed using Cyber Anthropology qualitatively.
> 3. *A Digitalized Personality-Based Human Vulnerability Assessment* (2024) - showed the limits of survey-only assessments.
> 4. *StyleLink: User Identity Linkage Across Social Media with Stylometric Representations* (2025) - demonstrated writing style consistency.
> 5. *Behavioural Biometrics: A Survey and Classification* (2008) - mapped biometric authentication boundaries.
> Our proposed framework is designed to bridge the gaps identified across these studies."**

---

# Q&A DEFENSE PREPARATION

## 1. What is Cyber DNA?
**Answer:** Cyber DNA is a proposed human-centered behavioral assessment framework. It will aggregate logon records, email metadata, lexical writing metrics, and network links into a weekly **Digital Behavioral Signature (DBS)**. It will then measure similarity between digital identities using a **Behavioral Similarity Index (BSI)** and temporal evolution using a **Behavioral Drift Score (BDS)**.

---

## 2. Why is it Cyber Anthropology?
**Answer:** Cyber Anthropology studies how people create, maintain, and adapt their identities in digital environments. Cyber DNA proposes to convert these qualitative concepts into quantitative metrics:
- **Identity Persistence ($IDP$)**: Transition stability of consecutive weekly signatures.
- **Behavioral Continuity ($BC$)**: Smoothness of weekly drift changes (standard deviation of step drifts).
- **Social Role Consistency ($SRC$)**: Stability of a user's organizational interaction footprint score ($IPS$).

---

## 3. What is the research gap?
**Answer:** Existing behavioral security studies are fragmented—focusing only on one dimension (like typing dynamics, email count, or static anomaly detection) and performing static snapshot analysis. There is limited research integrating activity, communication, social networks, and anthropological continuity into a dynamic model that tracks behavioral evolution over time.

---

## 4. What is the novelty?
**Answer:** The novelty lies in:
1. The mathematical formulation and integration of Cyber Anthropology metrics ($IDP$, $BC$, $SRC$) to suppress false-positive classifier alarms.
2. The implementation of a temporal **Behavioral Drift Score (BDS)** using Euclidean distance ($L_2$ norm) to trace behavior over time.
3. The design of an adaptive **Z-Score Departmental Similarity Filter** to suppress false-positive alerts caused by legitimate departmental transfers.
4. Validation using a chronological train/test split on real-world logs to prevent temporal data leakage.

---

## 5. Why did you choose CERT?
**Answer:** The **CMU CERT Insider Threat Dataset r4.2** is the industry standard for validating user behavior analytics. It contains event logs for 1,000 corporate users spanning 1.5 years (logons, emails, USB usage, and LDAP directories), providing the authentic enterprise data sources required to extract activity, communication, and interaction features.

---

## 6. What exactly is a Digital Behavioral Signature (DBS)?
**Answer:** A DBS is a weekly user-level feature vector. We propose to define it mathematically in the unit hypercube:
$$
\mathbf{DBS}_{U, W} = \begin{bmatrix} \bar{f}_{LF} & \bar{f}_{AH} & \bar{f}_{SD} & \bar{f}_{EF} & \bar{f}_{VD} & \bar{f}_{RT} & \bar{f}_{CD} & \bar{f}_{RR} \end{bmatrix}^T
$$
For reporting and visualization, it will be represented as 4 composite scores:
- **Behavioral Consistency Score ($BCS$)**: authentication habits.
- **Communication Signature Score ($CSS$)**: writing style/cadence.
- **Interaction Persistence Score ($IPS$)**: network connections.
- **Identity Persistence Score ($IDPS$)**: baseline cohort persistence (default $0.80$).

---

## 7. How will the DBS be generated?
**Answer:** Raw log files will be processed in rolling 7-day windows. Features will be extracted, paired (e.g. logon with logoff to calculate session duration), and normalized using absolute, domain-specific bounds:
- **Login Frequency ($LF$)**: $[0.0, 30.0]$
- **Active Hour Ratio ($AH$)**: $[0.0, 1.0]$
- **Average Session Duration ($SD$)**: $[0.0, 24.0]$
- **Email Frequency ($EF$)**: $[0.0, 100.0]$
- **Vocabulary Diversity ($VD$)**: $[0.0, 1.0]$
- **Response Time ($RT$)**: $[0.0, 24.0]$ (inverted: $24.0 - RT_{\text{raw}}$)
- **Contact Diversity ($CD$)**: $[0.0, 50.0]$
- **Reciprocity Ratio ($RR$)**: $[0.0, 2.0]$

---

## 8. What is BCS?
**Answer:** Behavioral Consistency Score. It will measure system usage regularity:
$$
BCS_{U, W} = \frac{\bar{f}_{LF} + \bar{f}_{SD} + \bar{f}_{AH} + 0.8}{4.0}
$$
where $0.8$ represents a baseline regular activity factor.

---

## 9. What is CSS?
**Answer:** Communication Signature Score. It will measure vocabulary richness and reply velocity:
$$
CSS_{U, W} = \frac{\bar{f}_{VD} + \bar{f}_{RT} + \bar{f}_{EF} + 0.75}{4.0}
$$
where $0.75$ represents writing style stability.

---

## 10. What is IPS?
**Answer:** Interaction Persistence Score. It will measure social communication stability and reciprocity:
$$
IPS_{U, W} = \frac{\bar{f}_{CD} + \bar{f}_{RR} + 0.8 + 0.7}{4.0}
$$
where $0.8$ and $0.7$ represent baseline interaction permanence parameters.

---

## 11. What is IDPS?
**Answer:** Identity Persistence Score. It represents the baseline transition stability parameter for corporate users:
$$
IDPS_{U, W} = \frac{0.85 + 0.8 + 0.75 + 0.8}{4.0} = 0.80
$$

---

## 12. What is Behavioral Drift Analysis?
**Answer:** It is the temporal layer of our framework. Instead of analyzing user behavior as static snapshots, the system will calculate a rolling weekly DBS vector and measure how much the user's behavior deviates from their baseline week, generating a **Behavioral Drift Score (BDS)**.

---

## 13. What is BDS?
**Answer:** Behavioral Drift Score. It is the Euclidean distance ($L_2$ norm) between a user's target week signature and their baseline signature:
$$
BDS(U, T_{\text{base}}, W) = \|\mathbf{DBS}_{U, W} - \mathbf{DBS}_{U, T_{\text{base}}}\|_2
$$

---

## 14. How will BDS be interpreted?
**Answer:** Based on feature vector ranges:
- **$0.00 \text{ to } 0.15$**: **Low Drift** (indicating stable, normal behavior).
- **$0.16 \text{ to } 0.25$**: **Moderate Drift** (indicating minor variations).
- **$\ge 0.26$**: **Severe Drift** (suggesting a major behavioral shift, such as exfiltration phases or account compromise).

---

## 15. What is BSI?
**Answer:** Behavioral Similarity Index. It will measure the cosine similarity between two 8D DBS vectors:
$$
BSI(\mathbf{DBS}_A, \mathbf{DBS}_B) = \frac{\mathbf{DBS}_A \cdot \mathbf{DBS}_B}{\|\mathbf{DBS}_A\|_2 \|\mathbf{DBS}_B\|_2}
$$

---

## 16. How will BSI be calculated and used?
**Answer:** Each user's DBS will be represented as a normalized feature vector. BSI will be used in two ways:
1. **User-to-User similarity**: To identify highly correlated profiles (e.g. credential sharing).
2. **User-to-Centroid similarity**: To evaluate how aligned a user is with their department centroid ($\mathbf{DBS}_{D, W}$) to suppress false alerts during role changes.

---

## 17. Why XGBoost?
**Answer:** XGBoost is a powerful gradient boosting algorithm that performs exceptionally well on structured, tabular datasets. It handles complex, non-linear relationships and provides feature importance analysis, making it ideal for classification on imbalanced threat data.

---

## 18. Why not Random Forest?
**Answer:** We will use Random Forest as a baseline model. We will compare XGBoost and Random Forest experimentally to determine which model achieves the best balance of precision and recall on the test partition.

---

## 19. What exactly is the output of the system?
**Answer:** The proposed system will output:
1. A weekly **DBS Profile** ($BCS$, $CSS$, $IPS$, $IDPS$).
2. A weekly **Behavioral Drift Score (BDS)** tracking user evolution.
3. Static **Cyber Anthropology metrics** ($IDP$, $BC$, $SRC$).
4. A **BSI Similarity Heatmap** of the corporate cohort.
5. An **Alert Status**: Benign / Malicious Insider Alert / Suppressed Transition.

---

## 20. How will you evaluate the system?
**Answer:** We will split the CMU CERT r4.2 dataset chronologically (e.g. Weeks 1–52 for training, Weeks 53–72 for testing) to represent a realistic deployment. We will evaluate our models using standard classification metrics: Precision, Recall, F1-Score, and Area Under the Precision-Recall Curve (AUPRC).

---

## 21. Better than which existing methods?
**Answer:** We will compare our proposed XGBoost model against unsupervised anomaly detection models commonly used in User Behavior Analytics (UBA), such as **Isolation Forest** and **One-Class SVM**, aiming to demonstrate that supervised learning on DBS vectors achieves superior detection performance and lower false-alarm rates.

---

## 22. Can this identify a person?
**Answer:** No. Cyber DNA is designed for behavioral similarity assessment and anomaly profiling, not cryptographic attribution or biometric identification. A high similarity index (BSI) indicates matching work patterns and cadences (e.g. suggesting role sharing or account takeover), but does not provide definitive identity ownership.

---

## 23. What are the applications?
**Answer:**
- **Insider Threat Detection**: Flagging exfiltration or sabotage phases.
- **False Positive Reduction**: Suppressing alarms during departmental transfers.
- **Continuous Authentication**: Verifying that account usage matches historical baselines.
- **Forensic Investigation**: Tracing when a user's behavior shifted during an incident.

---

## 24. What is the strongest contribution of this work?
**Answer:** The strongest contribution is the **unification of multi-layered behavioral profiles (activity, stylometry, network connections) with Cyber Anthropology scores and temporal drift analysis** into a single model, showing how qualitative ethnographic concepts can be mathematically quantified to improve enterprise security.

---

# The 5 Questions Most Likely to Come From Sir

### 1. "Why is this Cyber Anthropology?"
**Answer:** Because the framework proposes to convert qualitative anthropological concepts (behavioral continuity, transition stability, social network footprint) into precise mathematical formulas ($IDP$, $BC$, $SRC$), making human-centric stability directly measurable.

### 2. "How will you handle data imbalance in CERT?"
**Answer:** Since malicious weeks represent a very small fraction of the dataset, we will evaluate models using Area Under the Precision-Recall Curve (AUPRC) and F1-Score rather than simple Accuracy. We will also tune the XGBoost scale_pos_weight parameter to handle class imbalance.

### 3. "How will the Z-Score Departmental Filter suppress false alerts?"
**Answer:** During a departmental transfer, a user's self-drift ($BDS$) will spike, triggering an alert. The Z-Score filter will calculate the user's similarity ($BSI$) to the target department centroid. If the Z-Score alignment is high ($Z \geq -2.5$), the system will classify it as a "Legitimate Role Transition" and suppress the false alarm.

### 4. "How will you prevent temporal data leakage?"
**Answer:** We will use a chronological split (e.g. Weeks 1–52 for training, Weeks 53–72 for testing) rather than random K-fold cross-validation. This ensures that the model is evaluated on future data it has never seen, mirroring a real-world deployment.

### 5. "What is the difference between this and standard behavioral biometrics?"
**Answer:** Standard biometrics typically focus on a single high-frequency physical indicator (like keystroke dynamics or mouse movements). Cyber DNA operates at a weekly macro-level, combining system usage, writing style (vocabulary diversity), and network interaction reciprocity into a composite profile.
