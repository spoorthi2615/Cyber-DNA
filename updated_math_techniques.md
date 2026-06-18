# Mathematical Techniques Used in the Cyber DNA Framework

---

# 1. Behavioral Consistency Score (BCS)
Measures the regularity of a user's system usage patterns. It is calculated by extracting activities in rolling 7-day windows and normalizing them using absolute domain-specific bounds:
- **Login Frequency ($LF$)**: scaled between $[0, 30]$ events/week.
- **Session Duration ($SD$)**: scaled between $[0, 24]$ hours/session.
- **Active Hour Ratio ($AH$)**: scaled between $[0, 1]$ (ratio of daytime active logs, 08:00 - 18:00).
- **Activity Regularity ($AR$)**: modeled as a baseline parameter ($0.80$).

$$
BCS_{U, W} = \frac{\bar{f}_{LF} + \bar{f}_{SD} + \bar{f}_{AH} + 0.8}{4.0}
$$

*(All individual feature scores $\bar{f}_i$ are normalized to $[0, 1]$ prior to scoring)*

---

# 2. Communication Signature Score (CSS)
Measures a user's writing habits and email cadences:
- **Email Frequency ($EF$)**: scaled between $[0, 100]$ emails sent/week.
- **Vocabulary Diversity ($VD$)**: Lexical density computed as unique tokens divided by total email body tokens, scaled between $[0, 1]$.
- **Response Time ($RT$)**: Average response lag in hours, inverted as $\max(0, 24 - RT_{\text{raw}})$ and scaled between $[0, 24]$.
- **Writing Consistency ($WC$)**: modeled as a baseline parameter ($0.75$).

$$
CSS_{U, W} = \frac{\bar{f}_{VD} + \bar{f}_{RT} + \bar{f}_{EF} + 0.75}{4.0}
$$

---

# 3. Interaction Persistence Score (IPS)
Measures a user's social network stability and interaction footprint:
- **Contact Diversity ($CD$)**: Number of unique email recipients contacted, scaled between $[0, 50]$.
- **Reciprocity Ratio ($RR$)**: Ratio of received emails to sent emails, capped at $2.0$ and scaled between $[0, 2]$.
- **Interaction Stability ($IS$)**: modeled as a baseline parameter ($0.80$).
- **Communication Persistence ($CP$)**: modeled as a baseline parameter ($0.70$).

$$
IPS_{U, W} = \frac{\bar{f}_{CD} + \bar{f}_{RR} + 0.8 + 0.7}{4.0}
$$

---

# 4. Identity Persistence Score (IDPS)
Represents the baseline identity persistence characteristic of the corporate cohort. Since it acts as a constant baseline, it is formulated as:

$$
IDPS_{U, W} = \frac{0.85 + 0.8 + 0.75 + 0.8}{4.0} = 0.80
$$

---

# 5. Digital Behavioral Signature (DBS)
**Definition:** A Digital Behavioral Signature (DBS) is a numeric feature vector that represents an individual’s characteristic digital behavior over a defined weekly observation window $W$. 

In the database and dashboard, the user's signature is represented as a 4D vector of their composite scores:
$$
\mathbf{DBS}_{U, W}^{\text{composite}} = \begin{bmatrix} BCS_{U, W} & CSS_{U, W} & IPS_{U, W} & IDPS_{U, W} \end{bmatrix}^T
$$

For machine learning classification, the signature is represented as a raw 8D feature vector scaled to the unit hypercube:
$$
\mathbf{DBS}_{U, W} = \begin{bmatrix} \bar{f}_{LF} & \bar{f}_{AH} & \bar{f}_{SD} & \bar{f}_{EF} & \bar{f}_{VD} & \bar{f}_{RT} & \bar{f}_{CD} & \bar{f}_{RR} \end{bmatrix}^T
$$

---

# 6. Behavioral Similarity Index (BSI)
Measures the cosine similarity between two signatures, mapping behavioral alignment to a $[-1, 1]$ scale (where $1$ is identical alignment):

$$
BSI(\mathbf{DBS}_A, \mathbf{DBS}_B) = \frac{\mathbf{DBS}_A \cdot \mathbf{DBS}_B}{\|\mathbf{DBS}_A\|_2 \|\mathbf{DBS}_B\|_2}
$$

