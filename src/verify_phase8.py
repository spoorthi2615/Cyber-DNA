import pandas as pd
import numpy as np
import time
import os
import sys
import gc
import re

try:
    import psutil
except ModuleNotFoundError:
    psutil = None

# Ensure src dir is in import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocess import CERTDataLoader
from extractors.activity import extract_activity_features as extract_activity_new
from extractors.communication import extract_communication_features as extract_communication_new
from extractors.interaction import extract_interaction_features as extract_interaction_new

# --- Define original (old) implementations inline for comparison ---

def tokenize_content(text):
    if not isinstance(text, str):
        return []
    words = re.findall(r'\b\w+\b', text.lower())
    return words

def extract_activity_features_old(logons_df):
    if logons_df.empty:
        return pd.DataFrame(columns=['user', 'time_window', 'login_freq', 'avg_session', 'active_hours'])

    logons_df = logons_df.copy()
    logons_df['date'] = pd.to_datetime(logons_df['date'])
    
    logons_df['hour'] = logons_df['date'].dt.hour
    logons_df['is_business_hour'] = logons_df['hour'].between(8, 18).astype(int)
    
    active_hours_df = logons_df.groupby(['user', 'time_window'])['is_business_hour'].mean().reset_index()
    active_hours_df.rename(columns={'is_business_hour': 'active_hours'}, inplace=True)
    
    logon_only = logons_df[logons_df['activity'] == 'Logon']
    freq_df = logon_only.groupby(['user', 'time_window']).size().reset_index(name='login_freq')
    
    session_durations = []
    sorted_logs = logons_df.sort_values(['user', 'pc', 'date'])
    grouped = sorted_logs.groupby(['user', 'pc'])
    
    for (user, pc), group in grouped:
        logon_time = None
        for idx, row in group.iterrows():
            if row['activity'] == 'Logon':
                logon_time = row['date']
            elif row['activity'] == 'Logoff' and logon_time is not None:
                duration_hrs = (row['date'] - logon_time).total_seconds() / 3600.0
                if duration_hrs > 0 and duration_hrs < 24:
                    session_durations.append({
                        'user': user,
                        'time_window': row['time_window'],
                        'duration': duration_hrs
                    })
                logon_time = None
                
    if session_durations:
        sess_df = pd.DataFrame(session_durations)
        avg_sess_df = sess_df.groupby(['user', 'time_window'])['duration'].mean().reset_index(name='avg_session')
    else:
        avg_sess_df = pd.DataFrame(columns=['user', 'time_window', 'avg_session'])
        
    features_df = pd.merge(freq_df, active_hours_df, on=['user', 'time_window'], how='outer')
    features_df = pd.merge(features_df, avg_sess_df, on=['user', 'time_window'], how='left')
    
    features_df['login_freq'] = features_df['login_freq'].fillna(0.0)
    features_df['avg_session'] = features_df['avg_session'].fillna(0.0)
    features_df['active_hours'] = features_df['active_hours'].fillna(0.0)
    
    return features_df

def extract_communication_features_old(emails_df):
    if emails_df.empty:
        return pd.DataFrame(columns=['user', 'time_window', 'vocab_diversity', 'response_time', 'email_freq'])

    emails_df = emails_df.copy()
    emails_df['date'] = pd.to_datetime(emails_df['date'])

    freq_df = emails_df.groupby(['user', 'time_window']).size().reset_index(name='email_freq')

    grouped_text = emails_df.groupby(['user', 'time_window'])['content'].apply(
        lambda x: ' '.join(x.astype(str))
    ).reset_index()
    
    vocab_diversity_records = []
    for idx, row in grouped_text.iterrows():
        all_words = tokenize_content(row['content'])
        if len(all_words) > 0:
            diversity = len(set(all_words)) / len(all_words)
        else:
            diversity = 0.5
            
        vocab_diversity_records.append({
            'user': row['user'],
            'time_window': row['time_window'],
            'vocab_diversity': diversity
        })
        
    vocab_df = pd.DataFrame(vocab_diversity_records)

    exploded = emails_df[['date', 'user', 'to', 'time_window']].copy()
    exploded['to'] = exploded['to'].astype(str).apply(
        lambda x: [r.split('@')[0].upper().strip() for r in x.split(';') if r.strip()]
    )
    exploded = exploded.explode('to').dropna()
    exploded['sender'] = exploded['user'].str.upper().str.strip()
    exploded['receiver'] = exploded['to']
    
    exploded = exploded.sort_values('date')
    
    s = exploded['sender'].values
    r = exploded['receiver'].values
    c1 = np.where(s < r, s, r)
    c2 = np.where(s < r, r, s)
    exploded['pair_c1'] = c1
    exploded['pair_c2'] = c2
    
    pair_group = exploded.groupby(['pair_c1', 'pair_c2'])
    exploded['prev_sender'] = pair_group['sender'].shift(1)
    exploded['prev_receiver'] = pair_group['receiver'].shift(1)
    exploded['prev_date'] = pair_group['date'].shift(1)
    
    is_reply = (exploded['sender'] == exploded['prev_receiver'])
    time_diff = (exploded['date'] - exploded['prev_date']).dt.total_seconds() / 3600.0
    
    replies = exploded[is_reply & (time_diff > 0) & (time_diff < 24.0)].copy()
    replies['response_time'] = time_diff
    
    if not replies.empty:
        avg_resp_df = replies.groupby(['user', 'time_window'])['response_time'].mean().reset_index()
    else:
        avg_resp_df = pd.DataFrame(columns=['user', 'time_window', 'response_time'])

    features_df = pd.merge(freq_df, vocab_df, on=['user', 'time_window'], how='outer')
    features_df = pd.merge(features_df, avg_resp_df, on=['user', 'time_window'], how='left')

    features_df['email_freq'] = features_df['email_freq'].fillna(0.0)
    features_df['vocab_diversity'] = features_df['vocab_diversity'].fillna(0.5)
    features_df['response_time'] = features_df['response_time'].fillna(1.0)

    return features_df

