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
    print("      DEPT FILTER CALIBRATION STUDY (EXTENDED)     ")
    print("==================================================")
    
    data_dir = 'data/cert_r4.2/r4.2'
    loader = CERTDataLoader(data_dir)
    
    # Ingest labels
    insiders_df = loader.load_insider_labels()
    malicious_users = set(insiders_df['user'].unique())
    
    # Ingest logons
    logons_all = loader.load_logon_logs()
    all_users = set(logons_all['user'].unique())
    benign_users = all_users - malicious_users
    
    # Cohort
    np.random.seed(42)
    selected_benign = sorted(list(np.random.choice(list(benign_users), size=100, replace=False)))
    selected_malicious = sorted(list(malicious_users & all_users))
    cohort_users = set(selected_malicious + selected_benign)
    
    logons = logons_all[logons_all['user'].isin(cohort_users)].copy()
    del logons_all
    gc.collect()
    
    min_date = logons['date'].min()
    logons = loader.extract_time_windows(logons, window_size_days=7, min_date=min_date)
    
    # Ingest emails
    email_path = os.path.join(data_dir, 'email.csv')
    emails_chunks = []
    if os.path.exists(email_path):
        for chunk in pd.read_csv(email_path, chunksize=100000):
            filtered = chunk[chunk['user'].isin(cohort_users)].copy()
            emails_chunks.append(filtered)
        emails = pd.concat(emails_chunks).reset_index(drop=True)
    else:
        emails = pd.DataFrame()
        
    if not emails.empty:
        emails['date'] = pd.to_datetime(emails['date'], format='mixed', errors='coerce')
        emails = emails.dropna(subset=['date']).sort_values('date')
        emails = loader.extract_time_windows(emails, window_size_days=7, min_date=min_date)
        
    ldap_df = loader.load_ldap_records()
    
    # Features
    act_df = extract_activity_features(logons)
    comm_df = extract_communication_features(emails) if not emails.empty else pd.DataFrame(columns=['user', 'time_window', 'vocab_diversity', 'response_time', 'email_freq'])
    int_df = extract_interaction_features(emails) if not emails.empty else pd.DataFrame(columns=['user', 'time_window', 'contact_diversity', 'reciprocity'])
    
    raw_feats = pd.merge(act_df, comm_df, on=['user', 'time_window'], how='outer')
    raw_feats = pd.merge(raw_feats, int_df, on=['user', 'time_window'], how='outer').fillna(0.0)
    raw_feats = raw_feats[raw_feats['user'].isin(cohort_users)].copy()
    
    user_dept = dict(zip(ldap_df['user'], ldap_df['department']))
    raw_feats['department'] = raw_feats['user'].map(user_dept).fillna('Unknown')
    raw_feats = loader.generate_user_weeks_labels(raw_feats, insiders_df, min_date, window_size_days=7)
    
    del logons, emails
    gc.collect()
    
    feature_cols = [
        'login_freq', 'active_hours', 'avg_session', 
        'email_freq', 'vocab_diversity', 'response_time', 
        'contact_diversity', 'reciprocity'
    ]
    
    # Scaler
    train_mask = raw_feats['time_window'] <= 52
    test_mask = raw_feats['time_window'] > 52
    train_benign_mask = train_mask & (raw_feats['label'] == 0)
    train_benign_df = raw_feats[train_benign_mask]
    
    scaler = MinMaxScaler()
    scaler.fit(train_benign_df[feature_cols])
    
    scaled_feats = raw_feats.copy()
    scaled_feats[feature_cols] = scaler.transform(raw_feats[feature_cols]).clip(0.0, 1.0)
    
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
        
    # Department centroids
    dept_users = {}
    for u, dept in user_dept.items():
        if dept not in dept_users:
            dept_users[dept] = []
        dept_users[dept].append(u)
        
    weekly_centroids = {}
    weekly_cohesion = {}
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
                
                similarities = [cosine_similarity(signatures[u][w], centroid) for u in users_in_dept 
                                if u in signatures and w in signatures[u] and labels_dict[(u, w)] == 0]
                mean_bsi = np.mean(similarities)
                std_bsi = np.std(similarities)
                if std_bsi == 0:
                    std_bsi = 0.01
                weekly_cohesion[(dept, w)] = (mean_bsi, std_bsi)
                
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
            dept_centroids_avg[dept] = np.zeros(8)
            dept_cohesion_avg[dept] = (1.0, 0.01)
            
    # BDS, IPS, Anthro
    scaled_feats['IPS'] = (scaled_feats['contact_diversity'] + scaled_feats['reciprocity'] + 1.5) / 4.0
    user_earliest_week = {u: min(signatures[u].keys()) for u in signatures}
    
    bds_values = []
    for idx, row in scaled_feats.iterrows():
        u = row['user']
        w = int(row['time_window'])
        bds_values.append(np.linalg.norm(signatures[u][w] - signatures[u][user_earliest_week[u]]))
    scaled_feats['BDS'] = bds_values
    
    user_anthro = {}
    for u, weeks in signatures.items():
        sorted_w = sorted(list(weeks.keys()))
        W = len(sorted_w)
        bds_list = []
        ips_diffs = []
        for idx in range(W - 1):
            w1 = sorted_w[idx]
            w2 = sorted_w[idx + 1]
            bds_list.append(np.linalg.norm(weeks[w1] - weeks[w2]))
            
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
    
    # Compute department BSI similarity for all rows
    bsi_depts = []
    for idx, row in scaled_feats.iterrows():
        u = row['user']
        w = int(row['time_window'])
        dept = row['department']
        centroid = weekly_centroids.get((dept, w), dept_centroids_avg.get(dept, np.zeros(8))) if w <= 52 else dept_centroids_avg.get(dept, np.zeros(8))
        bsi_depts.append(cosine_similarity(signatures[u][w], centroid))
    scaled_feats['dept_BSI'] = bsi_depts
    
    # Split
    train_df = scaled_feats[scaled_feats['time_window'] <= 52]
    test_df = scaled_feats[scaled_feats['time_window'] > 52]
    
    full_feature_list = feature_cols + ['BDS', 'dept_BSI', 'IDP', 'BC', 'SRC']
    X_tr_full = train_df[full_feature_list].values
    X_te_full = test_df[full_feature_list].values
    y_train = train_df['label'].values
    y_test = test_df['label'].values
    
    # Train XGBoost
    ratio = (len(y_train) - np.sum(y_train)) / np.sum(y_train)
    clf = XGBClassifier(scale_pos_weight=ratio, random_state=42, eval_metric='logloss')
    clf.fit(X_tr_full, y_train)
    
    xgb_scores = clf.predict_proba(X_te_full)[:, 1]
    xgb_pred = clf.predict(X_te_full)
    
    total_alerts_before = int(np.sum(xgb_pred))
    print(f"Total alerts flagged by XGBoost before suppression: {total_alerts_before}")
    
    test_rows_list = test_df.reset_index(drop=True)
    
    # Joint sweep of Z threshold and BSI threshold
    z_thresholds = [-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 1.0, 2.0]
    bsi_thresholds = [0.85, 0.95, 0.99, 0.999, 0.9995]
    
    print("\n--- Sweeping Z-score and BSI Similarity Thresholds ---")
    results = []
    
    for b_thresh in bsi_thresholds:
        for z in z_thresholds:
            final_preds = []
            suppressed_count = 0
            benign_suppressed = 0
            malicious_suppressed = 0
            
            for idx, row in test_rows_list.iterrows():
                raw_pred = xgb_pred[idx]
                is_malicious = row['label']
                
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
                        
                        # Apply both criteria
                        if z_score >= z and bsi > b_thresh:
                            is_transition = True
                            break
                            
                    if is_transition:
                        final_preds.append(0)
                        suppressed_count += 1
                        if is_malicious == 0:
                            benign_suppressed += 1
                        else:
                            malicious_suppressed += 1
                    else:
                        final_preds.append(1)
                else:
                    final_preds.append(0)
                    
            prec = precision_score(y_test, final_preds, zero_division=0)
            rec = recall_score(y_test, final_preds, zero_division=0)
            f1 = f1_score(y_test, final_preds, zero_division=0)
            
            results.append({
                'BSI_thresh': b_thresh,
                'Z_thresh': z,
                'precision': prec,
                'recall': rec,
                'f1': f1,
                'suppressed': suppressed_count,
                'ben_sup': benign_suppressed,
                'mal_sup': malicious_suppressed
            })
            
    # Sort results by F1 score
    res_df = pd.DataFrame(results)
    sorted_res = res_df.sort_values('f1', ascending=False)
    
    print("\nTop 10 configurations by F1 Score:")
    print(sorted_res.head(10).to_string(index=False))
    
    # Print statistics for the baseline config (BSI > 0.85, Z >= -2.5)
    baseline_row = res_df[(res_df['BSI_thresh'] == 0.85) & (res_df['Z_thresh'] == -2.5)].iloc[0]
    print("\n--- Baseline Configuration Metrics (BSI > 0.85, Z >= -2.5) ---")
    print(f"  Precision:         {baseline_row['precision']:.4f}")
    print(f"  Recall:            {baseline_row['recall']:.4f}")
    print(f"  F1-Score:          {baseline_row['f1']:.4f}")
    print(f"  Alerts suppressed: {baseline_row['suppressed']} (Benign: {baseline_row['ben_sup']}, Malicious: {baseline_row['mal_sup']})")
    
if __name__ == '__main__':
    main()
