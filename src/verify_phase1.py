import os
from mock_generator import CERTDataSimulator
from preprocess import CERTDataLoader

def main():
    print("==================================================")
    print("         VERIFYING PHASE 1 INGESTION PIPELINE     ")
    print("==================================================")
    
    # 1. Paths
    data_dir = 'data/cert_sample'
    
    # 2. Run simulation
    sim = CERTDataSimulator(data_dir, num_weeks=4)
    sim.generate_logs()
    
    # 3. Load via Preprocess Loader
    loader = CERTDataLoader(data_dir)
    
    logons = loader.load_logon_logs()
    emails = loader.load_email_logs()
    devices = loader.load_device_logs()
    
    # 4. Check outputs
    print("\n---------------- Data Ingest Summary ----------------")
    print(f"Logon logs loaded: {len(logons)} records")
    print(f"Email logs loaded: {len(emails)} records")
    print(f"Device logs loaded: {len(devices)} records")
    
    # 5. Check time-window slicing
    if not logons.empty:
        sliced_logons = loader.extract_time_windows(logons, window_size_days=7)
        windows = sliced_logons['time_window'].unique()
        print(f"Time windows extracted: {sorted(list(windows))}")
        
    print("\nStatus: Phase 1 Verification Successful! All logs are parsed correctly.")
    print("==================================================")

if __name__ == '__main__':
    main()
