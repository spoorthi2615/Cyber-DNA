import pandas as pd
import numpy as np
import sys

from preprocess import CERTDataLoader
from extractors.activity import extract_activity_features
from extractors.communication import extract_communication_features
from extractors.interaction import extract_interaction_features
from signature import SignatureBuilder
from engine import CyberDNAEngine

def main():
    print("==================================================")
    print("         VERIFYING PHASE 3 MATHEMATICAL ENGINE    ")
    print("==================================================")
    
    data_dir = 'data/cert_sample'
    
    # 1. Load logs and time-slice
    loader = CERTDataLoader(data_dir)
    logons = loader.load_logon_logs()
    emails = loader.load_email_logs()
    
    if logons.empty or emails.empty:
        print("Error: Mock dataset empty. Please run verify_phase1.py first.")
        sys.exit(1)
        
    logons = loader.extract_time_windows(logons, 7)
    emails = loader.extract_time_windows(emails, 7)
    
    # 2. Extract raw features
    act_df = extract_activity_features(logons)
    comm_df = extract_communication_features(emails)
    int_df = extract_interaction_features(emails)
    
    raw_feats = pd.merge(act_df, comm_df, on=['user', 'time_window'], how='outer')
    raw_feats = pd.merge(raw_feats, int_df, on=['user', 'time_window'], how='outer').fillna(0.0)
    
    # 3. Build DBS signatures
    builder = SignatureBuilder(raw_feats)
    signatures, composite_df, anthro_df = builder.build_signatures()
    
    print("\n--- Layer 3.5: Anthropological Anthropology Scores ---")
    print(anthro_df.to_string(index=False))
    
    # 4. Compute BSI Similarity Matrix (Week 1)
    print("\n--- Layer 4: Behavioral Similarity Index (BSI) ---")
    users = list(signatures.keys())
    matrix = []
    
    for u1 in users:
        row = []
        for u2 in users:
            bsi = CyberDNAEngine.calculate_bsi(signatures[u1][1], signatures[u2][1])
            row.append(bsi)
        matrix.append(row)
        
    sim_df = pd.DataFrame(matrix, index=users, columns=users)
    print("Similarity Matrix (Time Window 1):")
    print(sim_df.round(4))
    
    # 5. Compute BDS Behavioral Drift (Temporal Analysis)
    print("\n--- Layer 5: Behavioral Drift Score (BDS) ---")
    drift_records = []
    for user in users:
        dbs_w1 = signatures[user][1]
        print(f"\nUser: {user}")
        for w in sorted(list(signatures[user].keys())):
            if w == 1:
                continue
            dbs_cw = signatures[user][w]
            bds = CyberDNAEngine.calculate_bds(dbs_w1, dbs_cw)
            
            # Status check
            if bds < 0.2:
                status = "STABLE"
            elif bds < 0.6:
                status = "MODERATE DRIFT"
            else:
                status = "SEVERE BEHAVIORAL DRIFT"
                
            print(f"  Week 1 -> Week {w}: BDS = {bds:.4f} ({status})")
            drift_records.append({
                'user': user,
                'target_window': w,
                'BDS': bds,
                'status': status
            })
            
    # 6. Safety Assertions
    print("\n--- Running Framework Assertions ---")
    
    # Check 1: Charlie and David are highly similar in Week 1
    cd_similarity = sim_df.loc['Charlie', 'David']
    print(f"Charlie-David Similarity (BSI): {cd_similarity:.4f}")
    assert cd_similarity > 0.98, "Charlie & David similarity check failed."
    print("  => Credential-Sharing Alert: SUCCESS")
    
    # Check 2: Bob displays severe drift in Week 3
    bob_drift = [r for r in drift_records if r['user'] == 'Bob' and r['target_window'] == 3][0]
    print(f"Bob's Week 3 Drift (BDS): {bob_drift['BDS']:.4f} ({bob_drift['status']})")
    assert bob_drift['BDS'] > 1.0, "Bob's drift detection failed."
    print("  => Threat Drift Alert: SUCCESS")
    
    # Check 3: Alice remains stable throughout
    alice_drifts = [r['BDS'] for r in drift_records if r['user'] == 'Alice']
    print(f"Alice's Max Drift (BDS): {max(alice_drifts):.4f}")
    assert max(alice_drifts) < 0.2, "Alice's stability check failed."
    print("  => Baseline Stability: SUCCESS")
    
    print("\nStatus: Phase 3 Verification Successful! The Cyber DNA mathematical engine is functioning perfectly.")
    print("==================================================")

if __name__ == '__main__':
    main()
