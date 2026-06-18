import pandas as pd
import numpy as np

def extract_interaction_features(emails_df):
    """
    Extracts Layer 3 (Interaction) features from email logs.
    Features:
    - contact_diversity: Number of unique email addresses contacted.
    - reciprocity: Ratio of emails received to emails sent.
    """
    if emails_df.empty:
        return pd.DataFrame(columns=['user', 'time_window', 'contact_diversity', 'reciprocity'])

    emails_df = emails_df.copy()
    emails_df['date'] = pd.to_datetime(emails_df['date'])

    # 1. Optimized Vectorized Contact Diversity (Count of unique recipients)
    temp_to = emails_df[['user', 'time_window', 'to']].copy()
    temp_to['to'] = temp_to['to'].astype(str).apply(
        lambda x: [r.strip().lower() for r in x.split(';') if r.strip()]
    )
    temp_to = temp_to.explode('to').dropna()
    diversity_df = temp_to.groupby(['user', 'time_window'])['to'].nunique().reset_index(name='contact_diversity')
    diversity_df['contact_diversity'] = diversity_df['contact_diversity'].astype(float)

    # 2. Optimized Vectorized Reciprocity (Received emails / Sent emails)
    # Count sent emails per user-week
    sent_counts = emails_df.groupby(['user', 'time_window']).size().reset_index(name='sent_count')
    sent_counts['user'] = sent_counts['user'].str.upper().str.strip()

    # Explode recipient columns (to, cc, bcc) to count received emails per user-week
    recipients_list = []
    for col in ['to', 'cc', 'bcc']:
        if col in emails_df.columns:
            temp = emails_df[['time_window', col]].copy()
            # Extract username prefix from email addresses
            temp[col] = temp[col].astype(str).apply(
                lambda x: [r.split('@')[0].upper().strip() for r in x.split(';') if r.strip() and r.lower() != 'nan']
            )
            temp = temp.explode(col).dropna()
            temp.rename(columns={col: 'user'}, inplace=True)
            recipients_list.append(temp)
            
    if recipients_list:
        all_received = pd.concat(recipients_list)
        received_df = all_received.groupby(['user', 'time_window']).size().reset_index(name='received_count')
        received_df['user'] = received_df['user'].str.upper().str.strip()
    else:
        received_df = pd.DataFrame(columns=['user', 'time_window', 'received_count'])

    # Merge sent and received counts to compute reciprocity
    recip_df = pd.merge(sent_counts, received_df, on=['user', 'time_window'], how='outer')
    recip_df['sent_count'] = recip_df['sent_count'].fillna(0.0)
    recip_df['received_count'] = recip_df['received_count'].fillna(0.0)
    
    # Reciprocity = received / sent (epsilon safety handled by pd.where/np.where)
    recip_df['reciprocity'] = np.where(
        recip_df['sent_count'] > 0, 
        recip_df['received_count'] / recip_df['sent_count'], 
        0.0
    )
    recip_df['reciprocity'] = recip_df['reciprocity'].clip(upper=2.0)
    
    # Merge with contact diversity
    # Standardize user name casings
    diversity_df['user'] = diversity_df['user'].str.upper().str.strip()
    
    features_df = pd.merge(
        diversity_df, 
        recip_df[['user', 'time_window', 'reciprocity']], 
        on=['user', 'time_window'], 
        how='outer'
    )
    features_df['contact_diversity'] = features_df['contact_diversity'].fillna(0.0)
    features_df['reciprocity'] = features_df['reciprocity'].fillna(0.0)

    return features_df