# --- Helper function to measure RAM ---
def get_memory_usage_mb():
    if psutil is not None:
        process = psutil.Process(os.getpid())
        return f"{process.memory_info().rss / (1024 * 1024):.2f} MB"
    else:
        return "N/A (psutil not installed)"

# --- Verification & Run ---
def main():
    print("==================================================")
    print("      VERIFYING PHASE 8 FEATURE CALIBRATION       ")
    print("==================================================")
    
    # --- PART 1: Parity check on synthetic dataset ---
    print("\n[PART 1] Running Parity Checks on Synthetic Sample...")
    sample_dir = 'data/cert_sample'
    if not os.path.exists(sample_dir):
        print("Mock data not found, generating mock logs...")
        from mock_generator import CERTDataSimulator
        sim = CERTDataSimulator(sample_dir, num_weeks=4)
        sim.generate_logs()
        
    loader = CERTDataLoader(sample_dir)
    logons_mock = loader.load_logon_logs()
    emails_mock = loader.load_email_logs()
    
    logons_mock = loader.extract_time_windows(logons_mock, window_size_days=7)
    emails_mock = loader.extract_time_windows(emails_mock, window_size_days=7)
    
    # 1. Activity parity
    t0 = time.time()
    act_old = extract_activity_features_old(logons_mock)
    time_act_old = time.time() - t0
    
    t0 = time.time()
    act_new = extract_activity_new(logons_mock)
    time_act_new = time.time() - t0
    
    # Compare
    act_old_sorted = act_old.sort_values(['user', 'time_window']).reset_index(drop=True)
    act_new_sorted = act_new.sort_values(['user', 'time_window']).reset_index(drop=True)
    pd.testing.assert_frame_equal(act_old_sorted, act_new_sorted, check_dtype=False)
    print(f"  => Activity Extractor Parity check: PASSED!")
    print(f"     Old runtime: {time_act_old:.4f}s | New runtime: {time_act_new:.4f}s")
    
    # 2. Communication parity
    t0 = time.time()
    comm_old = extract_communication_features_old(emails_mock)
    time_comm_old = time.time() - t0
    
    t0 = time.time()
    comm_new = extract_communication_new(emails_mock)
    time_comm_new = time.time() - t0
    
    # Compare
    comm_old_sorted = comm_old.sort_values(['user', 'time_window']).reset_index(drop=True)
    comm_new_sorted = comm_new.sort_values(['user', 'time_window']).reset_index(drop=True)
    pd.testing.assert_frame_equal(comm_old_sorted, comm_new_sorted, check_dtype=False)
    print(f"  => Communication Extractor Parity check: PASSED!")
    print(f"     Old runtime: {time_comm_old:.4f}s | New runtime: {time_comm_new:.4f}s")
    
    # Clean up mock memory
    del logons_mock, emails_mock, act_old, act_new, comm_old, comm_new
    gc.collect()
    
    # --- PART 2: Speed and Memory Benchmarks on full CERT Dataset ---
    print("\n[PART 2] Running Speed & Memory Benchmarks on Cohort...")
    cert_dir = 'data/cert_r4.2/r4.2'
    cert_loader = CERTDataLoader(cert_dir)
    
    # Measure baseline memory
    base_mem = get_memory_usage_mb()
    print(f"  Baseline RAM: {base_mem}")
    
    # 1. Logon logs benchmark
    print("\n  Ingesting full logon.csv...")
    t0 = time.time()
    logons_cert = cert_loader.load_logon_logs()
    t_ingest_logon = time.time() - t0
    
    logons_cert = cert_loader.extract_time_windows(logons_cert, window_size_days=7)
    
    # Save min logon date for email alignment before deletion
    logon_min_date = logons_cert['date'].min()
    
    # Execute new activity extractor
    print("  Running vectorized Activity feature extractor on full logon dataset...")
    t0 = time.time()
    act_cert = extract_activity_new(logons_cert)
    t_act_cert = time.time() - t0
    mem_act = get_memory_usage_mb()
    
    print(f"  - Logon Ingest time: {t_ingest_logon:.4f}s")
    print(f"  - Activity extraction time: {t_act_cert:.4f}s")
    print(f"  - Activity matrix dimensions: {act_cert.shape}")
    print(f"  - RAM after activity: {mem_act}")
    
    # Delete logon logs to free memory
    del logons_cert
    gc.collect()
    
    # 2. Email logs benchmark (optimized load via chunking + cohort filter)
    print("\n  Ingesting email.csv in chunks (filtering to cohort)...")
    # Identify a cohort of 50 users from the logon logs
    cohort_users = sorted(list(act_cert['user'].unique()[:50]))
    print(f"  Filtering email.csv to cohort of {len(cohort_users)} users...")
    
    t0 = time.time()
    chunks = []
    # Load in chunks and filter
    email_path = os.path.join(cert_dir, 'email.csv')
    if os.path.exists(email_path):
        for chunk in pd.read_csv(email_path, chunksize=100000):
            filtered = chunk[chunk['user'].isin(cohort_users)].copy()
            chunks.append(filtered)
        emails_cert = pd.concat(chunks).reset_index(drop=True)
    else:
        emails_cert = pd.DataFrame()
        
    t_ingest_email = time.time() - t0
    print(f"  - Ingest & Filter time: {t_ingest_email:.4f}s (Loaded {len(emails_cert)} records for cohort)")
    
    if not emails_cert.empty:
        # Standardize dates for emails
        emails_cert['date'] = pd.to_datetime(emails_cert['date'], format='mixed', errors='coerce')
        emails_cert = emails_cert.dropna(subset=['date']).sort_values('date')
        emails_cert = cert_loader.extract_time_windows(emails_cert, window_size_days=7, min_date=logon_min_date)
        
        # Execute new communication extractor
        print("  Running optimized Communication feature extractor...")
        t0 = time.time()
        comm_cert = extract_communication_new(emails_cert)
        t_comm_cert = time.time() - t0
        mem_comm = get_memory_usage_mb()
        
        # Execute interaction graph extractor
        print("  Running optimized Interaction feature extractor...")
        t0 = time.time()
        int_cert = extract_interaction_new(emails_cert)
        t_int_cert = time.time() - t0
        mem_int = get_memory_usage_mb()
        
        # Merge all extracted features
        # Filter act_cert to cohort_users to match
        act_cert_cohort = act_cert[act_cert['user'].isin(cohort_users)].copy()
        merged_cert = pd.merge(act_cert_cohort, comm_cert, on=['user', 'time_window'], how='outer')
        merged_cert = pd.merge(merged_cert, int_cert, on=['user', 'time_window'], how='outer').fillna(0.0)
        
        print("\n---------------- PHASE 8 RESULTS ----------------")
        print(f"Feature Matrix Dimensions:      {merged_cert.shape}")
        print(f"Total Unique Users Extracted:   {merged_cert['user'].nunique()}")
        print(f"Total User-Weeks Extracted:     {len(merged_cert)}")
        print(f"Runtime (Activity Extraction):  {t_act_cert:.4f} seconds")
        print(f"Runtime (Communication Extr.):  {t_comm_cert:.4f} seconds")
        print(f"Runtime (Interaction Extr.):    {t_int_cert:.4f} seconds")
        print(f"Peak RAM Usage:                 {mem_int} (Baseline: {base_mem})")
        print("-------------------------------------------------\n")
    else:
        print("  No email records found for cohort.")
    
    print("Status: Phase 8 Vectorized Calibration successfully validated!")
    print("==================================================")

if __name__ == '__main__':
    main()
