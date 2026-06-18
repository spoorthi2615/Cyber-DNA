import pandas as pd
import numpy as np
import re

# Compile regex once at module level for speed
WORD_RE = re.compile(r'\b\w+\b')

def tokenize_content(text):
    """
    Cleans and splits email body content into a list of lowercase words.
    """
    if not isinstance(text, str) or not text:
        return []
    return WORD_RE.findall(text.lower())

def extract_communication_features(emails_df):
    """
    Extracts Layer 2 (Communication) features from email logs.
    Features:
    - vocab_diversity: Unique words / Total words in sent emails.
    - response_time: Average time to reply to incoming emails (in hours).
    - email_freq: Total emails sent per week.
    """
    if emails_df.empty:
        return pd.DataFrame(columns=['user', 'time_window', 'vocab_diversity', 'response_time', 'email_freq'])

    emails_df = emails_df.copy()
    emails_df['date'] = pd.to_datetime(emails_df['date'])

    # 1. Email Frequency (Count of emails sent per user)
    freq_df = emails_df.groupby(['user', 'time_window']).size().reset_index(name='email_freq')

    # 2. Optimized Vocabulary Diversity (Individual tokenization + set union)
    # Clean email content and tokenize per message to avoid large string allocations
    emails_df['content_str'] = emails_df['content'].fillna('').astype(str)
    # Run tokenize_content only on non-empty content strings to speed up execution
    non_empty_mask = emails_df['content_str'].str.len() > 0
    non_empty_content = emails_df['content_str'][non_empty_mask]
    
    tokens_series = non_empty_content.apply(tokenize_content)
    
    # Map tokens back to emails_df
    emails_df['tokens'] = pd.Series([[]] * len(emails_df), index=emails_df.index, dtype=object)
    emails_df.loc[non_empty_content.index, 'tokens'] = tokens_series
    emails_df['word_count'] = emails_df['tokens'].apply(len)
    
    grouped_vocab = emails_df.groupby(['user', 'time_window'])
    
    vocab_diversity_records = []
    for (user, w), group in grouped_vocab:
        total_words = group['word_count'].sum()
        if total_words > 0:
            unique_words = set()
            for t_list in group['tokens']:
                unique_words.update(t_list)
            diversity = len(unique_words) / total_words
        else:
            diversity = 0.5  # default baseline
            
        vocab_diversity_records.append({
            'user': user,
            'time_window': w,
            'vocab_diversity': diversity
        })
        
    vocab_df = pd.DataFrame(vocab_diversity_records)

    # 3. Optimized Vectorized Response Time Calculation
    # Explode recipients and standardize usernames
    exploded = emails_df[['date', 'user', 'to', 'time_window']].copy()
    exploded['to'] = exploded['to'].astype(str).apply(
        lambda x: [r.split('@')[0].upper().strip() for r in x.split(';') if r.strip()]
    )
    exploded = exploded.explode('to').dropna()
    exploded['sender'] = exploded['user'].str.upper().str.strip()
    exploded['receiver'] = exploded['to']
    
    # Sort chronologically
    exploded = exploded.sort_values('date')
    
    # Vectorized sorting of sender-receiver pairs to create group keys
    s = exploded['sender'].values
    r = exploded['receiver'].values
    c1 = np.where(s < r, s, r)
    c2 = np.where(s < r, r, s)
    exploded['pair_c1'] = c1
    exploded['pair_c2'] = c2
    
    # Group by pair and shift columns to find consecutive messages between the same pair
    pair_group = exploded.groupby(['pair_c1', 'pair_c2'])
    exploded['prev_sender'] = pair_group['sender'].shift(1)
    exploded['prev_receiver'] = pair_group['receiver'].shift(1)
    exploded['prev_date'] = pair_group['date'].shift(1)
    
    # A reply occurs when: current_sender == prev_receiver
    is_reply = (exploded['sender'] == exploded['prev_receiver'])
    time_diff = (exploded['date'] - exploded['prev_date']).dt.total_seconds() / 3600.0
    
    # Filter valid replies (reply lag must be positive and under 24 hours)
    replies = exploded[is_reply & (time_diff > 0) & (time_diff < 24.0)].copy()
    replies['response_time'] = time_diff
    
    if not replies.empty:
        avg_resp_df = replies.groupby(['user', 'time_window'])['response_time'].mean().reset_index()
    else:
        avg_resp_df = pd.DataFrame(columns=['user', 'time_window', 'response_time'])

    # Merge features
    features_df = pd.merge(freq_df, vocab_df, on=['user', 'time_window'], how='outer')
    features_df = pd.merge(features_df, avg_resp_df, on=['user', 'time_window'], how='left')

    # Fill NaNs
    features_df['email_freq'] = features_df['email_freq'].fillna(0.0)
    features_df['vocab_diversity'] = features_df['vocab_diversity'].fillna(0.5)
    features_df['response_time'] = features_df['response_time'].fillna(1.0) # default reply lag of 1 hour

    return features_df
