import pandas as pd
import numpy as np
import os

class CERTDataLoader:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        
    def load_csv(self, filename, expected_cols):
        """
        Generic helper to load a CSV log file with date parsing and column checking.
        """
        file_path = os.path.join(self.data_dir, filename)
        if not os.path.exists(file_path):
            print(f"Warning: File {filename} not found at {file_path}. Data loader returning empty DataFrame.")
            return pd.DataFrame(columns=expected_cols)
            
        print(f"Ingesting file: {filename}...")
        try:
            # Parse dates dynamically with format='mixed' to handle format variations
            df = pd.read_csv(file_path)
            
            # Check expected columns
            for col in expected_cols:
                if col not in df.columns:
                    raise ValueError(f"Missing expected column '{col}' in {filename}")
                    
            # Standardize dates
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], format='mixed', errors='coerce')
                df = df.dropna(subset=['date']).sort_values('date')
                
            return df
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return pd.DataFrame(columns=expected_cols)

    def load_logon_logs(self, filename="logon.csv"):
        """
        Loads logon logs containing user logins and logoffs.
        Schema: id, date, user, pc, activity (Logon/Logoff)
        """
        expected_cols = ['id', 'date', 'user', 'pc', 'activity']
        df = self.load_csv(filename, expected_cols)
        return df

    def load_email_logs(self, filename="email.csv"):
        """
        Loads email communication logs.
        Schema: id, date, user, pc, to, cc, bcc, from, size, attachments (or attachment), content
        """
        file_path = os.path.join(self.data_dir, filename)
        if not os.path.exists(file_path):
            print(f"Warning: File {filename} not found. Returning empty DataFrame.")
            return pd.DataFrame()
            
        print(f"Ingesting file: {filename}...")
        df = pd.read_csv(file_path)
        
        if 'attachments' in df.columns:
            df.rename(columns={'attachments': 'attachment'}, inplace=True)
            
        expected_cols = ['id', 'date', 'user', 'pc', 'to', 'cc', 'bcc', 'from', 'size', 'attachment', 'content']
        for col in expected_cols:
            if col not in df.columns:
                raise ValueError(f"Missing expected column '{col}' in {filename}")
                
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], format='mixed', errors='coerce')
            df = df.dropna(subset=['date']).sort_values('date')
            
        return df

    def load_device_logs(self, filename="device.csv"):
        """
        Loads device connection logs (USB connect/disconnect).
        Schema: id, date, user, pc, activity (Connect/Disconnect)
        """
        expected_cols = ['id', 'date', 'user', 'pc', 'activity']
        df = self.load_csv(filename, expected_cols)
        return df

    def load_ldap_records(self, filename="ldap.csv"):
        """
        Loads LDAP employee directories.
        Schema: employee_name, user_id, email, role, department (or business_unit)
        Returns a DataFrame mapping user to department.
        """
        expected_cols = ['employee_name', 'user_id', 'email', 'role', 'department']
        file_path = os.path.join(self.data_dir, filename)
        
        # If ldap.csv doesn't exist, try loading LDAP/YYYY-MM.csv snapshots
        if not os.path.exists(file_path):
            ldap_dir = os.path.join(self.data_dir, "LDAP")
            if os.path.exists(ldap_dir):
                files = [f for f in os.listdir(ldap_dir) if f.endswith('.csv')]
                if files:
                    dfs = []
                    for f in sorted(files):
                        p = os.path.join(ldap_dir, f)
                        df_part = self.load_csv(os.path.relpath(p, self.data_dir), expected_cols)
                        if not df_part.empty:
                            dfs.append(df_part)
                    df = pd.concat(dfs).drop_duplicates(subset=['user_id']) if dfs else pd.DataFrame(columns=expected_cols)
                else:
                    df = pd.DataFrame(columns=expected_cols)
            else:
                # Fallback to business_unit column in case of schema variations
                expected_cols = ['employee_name', 'user_id', 'email', 'role', 'business_unit']
                df = self.load_csv(filename, expected_cols)
        else:
            df = self.load_csv(filename, expected_cols)
            
        if not df.empty:
            # Rename columns to standard keys
            if 'department' not in df.columns and 'business_unit' in df.columns:
                df.rename(columns={'business_unit': 'department'}, inplace=True)
            df.rename(columns={'user_id': 'user'}, inplace=True)
            df['user'] = df['user'].str.strip()
            df['department'] = df['department'].str.strip()
            
        return df[['user', 'department']] if not df.empty else pd.DataFrame(columns=['user', 'department'])

    def load_insider_labels(self, filename="../answers/insiders.csv"):
        """
        Loads ground truth threat records from insiders.csv.
        Filters for dataset 4.2.
        Returns a DataFrame with columns: user, start, end, scenario
        """
        # Attempt to find the file in multiple likely locations
        file_path = os.path.join(self.data_dir, filename)
        if not os.path.exists(file_path):
            file_path = os.path.abspath(os.path.join(self.data_dir, "..", "answers", "insiders.csv"))
            if not os.path.exists(file_path):
                file_path = os.path.abspath("data/cert_r4.2/answers/insiders.csv")
                
        if not os.path.exists(file_path):
            print(f"Warning: Ground truth file {filename} not found. Returning empty DataFrame.")
            return pd.DataFrame(columns=['user', 'start', 'end', 'scenario'])
            
        print(f"Ingesting ground truth labels from: {file_path}...")
        try:
            df = pd.read_csv(file_path)
            df['dataset_str'] = df['dataset'].astype(str).str.strip()
            df_42 = df[df['dataset_str'] == '4.2'].copy()
            
            # Parse start and end timestamps
            df_42['start'] = pd.to_datetime(df_42['start'], format='mixed', errors='coerce')
            df_42['end'] = pd.to_datetime(df_42['end'], format='mixed', errors='coerce')
            
            return df_42[['user', 'start', 'end', 'scenario']]
        except Exception as e:
            print(f"Error loading insiders.csv: {e}")
            return pd.DataFrame(columns=['user', 'start', 'end', 'scenario'])

    def extract_time_windows(self, df, window_size_days=7, min_date=None):
        """
        Slices log dataframes into rolling time windows (e.g., 7 days)
        to enable chronological drift analysis.
        Adds a 'time_window' column denoting the period index.
        """
        if df.empty or 'date' not in df.columns:
            df['time_window'] = 0
            return df
            
        if min_date is None:
            min_date = df['date'].min()
            
        df['time_window'] = df['date'].apply(
            lambda x: int((x - min_date).days / window_size_days) + 1
        )
        return df

    def generate_user_weeks_labels(self, active_user_weeks, insiders_df, min_date, window_size_days=7):
        """
        active_user_weeks: DataFrame containing at least ['user', 'time_window']
        insiders_df: DataFrame containing ['user', 'start', 'end', 'scenario']
        min_date: The dataset global reference start date (datetime object)
        Returns:
        DataFrame with ['user', 'time_window', 'label', 'scenario']
        """
        active_user_weeks = active_user_weeks.copy()
        
        # Create a dictionary of threat periods for fast lookup: user -> list of (start, end, scenario)
        threat_dict = {}
        for idx, row in insiders_df.iterrows():
            u = str(row['user']).strip().upper()
            if u not in threat_dict:
                threat_dict[u] = []
            threat_dict[u].append((row['start'], row['end'], row['scenario']))
            
        labels = []
        scenarios = []
        
        for idx, row in active_user_weeks.iterrows():
            user = str(row['user']).strip().upper()
            w = int(row['time_window'])
            
            # Calculate the time interval of this week window
            t_start_w = min_date + pd.Timedelta(days=(w - 1) * window_size_days)
            t_end_w = min_date + pd.Timedelta(days=w * window_size_days)
            
            is_malicious = 0
            matching_scenario = 0
            
            if user in threat_dict:
                for start_t, end_t, scen in threat_dict[user]:
                    # Check if the active threat period overlaps with this week window
                    if start_t <= t_end_w and end_t >= t_start_w:
                        is_malicious = 1
                        matching_scenario = int(scen)
                        break
                        
            labels.append(is_malicious)
            scenarios.append(matching_scenario)
            
        active_user_weeks['label'] = labels
        active_user_weeks['scenario'] = scenarios
        return active_user_weeks

    def partition_train_test(self, user_weeks_df, split_week=52):
        """
        Partitions user_weeks_df into train and test splits chronologically.
        train: time_window <= split_week
        test: time_window > split_week
        """
        train_df = user_weeks_df[user_weeks_df['time_window'] <= split_week].copy()
        test_df = user_weeks_df[user_weeks_df['time_window'] > split_week].copy()
        return train_df, test_df
