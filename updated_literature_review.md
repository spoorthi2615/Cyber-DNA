# Literature Review

## 1. Human Vulnerability Assessment in Cybersecurity: A Systematic Literature Review (2026)

### Objective of the Study
The paper presents a systematic review of Human Vulnerability Assessment (HVA) techniques used in cybersecurity. The authors analyzed research published between 2014 and 2025 to understand how human vulnerabilities are measured and assessed.

### Methodology Used
The study reviewed existing cybersecurity literature related to human behavior, phishing susceptibility, insider threats, security awareness, and user risk assessment.

### Major Findings
The authors found that human vulnerability is influenced by several factors including psychological traits, cognitive limitations, user behavior, and environmental conditions. The study also highlighted that human error remains one of the leading causes of cybersecurity incidents.

### Limitations
Most existing assessment methods evaluate only a single aspect of human vulnerability. The approaches are generally static and fail to capture behavioral changes over time. Very few studies combine psychological, behavioral, and contextual factors into one framework.

### What We Take from this Paper
This paper provides the theoretical foundation for understanding human cyber vulnerability. We adopt the concept that human behavior should be considered a measurable cybersecurity factor.

### How Our Work is Different
While this study focuses on identifying static vulnerability factors, our Cyber DNA framework continuously extracts dynamic behavior and constructs a weekly **Digital Behavioral Signature (DBS)**. We validate this on the industry-standard **CMU CERT r4.2 dataset** (1,000 corporate users, 67,167 user-weeks) using a chronological split (Weeks 1–52 for training, Weeks 53–72 for testing) to prevent temporal data leakage. We also implement a **Behavioral Drift Score (BDS)** that calculates the Euclidean distance ($L_2$ norm) of a user's weekly behavior from their baseline to mathematically capture behavioral evolution over time.

---

## 2. People, the Weak Link in Cyber-security: Can Ethnography Bridge the Gap? (2015)

### Objective of the Study
The paper investigates cybersecurity using ethnographic methods and studies how organizational culture, workplace practices, and social interactions affect security behavior.

### Methodology Used
The authors used interviews, observations, and qualitative analysis to understand the relationship between people and cybersecurity practices.

### Major Findings
The study found that user behavior is strongly influenced by social context, organizational culture, communication patterns, and beliefs. Security incidents often occur because of misunderstandings between users and security teams.

### Limitations
The study is purely qualitative and does not provide any computational framework or behavioral scoring model. It also lacks predictive capabilities.

### What We Take from this Paper
We adopt the Cyber Anthropology perspective that digital behavior cannot be understood only through technical data. Human culture, identity, and social interactions must also be considered.

### How Our Work is Different
We translate these qualitative anthropological concepts into concrete mathematical indicators:
1. **Identity Persistence ($IDP$)**: Measures the transition stability of consecutive weekly signatures.
2. **Behavioral Continuity ($BC$)**: Measures the smoothness of weekly drift shifts (standard deviation of step-to-step drifts).
3. **Social Role Consistency ($SRC$)**: Tracks the variation in a user's Interaction Footprint Score ($IPS$).

Integrating these mathematical anthropology scores into our XGBoost classifier **increases precision from 14.55% to 44.44%** on the CERT r4.2 dataset, demonstrating that cyber anthropological metrics significantly suppress false-positive alerts.

---

## 3. A Digitalized Personality-Based Human Vulnerability Assessment for Improving Cyber Security and Cyber Resilience (2024)

### Objective of the Study
The research aims to assess cybersecurity vulnerability using personality traits and psychological characteristics.

### Methodology Used
The study analyzes different personality profiles and evaluates how they influence cybersecurity decisions and risk exposure.

### Major Findings
The authors found that personality traits significantly impact cybersecurity behavior. Different personality types show different levels of cyber risk and vulnerability.

### Limitations
The framework mainly relies on personality assessments and does not incorporate actual behavioral activity, communication patterns, or interaction history.

### What We Take from this Paper
We adopt the idea that cybersecurity assessments should be personalized rather than treating all users equally.

### How Our Work is Different
Instead of relying on self-reported personality surveys, Cyber DNA collects actual behavioral evidence. Our framework continuously logs logon events, email communications, and interaction networks. The 8-dimensional DBS vector processes these events into normalized scores ($BCS$, $CSS$, $IPS$), modeling actual work habits, vocabulary diversity, response reply times, and social contact diversity.

---

## 4. Human Behaviour as an Aspect of Cyber Security Assurance (2016)

### Objective of the Study
The study investigates the role of human behavior in cybersecurity assurance and examines how human errors contribute to security breaches.

### Methodology Used
The authors reviewed cybersecurity incidents, security assurance frameworks, and human-factor research to identify weaknesses in existing approaches.

### Major Findings
The study highlights that a significant number of cybersecurity incidents occur because of human mistakes. Traditional awareness training alone is often insufficient to reduce risks.

### Limitations
The paper focuses on policy and assurance mechanisms rather than individual behavioral modeling. No behavioral profiling framework is proposed.

### What We Take from this Paper
We adopt the concept that human behavior should be continuously measured and quantified within cybersecurity systems.

