import pandas as pd
import numpy as np

def extract_activity_features(logons_df):
    """
    Extracts Layer 1 (Activity) features from logon logs grouped by user and time_window.
    Features:
    - login_freq: Raw count of Logon events.
    - avg_session: Average logon duration in hours.
    - active_hours: Ratio of activities within business hours (8 AM - 6 PM).
    """
    if logons_df.empty:
        return pd.DataFrame(columns=['user', 'time_window', 'login_freq', 'avg_session', 'active_hours'])

    # Ensure dates are parsed
    df = logons_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # 1. Active Hours Consistency (Ratio of business hour events)
    df['hour'] = df['date'].dt.hour
    df['is_business_hour'] = df['hour'].between(8, 18).astype(int)
    active_hours_df = df.groupby(['user', 'time_window'])['is_business_hour'].mean().reset_index(name='active_hours')
    
    # 2. Login Frequency (Count of Logon events)
    logon_only = df[df['activity'] == 'Logon']
    freq_df = logon_only.groupby(['user', 'time_window']).size().reset_index(name='login_freq')
    
    # 3. Session Duration (Average time between logon and logoff)
    # Sort chronologically within user-PC groups
    sorted_logs = df.sort_values(['user', 'pc', 'date'])
    
    # Shift to align subsequent activity, dates, and time windows
    sorted_logs['next_activity'] = sorted_logs.groupby(['user', 'pc'])['activity'].shift(-1)
    sorted_logs['next_date'] = sorted_logs.groupby(['user', 'pc'])['date'].shift(-1)
    sorted_logs['next_time_window'] = sorted_logs.groupby(['user', 'pc'])['time_window'].shift(-1)
    
    # Filter valid logon sessions matched with their immediate logoff
    sessions = sorted_logs[
        (sorted_logs['activity'] == 'Logon') & 
        (sorted_logs['next_activity'] == 'Logoff')
    ].copy()
    
    # Calculate duration in hours
    sessions['duration'] = (sessions['next_date'] - sessions['date']).dt.total_seconds() / 3600.0
    
    # Enforce domain sanity bounds (e.g. skip negative times or sessions exceeding 24 hours)
    valid_sessions = sessions[(sessions['duration'] > 0) & (sessions['duration'] < 24.0)].copy()
    
    # Assign the time window of the logoff event to match the old loop implementation
    valid_sessions['time_window'] = valid_sessions['next_time_window'].astype(int)
    
    # Aggregate weekly averages
    if not valid_sessions.empty:
        avg_sess_df = valid_sessions.groupby(['user', 'time_window'])['duration'].mean().reset_index(name='avg_session')
    else:
        avg_sess_df = pd.DataFrame(columns=['user', 'time_window', 'avg_session'])
        
    # Merge all features together
    features_df = pd.merge(freq_df, active_hours_df, on=['user', 'time_window'], how='outer')
    features_df = pd.merge(features_df, avg_sess_df, on=['user', 'time_window'], how='left')
    
    # Fill NaN values (e.g. if no session pairs found, set avg_session to 0)
    features_df['login_freq'] = features_df['login_freq'].fillna(0.0)
    features_df['avg_session'] = features_df['avg_session'].fillna(0.0)
    features_df['active_hours'] = features_df['active_hours'].fillna(0.0)
    
    return features_df
