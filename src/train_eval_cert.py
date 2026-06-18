import pandas as pd
import numpy as np
import time
import os
import sys
import gc
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.metrics import precision_score, recall_score, f1_score, precision_recall_curve, auc, confusion_matrix
from xgboost import XGBClassifier

# Ensure src dir is in import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocess import CERTDataLoader
from extractors.activity import extract_activity_features
from extractors.communication import extract_communication_features
from extractors.interaction import extract_interaction_features

def cosine_similarity(a, b):
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def calculate_auprc(y_true, y_scores):
    if len(np.unique(y_true)) <= 1:
        return 0.0
    precision, recall, _ = precision_recall_curve(y_true, y_scores)
    return float(auc(recall, precision))

def main():
    print("==================================================")
    print("      CYBER DNA: PHASE 9 RIGOROUS EVALUATION       ")
    print("==================================================")
    
    data_dir = 'data/cert_r4.2/r4.2'
    loader = CERTDataLoader(data_dir)
    
    # 1. Load ground truth labels to identify malicious users
    print("Loading ground truth labels...")
    insiders_df = loader.load_insider_labels()
    if insiders_df.empty:
        print("Error: insiders.csv is empty or not found.")
        sys.exit(1)
        
    malicious_users = set(insiders_df['user'].unique())
    print(f"Found {len(malicious_users)} malicious users in registry.")
    
    # 2. Ingest logon logs to identify all unique users and select cohort
    print("Ingesting logon.csv...")
    logons_all = loader.load_logon_logs()
    if logons_all.empty:
        print("Error: logon.csv is empty.")
        sys.exit(1)
        
    all_users = set(logons_all['user'].unique())
    benign_users = all_users - malicious_users
    
    # Randomly select 100 benign users using a fixed seed
    np.random.seed(42)
    selected_benign = sorted(list(np.random.choice(list(benign_users), size=100, replace=False)))
    selected_malicious = sorted(list(malicious_users & all_users))
    
    cohort_users = set(selected_malicious + selected_benign)
    print(f"Selected Cohort: {len(cohort_users)} users ({len(selected_malicious)} malicious, {len(selected_benign)} benign).")
    
    # Filter logons to cohort users
    logons = logons_all[logons_all['user'].isin(cohort_users)].copy()
    del logons_all
    gc.collect()
    
    # Set global start date
    min_date = logons['date'].min()
    print(f"Global Reference Start Date (min_date): {min_date}")
    
    # Extract time windows for logons
    logons = loader.extract_time_windows(logons, window_size_days=7, min_date=min_date)
    
    # 3. Load email logs in chunks and filter to cohort users to prevent OOM
    print("Ingesting email.csv in chunks (filtering to cohort)...")
    email_path = os.path.join(data_dir, 'email.csv')
    emails_chunks = []
    if os.path.exists(email_path):
        for chunk in pd.read_csv(email_path, chunksize=100000):
            filtered = chunk[chunk['user'].isin(cohort_users)].copy()
            emails_chunks.append(filtered)
        emails = pd.concat(emails_chunks).reset_index(drop=True)
    else:
        emails = pd.DataFrame()
        
    print(f"Email Ingestion complete. Loaded {len(emails)} records for cohort.")
    
    # Parse dates for emails
    if not emails.empty:
        emails['date'] = pd.to_datetime(emails['date'], format='mixed', errors='coerce')
        emails = emails.dropna(subset=['date']).sort_values('date')
        emails = loader.extract_time_windows(emails, window_size_days=7, min_date=min_date)
        
    print("Ingesting LDAP directory...")
    ldap_df = loader.load_ldap_records()
    
    # 4. Extract Layer 1, 2, and 3 Features
    t0 = time.time()
    print("Extracting Activity features...")
    act_df = extract_activity_features(logons)
    
    print("Extracting Communication features...")
    comm_df = extract_communication_features(emails) if not emails.empty else pd.DataFrame(columns=['user', 'time_window', 'vocab_diversity', 'response_time', 'email_freq'])
    
    print("Extracting Interaction features...")
    int_df = extract_interaction_features(emails) if not emails.empty else pd.DataFrame(columns=['user', 'time_window', 'contact_diversity', 'reciprocity'])
    
    # Merge features
    raw_feats = pd.merge(act_df, comm_df, on=['user', 'time_window'], how='outer')
    raw_feats = pd.merge(raw_feats, int_df, on=['user', 'time_window'], how='outer').fillna(0.0)
    
    # Enforce cohort filter on final raw features (in case recipient outer-joins added other users)
    raw_feats = raw_feats[raw_feats['user'].isin(cohort_users)].copy()
    
    # Map LDAP departments
    user_dept = dict(zip(ldap_df['user'], ldap_df['department']))
    raw_feats['department'] = raw_feats['user'].map(user_dept).fillna('Unknown')
    
    # Generate labels
    raw_feats = loader.generate_user_weeks_labels(raw_feats, insiders_df, min_date, window_size_days=7)
    
    # Clean up raw log dataframes to free RAM
    del logons, emails
    gc.collect()
    print(f"Feature extraction complete in {time.time() - t0:.2f} seconds.")
    
    feature_cols = [
        'login_freq', 'active_hours', 'avg_session', 
        'email_freq', 'vocab_diversity', 'response_time', 
        'contact_diversity', 'reciprocity'
    ]
    
    # 5. Fit scaler ONLY on train benign partition
    train_mask = raw_feats['time_window'] <= 52
    train_benign_mask = train_mask & (raw_feats['label'] == 0)
    
    train_benign_df = raw_feats[train_benign_mask]
    if train_benign_df.empty:
        print("Error: No training benign data found. Scaling cannot be completed.")
        sys.exit(1)
        
    scaler = MinMaxScaler()
    scaler.fit(train_benign_df[feature_cols])
    
    # Scale all features
    scaled_feats = raw_feats.copy()
    scaled_feats[feature_cols] = scaler.transform(raw_feats[feature_cols]).clip(0.0, 1.0)
    
    # Save scaled DBS signatures dictionary: user -> week -> dbs_vector
    signatures = {}
    labels_dict = {}
    for idx, row in scaled_feats.iterrows():
        u = row['user']
        w = int(row['time_window'])
        vector = row[feature_cols].values.astype(float)
        if u not in signatures:
            signatures[u] = {}
        signatures[u][w] = vector
        labels_dict[(u, w)] = int(row['label'])
        
    # 6. Build Department Centroids using training partition and benign weeks
    print("Building department centroids from training partition benign weeks...")
    dept_users = {}
    for u, dept in user_dept.items():
        if dept not in dept_users:
            dept_users[dept] = []
        dept_users[dept].append(u)
        
    weekly_centroids = {} # (dept, week) -> vector
    weekly_cohesion = {}  # (dept, week) -> (mean, std)
    
    departments = [d for d in ldap_df['department'].unique() if pd.notna(d)]
    
    for dept in departments:
        users_in_dept = dept_users.get(dept, [])
        if not users_in_dept:
            continue
            
        for w in range(1, 53):
            vectors = []
            for u in users_in_dept:
                if u in signatures and w in signatures[u] and labels_dict[(u, w)] == 0:
                    vectors.append(signatures[u][w])
            if vectors:
                centroid = np.mean(vectors, axis=0)
                weekly_centroids[(dept, w)] = centroid
                
                # Cohesion BSI similarity
                similarities = [cosine_similarity(signatures[u][w], centroid) for u in users_in_dept 
                                if u in signatures and w in signatures[u] and labels_dict[(u, w)] == 0]
                mean_bsi = np.mean(similarities)
                std_bsi = np.std(similarities)
                if std_bsi == 0:
                    std_bsi = 0.01
                weekly_cohesion[(dept, w)] = (mean_bsi, std_bsi)
                
    # Compute average historical centroid/cohesion for each department (leakage-free baseline for test weeks)
    dept_centroids_avg = {}
    dept_cohesion_avg = {}
    for dept in departments:
        dept_vecs = [weekly_centroids[(dept, w)] for w in range(1, 53) if (dept, w) in weekly_centroids]
        if dept_vecs:
            dept_centroids_avg[dept] = np.mean(dept_vecs, axis=0)
            
            means = [weekly_cohesion[(dept, w)][0] for w in range(1, 53) if (dept, w) in weekly_cohesion]
            stds = [weekly_cohesion[(dept, w)][1] for w in range(1, 53) if (dept, w) in weekly_cohesion]
            dept_cohesion_avg[dept] = (np.mean(means), np.mean(stds))
        else:
            # Fallback in case of empty training weeks
            dept_centroids_avg[dept] = np.zeros(8)
            dept_cohesion_avg[dept] = (1.0, 0.01)
            
    # 7. Compute BDS (Temporal Self-Drift) for all user-weeks
    # BDS is Euclidean distance relative to the user's earliest active week DBS
    user_earliest_week = {}
    for u in signatures:
        user_earliest_week[u] = min(signatures[u].keys())
        
    bds_values = []
    for idx, row in scaled_feats.iterrows():
        u = row['user']
        w = int(row['time_window'])
        w_min = user_earliest_week[u]
        dbs_now = signatures[u][w]
        dbs_base = signatures[u][w_min]
        bds = np.linalg.norm(dbs_now - dbs_base)
        bds_values.append(bds)
    scaled_feats['BDS'] = bds_values
    
    # 8. Compute anthropology scores (IDP, BC, SRC) for all users
    print("Computing mathematical anthropology metrics (IDP, BC, SRC)...")
    scaled_feats['IPS'] = (scaled_feats['contact_diversity'] + scaled_feats['reciprocity'] + 1.5) / 4.0
    
    user_anthro = {}
    for u, weeks in signatures.items():
        sorted_w = sorted(list(weeks.keys()))
        W = len(sorted_w)
        
        bds_list = []
        ips_diffs = []
        for idx in range(W - 1):
            w1 = sorted_w[idx]
            w2 = sorted_w[idx + 1]
            
            bds = np.linalg.norm(weeks[w1] - weeks[w2])
            bds_list.append(bds)
            
            ips_w1 = scaled_feats[(scaled_feats['user'] == u) & (scaled_feats['time_window'] == w1)]['IPS'].values[0]
            ips_w2 = scaled_feats[(scaled_feats['user'] == u) & (scaled_feats['time_window'] == w2)]['IPS'].values[0]
            ips_diffs.append(abs(ips_w1 - ips_w2))
            
        idp = np.exp(-np.mean(bds_list)) if (W > 1 and bds_list) else 1.0
        bc = np.exp(-np.std(bds_list)) if (W > 2 and len(bds_list) > 1) else 1.0
        src = 1.0 - np.mean(ips_diffs) if (W > 1 and ips_diffs) else 1.0
        
        user_anthro[u] = {'IDP': idp, 'BC': bc, 'SRC': src}
        
    scaled_feats['IDP'] = scaled_feats['user'].map(lambda x: user_anthro[x]['IDP'])
    scaled_feats['BC'] = scaled_feats['user'].map(lambda x: user_anthro[x]['BC'])
    scaled_feats['SRC'] = scaled_feats['user'].map(lambda x: user_anthro[x]['SRC'])
    
    # 9. Partition Train and Test sets
    train_mask = scaled_feats['time_window'] <= 52
    test_mask = scaled_feats['time_window'] > 52
    
    train_df = scaled_feats[train_mask]
    test_df = scaled_feats[test_mask]
    
    X_train_raw = train_df[feature_cols].values
    X_test_raw = test_df[feature_cols].values
    
    y_train = train_df['label'].values
    y_test = test_df['label'].values
    
    # 10. Train supervised classifiers
    print("\nTraining supervised models on training partition (Weeks 1 to 52)...")
    # Random Forest
    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
    rf.fit(X_train_raw, y_train)
    rf_pred = rf.predict(X_test_raw)
    rf_scores = rf.predict_proba(X_test_raw)[:, 1]
    
    # XGBoost
    ratio = (len(y_train) - np.sum(y_train)) / np.sum(y_train)
    xgb = XGBClassifier(scale_pos_weight=ratio, random_state=42, eval_metric='logloss')
    xgb.fit(X_train_raw, y_train)
    xgb_pred = xgb.predict(X_test_raw)
    xgb_scores = xgb.predict_proba(X_test_raw)[:, 1]
    
    # 11. Train unsupervised baselines
    print("Training unsupervised baselines...")
    contam = max(0.001, np.sum(y_train) / len(y_train))
    iso = IsolationForest(contamination=contam, random_state=42)
    iso.fit(X_train_raw)
    iso_scores = -iso.score_samples(X_test_raw)
    iso_pred = np.where(iso.predict(X_test_raw) == -1, 1, 0)
    
    oc_svm = OneClassSVM(nu=contam, kernel='rbf', gamma='scale')
    oc_svm.fit(X_train_raw[y_train == 0])
    oc_scores = -oc_svm.score_samples(X_test_raw)
    oc_pred = np.where(oc_svm.predict(X_test_raw) == -1, 1, 0)
    
    # --- REPORTING ---
    
    def report_metrics(name, y_true, y_pred, y_scores):
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        auprc = calculate_auprc(y_true, y_scores)
        cm = confusion_matrix(y_true, y_pred)
        
        print(f"\n>>> Model: {name}")
        print(f"  Precision: {prec:.4f}")
        print(f"  Recall:    {rec:.4f}")
        print(f"  F1-Score:  {f1:.4f}")
        print(f"  AUPRC:     {auprc:.4f}")
        print(f"  Confusion Matrix:\n{cm}")
        return {'prec': prec, 'rec': rec, 'f1': f1, 'auprc': auprc}
        
    print("\n---------------- MODEL EVALUATIONS (TEST SPLIT ONLY) ----------------")
    rf_m = report_metrics("Random Forest", y_test, rf_pred, rf_scores)
    xgb_m = report_metrics("XGBoost", y_test, xgb_pred, xgb_scores)
    iso_m = report_metrics("Isolation Forest (Baseline)", y_test, iso_pred, iso_scores)
    oc_m = report_metrics("One-Class SVM (Baseline)", y_test, oc_pred, oc_scores)
    print("---------------------------------------------------------------------\n")
    
    # 12. Generate descriptive statistics
    print("---------------- DESCRIPTIVE STATISTICS ----------------")
    benign_bds = scaled_feats[scaled_feats['label'] == 0]['BDS'].mean()
    malicious_bds = scaled_feats[scaled_feats['label'] == 1]['BDS'].mean()
    print(f"Average BDS (Benign Weeks):     {benign_bds:.4f}")
    print(f"Average BDS (Malicious Weeks):  {malicious_bds:.4f}")
    
    benign_users_list = [u for u in cohort_users if u not in malicious_users]
    malicious_users_list = [u for u in cohort_users if u in malicious_users]
    
    benign_idp = np.mean([user_anthro[u]['IDP'] for u in benign_users_list if u in user_anthro])
    malicious_idp = np.mean([user_anthro[u]['IDP'] for u in malicious_users_list if u in user_anthro])
    benign_src = np.mean([user_anthro[u]['SRC'] for u in benign_users_list if u in user_anthro])
    malicious_src = np.mean([user_anthro[u]['SRC'] for u in malicious_users_list if u in user_anthro])
    
    print(f"Average IDP (Benign Users):     {benign_idp:.4f}")
    print(f"Average IDP (Malicious Users):  {malicious_idp:.4f}")
    print(f"Average SRC (Benign Users):     {benign_src:.4f}")
    print(f"Average SRC (Malicious Users):  {malicious_src:.4f}")
    print("--------------------------------------------------------\n")
    
    # 13. Produce Ablation Study
    print("---------------- ABLATION STUDY ----------------")
    
    def run_ablation_xgb(name, feature_list, train_data, test_data):
        X_tr = train_data[feature_list].values
        X_te = test_data[feature_list].values
        
        ratio = (len(y_train) - np.sum(y_train)) / np.sum(y_train)
        clf = XGBClassifier(scale_pos_weight=ratio, random_state=42, eval_metric='logloss')
        clf.fit(X_tr, y_train)
        pred = clf.predict(X_te)
        scores = clf.predict_proba(X_te)[:, 1]
        
        prec = precision_score(y_test, pred, zero_division=0)
        rec = recall_score(y_test, pred, zero_division=0)
        f1 = f1_score(y_test, pred, zero_division=0)
        auprc = calculate_auprc(y_test, scores)
        
        print(f"Configuration: {name}")
        print(f"  Precision: {prec:.4f} | Recall: {rec:.4f} | F1: {f1:.4f} | AUPRC: {auprc:.4f}")
        return {'prec': prec, 'rec': rec, 'f1': f1, 'auprc': auprc}
        
    # A. Raw Features Only
    raw_train = raw_feats[train_mask]
    raw_test = raw_feats[test_mask]
    run_ablation_xgb("A. Raw Features Only", feature_cols, raw_train, raw_test)
    
    # B. DBS Only
    run_ablation_xgb("B. DBS Only", feature_cols, train_df, test_df)
    
    # C. DBS + BSI/BDS
    bsi_depts = []
    for idx, row in scaled_feats.iterrows():
        u = row['user']
        w = int(row['time_window'])
        dept = row['department']
        
        if w <= 52:
            centroid = weekly_centroids.get((dept, w), np.zeros(8))
        else:
            centroid = dept_centroids_avg.get(dept, np.zeros(8))
            
        bsi = cosine_similarity(signatures[u][w], centroid)
        bsi_depts.append(bsi)
    
    scaled_feats_ab = scaled_feats.copy()
    scaled_feats_ab['dept_BSI'] = bsi_depts
    
    train_df_ab = scaled_feats_ab[train_mask]
    test_df_ab = scaled_feats_ab[test_mask]
    run_ablation_xgb("C. DBS + BSI/BDS", feature_cols + ['BDS', 'dept_BSI'], train_df_ab, test_df_ab)
    
    # D. DBS + Anthropology Metrics
    run_ablation_xgb("D. DBS + Anthropology", feature_cols + ['IDP', 'BC', 'SRC'], train_df, test_df)
    
    # E. Full Cyber DNA
    print("\nEvaluating E. Full Cyber DNA (with Z-Score Departmental Suppression Filter)...")
    full_feature_list = feature_cols + ['BDS', 'dept_BSI', 'IDP', 'BC', 'SRC']
    X_tr_full = train_df_ab[full_feature_list].values
    X_te_full = test_df_ab[full_feature_list].values
    
    clf_full = XGBClassifier(scale_pos_weight=ratio, random_state=42, eval_metric='logloss')
    clf_full.fit(X_tr_full, y_train)
    
    xgb_full_scores = clf_full.predict_proba(X_te_full)[:, 1]
    xgb_full_pred = clf_full.predict(X_te_full)
    
    final_predictions = []
    test_rows_list = test_df_ab.reset_index(drop=True)
    for idx, row in test_rows_list.iterrows():
        raw_pred = xgb_full_pred[idx]
        
        if raw_pred == 1:
            u = row['user']
            w = int(row['time_window'])
            dept = row['department']
            vector = signatures[u][w]
            
            is_transition = False
            for other_dept in departments:
                if other_dept == dept:
                    continue
                    
                centroid = dept_centroids_avg.get(other_dept, np.zeros(8))
                mean_bsi, std_bsi = dept_cohesion_avg.get(other_dept, (1.0, 0.01))
                
                bsi = cosine_similarity(vector, centroid)
                z_score = (bsi - mean_bsi) / std_bsi
                
                if z_score >= -2.5 and bsi > 0.85:
                    is_transition = True
                    break
            
            if is_transition:
                final_predictions.append(0)
            else:
                final_predictions.append(1)
        else:
            final_predictions.append(0)
            
    y_test_final = test_df_ab['label'].values
    final_prec = precision_score(y_test_final, final_predictions, zero_division=0)
    final_rec = recall_score(y_test_final, final_predictions, zero_division=0)
    final_f1 = f1_score(y_test_final, final_predictions, zero_division=0)
    final_auprc = calculate_auprc(y_test_final, xgb_full_scores)
    
    print("Configuration: E. Full Cyber DNA (with Z-Score Filter)")
    print(f"  Precision: {final_prec:.4f} | Recall: {final_rec:.4f} | F1: {final_f1:.4f} | AUPRC: {final_auprc:.4f}")
    print("------------------------------------------------\n")
    
    print("Status: Phase 9 ML evaluation completed successfully!")
    print("==================================================")

if __name__ == '__main__':
    main()
