import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

class CERTDataSimulator:
    def __init__(self, output_dir, num_weeks=4):
        self.output_dir = output_dir
        self.num_weeks = num_weeks
        self.users = ['Alice', 'Bob', 'Charlie', 'David', 'Eve']
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_logs(self):
        """
        Generates simulated logon, email, and device connect logs mimicking CERT schema.
        - Alice: High regularity, office hours (9am-5pm), stable email patterns. (Engineering)
        - Bob: Normal office hours in Week 1-2. In Week 3-4, he exhibits late night logons (2am),
               mass emailing to external recipients, and excessive USB device insertions (copying data). (Engineering)
        - Charlie & David: Share near-identical habits (session intervals, vocabulary) to simulate shared credentials. (Sales)
        - Eve: HR in Weeks 1-2 (9am-5pm logons, onboarding emails). In Weeks 3-4, she transitions to Sales
               (8:30am-4:30pm logons, invoicing emails) to simulate a legitimate departmental role transition. (HR)
        """
        print(f"Generating synthetic logs in: {self.output_dir}...")
        
        start_date = datetime(2026, 6, 1, 8, 0, 0)
        
        logon_records = []
        email_records = []
        device_records = []
        
        logon_id = 1
        email_id = 1
        device_id = 1
        
        for week in range(self.num_weeks):
            week_start = start_date + timedelta(weeks=week)
            
            for day in range(5):  # Monday to Friday
                current_day = week_start + timedelta(days=day)
                
                # --- Generate Alice's Daily Logs (Consistent 9-5) ---
                logon_time = current_day.replace(hour=9, minute=0, second=np.random.randint(0, 59))
                logoff_time = current_day.replace(hour=17, minute=0, second=np.random.randint(0, 59))
                
                logon_records.append([f"L-{logon_id}", logon_time.strftime('%m/%d/%Y %H:%M:%S'), 'Alice', 'PC-1001', 'Logon'])
                logon_id += 1
                logon_records.append([f"L-{logon_id}", logoff_time.strftime('%m/%d/%Y %H:%M:%S'), 'Alice', 'PC-1001', 'Logoff'])
                logon_id += 1
                
                # Alice's emails during the day
                for h in [10, 14]:
                    email_time = current_day.replace(hour=h, minute=np.random.randint(0, 59))
                    email_records.append([
                        f"E-{email_id}", email_time.strftime('%m/%d/%Y %H:%M:%S'), 'Alice', 'PC-1001',
                        'manager@company.com', 'team@company.com', '', 'Alice', 15000, 'none',
                        "Dear team, here is the weekly project status report. Let me know if you have any feedback."
                    ])
                    email_id += 1

                # --- Generate Bob's Daily Logs ---
                if week < 2:  # Bob is normal in weeks 1 and 2
                    b_logon = current_day.replace(hour=9, minute=30, second=np.random.randint(0, 59))
                    b_logoff = current_day.replace(hour=17, minute=30, second=np.random.randint(0, 59))
                    
                    logon_records.append([f"L-{logon_id}", b_logon.strftime('%m/%d/%Y %H:%M:%S'), 'Bob', 'PC-2002', 'Logon'])
                    logon_id += 1
                    logon_records.append([f"L-{logon_id}", b_logoff.strftime('%m/%d/%Y %H:%M:%S'), 'Bob', 'PC-2002', 'Logoff'])
                    logon_id += 1
                    
                    # Bob's normal emails
                    email_time = current_day.replace(hour=11, minute=np.random.randint(0, 59))
                    email_records.append([
                        f"E-{email_id}", email_time.strftime('%m/%d/%Y %H:%M:%S'), 'Bob', 'PC-2002',
                        'developer@company.com', '', '', 'Bob', 5000, 'none',
                        "Let's catch up later to review the latest code changes and check the server configurations."
                    ])
                    email_id += 1
                else:  # Bob drifts significantly in weeks 3 and 4
                    # Late night malicious logon
                    b_logon_night = current_day.replace(hour=2, minute=15, second=np.random.randint(0, 59))
                    b_logoff_night = current_day.replace(hour=3, minute=45, second=np.random.randint(0, 59))
                    
                    logon_records.append([f"L-{logon_id}", b_logon_night.strftime('%m/%d/%Y %H:%M:%S'), 'Bob', 'PC-2002', 'Logon'])
                    logon_id += 1
                    logon_records.append([f"L-{logon_id}", b_logoff_night.strftime('%m/%d/%Y %H:%M:%S'), 'Bob', 'PC-2002', 'Logoff'])
                    logon_id += 1
                    
                    # Malicious email sending
                    for offset in range(3):
                        email_time = b_logon_night + timedelta(minutes=15 * offset)
                        email_records.append([
                            f"E-{email_id}", email_time.strftime('%m/%d/%Y %H:%M:%S'), 'Bob', 'PC-2002',
                            'hacker@external.net', 'partner@competitor.com', '', 'Bob', 8500000, 'sensitive_archive.zip',
                            "Exfiltrating data now. Check the attachment."
                        ])
                        email_id += 1
                        
                    # USB Device connection (copying files)
                    dev_time = b_logon_night + timedelta(minutes=5)
                    device_records.append([f"D-{device_id}", dev_time.strftime('%m/%d/%Y %H:%M:%S'), 'Bob', 'PC-2002', 'Connect'])
                    device_id += 1
                    dev_time_disc = b_logon_night + timedelta(minutes=55)
                    device_records.append([f"D-{device_id}", dev_time_disc.strftime('%m/%d/%Y %H:%M:%S'), 'Bob', 'PC-2002', 'Disconnect'])
                    device_id += 1

                # --- Generate Charlie & David Daily Logs (Credential Sharing Simulation - Sales) ---
                # Identical logon profiles, same time distributions
                c_logon = current_day.replace(hour=8, minute=30, second=np.random.randint(0, 59))
                c_logoff = current_day.replace(hour=16, minute=30, second=np.random.randint(0, 59))
                
                logon_records.append([f"L-{logon_id}", c_logon.strftime('%m/%d/%Y %H:%M:%S'), 'Charlie', 'PC-3003', 'Logon'])
                logon_id += 1
                logon_records.append([f"L-{logon_id}", c_logoff.strftime('%m/%d/%Y %H:%M:%S'), 'Charlie', 'PC-3003', 'Logoff'])
                logon_id += 1
                
                d_logon = c_logon + timedelta(minutes=np.random.randint(-5, 5))
                d_logoff = c_logoff + timedelta(minutes=np.random.randint(-5, 5))
                
                logon_records.append([f"L-{logon_id}", d_logon.strftime('%m/%d/%Y %H:%M:%S'), 'David', 'PC-4004', 'Logon'])
                logon_id += 1
                logon_records.append([f"L-{logon_id}", d_logoff.strftime('%m/%d/%Y %H:%M:%S'), 'David', 'PC-4004', 'Logoff'])
                logon_id += 1

                # Emails (near identical patterns)
                email_time_c = current_day.replace(hour=13, minute=15)
                email_records.append([
                    f"E-{email_id}", email_time_c.strftime('%m/%d/%Y %H:%M:%S'), 'Charlie', 'PC-3003',
                    'client@external.com', '', '', 'Charlie', 12000, 'invoice.pdf',
                    "Hello, please find the invoice for this month's services attached. Thank you."
                ])
                email_id += 1
                
                email_time_d = email_time_c + timedelta(minutes=np.random.randint(-3, 3))
                email_records.append([
                    f"E-{email_id}", email_time_d.strftime('%m/%d/%Y %H:%M:%S'), 'David', 'PC-4004',
                    'client@external.com', '', '', 'David', 11800, 'invoice_draft.pdf',
                    "Hello, please find the invoice for this month's services attached. Thank you."
                ])
                email_id += 1

                # --- Generate Eve's Daily Logs (Role Transition Simulation: HR -> Sales) ---
                if week < 2:  # HR
                    # 4 logins per day (20 logins per week)
                    for h_idx, (h_on, h_off) in enumerate([(9, 10), (11, 12), (13, 14), (15, 16)]):
                        e_logon = current_day.replace(hour=h_on, minute=0, second=np.random.randint(0, 59))
                        e_logoff = current_day.replace(hour=h_off, minute=0, second=np.random.randint(0, 59))
                        logon_records.append([f"L-{logon_id}", e_logon.strftime('%m/%d/%Y %H:%M:%S'), 'Eve', 'PC-5005', 'Logon'])
                        logon_id += 1
                        logon_records.append([f"L-{logon_id}", e_logoff.strftime('%m/%d/%Y %H:%M:%S'), 'Eve', 'PC-5005', 'Logoff'])
                        logon_id += 1
                    
                    # 8 onboarding emails per day (40 emails per week)
                    for e_idx in range(8):
                        email_time_e = current_day.replace(hour=10, minute=5 * e_idx)
                        recipient = f"employee_{week}_{day}_{e_idx}@company.com"
                        email_records.append([
                            f"E-{email_id}", email_time_e.strftime('%m/%d/%Y %H:%M:%S'), 'Eve', 'PC-5005',
                            recipient, '', '', 'Eve', 14000, 'onboarding.pdf',
                            "Welcome to the company, please review the onboarding documents."
                        ])
                        email_id += 1
                else:  # Sales
                    e_logon = current_day.replace(hour=8, minute=30, second=np.random.randint(0, 59))
                    e_logoff = current_day.replace(hour=16, minute=30, second=np.random.randint(0, 59))
                    logon_records.append([f"L-{logon_id}", e_logon.strftime('%m/%d/%Y %H:%M:%S'), 'Eve', 'PC-5005', 'Logon'])
                    logon_id += 1
                    logon_records.append([f"L-{logon_id}", e_logoff.strftime('%m/%d/%Y %H:%M:%S'), 'Eve', 'PC-5005', 'Logoff'])
                    logon_id += 1
                    
                    # Sales invoice email
                    email_time_e = current_day.replace(hour=13, minute=15)
                    email_records.append([
                        f"E-{email_id}", email_time_e.strftime('%m/%d/%Y %H:%M:%S'), 'Eve', 'PC-5005',
                        'client@external.com', '', '', 'Eve', 12100, 'invoice.pdf',
                        "Hello, please find the invoice for this month's services attached. Thank you."
                    ])
                    email_id += 1

        # Save logs to CSV
        pd.DataFrame(logon_records, columns=['id', 'date', 'user', 'pc', 'activity']).to_csv(
            os.path.join(self.output_dir, 'logon.csv'), index=False
        )
        pd.DataFrame(email_records, columns=['id', 'date', 'user', 'pc', 'to', 'cc', 'bcc', 'from', 'size', 'attachment', 'content']).to_csv(
            os.path.join(self.output_dir, 'email.csv'), index=False
        )
        pd.DataFrame(device_records, columns=['id', 'date', 'user', 'pc', 'activity']).to_csv(
            os.path.join(self.output_dir, 'device.csv'), index=False
        )
        
        # Save LDAP directory
        ldap_records = [
            ['Alice Smith', 'Alice', 'alice@company.com', 'Engineer', 'Engineering'],
            ['Bob Jones', 'Bob', 'bob@company.com', 'Engineer', 'Engineering'],
            ['Charlie Brown', 'Charlie', 'charlie@company.com', 'Sales Rep', 'Sales'],
            ['David Miller', 'David', 'david@company.com', 'Sales Rep', 'Sales'],
            ['Eve Davis', 'Eve', 'eve@company.com', 'HR Assistant', 'HR']
        ]
        pd.DataFrame(ldap_records, columns=['employee_name', 'user_id', 'email', 'role', 'department']).to_csv(
            os.path.join(self.output_dir, 'ldap.csv'), index=False
        )
        
        print(f"Log files and ldap.csv successfully saved in {self.output_dir}.")

if __name__ == '__main__':
    import sys
    out_dir = sys.argv[1] if len(sys.argv) > 1 else 'data/cert_sample'
    sim = CERTDataSimulator(out_dir)
    sim.generate_logs()
