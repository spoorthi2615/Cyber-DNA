import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from xgboost import XGBClassifier
import os
import sys

# Append parent dir to path if running directly in src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocess import CERTDataLoader
from extractors.activity import extract_activity_features
from extractors.communication import extract_communication_features
from extractors.interaction import extract_interaction_features
from signature import SignatureBuilder

class CyberDNAClassifier:
    def __init__(self, data_dir='data/cert_cohort'):
        self.data_dir = data_dir
        
    def generate_large_cohort(self, num_users=100, anomaly_ratio=0.05):
        """
        Generates raw logs for a cohort of users to build a larger training dataset.
        Also generates and saves the ldap.csv user directory.
        - Regular users: normal daytime office hours, low emails.
        - Anomaly users: normal first 2 weeks, severe drift in weeks 3-4.
        """
        os.makedirs(self.data_dir, exist_ok=True)
        print(f"Generating synthetic cohort logs for {num_users} users in {self.data_dir}...")
        
        num_anomalous = int(num_users * anomaly_ratio)
        anomalous_users = [f"ThreatUser_{i}" for i in range(num_anomalous)]
        normal_users = [f"User_{i}" for i in range(num_users - num_anomalous)]
        
        start_date = pd.to_datetime("2026-06-01 08:00:00")
        
        logon_records = []
        email_records = []
        device_records = []
        ldap_records = []
        
        logon_id = 1
        email_id = 1
        device_id = 1
        
        # 1. Map users to departments (for LDAP directory)
        depts = ['HR', 'Sales', 'Engineering']
        
        # Normal users
        for idx, user in enumerate(normal_users):
            dept = depts[idx % len(depts)]
            ldap_records.append([user.replace('_', ' '), user, f"{user.lower()}@company.com", "Employee", dept])
            
        # Anomalous users (all assigned to Engineering)
        for user in anomalous_users:
            ldap_records.append([user.replace('_', ' '), user, f"{user.lower()}@company.com", "Developer", "Engineering"])
        
        # Save LDAP directory
        pd.DataFrame(ldap_records, columns=['employee_name', 'user_id', 'email', 'role', 'department']).to_csv(
            os.path.join(self.data_dir, 'ldap.csv'), index=False
        )
        
        # 2. Daily Log Generation
        for week in range(4):
            week_start = start_date + pd.Timedelta(weeks=week)
            
            for day in range(5):  # Monday-Friday
                current_day = week_start + pd.Timedelta(days=day)
                
                # Normal users logs
                for idx, user in enumerate(normal_users):
                    h_on = np.random.choice([8, 9, 10])
                    h_off = np.random.choice([16, 17, 18])
                    t_on = current_day.replace(hour=h_on, minute=np.random.randint(0, 59))
                    t_off = current_day.replace(hour=h_off, minute=np.random.randint(0, 59))
                    
                    logon_records.append([f"L-{logon_id}", t_on.strftime('%m/%d/%Y %H:%M:%S'), user, 'PC-Normal', 'Logon'])
                    logon_id += 1
                    logon_records.append([f"L-{logon_id}", t_off.strftime('%m/%d/%Y %H:%M:%S'), user, 'PC-Normal', 'Logoff'])
                    logon_id += 1
                    
                    if np.random.rand() > 0.3:
                        email_time = current_day.replace(hour=np.random.randint(9, 16), minute=np.random.randint(0, 59))
                        email_records.append([
                            f"E-{email_id}", email_time.strftime('%m/%d/%Y %H:%M:%S'), user, 'PC-Normal',
                            'internal@company.com', '', '', user, 12000, 'none',
                            "Status report update for the team review."
                        ])
                        email_id += 1
                        
                # Anomalous users logs
                for user in anomalous_users:
                    is_anom_week = (week >= 2)
                    
                    if not is_anom_week:
                        h_on = np.random.choice([8, 9, 10])
                        h_off = np.random.choice([16, 17, 18])
                        t_on = current_day.replace(hour=h_on, minute=np.random.randint(0, 59))
                        t_off = current_day.replace(hour=h_off, minute=np.random.randint(0, 59))
                        
                        logon_records.append([f"L-{logon_id}", t_on.strftime('%m/%d/%Y %H:%M:%S'), user, 'PC-Anom', 'Logon'])
                        logon_id += 1
                        logon_records.append([f"L-{logon_id}", t_off.strftime('%m/%d/%Y %H:%M:%S'), user, 'PC-Anom', 'Logoff'])
                        logon_id += 1
                        
                        email_time = current_day.replace(hour=11, minute=np.random.randint(0, 59))
                        email_records.append([
                            f"E-{email_id}", email_time.strftime('%m/%d/%Y %H:%M:%S'), user, 'PC-Anom',
                            'internal@company.com', '', '', user, 5000, 'none',
                            "Documentation links update."
                        ])
                        email_id += 1
                    else:
                        # Night activity
                        t_on = current_day.replace(hour=np.random.choice([1, 2, 3]), minute=np.random.randint(0, 59))
                        t_off = t_on + pd.Timedelta(hours=np.random.choice([1, 2]))
                        
                        logon_records.append([f"L-{logon_id}", t_on.strftime('%m/%d/%Y %H:%M:%S'), user, 'PC-Anom', 'Logon'])
                        logon_id += 1
                        logon_records.append([f"L-{logon_id}", t_off.strftime('%m/%d/%Y %H:%M:%S'), user, 'PC-Anom', 'Logoff'])
                        logon_id += 1
                        
                        # Data leak exfiltration
                        for i in range(5):
                            email_time = t_on + pd.Timedelta(minutes=10 * i)
                            email_records.append([
                                f"E-{email_id}", email_time.strftime('%m/%d/%Y %H:%M:%S'), user, 'PC-Anom',
                                'adversary@external.org', '', '', user, 95000000, 'archive_leak.zip',
                                "Leaking files now."
                            ])
                            email_id += 1
                            
                        # Device connects
                        dev_time = t_on + pd.Timedelta(minutes=5)
                        device_records.append([f"D-{device_id}", dev_time.strftime('%m/%d/%Y %H:%M:%S'), user, 'PC-Anom', 'Connect'])
                        device_id += 1
                        
        # Save CSV files
        pd.DataFrame(logon_records, columns=['id', 'date', 'user', 'pc', 'activity']).to_csv(os.path.join(self.data_dir, 'logon.csv'), index=False)
        pd.DataFrame(email_records, columns=['id', 'date', 'user', 'pc', 'to', 'cc', 'bcc', 'from', 'size', 'attachment', 'content']).to_csv(os.path.join(self.data_dir, 'email.csv'), index=False)
        pd.DataFrame(device_records, columns=['id', 'date', 'user', 'pc', 'activity']).to_csv(os.path.join(self.data_dir, 'device.csv'), index=False)
        print("Cohort logs generated successfully.")

    def build_ml_dataset(self):
        loader = CERTDataLoader(self.data_dir)
        logons = loader.load_logon_logs()
        emails = loader.load_email_logs()
        
        logons = loader.extract_time_windows(logons, 7)
        emails = loader.extract_time_windows(emails, 7)
        
        act_df = extract_activity_features(logons)
        comm_df = extract_communication_features(emails)
        int_df = extract_interaction_features(emails)
        
        merged = pd.merge(act_df, comm_df, on=['user', 'time_window'], how='outer')
        merged = pd.merge(merged, int_df, on=['user', 'time_window'], how='outer').fillna(0.0)
        
        builder = SignatureBuilder(merged)
        signatures, _, _ = builder.build_signatures()
        
        X = []
        y = []
        user_window_keys = []
        
        for user, weeks in signatures.items():
            for week, vector in weeks.items():
                X.append(vector)
                is_anom = "ThreatUser" in user and week >= 3
                y.append(1 if is_anom else 0)
                user_window_keys.append((user, week))
                
        return np.array(X), np.array(y), user_window_keys

    def evaluate_model(self, model_name, y_test, y_pred, y_prob=None):
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        roc = roc_auc_score(y_test, y_prob) if (y_prob is not None and len(np.unique(y_test)) > 1) else 0.0
        cm = confusion_matrix(y_test, y_pred)
        
        print(f"\n>>> Model: {model_name}")
        print(f"  Accuracy:  {acc:.4f}")
        print(f"  Precision: {prec:.4f}")
        print(f"  Recall:    {rec:.4f}")
        print(f"  F1-Score:  {f1:.4f}")
        if y_prob is not None:
            print(f"  ROC-AUC:   {roc:.4f}")
        print(f"  Confusion Matrix:\n{cm}")
        
        return {'acc': acc, 'prec': prec, 'rec': rec, 'f1': f1}

    def train_models(self):
        # 1. Generate data
        self.generate_large_cohort(num_users=100, anomaly_ratio=0.05)
        
        # 2. Extract features and label
        X, y, keys = self.build_ml_dataset()
        print(f"\nDataset prepared: {X.shape[0]} samples, {X.shape[1]} features.")
        print(f"Class imbalance: {np.sum(y)} anomalous weeks, {len(y) - np.sum(y)} normal weeks.")
        
        # 3. Stratified Train-Test Split (20% test size)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42, stratify=y
        )
        
        evaluation_results = {}
        
        # 4. Supervised Classifier 1: Random Forest
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_test)
        rf_prob = rf.predict_proba(X_test)[:, 1]
        evaluation_results['Random Forest'] = self.evaluate_model("Random Forest", y_test, rf_pred, rf_prob)
        
        # 5. Supervised Classifier 2: XGBoost
        ratio = (len(y_train) - np.sum(y_train)) / np.sum(y_train)
        xgb = XGBClassifier(scale_pos_weight=ratio, random_state=42, eval_metric='logloss')
        xgb.fit(X_train, y_train)
        xgb_pred = xgb.predict(X_test)
        xgb_prob = xgb.predict_proba(X_test)[:, 1]
        evaluation_results['XGBoost'] = self.evaluate_model("XGBoost", y_test, xgb_pred, xgb_prob)
        
        # 6. Unsupervised Baseline 1: Isolation Forest
        # Train on the entire training set (containing anomalous and normal weeks)
        iso = IsolationForest(contamination=0.05, random_state=42)
        iso.fit(X_train)
        iso_raw = iso.predict(X_test)
        # Convert Isolation Forest output: -1 for anomaly, 1 for normal
        iso_pred = np.where(iso_raw == -1, 1, 0)
        evaluation_results['Isolation Forest'] = self.evaluate_model("Isolation Forest (Unsupervised Baseline)", y_test, iso_pred)
        
        # 7. Unsupervised Baseline 2: One-Class SVM
        oc_svm = OneClassSVM(nu=0.05, kernel='rbf', gamma='scale')
        oc_svm.fit(X_train)
        oc_raw = oc_svm.predict(X_test)
        oc_pred = np.where(oc_raw == -1, 1, 0)
        evaluation_results['One-Class SVM'] = self.evaluate_model("One-Class SVM (Unsupervised Baseline)", y_test, oc_pred)
        
        print(f"\nStatus: Supervised Classifiers and Unsupervised Baselines Trained successfully.")
        return evaluation_results

if __name__ == '__main__':
    classifier = CyberDNAClassifier()
    classifier.train_models()
