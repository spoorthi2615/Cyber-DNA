# What Cyber DNA actually does?

### Input

Enterprise user log data from the **CMU CERT Insider Threat Dataset r4.2** (or corporate logs):

- **Authentication records** (`logon.csv`): Logon/logoff timestamps, device IDs.
- **Email communications** (`email.csv`): Timestamp, sender, recipients, text body content.
- **File & Device records** (`device.csv`, `file.csv`): USB connection events, file access.
- **Organizational context** (`ldap.csv`): Monthly corporate directories mapping users to departments.

---

### Step 1: Extract behavioral features

The system extracts 8 normalized features across rolling **7-day weekly windows**:

1. **Login Frequency ($LF$)**: Weekly count of logon events.
2. **Active Hour Ratio ($AH$)**: Ratio of activities performed during standard business hours (08:00 - 18:00).
3. **Average Session Duration ($SD$)**: Average duration of logon-logoff sessions.
4. **Email Frequency ($EF$)**: Number of sent emails per week.
5. **Vocabulary Diversity ($VD$)**: Lexical density computed as unique tokens divided by total tokens in email bodies.
6. **Response Time ($RT$)**: Average response lag in hours for replied emails (inverted so faster response is higher).
7. **Contact Diversity ($CD$)**: Number of unique email recipients contacted.
8. **Reciprocity Ratio ($RR$)**: Ratio of received emails to sent emails.

---

### Step 2: Generate a Digital Behavioral Signature (DBS)

These 8 normalized features are scaled to the unit hypercube $[0, 1]^8$ to form the **Digital Behavioral Signature (DBS)** vector:

$$
\mathbf{DBS}_{U, W} = \begin{bmatrix} \bar{f}_{LF} & \bar{f}_{AH} & \bar{f}_{SD} & \bar{f}_{EF} & \bar{f}_{VD} & \bar{f}_{RT} & \bar{f}_{CD} & \bar{f}_{RR} \end{bmatrix}^T
$$

From this vector, the system computes 4 weekly composite scores:

- **Behavioral Consistency Score ($BCS$)**: System usage regularity.
- **Communication Signature Score ($CSS$)**: Writing cadence and text diversity.
- **Interaction Persistence Score ($IPS$)**: Social contact footprint and reciprocity.
- **Identity Persistence Score ($IDPS$)**: Default baseline persistence parameter ($0.80$).

This weekly vector becomes the user's **behavioral fingerprint**.

---

### Step 3: Calculate Behavioral Similarity (BSI)

Compare the signatures of two users, or a user against their department baseline centroid ($\mathbf{DBS}_{D, W}$):

$$
BSI(\mathbf{DBS}_A, \mathbf{DBS}_B) = \frac{\mathbf{DBS}_A \cdot \mathbf{DBS}_B}{\|\mathbf{DBS}_A\|_2 \|\mathbf{DBS}_B\|_2}
$$

**Meaning:**
- **High BSI ($\ge 0.95$)**: Uniform behavioral footprints (e.g. corporate departments share highly uniform schedules and basic email counts).
- **Lower BSI**: Distinct behavioral habits.

---

### Step 4: Behavioral Drift Analysis (New Part)

Generate a DBS for each consecutive week and measure the distance from the baseline week ($T_{\text{base}}$) using Euclidean distance ($L_2$ norm) to calculate the **Behavioral Drift Score (BDS)**:

$$
BDS(U, T_{\text{base}}, W) = \|\mathbf{DBS}_{U, W} - \mathbf{DBS}_{U, T_{\text{base}}}\|_2
$$

**Output:**
- **Low Drift ($BDS \approx 0.13$)**: Normal, stable behavior.
- **High Drift ($BDS \ge 0.19$ or spikes to $0.60+$)**: Major behavioral shift (e.g. exfiltration spikes, credential sharing, or account compromise).

[NOTE: Behavioral Drift Analysis is an additional layer in Cyber DNA that measures how a user's Digital Behavioral Signature changes over time. Existing behavioral analytics methods generally analyze behavior at a single point in time, whereas our approach studies behavioral evolution through a weekly Behavioral Drift Score. This allows Cyber DNA not only to assess behavioral similarity but also to understand how digital identities change and adapt over time, making the framework more dynamic and research-oriented.]

---

# Final Output

For every user-week, the classifier generates a **Cyber DNA Profile**:

```
Cyber DNA Profile (User-Week)

Behavioral Features (DBS):
  BCS = 0.86  (Consistency)
  CSS = 0.76  (Communication)
  IPS = 0.88  (Interaction)
  IDPS = 0.80 (Default Base)

Static Anthropology Scores:
  IDP  = 0.8647 (Identity Persistence - Transition stability)
  BC   = 0.9238 (Behavioral Continuity - Drift smoothness)
  SRC  = 0.9858 (Social Role Consistency - Network stability)

Temporal Drift (BDS) = 13.41%

Classification: Benign / Stable (Alert Suppressed via Departmental Similarity Filter)
```

---

# One-line answer

> **Cyber DNA creates a weekly behavioral fingerprint of a user from activity, communication, and interaction patterns, measures similarity between digital identities, and analyzes how those behaviors evolve over time using Behavioral Drift Analysis, verified on the CMU CERT r4.2 dataset.**
> 

---

# What makes it different?

Most existing work does **one thing**:

- **Behavioral biometrics** → typing/login behavior
- **Stylometry** → writing style (vocabulary only)
- **User profiling** → raw activity counts
- **Insider threat systems** → static anomaly detection without temporal context

Your project integrates all of these layers with **Cyber Anthropology** and **Cohesion Filtering**:

```
  Activity Behavior (Logons, Active Hours, Sessions)
+ Communication Behavior (Email Frequency, Vocabulary Diversity, Response Time)
+ Interaction Behavior (Contact Diversity, Reciprocal Communication)
+ Cyber Anthropology (Identity Persistence, Behavioral Continuity, Social Role Consistency)
+ Temporal Behavioral Drift (BDS Timeline tracing)
+ Departmental Similarity Filter (Z-Score suppression of legitimate transitions)
===================================================================================
= Cyber DNA Framework
```

### Core Differentiator:
1. **Dynamic Temporal Tracking**: Incorporating weekly $BDS$ timelines instead of static snapshot audits.
2. **False Alarm Suppression**: A **Z-Score Departmental Similarity Filter** that automatically suppresses alerts during legitimate corporate transfers (e.g. mapping transition signatures to target department centroids).
3. **Cyber Anthropology Guardrails**: Integrating $IDP$, $BC$, and $SRC$ consistency scores, which successfully **increases XGBoost classifier precision from 14.55% to 44.44%** on the real-world CMU CERT r4.2 dataset.
