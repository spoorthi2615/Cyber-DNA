import pandas as pd
import os
import sys

# Ensure src dir is in import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from preprocess import CERTDataLoader

def main():
    print("==================================================")
    print("      VERIFYING PHASE 1 CERT DATASET MIGRATION     ")
    print("==================================================")
    
    data_dir = 'data/cert_r4.2/r4.2'
    
    # 1. Initialize Loader
    loader = CERTDataLoader(data_dir)
    
    # 2. Load Logon Logs to get users and active periods
    logons = loader.load_logon_logs()
    if logons.empty:
        print("Error: logon.csv is empty or not found.")
        sys.exit(1)
        
    # Get global reference start date
    min_date = logons['date'].min()
    print(f"Global Reference Start Date (min_date): {min_date}")
    
    # Extract time windows (7-day intervals)
    logons = loader.extract_time_windows(logons, window_size_days=7, min_date=min_date)
    
    # Identify unique active user-weeks
    active_user_weeks = logons[['user', 'time_window']].drop_duplicates().sort_values(['user', 'time_window']).reset_index(drop=True)
    
    # 3. Load Insider Threat Ground Truth
    insiders_df = loader.load_insider_labels()
    if insiders_df.empty:
        print("Error: insiders.csv is empty or not found.")
        sys.exit(1)
        
    # 4. Generate Temporal Labels
    labeled_weeks = loader.generate_user_weeks_labels(active_user_weeks, insiders_df, min_date, window_size_days=7)
    
    # 5. Chronological Partitioning (Weeks 1-52 as Train, 53+ as Test)
    train_df, test_df = loader.partition_train_test(labeled_weeks, split_week=52)
    
    # 6. Calculate statistics
    all_users = labeled_weeks['user'].unique()
    malicious_users = insiders_df['user'].unique()
    
    # Verify mapping: how many of the insiders are present in our logon logs?
    malicious_in_logons = [u for u in malicious_users if u in all_users]
    benign_users = [u for u in all_users if u not in malicious_users]
    
    total_user_weeks = len(labeled_weeks)
    total_malicious_weeks = labeled_weeks['label'].sum()
    total_benign_weeks = total_user_weeks - total_malicious_weeks
    
    train_malicious_weeks = train_df['label'].sum()
    train_benign_weeks = len(train_df) - train_malicious_weeks
    
    test_malicious_weeks = test_df['label'].sum()
    test_benign_weeks = len(test_df) - test_malicious_weeks
    
    # 7. Print statistics
    print("\n---------------- PHASE 1 STATISTICS ----------------")
    print(f"Total Users:             {len(all_users)}")
    print(f"Total Malicious Users:   {len(malicious_in_logons)} (out of {len(malicious_users)} in scenario registry)")
    print(f"Total Benign Users:      {len(benign_users)}")
    print(f"Total User-Weeks:        {total_user_weeks}")
    print(f"Total Malicious Weeks:   {total_malicious_weeks} (Ratio: {total_malicious_weeks / total_user_weeks:.4%})")
    print(f"Total Benign Weeks:      {total_benign_weeks}")
    print("\n--- Train/Test Partition Split (Split Week: 52) ---")
    print(f"Train User-Weeks:        {len(train_df)} (Weeks 1 to 52)")
    print(f"  - Benign Weeks:        {train_benign_weeks}")
    print(f"  - Malicious Weeks:     {train_malicious_weeks}")
    print(f"Test User-Weeks:         {len(test_df)} (Weeks 53 to {labeled_weeks['time_window'].max()})")
    print(f"  - Benign Weeks:        {test_benign_weeks}")
    print(f"  - Malicious Weeks:     {test_malicious_weeks}")
    print("----------------------------------------------------\n")
    
    # 8. Sanity Check Assertions
    print("--- Running Assertions ---")
    
    # Check 1: Benign users must have 0 malicious weeks
    benign_user_weeks = labeled_weeks[labeled_weeks['user'].isin(benign_users)]
    assert benign_user_weeks['label'].sum() == 0, "Assertion Failed: Benign users must not have any malicious weeks."
    print("  [PASSED] Benign users have zero malicious weeks.")
    
    # Check 2: Malicious users must have at least one malicious week (if they had logon activity during their attack)
    malicious_user_weeks = labeled_weeks[labeled_weeks['user'].isin(malicious_in_logons)]
    malicious_user_weeks_with_1 = malicious_user_weeks[malicious_user_weeks['label'] == 1]
    assert len(malicious_user_weeks_with_1) > 0, "Assertion Failed: Malicious users must have at least some malicious weeks."
    print(f"  [PASSED] Malicious users have active threat weeks labeled (Total: {len(malicious_user_weeks_with_1)}).")
    
    # Check 3: Check a specific malicious user's timeline to ensure dynamic temporal labeling works
    sample_malicious_user = malicious_in_logons[0]
    sample_history = labeled_weeks[labeled_weeks['user'] == sample_malicious_user].sort_values('time_window')
    sample_malicious_weeks = sample_history[sample_history['label'] == 1]['time_window'].tolist()
    sample_benign_weeks = sample_history[sample_history['label'] == 0]['time_window'].tolist()
    
    assert len(sample_malicious_weeks) > 0 and len(sample_benign_weeks) > 0, \
        f"Assertion Failed: User {sample_malicious_user} must show both normal and active threat weeks."
    print(f"  [PASSED] Dynamic temporal labeling verified for user {sample_malicious_user}:")
    print(f"           - Benign Weeks:    {sample_benign_weeks[:5]}... (example)")
    print(f"           - Malicious Weeks: {sample_malicious_weeks}")
    
    # Check 4: Check that split partitions are disjoint and cover the entire duration
    assert len(train_df) + len(test_df) == total_user_weeks, \
        "Assertion Failed: Split partitions must equal the total number of user-weeks."
    assert set(train_df['time_window']).isdisjoint(set(test_df['time_window'])), \
        "Assertion Failed: Train and test partitions must have disjoint time windows."
    print("  [PASSED] Train/Test partitioning is disjoint and exhaustive.")
    
    print("\nStatus: All Phase 1 Verification Checks PASSED successfully!")
    print("==================================================")

if __name__ == '__main__':
    main()