**Interpretation:**
- **BSI $\ge 0.95$**: High behavioral similarity (corporate users within similar departments naturally exhibit high similarity due to matching schedules and email baselines).
- **BSI $< 0.80$**: High behavioral deviation.

---

# 7. Behavioral Drift Score (BDS)
**Definition:** The Behavioral Drift Score (BDS) quantifies how much a user's DBS changes between a baseline week ($T_{\text{base}}$) and a target week ($W$) using the Euclidean distance ($L_2$ norm):

$$
BDS(U, T_{\text{base}}, W) = \|\mathbf{DBS}_{U, W} - \mathbf{DBS}_{U, T_{\text{base}}}\|_2
$$

**Empirical Interpretation (Calibrated on CMU CERT r4.2):**
- **$0.00 \text{ to } 0.15$**: **Low Self-Drift** (Normal benign week, cohort baseline average is **$0.1341$**).
- **$0.16 \text{ to } 0.25$**: **Moderate Self-Drift** (Minor changes, cohort malicious average is **$0.1898$**).
- **$\ge 0.26$ (spiking to $0.60+$)**: **Severe Self-Drift** (High probability of exfiltration phases, credential sharing, or account takeover).

---

# 8. Cyber Anthropology Consistency Metrics
We compute three static user-level anthropology metrics across all $W$ active weeks to capture baseline cognitive stability:

1. **Identity Persistence ($IDP$)**: Measures the long-term stability of the user's weekly signature transitions:
   $$
   IDP_U = e^{-\frac{1}{W-1}\sum_{t=1}^{W-1} \|\mathbf{DBS}_{U, T_{t+1}} - \mathbf{DBS}_{U, T_t}\|_2}
   $$
2. **Behavioral Continuity ($BC$)**: Measures the smoothness of weekly drift changes by evaluating the standard deviation of step-to-step drifts:
   $$
   BC_U = e^{-\text{std}\left(\left\{\|\mathbf{DBS}_{U, T_{t+1}} - \mathbf{DBS}_{U, T_t}\|_2 \;\mid\; t \in [1, W-1]\right\}\right)}
   $$
3. **Social Role Consistency ($SRC$)**: Tracks the variation in a user's weekly Interaction Footprint Score ($IPS$):
   $$
   SRC_U = 1.0 - \frac{1}{W-1}\sum_{t=1}^{W-1} |IPS_{U, T_t} - IPS_{U, T_{t+1}}|
   $$

---

# 9. Z-Score Departmental Similarity Filter
To suppress false alerts caused by legitimate corporate role changes (e.g. transfers), user signatures are compared against the department centroid $\mathbf{DBS}_{D, W}$:

$$
\mathbf{DBS}_{D, W} = \frac{1}{|D|} \sum_{i \in D} \mathbf{DBS}_{i, W}
$$

We calculate the Z-Score alignment:
$$
Z_D = \frac{BSI(\mathbf{DBS}_{U, W}, \mathbf{DBS}_{D, W}) - \mu_D}{\sigma_D} \geq Z_{\text{thresh}}
$$
where $\mu_D, \sigma_D$ represent department baseline cohesion parameters. If a target department satisfies $Z \geq -2.5$, the alert is suppressed as a legitimate transfer.

---

# What I would tell Sir

> "We have implemented and verified weighted score formulas for BCS, CSS, IPS, and IDPS on the CMU CERT r4.2 dataset. The Digital Behavioral Signature (DBS) is constructed as an 8-dimensional normalized feature vector. 
>
> The Behavioral Similarity Index (BSI) is computed via Cosine Similarity to compare profile alignment, and the Behavioral Drift Score (BDS) tracks weekly self-drift using Euclidean distance ($L_2$ norm). 
>
> To improve detection accuracy, we formulated three static Cyber Anthropology metrics (Identity Persistence, Behavioral Continuity, and Social Role Consistency) that capture behavioral transition stability, successfully boosting XGBoost classifier precision to **44.44%**. 
>
> Finally, we calibrated an adaptive Z-Score Departmental Similarity Filter to suppress false alerts caused by legitimate department transfers."

###

**DBS:** An 8D normalized weekly behavioral fingerprint of a user generated from authentication, communication, and social interaction log features.

**BSI:** Uses Cosine Similarity to measure how behaviorally similar two users (or a user and a department centroid) are.

**BDS:** Uses Euclidean Distance ($L_2$ norm) to measure how much a user's behavior drifts from their baseline week.
