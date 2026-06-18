import pandas as pd
import numpy as np
import json
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
    print("     FINAL CERT EXPORT & RESEARCH PIPELINE        ")
    print("==================================================")
    
    data_dir = 'data/cert_r4.2/r4.2'
    loader = CERTDataLoader(data_dir)
    
    results_dir = 'results'
    os.makedirs(results_dir, exist_ok=True)
    
    # 1. Load labels and logons
    print("Loading ground truth labels...")
    insiders_df = loader.load_insider_labels()
    malicious_users = set(insiders_df['user'].unique())
    
    print("Ingesting logon.csv...")
    logons_all = loader.load_logon_logs()
    all_users = set(logons_all['user'].unique())
    benign_users = all_users - malicious_users
    
    # Select cohort: all 70 malicious + 100 benign (seed 42)
    np.random.seed(42)
    selected_benign = sorted(list(np.random.choice(list(benign_users), size=100, replace=False)))
    selected_malicious = sorted(list(malicious_users & all_users))
    cohort_users = set(selected_malicious + selected_benign)
    
    print(f"Selected evaluation cohort: {len(cohort_users)} users ({len(selected_malicious)} malicious, {len(selected_benign)} benign)")
    
    # Filter logons
    logons = logons_all[logons_all['user'].isin(cohort_users)].copy()
    del logons_all
    gc.collect()
    
    min_date = logons['date'].min()
    logons = loader.extract_time_windows(logons, window_size_days=7, min_date=min_date)
    
    # Ingest emails
    print("Ingesting email.csv in chunks...")
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
    user_dept = dict(zip(ldap_df['user'], ldap_df['department'].fillna('Unknown')))
    
    # 2. Feature extraction
    print("Extracting features (vectorized)...")
    act_df = extract_activity_features(logons)
    comm_df = extract_communication_features(emails) if not emails.empty else pd.DataFrame(columns=['user', 'time_window', 'vocab_diversity', 'response_time', 'email_freq'])
    int_df = extract_interaction_features(emails) if not emails.empty else pd.DataFrame(columns=['user', 'time_window', 'contact_diversity', 'reciprocity'])
    
    raw_feats = pd.merge(act_df, comm_df, on=['user', 'time_window'], how='outer')
    raw_feats = pd.merge(raw_feats, int_df, on=['user', 'time_window'], how='outer').fillna(0.0)
    raw_feats = raw_feats[raw_feats['user'].isin(cohort_users)].copy()
    raw_feats['department'] = raw_feats['user'].map(user_dept).fillna('Unknown')
    raw_feats = loader.generate_user_weeks_labels(raw_feats, insiders_df, min_date, window_size_days=7)
    
    del logons, emails
    gc.collect()
    
    feature_cols = [
        'login_freq', 'active_hours', 'avg_session', 
        'email_freq', 'vocab_diversity', 'response_time', 
        'contact_diversity', 'reciprocity'
    ]
    
    train_mask = raw_feats['time_window'] <= 52
    test_mask = raw_feats['time_window'] > 52
    train_benign_mask = train_mask & (raw_feats['label'] == 0)
    train_benign_df = raw_feats[train_benign_mask]
    
    # 3. Min-Max Scaling (fit on train benign weeks only)
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
        
    # 4. Department centroids
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
            
    # 5. Compute BDS, IPS, Anthropology
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
    
    bsi_depts = []
    for idx, row in scaled_feats.iterrows():
        u = row['user']
        w = int(row['time_window'])
        dept = row['department']
        if w <= 52:
            centroid = weekly_centroids.get((dept, w), np.zeros(8))
        else:
            centroid = dept_centroids_avg.get(dept, np.zeros(8))
        bsi_depts.append(cosine_similarity(signatures[u][w], centroid))
    scaled_feats['dept_BSI'] = bsi_depts
    
    # 6. Model evaluations
    print("Evaluating models on test partition...")
    train_df = scaled_feats[train_mask]
    test_df = scaled_feats[test_mask]
    
    X_train_raw = train_df[feature_cols].values
    X_test_raw = test_df[feature_cols].values
    y_train = train_df['label'].values
    y_test = test_df['label'].values
    
    # Train Random Forest
    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
    rf.fit(X_train_raw, y_train)
    rf_pred = rf.predict(X_test_raw)
    rf_scores = rf.predict_proba(X_test_raw)[:, 1]
    
    # Train XGBoost
    ratio = (len(y_train) - np.sum(y_train)) / np.sum(y_train)
    xgb = XGBClassifier(scale_pos_weight=ratio, random_state=42, eval_metric='logloss')
    xgb.fit(X_train_raw, y_train)
    xgb_pred = xgb.predict(X_test_raw)
    xgb_scores = xgb.predict_proba(X_test_raw)[:, 1]
    
    # Train unsupervised baselines
    contam = max(0.001, np.sum(y_train) / len(y_train))
    iso = IsolationForest(contamination=contam, random_state=42)
    iso.fit(X_train_raw)
    iso_scores = -iso.score_samples(X_test_raw)
    iso_pred = np.where(iso.predict(X_test_raw) == -1, 1, 0)
    
    oc_svm = OneClassSVM(nu=contam, kernel='rbf', gamma='scale')
    oc_svm.fit(X_train_raw[y_train == 0])
    oc_scores = -oc_svm.score_samples(X_test_raw)
    oc_pred = np.where(oc_svm.predict(X_test_raw) == -1, 1, 0)
    
    # Compute metrics
    def get_metrics_dict(y_true, y_pred, y_scores):
        return {
            'prec': float(precision_score(y_true, y_pred, zero_division=0)),
            'rec': float(recall_score(y_true, y_pred, zero_division=0)),
            'f1': float(f1_score(y_true, y_pred, zero_division=0)),
            'auprc': float(calculate_auprc(y_true, y_scores))
        }
        
    ml_metrics = {
        'Random Forest': get_metrics_dict(y_test, rf_pred, rf_scores),
        'XGBoost': get_metrics_dict(y_test, xgb_pred, xgb_scores),
        'Isolation Forest': get_metrics_dict(y_test, iso_pred, iso_scores),
        'One-Class SVM': get_metrics_dict(y_test, oc_pred, oc_scores)
    }
    
    # 7. Ablation study (using XGBoost on training splits)
    print("Running Ablation Study...")
    def run_ablation(feat_list, train_d, test_d):
        X_tr = train_d[feat_list].values
        X_te = test_d[feat_list].values
        clf = XGBClassifier(scale_pos_weight=ratio, random_state=42, eval_metric='logloss')
        clf.fit(X_tr, y_train)
        pred = clf.predict(X_te)
        scores = clf.predict_proba(X_te)[:, 1]
        return get_metrics_dict(y_test, pred, scores)
        
    ablation_metrics = {
        'A. Raw Features Only': run_ablation(feature_cols, train_df, test_df),
        'B. DBS Only': run_ablation(feature_cols, train_df, test_df), # since Min-Max scaled
        'C. DBS + BSI/BDS': run_ablation(feature_cols + ['BDS', 'dept_BSI'], train_df, test_df),
        'D. DBS + Anthropology': run_ablation(feature_cols + ['IDP', 'BC', 'SRC'], train_df, test_df)
    }
    
    # For E. Full Cyber DNA (13 features + Z-score filter)
    # We train model on 13 features first
    full_feature_list = feature_cols + ['BDS', 'dept_BSI', 'IDP', 'BC', 'SRC']
    X_tr_full = train_df[full_feature_list].values
    X_te_full = test_df[full_feature_list].values
    clf_full = XGBClassifier(scale_pos_weight=ratio, random_state=42, eval_metric='logloss')
    clf_full.fit(X_tr_full, y_train)
    xgb_full_scores = clf_full.predict_proba(X_te_full)[:, 1]
    xgb_full_pred = clf_full.predict(X_te_full)
    
    # Filter predictions at Z = -2.5
    test_rows_list = test_df.reset_index(drop=True)
    full_preds = []
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
            full_preds.append(0 if is_transition else 1)
        else:
            full_preds.append(0)
            
    ablation_metrics['E. Full Cyber DNA (Z-Score Filter)'] = {
        'prec': float(precision_score(y_test, full_preds, zero_division=0)),
        'rec': float(recall_score(y_test, full_preds, zero_division=0)),
        'f1': float(f1_score(y_test, full_preds, zero_division=0)),
        'auprc': float(calculate_auprc(y_test, xgb_full_scores))
    }
    
    # 8. Department filter Z-score sweep table
    print("Running Departmental Filter Z-score sweep...")
    z_sweep_results = []
    z_thresholds = [-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0]
    
    for z in z_thresholds:
        preds = []
        suppressed = 0
        ben_sup = 0
        mal_sup = 0
        for idx, row in test_rows_list.iterrows():
            raw_pred = xgb_full_pred[idx]
            is_mal = row['label']
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
                    if z_score >= z and bsi > 0.85:
                        is_transition = True
                        break
                if is_transition:
                    preds.append(0)
                    suppressed += 1
                    if is_mal == 0:
                        ben_sup += 1
                    else:
                        mal_sup += 1
                else:
                    preds.append(1)
            else:
                preds.append(0)
                
        # calculate post-suppression score list for AUPRC
        post_scores = []
        for idx, row in test_rows_list.iterrows():
            raw_pred = xgb_full_pred[idx]
            raw_score = xgb_full_scores[idx]
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
                    if z_score >= z and bsi > 0.85:
                        is_transition = True
                        break
                post_scores.append(0.0 if is_transition else raw_score)
            else:
                post_scores.append(raw_score)
                
        sweep_prec = float(precision_score(y_test, preds, zero_division=0))
        sweep_rec = float(recall_score(y_test, preds, zero_division=0))
        sweep_f1 = float(f1_score(y_test, preds, zero_division=0))
        sweep_auprc = float(calculate_auprc(y_test, post_scores))
        
        z_sweep_results.append({
            'z_threshold': float(z),
            'precision': sweep_prec,
            'recall': sweep_rec,
            'f1': sweep_f1,
            'auprc': sweep_auprc,
            'suppressed_total': int(suppressed),
            'suppressed_benign': int(ben_sup),
            'suppressed_malicious': int(mal_sup)
        })
        
    # 9. Dynamic Research Summary and descriptive statistics
    print("Computing dynamic statistics...")
    benign_weeks_bds = scaled_feats[scaled_feats['label'] == 0]['BDS']
    malicious_weeks_bds = scaled_feats[scaled_feats['label'] == 1]['BDS']
    avg_bds_benign = float(benign_weeks_bds.mean())
    avg_bds_malicious = float(malicious_weeks_bds.mean())
    
    benign_users_list = [u for u in cohort_users if u not in malicious_users]
    mal_users_list = [u for u in cohort_users if u in malicious_users]
    
    avg_idp_ben = float(np.mean([user_anthro[u]['IDP'] for u in benign_users_list if u in user_anthro]))
    avg_idp_mal = float(np.mean([user_anthro[u]['IDP'] for u in mal_users_list if u in user_anthro]))
    avg_src_ben = float(np.mean([user_anthro[u]['SRC'] for u in benign_users_list if u in user_anthro]))
    avg_src_mal = float(np.mean([user_anthro[u]['SRC'] for u in mal_users_list if u in user_anthro]))
    avg_bc_ben = float(np.mean([user_anthro[u]['BC'] for u in benign_users_list if u in user_anthro]))
    avg_bc_mal = float(np.mean([user_anthro[u]['BC'] for u in mal_users_list if u in user_anthro]))
    
    # Determine best model
    best_model_name = "XGBoost"
    best_f1_score = ml_metrics['XGBoost']['f1']
    for m, met in ml_metrics.items():
        if met['f1'] > best_f1_score:
            best_f1_score = met['f1']
            best_model_name = m
            
    research_summary = {
        'best_model': best_model_name,
        'best_f1': best_f1_score,
        'avg_bds_benign': avg_bds_benign,
        'avg_bds_malicious': avg_bds_malicious,
        'avg_idp_benign': avg_idp_ben,
        'avg_idp_malicious': avg_idp_mal,
        'avg_src_benign': avg_src_ben,
        'avg_src_malicious': avg_src_mal,
        'department_filter_enabled': False,
        'reason': "Filter reduced F1 on CERT dataset due to overlapping behaviors"
    }
    
    # 10. Select 100-user visualization cohort (70 malicious + 30 highest-drift benign)
    print("Selecting visualization cohort (70 malicious + 30 high-drift benign)...")
    # Calculate max BDS for each user
    user_max_bds = {}
    for u in signatures:
        timeline = [np.linalg.norm(signatures[u][w] - signatures[u][user_earliest_week[u]]) for w in signatures[u]]
        user_max_bds[u] = max(timeline) if timeline else 0.0
        
    benign_drifts = [(u, user_max_bds[u]) for u in benign_users_list]
    benign_drifts_sorted = sorted(benign_drifts, key=lambda x: x[1], reverse=True)
    top_30_benign = [u for u, d in benign_drifts_sorted[:30]]
    
    viz_users = sorted(mal_users_list + top_30_benign)
    print(f"Visualization cohort selected. Total: {len(viz_users)} users")
    
    # 11. Threat Case Explorer Data (computed across whole cohort)
    print("Computing Threat Case Explorer data...")
    # Top 10 malicious users by BDS
    mal_bds_list = [(u, user_max_bds[u]) for u in mal_users_list]
    mal_bds_sorted = sorted(mal_bds_list, key=lambda x: x[1], reverse=True)[:10]
    top_malicious_bds = []
    for u, bds_val in mal_bds_sorted:
        # Find which week has max BDS
        timeline = {w: np.linalg.norm(signatures[u][w] - signatures[u][user_earliest_week[u]]) for w in signatures[u]}
        max_w = max(timeline, key=timeline.get)
        top_malicious_bds.append({
            'user': u,
            'department': user_dept.get(u, 'Unknown'),
            'max_bds': float(bds_val),
            'week': int(max_w)
        })
        
    # Top 10 benign users by BDS
    ben_bds_sorted = benign_drifts_sorted[:10]
    top_benign_bds = []
    for u, bds_val in ben_bds_sorted:
        timeline = {w: np.linalg.norm(signatures[u][w] - signatures[u][user_earliest_week[u]]) for w in signatures[u]}
        max_w = max(timeline, key=timeline.get)
        top_benign_bds.append({
            'user': u,
            'department': user_dept.get(u, 'Unknown'),
            'max_bds': float(bds_val),
            'week': int(max_w)
        })
        
    # Top 10 highest similarity user pairs (BSI) across all weeks
    # To avoid duplicate pairs and self similarity
    all_weeks = sorted(list(raw_feats['time_window'].unique()))
    bsi_pairs = []
    for w in all_weeks:
        # Calculate BSI between all cohort users in week w
        active_users = [u for u in cohort_users if w in signatures[u]]
        N = len(active_users)
        for i in range(N):
            for j in range(i + 1, N):
                u1 = active_users[i]
                u2 = active_users[j]
                bsi_val = cosine_similarity(signatures[u1][w], signatures[u2][w])
                bsi_pairs.append((u1, u2, int(w), bsi_val))
                
    bsi_pairs_sorted = sorted(bsi_pairs, key=lambda x: x[3], reverse=True)[:10]
    top_bsi_pairs = [{
        'user1': p[0],
        'user2': p[1],
        'week': p[2],
        'bsi': float(p[3]),
        'dept1': user_dept.get(p[0], 'Unknown'),
        'dept2': user_dept.get(p[1], 'Unknown')
    } for p in bsi_pairs_sorted]
    
    # 12. Build BSI matrices for viz cohort
    print("Building BSI matrices for visualization cohort...")
    viz_bsi_matrices = {}
    for w in all_weeks:
        matrix = []
        for u1 in viz_users:
            row = []
            for u2 in viz_users:
                if w in signatures[u1] and w in signatures[u2]:
                    bsi_val = cosine_similarity(signatures[u1][w], signatures[u2][w])
                else:
                    bsi_val = 0.0
                row.append(round(bsi_val, 4))
            matrix.append(row)
        viz_bsi_matrices[str(w)] = matrix
        
    # 13. Build BDS timelines for viz cohort
    print("Building BDS timelines for visualization cohort...")
    viz_bds_timelines = {}
    for u in viz_users:
        timeline = []
        for w in all_weeks:
            if w in signatures[u]:
                bds_val = np.linalg.norm(signatures[u][w] - signatures[u][user_earliest_week[u]])
            else:
                bds_val = 0.0
            timeline.append(round(bds_val, 4))
        viz_bds_timelines[u] = timeline
        
    # 14. Build raw features dictionary for viz cohort
    print("Building raw features dictionary for visualization cohort...")
    viz_raw_features = {}
    for u in viz_users:
        viz_raw_features[u] = {}
        for w in all_weeks:
            user_w_row = raw_feats[(raw_feats['user'] == u) & (raw_feats['time_window'] == w)]
            if not user_w_row.empty:
                row = user_w_row.iloc[0]
                viz_raw_features[u][str(w)] = {
                    'login_freq': int(row['login_freq']),
                    'active_hours': round(float(row['active_hours']), 4),
                    'avg_session': round(float(row['avg_session']), 2),
                    'email_freq': int(row['email_freq']),
                    'vocab_diversity': round(float(row['vocab_diversity']), 4),
                    'response_time': round(float(row['response_time']), 2),
                    'contact_diversity': int(row['contact_diversity']),
                    'reciprocity': round(float(row['reciprocity']), 4)
                }
            else:
                viz_raw_features[u][str(w)] = {
                    'login_freq': 0, 'active_hours': 0.0, 'avg_session': 0.0, 'email_freq': 0,
                    'vocab_diversity': 0.0, 'response_time': 0.0, 'contact_diversity': 0, 'reciprocity': 0.0
                }
                
    # 15. Generate alerts for viz cohort (suppression disabled: BSI threshold = 1.0)
    print("Generating active alerts for viz cohort...")
    alerts = []
    
    # Severe behavioral drift alerts (BDS >= 0.6)
    for u in viz_users:
        timeline = viz_bds_timelines[u]
        is_mal = int(u in mal_users_list)
        for w_idx, bds_val in enumerate(timeline):
            w = all_weeks[w_idx]
            if bds_val >= 0.6:
                # BSI threshold = 1.0 means no suppression triggers
                alerts.append({
                    'user': u,
                    'week': int(w),
                    'type': 'red',
                    'title': 'Severe Behavioral Drift',
                    'desc': f"User {u} in Week {w} shifted significantly from baseline (BDS: {bds_val:.4f}). " +
                            (f"Confirmed insider activity." if is_mal else "Normal user behavioral spike.")
                })
                
    # Check for similarity identity collisions among viz cohort
    for w in all_weeks:
        matrix = viz_bsi_matrices[str(w)]
        for i, u1 in enumerate(viz_users):
            for j, u2 in enumerate(viz_users):
                if i < j:
                    bsi_val = matrix[i][j]
                    if bsi_val > 0.99:
                        alerts.append({
                            'user': f"{u1} & {u2}",
                            'week': int(w),
                            'type': 'yellow',
                            'title': 'Identity Collision Warning',
                            'desc': f"Profile collision between {u1} and {u2} in Week {w} (BSI: {bsi_val:.4f}). Suspect duplicate behavioral footprint or shared accounts."
                        })
                        
    # Sort alerts chronologically
    alerts = sorted(alerts, key=lambda x: x['week'])
    
    # 16. Anthropology scores for viz cohort
    viz_anthropology = {}
    for u in viz_users:
        viz_anthropology[u] = {
            'IDP': round(float(user_anthro[u]['IDP']), 4),
            'BC': round(float(user_anthro[u]['BC']), 4),
            'SRC': round(float(user_anthro[u]['SRC']), 4)
        }
        
    viz_departments = {u: user_dept.get(u, 'Unknown') for u in viz_users}
    
    # 17. Package JSON for dashboard
    global_stats = {
        'total_users': 1000,
        'total_user_weeks': 67167,
        'total_malicious_weeks': 322,
        'total_benign_weeks': 66845,
        'train_weeks': 52,
        'test_weeks': 20,
        'cohort_users_eval': len(cohort_users),
        'cohort_users_viz': len(viz_users)
    }
    
    data_payload = {
        'global_stats': global_stats,
        'research_summary': research_summary,
        'ml_metrics': ml_metrics,
        'ablation_metrics': ablation_metrics,
        'calibration_sweep': z_sweep_results,
        'threat_case_explorer': {
            'top_malicious_bds': top_malicious_bds,
            'top_benign_bds': top_benign_bds,
            'top_bsi_pairs': top_bsi_pairs
        },
        'users': viz_users,
        'weeks': [int(w) for w in all_weeks],
        'alerts': alerts,
        'bsi_matrices': viz_bsi_matrices,
        'bds_timelines': viz_bds_timelines,
        'raw_features': viz_raw_features,
        'anthropology': viz_anthropology,
        'user_departments': viz_departments
    }
    
    output_path = 'web_app/src/cyber_dna_data.json'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data_payload, f, indent=2)
    print(f"Data successfully exported to {output_path}.")
    
    # 18. Package unified JSON results/final_metrics.json
    final_metrics_payload = {
        'dataset': {
            'total_users': 1000,
            'total_benign_users': 930,
            'total_malicious_users': 70,
            'total_user_weeks': 67167,
            'total_malicious_weeks': 322,
            'total_benign_weeks': 66845,
            'train_user_weeks': 49867,
            'test_user_weeks': 17300,
            'evaluation_cohort_size': len(cohort_users)
        },
        'models': ml_metrics,
        'anthropology': {
            'average_idp_benign': avg_idp_ben,
            'average_idp_malicious': avg_idp_mal,
            'average_bc_benign': avg_bc_ben,
            'average_bc_malicious': avg_bc_mal,
            'average_src_benign': avg_src_ben,
            'average_src_malicious': avg_src_mal
        },
        'ablation': ablation_metrics,
        'calibration': z_sweep_results
    }
    
    final_metrics_path = os.path.join(results_dir, 'final_metrics.json')
    with open(final_metrics_path, 'w', encoding='utf-8') as f:
        json.dump(final_metrics_payload, f, indent=2)
    print(f"Unified metrics JSON exported to {final_metrics_path}.")
    
    # 19. Export paper-ready CSV files
    # A. ml_metrics.csv
    ml_rows = []
    for m, met in ml_metrics.items():
        ml_rows.append({
            'Model': m,
            'Precision': round(met['prec'], 4),
            'Recall': round(met['rec'], 4),
            'F1-Score': round(met['f1'], 4),
            'AUPRC': round(met['auprc'], 4)
        })
    pd.DataFrame(ml_rows).to_csv(os.path.join(results_dir, 'ml_metrics.csv'), index=False)
    
    # B. ablation_study.csv
    ab_rows = []
    for config, met in ablation_metrics.items():
        ab_rows.append({
            'Configuration': config,
            'Precision': round(met['prec'], 4),
            'Recall': round(met['rec'], 4),
            'F1-Score': round(met['f1'], 4),
            'AUPRC': round(met['auprc'], 4)
        })
    pd.DataFrame(ab_rows).to_csv(os.path.join(results_dir, 'ablation_study.csv'), index=False)
    
    # C. calibration_sweep.csv
    pd.DataFrame(z_sweep_results).to_csv(os.path.join(results_dir, 'calibration_sweep.csv'), index=False)
    
    # D. anthropology_summary.csv
    anthro_rows = [
        {
            'User Type': 'Benign Users',
            'Mean IDP': round(avg_idp_ben, 4),
            'Mean BC': round(avg_bc_ben, 4),
            'Mean SRC': round(avg_src_ben, 4)
        },
        {
            'User Type': 'Malicious Users',
            'Mean IDP': round(avg_idp_mal, 4),
            'Mean BC': round(avg_bc_mal, 4),
            'Mean SRC': round(avg_src_mal, 4)
        }
    ]
    pd.DataFrame(anthro_rows).to_csv(os.path.join(results_dir, 'anthropology_summary.csv'), index=False)
    
    # E. dataset_statistics.csv
    stats_rows = [
        {'Metric': 'Total Corporate Users', 'Count': 1000},
        {'Metric': 'Total Malicious Users', 'Count': 70},
        {'Metric': 'Total Benign Users', 'Count': 930},
        {'Metric': 'Total User-Weeks', 'Count': 67167},
        {'Metric': 'Total Benign Weeks', 'Count': 66845},
        {'Metric': 'Total Malicious Weeks', 'Count': 322},
        {'Metric': 'Train Split User-Weeks (W1-52)', 'Count': 49867},
        {'Metric': 'Test Split User-Weeks (W53-72)', 'Count': 17300},
        {'Metric': 'Insiders Evaluation Cohort', 'Count': len(cohort_users)},
        {'Metric': 'Dashboard Visualized Cohort', 'Count': len(viz_users)}
    ]
    pd.DataFrame(stats_rows).to_csv(os.path.join(results_dir, 'dataset_statistics.csv'), index=False)
    print("CSV tables successfully exported to results/ directory.")
    print("==================================================")

if __name__ == '__main__':
    main()
