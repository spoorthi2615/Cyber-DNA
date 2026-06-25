import pandas as pd
import numpy as np
import json
import os
import sys
from scipy.spatial.distance import euclidean, pdist

# Add root directory to path to import ablation script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cyber_dna_phase11_ablation import (
    load_ground_truth, load_data, extract_logon_features, 
    extract_email_features, extract_device_features
)

RESULTS_DIR = r"C:\Users\SPOORTHI\Desktop\Cyber DNA\results"
JSON_OUT_PATH = r"C:\Users\SPOORTHI\Desktop\Cyber DNA\web_app\src\cyber_dna_data.json"

def compute_metrics():
    print("--- Dashboard Export: Computing Real Metrics ---")
    
    malicious_set = load_ground_truth()
    logon_df, email_df, device_df = load_data()
    
    lf = extract_logon_features(logon_df)
    ef = extract_email_features(email_df)
    df = extract_device_features(device_df)
    
    dbs = pd.merge(pd.merge(lf, ef, on=['user', 'week'], how='outer'), df, on=['user', 'week'], how='outer').fillna(0)
    dbs['is_malicious'] = dbs.apply(lambda r: 1 if (r['user'], r['week']) in malicious_set else 0, axis=1)
    
    # Feature set for E. Full Phase 11
    features = [
        'login_freq', 'active_hours_ratio', 'avg_session_duration', 'workstation_diversity', 
        'after_hours_logins', 'weekend_activity', 'email_freq', 'contact_diversity', 'vocab_diversity', 
        'reciprocity_ratio', 'response_time', 'usb_transfers',
        'usb_event_count', 'usb_active_days', 'usb_after_hours_count', 'usb_weekend_count',
        'unique_pc_count', 'new_pc_count', 'pc_switch_count',
        'after_hours_logon_count', 'after_hours_logon_ratio', 'weekend_logon_count', 'weekend_logon_ratio',
        'emails_sent_after_hours', 'emails_sent_weekend'
    ]
    
    print("-> Computing weekly BDS per user...")
    dbs_sorted = dbs.sort_values(['user', 'week']).copy()
    first_weeks = dbs_sorted.groupby('user').first()[features].reset_index()
    first_weeks.columns = ['user'] + [f"{c}_base" for c in features]
    dbs_config = pd.merge(dbs_sorted, first_weeks, on='user', how='left')
    
    def calc_bds(row): return euclidean(row[features].values.astype(float), row[[f"{c}_base" for c in features]].values.astype(float))
    dbs_config['BDS'] = dbs_config.apply(calc_bds, axis=1)
    
    print("-> Computing Temporal Drift (Weekly Mean BDS)...")
    temporal_drift = []
    
    # Range: W1 to W72
    weeks = sorted(dbs_config['week'].unique())
    for w in weeks:
        if w > 72: continue
        week_df = dbs_config[dbs_config['week'] == w]
        if len(week_df) == 0: continue
        
        benign = week_df[week_df['is_malicious'] == 0]
        malicious = week_df[week_df['is_malicious'] == 1]
        
        b_mean = benign['BDS'].mean() if len(benign) > 0 else 0.0
        m_mean = malicious['BDS'].mean() if len(malicious) > 0 else 0.0
        
        temporal_drift.append({
            "week": f"W{int(w)}",
            "benign_bds": float(b_mean),
            "malicious_bds": float(m_mean)
        })
    
    drift_df = pd.DataFrame(temporal_drift)
    drift_df.to_csv(os.path.join(RESULTS_DIR, 'dashboard_temporal_drift.csv'), index=False)
    print("   Saved dashboard_temporal_drift.csv")
    
    print("-> Computing BSI Distribution (Training Period Means)...")
    train_df = dbs_config[dbs_config['week'] <= 52].copy()
    
    # Build per-user mean vectors for training period
    user_vectors = train_df.groupby('user')[features].mean()
    
    malicious_users = set([u for u, w in malicious_set])
    
    users = user_vectors.index.tolist()
    vectors = user_vectors.values
    
    print(f"   Computing pairwise cosine similarity for {len(users)} users...")
    if len(users) > 1:
        dist_matrix = pdist(vectors, metric='cosine')
        # similarity = 1 - distance
        sim_matrix = 1.0 - np.nan_to_num(dist_matrix)
    else:
        sim_matrix = np.array([])
        
    print("   Bucketing pairs...")
    
    idx = 0
    bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    bin_labels = ["0.00-0.10", "0.10-0.20", "0.20-0.30", "0.30-0.40", "0.40-0.50", "0.50-0.60", "0.60-0.70", "0.70-0.80", "0.80-0.90", "0.90-1.00"]
    
    results_bins = {label: {"benign_benign": 0, "benign_malicious": 0, "malicious_malicious": 0} for label in bin_labels}
    
    n = len(users)
    for i in range(n):
        for j in range(i+1, n):
            sim = sim_matrix[idx]
            idx += 1
            
            u1, u2 = users[i], users[j]
            m1 = u1 in malicious_users
            m2 = u2 in malicious_users
            
            if m1 and m2:
                pair_type = "malicious_malicious"
            elif m1 or m2:
                pair_type = "benign_malicious"
            else:
                pair_type = "benign_benign"
                
            for b_idx in range(len(bins)-1):
                if b_idx == len(bins)-2: # last bin
                    if bins[b_idx] <= sim <= bins[b_idx+1]:
                        results_bins[bin_labels[b_idx]][pair_type] += 1
                        break
                else:
                    if bins[b_idx] <= sim < bins[b_idx+1]:
                        results_bins[bin_labels[b_idx]][pair_type] += 1
                        break
    
    bsi_distribution = []
    for label in bin_labels:
        entry = {"range": label}
        entry.update(results_bins[label])
        bsi_distribution.append(entry)
        
    bsi_df = pd.DataFrame(bsi_distribution)
    bsi_df.to_csv(os.path.join(RESULTS_DIR, 'dashboard_bsi_distribution.csv'), index=False)
    print("   Saved dashboard_bsi_distribution.csv")
    
    print("-> Injecting into cyber_dna_data.json...")
    with open(JSON_OUT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if "dashboard_illustrative_data" in data:
        del data["dashboard_illustrative_data"]
        
    data["dashboard_computed_metrics"] = {
        "temporal_drift": temporal_drift,
        "bsi_distribution": bsi_distribution,
        "metadata": {
            "bsi_vector_basis": "mean training-period DBS per user",
            "bsi_similarity": "cosine similarity",
            "temporal_drift_definition": "weekly cohort mean BDS",
            "source": "computed from CERT r4.2 Phase 11 feature pipeline"
        }
    }
    
    with open(JSON_OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print("   JSON updated successfully.")
    
    with open(os.path.join(RESULTS_DIR, 'dashboard_metrics_summary.json'), 'w') as f:
        json.dump(data["dashboard_computed_metrics"], f, indent=2)

if __name__ == '__main__':
    compute_metrics()
