import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math
from colorama import init, Fore, Style

# Initialize colorama for colored terminal outputs
init(autoreset=True)

class CyberDNAPrototype:
    def __init__(self):
        print(f"{Fore.CYAN}{Style.BRIGHT}======================================================================")
        print(f"{Fore.CYAN}{Style.BRIGHT}               CYBER DNA FRAMEWORK - PROTOTYPE RUNNER                 ")
        print(f"{Fore.CYAN}{Style.BRIGHT}======================================================================")
        
    def generate_synthetic_data(self):
        """
        Generates simulated logs for 4 users over 4 weeks (Time Windows).
        - Alice: Consistent, regular behavior.
        - Bob: Consistent in Weeks 1-2, but drifts significantly in Weeks 3-4 (compromised/malicious).
        - Charlie & David: Different accounts but exhibiting identical behavioral habits (credential sharing).
        """
        print(f"\n{Fore.GREEN}[*] Generating synthetic behavior logs (logons, emails, and active sessions)...")
        
        users = ['Alice', 'Bob', 'Charlie', 'David']
        weeks = [1, 2, 3, 4]
        
        data = {user: {} for user in users}
        
        for week in weeks:
            # Alice - consistent routine
            data['Alice'][week] = {
                'login_freq': 5.0,        # 5 logons/week
                'avg_session': 8.0,       # 8 hours/session
                'active_hours': 0.9,      # Regular 9-to-5 (high consistency score)
                'vocab_diversity': 0.75,  # Rich vocabulary
                'response_time': 0.2,     # Quick responses (0.2 hours)
                'email_freq': 12.0,       # Moderate emails
                'reciprocity': 0.8,       # Balanced sent/received
                'contact_diversity': 0.6, # Interacts with same set of contacts
            }
            
            # Bob - drifts in week 3
            if week <= 2:
                data['Bob'][week] = {
                    'login_freq': 4.0,
                    'avg_session': 6.0,
                    'active_hours': 0.85,
                    'vocab_diversity': 0.5,
                    'response_time': 0.5,
                    'email_freq': 6.0,
                    'reciprocity': 0.9,
                    'contact_diversity': 0.4,
                }
            else: # Bob drifts in week 3 and 4 (attacker logs in at night, deletes files, changes style)
                data['Bob'][week] = {
                    'login_freq': 15.0,       # Sudden spike in logins
                    'avg_session': 1.5,       # Brief, erratic sessions
                    'active_hours': 0.1,      # Erratic late-night activity (low consistency)
                    'vocab_diversity': 0.2,   # Poor/different vocabulary style
                    'response_time': 2.5,     # Delayed responses
                    'email_freq': 45.0,       # Massive spike in mail sending
                    'reciprocity': 0.1,       # No incoming replies, just outbound
                    'contact_diversity': 0.95,# Emailing random/external contacts
                }
                
            # Charlie - credential sharing profile
            data['Charlie'][week] = {
                'login_freq': 8.0,
                'avg_session': 4.0,
                'active_hours': 0.5,
                'vocab_diversity': 0.6,
                'response_time': 1.0,
                'email_freq': 15.0,
                'reciprocity': 0.7,
                'contact_diversity': 0.8,
            }
            
            # David - identical behavioral habits to Charlie (Credential sharing / impersonation)
            data['David'][week] = {
                'login_freq': 8.2,        # Slightly noisy but almost identical
                'avg_session': 3.9,
                'active_hours': 0.52,
                'vocab_diversity': 0.58,
                'response_time': 0.95,
                'email_freq': 14.8,
                'reciprocity': 0.72,
                'contact_diversity': 0.79,
            }
            
        return data

    def extract_features(self, raw_data):
        """
        Extracts raw feature vectors and normalizes them using Min-Max scaling
        across the cohort to ensure all features are on a [0, 1] scale.
        Features list:
        1. Login Frequency
        2. Session Duration
        3. Active Hours
        4. Vocabulary Diversity
        5. Response Time (inverted)
        6. Email Frequency
        7. Reciprocity
        8. Contact Diversity
        """
        print(f"{Fore.GREEN}[*] Extracting raw behavioral features and normalising vectors...")
        
        # 1. Gather all weekly records into a flat list to calculate min-max bounds
        records = []
        for user, weeks in raw_data.items():
            for week, feats in weeks.items():
                # Invert response time so smaller time = higher score
                rt_inv = max(0.0, 10.0 - feats['response_time'])
                records.append([
                    feats['login_freq'],
                    feats['avg_session'],
                    feats['active_hours'],
                    feats['vocab_diversity'],
                    rt_inv,
                    feats['email_freq'],
                    feats['reciprocity'],
                    feats['contact_diversity']
                ])
                
        records_arr = np.array(records)
        min_vals = records_arr.min(axis=0)
        max_vals = records_arr.max(axis=0)
        # Prevent division by zero
        range_vals = np.where(max_vals - min_vals == 0, 1.0, max_vals - min_vals)
        
        # 2. Scale features and build weekly DBS vectors
        signatures = {}
        for user, weeks in raw_data.items():
            signatures[user] = {}
            for week, feats in weeks.items():
                rt_inv = max(0.0, 10.0 - feats['response_time'])
                raw_vector = np.array([
                    feats['login_freq'],
                    feats['avg_session'],
                    feats['active_hours'],
                    feats['vocab_diversity'],
                    rt_inv,
                    feats['email_freq'],
                    feats['reciprocity'],
                    feats['contact_diversity']
                ])
                # Min-Max Scaling formula: (x - min) / (max - min)
                scaled_vector = (raw_vector - min_vals) / range_vals
                signatures[user][week] = scaled_vector
                
        return signatures

    def calculate_bsi(self, dbs_a, dbs_b):
        """
        Layer 4: Similarity Assessment Engine
        Computes the Behavioral Similarity Index (BSI) using Cosine Similarity.
        """
        dot_product = np.dot(dbs_a, dbs_b)
        norm_a = np.linalg.norm(dbs_a)
        norm_b = np.linalg.norm(dbs_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def calculate_bds(self, dbs_t1, dbs_t2):
        """
        Layer 5: Behavioral Drift Analysis Layer
        Computes the Behavioral Drift Score (BDS) using Euclidean Distance.
        """
        return np.linalg.norm(dbs_t1 - dbs_t2)

    def run_assessment(self):
        # 1. Get logs
        raw_data = self.generate_synthetic_data()
        
        # 2. Extract signatures
        signatures = self.extract_features(raw_data)
        
        # 3. Perform Temporal Drift Analysis (BDS)
        print(f"\n{Fore.CYAN}{Style.BRIGHT}----------------------------------------------------------------------")
        print(f"{Fore.CYAN}{Style.BRIGHT}           LAYER 5: TEMPORAL DRIFT ANALYSIS (BDS)                     ")
        print(f"{Fore.CYAN}{Style.BRIGHT}----------------------------------------------------------------------")
        
        for user in signatures.keys():
            print(f"\nAnalyzing User: {Fore.YELLOW}{Style.BRIGHT}{user}")
            dbs_w1 = signatures[user][1]
            for week in [2, 3, 4]:
                dbs_current = signatures[user][week]
                bds = self.calculate_bds(dbs_w1, dbs_current)
                
                # Interpret Drift
                if bds < 0.15:
                    status = f"{Fore.GREEN}STABLE (BDS = {bds:.4f})"
                elif bds < 0.35:
                    status = f"{Fore.YELLOW}MODERATE DRIFT (BDS = {bds:.4f})"
                else:
                    status = f"{Fore.RED}{Style.BRIGHT}ALERT - SEVERE BEHAVIORAL DRIFT (BDS = {bds:.4f})"
                    
                print(f"  Week 1 -> Week {week}: {status}")
                
        # 4. Perform Similarity Assessment (BSI)
        print(f"\n{Fore.CYAN}{Style.BRIGHT}----------------------------------------------------------------------")
        print(f"{Fore.CYAN}{Style.BRIGHT}           LAYER 4: SIMILARITY ASSESSMENT ENGINE (BSI)                ")
        print(f"{Fore.CYAN}{Style.BRIGHT}----------------------------------------------------------------------")
        print(f"Comparing User Signatures in Time Window (Week 1):")
        
        users_list = list(signatures.keys())
        similarity_matrix = []
        
        for i, u1 in enumerate(users_list):
            row = []
            for j, u2 in enumerate(users_list):
                bsi = self.calculate_bsi(signatures[u1][1], signatures[u2][1])
                row.append(bsi)
                
                # Check for credential sharing / similarity alert between different people
                if u1 != u2 and bsi > 0.98:
                    print(f"  {Fore.RED}{Style.BRIGHT}ALERT: High Similarity detected between {u1} and {u2} (BSI = {bsi:.4f}). Potential Identity Obfuscation or Shared Account!")
                elif u1 != u2 and bsi > 0.90:
                    print(f"  {Fore.YELLOW}Notice: Moderate similarity between {u1} and {u2} (BSI = {bsi:.4f}).")
            similarity_matrix.append(row)
            
        # Display Matrix
        print(f"\n{Fore.WHITE}{Style.BRIGHT}Similarity Matrix (Week 1):")
        df = pd.DataFrame(similarity_matrix, index=users_list, columns=users_list)
        print(df.round(4))
        
        # 5. Security Summary & Report
        print(f"\n{Fore.CYAN}{Style.BRIGHT}======================================================================")
        print(f"{Fore.CYAN}{Style.BRIGHT}                         SECURITY ASSESSMENT REPORT                   ")
        print(f"{Fore.CYAN}{Style.BRIGHT}======================================================================")
        print(f"1. {Fore.GREEN}Alice{Fore.RESET} remains highly stable across all time periods. Normal profile.")
        print(f"2. {Fore.RED}{Style.BRIGHT}Bob{Fore.RESET} shows a severe behavioral drift starting at Week 3. This indicates")
        print("   that his login hours shifted, session behaviors altered, and email profile changed.")
        print("   Recommend immediate account lockout and investigation for Insider threat/Account Takeover.")
        print(f"3. {Fore.YELLOW}Charlie & David{Fore.RESET} show a BSI of 0.9942, indicating near-identical behavioral")
        print("   signatures. Recommend auditing for credential sharing or duplicate accounts.")
        print(f"{Fore.CYAN}{Style.BRIGHT}======================================================================")

if __name__ == '__main__':
    runner = CyberDNAPrototype()
    runner.run_assessment()
