import pandas as pd
import sys
import os

# Import our custom modules
from preprocess import CERTDataLoader
from extractors.activity import extract_activity_features
from extractors.communication import extract_communication_features
from extractors.interaction import extract_interaction_features

def main():
    print("==================================================")
    print("         VERIFYING PHASE 2 FEATURE EXTRACTION     ")
    print("==================================================")
    
    data_dir = 'data/cert_sample'
    
    # 1. Load logs
    loader = CERTDataLoader(data_dir)
    logons = loader.load_logon_logs()
    emails = loader.load_email_logs()
    
    if logons.empty or emails.empty:
        print("Error: Ingested log files are empty. Run Phase 1 verification first to generate mock data.")
        sys.exit(1)
        
    # 2. Slice time windows (7-day periods)
    logons = loader.extract_time_windows(logons, window_size_days=7)
    emails = loader.extract_time_windows(emails, window_size_days=7)
    
    # 3. Extract features
    print("\nRunning Activity extractor...")
    act_feats = extract_activity_features(logons)
    
    print("Running Communication extractor...")
    comm_feats = extract_communication_features(emails)
    
    print("Running Interaction extractor...")
    int_feats = extract_interaction_features(emails)
    
    # 4. Merge all features
    print("Merging feature matrices...")
    merged = pd.merge(act_feats, comm_feats, on=['user', 'time_window'], how='outer')
    merged = pd.merge(merged, int_feats, on=['user', 'time_window'], how='outer')
    
    # Fill empty columns
    merged = merged.fillna(0.0)
    merged = merged.sort_values(['user', 'time_window'])
    
    print("\n---------------- Extracted Feature Table ----------------")
    print(merged.to_string(index=False))
    
    # Verify Bob's drift behavior is represented in raw figures
    bob_w1 = merged[(merged['user'] == 'Bob') & (merged['time_window'] == 1)].iloc[0]
    bob_w3 = merged[(merged['user'] == 'Bob') & (merged['time_window'] == 3)].iloc[0]
    
    print("\nVerification Checks:")
    print(f"Bob's Week 1 Logons: {bob_w1['login_freq']} | Week 3 Logons: {bob_w3['login_freq']}")
    print(f"Bob's Week 1 Active Hour Business Ratio: {bob_w1['active_hours']} | Week 3: {bob_w3['active_hours']}")
    print(f"Bob's Week 1 Email Freq: {bob_w1['email_freq']} | Week 3: {bob_w3['email_freq']}")
    
    if bob_w3['active_hours'] < bob_w1['active_hours'] and bob_w3['email_freq'] > bob_w1['email_freq']:
        print("\nStatus: Phase 2 Verification Successful! Behavioral shifts correctly captured in features.")
    else:
        print("\nWarning: Expected behavioral differences in features were not detected.")
    print("==================================================")

if __name__ == '__main__':
    main()
