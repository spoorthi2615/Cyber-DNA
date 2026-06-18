import pandas as pd
import numpy as np

class SignatureBuilder:
    def __init__(self, raw_features_df):
        self.raw_df = raw_features_df.copy()
        self.feature_cols = [
            'login_freq', 'active_hours', 'avg_session', 
            'email_freq', 'vocab_diversity', 'response_time', 
            'contact_diversity', 'reciprocity'
        ]
        
    def normalize_features(self):
        """
        Applies absolute domain-specific normalization to the behavioral features.
        This prevents feature-range inflation on small datasets or quiet cohorts.
        """
        df = self.raw_df.copy()
        
        # 1. Invert response_time (shorter response time = higher communication score)
        df['response_time'] = df['response_time'].apply(lambda x: max(0.0, 24.0 - x))
        
        # Define absolute bounds: { feature_name: (min_val, max_val) }
        bounds = {
            'login_freq': (0.0, 30.0),       # Up to 30 logins per week
            'active_hours': (0.0, 1.0),      # Business hours ratio (0.0 to 1.0)
            'avg_session': (0.0, 24.0),      # Average session duration (0 to 24 hours)
            'email_freq': (0.0, 100.0),      # Up to 100 emails sent per week
            'vocab_diversity': (0.0, 1.0),   # Lexical diversity ratio (0.0 to 1.0)
            'response_time': (0.0, 24.0),    # Inverted reply lag (0 to 24 hours)
            'contact_diversity': (0.0, 50.0), # Up to 50 contacts
            'reciprocity': (0.0, 2.0)        # Reciprocity ratio (0.0 to 2.0)
        }
        
        # Apply scaling: (x - min) / (max - min) capped between 0 and 1
        for col in self.feature_cols:
            col_min, col_max = bounds[col]
            df[col] = (df[col] - col_min) / (col_max - col_min)
            df[col] = df[col].clip(0.0, 1.0)
                
        return df

    def build_signatures(self):
        """
        Assembles weekly Digital Behavioral Signatures (DBS) for all users.
        Also calculates composite scores (BCS, CSS, IPS, IDPS) for reporting.
        Returns a dictionary mapping: user -> { week -> dbs_vector }
        and a DataFrame with composite scores.
        """
        normalized_df = self.normalize_features()
        signatures = {}
        composite_records = []
        
        for idx, row in normalized_df.iterrows():
            user = row['user']
            week = int(row['time_window'])
            
            # Extract normalized feature vector
            vector = np.array([
                row['login_freq'],
                row['active_hours'],
                row['avg_session'],
                row['email_freq'],
                row['vocab_diversity'],
                row['response_time'],
                row['contact_diversity'],
                row['reciprocity']
            ])
            
            if user not in signatures:
                signatures[user] = {}
            signatures[user][week] = vector
            
            # Calculate Composite Scores (as defined in Cyber DNA math framework)
            # BCS = (login_freq + avg_session + active_hours + baseline_regularity(0.8)) / 4
            bcs = (row['login_freq'] + row['avg_session'] + row['active_hours'] + 0.8) / 4.0
            
            # CSS = (vocab_diversity + response_time + email_freq + baseline_writing(0.75)) / 4
            css = (row['vocab_diversity'] + row['response_time'] + row['email_freq'] + 0.75) / 4.0
            
            # IPS = (contact_diversity + reciprocity + baseline_stability(0.8) + baseline_persistence(0.7)) / 4
            ips = (row['contact_diversity'] + row['reciprocity'] + 0.8 + 0.7) / 4.0
            
            # IDPS = (anthropological baseline defaults)
            idps = (0.85 + 0.8 + 0.75 + 0.8) / 4.0
            
            composite_records.append({
                'user': user,
                'time_window': week,
                'BCS': bcs,
                'CSS': css,
                'IPS': ips,
                'IDPS': idps
            })
            
        composite_df = pd.DataFrame(composite_records)
        anthro_df = self.calculate_anthropology_scores(signatures, composite_df)
        return signatures, composite_df, anthro_df

    def calculate_anthropology_scores(self, signatures, composite_df):
        """
        Calculates the static anthropological metrics:
        - IDP: Identity Persistence (exponential decay of average BDS)
        - BC: Behavioral Continuity (exponential decay of BDS variance/std)
        - SRC: Social Role Consistency (stability of IPS over time)
        """
        records = []
        for user, weeks in signatures.items():
            sorted_weeks = sorted(list(weeks.keys()))
            W = len(sorted_weeks)
            
            bds_list = []
            ips_diffs = []
            
            for idx in range(W - 1):
                w1 = sorted_weeks[idx]
                w2 = sorted_weeks[idx + 1]
                
                # BDS
                bds = np.linalg.norm(weeks[w1] - weeks[w2])
                bds_list.append(bds)
                
                # IPS difference
                row_w1 = composite_df[(composite_df['user'] == user) & (composite_df['time_window'] == w1)]
                row_w2 = composite_df[(composite_df['user'] == user) & (composite_df['time_window'] == w2)]
                
                if not row_w1.empty and not row_w2.empty:
                    ips_w1 = row_w1['IPS'].values[0]
                    ips_w2 = row_w2['IPS'].values[0]
                    ips_diffs.append(abs(ips_w1 - ips_w2))
                else:
                    ips_diffs.append(0.0)
                    
            # 1. Identity Persistence (IDP)
            if W > 1 and len(bds_list) > 0:
                idp = np.exp(-np.mean(bds_list))
            else:
                idp = 1.0
                
            # 2. Behavioral Continuity (BC)
            if W > 2 and len(bds_list) > 1:
                bc = np.exp(-np.std(bds_list))
            else:
                bc = 1.0
                
            # 3. Social Role Consistency (SRC)
            if W > 1 and len(ips_diffs) > 0:
                src = 1.0 - np.mean(ips_diffs)
            else:
                src = 1.0
                
            records.append({
                'user': user,
                'IDP': float(idp),
                'BC': float(bc),
                'SRC': float(src)
            })
            
        return pd.DataFrame(records)