### How Our Work is Different
Cyber DNA implements a fully automated, vectorized feature extraction pipeline (session pairing, lexical email content parsing, reciprocity calculation) capable of scaling to gigabytes of event logs. It processes logon activity, email text, and contact reciprocity into weekly signatures, which are evaluated by machine learning models (XGBoost, Random Forest) to continuously predict insider threats with a raw XGBoost F1-score of **11.68%** (outperforming One-Class SVM and Isolation Forest).

---

## 5. Behavioural Biometrics: A Survey and Classification (2008)

### Objective of the Study
The paper surveys behavioral biometrics techniques used for user verification and authentication.

### Methodology Used
The authors reviewed multiple behavioral biometric methods including keystroke dynamics, mouse movements, communication behavior, gait analysis, and user activity profiling.

### Major Findings
The study demonstrates that human behavior can serve as a reliable identity indicator. Behavioral characteristics remain relatively stable and can be used for verification purposes.

### Limitations
The focus is primarily on authentication and identity verification rather than understanding behavioral evolution or social behavior.

### What We Take from this Paper
We adopt the concept of using behavioral features as digital identifiers.

### How Our Work is Different
Cyber DNA extends beyond static authentication by incorporating group cohesion metrics and dynamic drift. We introduce an adaptive **Departmental Similarity Filter (Z-Score Filter)** that suppresses false-positive alerts by comparing user signatures to their department centroids ($\mathbf{DBS}_{D, W}$). This allows the system to distinguish between malicious deviations and legitimate role transitions (transfers or promotions), avoiding the limitations of pure behavioral biometrics.

---

## 6. StyleLink: User Identity Linkage Across Social Media with Stylometric Representations (2025)

### Objective of the Study
The study aims to identify the same user across different social media platforms using writing style analysis and network structures.

### Methodology Used
The authors combine stylometric analysis with Graph Neural Networks (GNNs) to perform user identity linkage.

### Major Findings
The research demonstrates that writing style remains relatively consistent across different platforms and can be used for user identification.

### Limitations
The framework focuses only on identity linkage and does not analyze long-term behavioral evolution or behavioral change.

### What We Take from this Paper
We adopt stylometric features and communication signatures as important indicators of digital identity.

### How Our Work is Different
Instead of static linkage, Cyber DNA incorporates stylometric indices (Weekly Vocabulary Diversity $VD$ and Response Time $RT$) into an active weekly DBS profile. These features are evaluated dynamically alongside activity metrics, enabling the tracking of stylistic drift over time using our **Behavioral Similarity Index (BSI)** and detecting malicious writing cadence deviations during active insider threat exfiltration phases.

---

## 7. Social Identity Construction in Digital Communities (2024)

### Objective of the Study
The research explores how social identities are formed and maintained within online communities.

### Methodology Used
The authors conducted interviews, observations, and content analysis of digital communities and social media users.

### Major Findings
The study found that social media plays a major role in identity formation through social categorization, social identification, and social comparison processes.

### Limitations
The study is qualitative and does not provide computational methods for measuring identity-related behavior.

### What We Take from this Paper
We adopt the concepts of social identity, group affiliation, and identity persistence from Cyber Anthropology and Social Identity Theory.

### How Our Work is Different
Cyber DNA maps these concepts to a computational framework by constructing weekly **departmental centroids** ($DBS_{D, W}$) across organizational units (e.g. Sales, HR, Engineering). Our calibration sweeps confirm that corporate departments exhibit a high baseline similarity ($BSI > 0.95$) with a very narrow cohesion variance ($\sigma_D \approx 0.01$), allowing us to mathematically model social role cohesion and suppress false alarms during departmental alignment shifts.

---

# Overall Research Gap

From the literature review, it is observed that existing studies focus on individual areas such as:
- Human vulnerability assessment
- Personality-based cybersecurity analysis
- Behavioral biometrics
- Identity linkage
- Digital identity formation
- Human-factor cybersecurity assurance

However, **no existing framework combines all these dimensions into a single behavioral assessment model.** Most existing approaches also perform static analysis and do not consider how behavior changes over time.

---

# Proposed Solution

To address these limitations, this research proposes **Cyber DNA**, a behavioral assessment framework that:
1. **Generates Digital Behavioral Signatures (DBS)**: Normalizes weekly authentication, communication, and interaction features into a unit hypercube vector.
2. **Computes a Behavioral Similarity Index (BSI)**: Uses cosine similarity to align signatures against baseline profiles and departmental centroids.
3. **Measures a Behavioral Drift Score (BDS)**: Traces temporal self-drift relative to baseline weeks using Euclidean distance ($L_2$ norm).
4. **Incorporates Cyber Anthropology Metrics**: Formulates metrics for Identity Persistence ($IDP$), Behavioral Continuity ($BC$), and Social Role Consistency ($SRC$) to mathematically model profile stability.
5. **Uses Machine Learning Classifier Engines**: Trains XGBoost and Random Forest models on chronological partitions (preventing leakage) for automated detection.
6. **Suppresses Legitimate Deviations**: Utilizes an adaptive Z-Score Departmental Filter to suppress false alerts during promotions or departmental transitions.

By evaluating these components on the real-world **CMU CERT r4.2 dataset**, Cyber DNA bridges the gap between Cybersecurity, Behavioral Analytics, and Cyber Anthropology, presenting a validated, dynamic framework for modeling human digital behavior.
