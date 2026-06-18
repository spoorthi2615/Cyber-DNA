import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Append parent dir to path if running directly in src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocess import CERTDataLoader
from extractors.activity import extract_activity_features
from extractors.communication import extract_communication_features
from extractors.interaction import extract_interaction_features
from signature import SignatureBuilder
from engine import CyberDNAEngine

# --- Premium UI Page Configuration ---
st.set_page_config(
    page_title="Cyber DNA Analytics Dashboard",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Sleek CSS for modern dark-themed glassmorphism
st.markdown("""
<style>
    .reportview-container {
        background: #0d0f12;
        color: #e2e8f0;
    }
    h1, h2, h3 {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
        background: linear-gradient(135deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    .alert-box-red {
        background: rgba(239, 68, 68, 0.15);
        border-left: 5px solid #ef4444;
        border-radius: 6px;
        padding: 15px;
        margin-bottom: 10px;
        color: #fca5a5;
    }
    .alert-box-yellow {
        background: rgba(245, 158, 11, 0.15);
        border-left: 5px solid #f59e0b;
        border-radius: 6px;
        padding: 15px;
        margin-bottom: 10px;
        color: #fde047;
    }
</style>
""", unsafe_type=True)

# --- Data Loading Caching ---
@st.cache_data
def load_and_process_data(data_dir):
    loader = CERTDataLoader(data_dir)
    logons = loader.load_logon_logs()
    emails = loader.load_email_logs()
    
    logons = loader.extract_time_windows(logons, 7)
    emails = loader.extract_time_windows(emails, 7)
    
    act_df = extract_activity_features(logons)
    comm_df = extract_communication_features(emails)
    int_df = extract_interaction_features(emails)
    
    raw_feats = pd.merge(act_df, comm_df, on=['user', 'time_window'], how='outer')
    raw_feats = pd.merge(raw_feats, int_df, on=['user', 'time_window'], how='outer').fillna(0.0)
    
    builder = SignatureBuilder(raw_feats)
    signatures, composite_df = builder.build_signatures()
    
    return raw_feats, signatures, composite_df

# --- Sidebar Controls ---
st.sidebar.title("🧬 Cyber DNA Control Panel")
st.sidebar.markdown("Configure analytical settings for similarity and temporal drift calculations.")

data_source = st.sidebar.selectbox(
    "Select Dataset Directory",
    ["data/cert_sample", "data/cert_cohort"],
    index=0
)

# Load data
try:
    raw_feats, signatures, composite_df = load_and_process_data(data_source)
    users = list(signatures.keys())
    weeks = sorted(list(raw_feats['time_window'].unique()))
except Exception as e:
    st.error(f"Failed to load dataset: {e}. Please make sure Phase 1 is verified.")
    st.stop()

selected_week = st.sidebar.slider("Select Assessment Week", min_value=int(min(weeks)), max_value=int(max(weeks)), value=1)
st.sidebar.info(f"Loaded {len(users)} user profiles over {len(weeks)} weeks.")

# --- App Header ---
st.title("Cyber DNA Anomaly & Attribution Portal")
st.markdown("🧬 **Human-Centered Behavioral Similarity Framework with Behavioral Drift Analysis**")

# Tabs
tab_overview, tab_similarity, tab_drift, tab_profiles = st.tabs([
    "📊 Overview & Alerts", 
    "🔥 Identity Similarity (BSI)", 
    "📈 Temporal Drift Explorer (BDS)", 
    "🔬 Profile Feature Details"
])

# --- TAB 1: OVERVIEW & ALERTS ---
with tab_overview:
    st.header("Security Overview & Active Alerts")
    
    # Calculate global metrics
    anomalies_detected = 0
    credential_sharing_alerts = 0
    
    # 1. Pre-calculate metrics for alerts
    alerts_html = []
    
    # BDS Anomaly Checks
    for user in users:
        dbs_w1 = signatures[user][1]
        for w in weeks:
            if w == 1 or w not in signatures[user]:
                continue
            bds = CyberDNAEngine.calculate_bds(dbs_w1, signatures[user][w])
            if bds >= 0.6:
                anomalies_detected += 1
                alerts_html.append(f"""
                <div class="alert-box-red">
                    <strong>🔴 SEVERE BEHAVIORAL DRIFT:</strong> User <b>{user}</b> in Week {w} shifted from baseline 
                    (Drift Score: {bds:.4f}). High risk of compromised account or insider exfiltration!
                </div>
                """)
                
    # BSI Credential Sharing Checks
    week_signatures = {u: signatures[u][selected_week] for u in users if selected_week in signatures[u]}
    for i, u1 in enumerate(users):
        for j, u2 in enumerate(users):
            if i >= j or u1 not in week_signatures or u2 not in week_signatures:
                continue
            bsi = CyberDNAEngine.calculate_bsi(week_signatures[u1], week_signatures[u2])
            if bsi > 0.99:
                credential_sharing_alerts += 1
                alerts_html.append(f"""
                <div class="alert-box-yellow">
                    <strong>🟡 IDENTITY COLLISION:</strong> High profile similarity detected between <b>{u1}</b> and <b>{u2}</b> 
                    in Week {selected_week} (BSI: {bsi:.4f}). Suspect credential sharing, multiple account usage, or cloning!
                </div>
                """)

    # Metric Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <small style="color: #64748b;">TOTAL PROFILES</small>
            <h2 style="margin: 5px 0 0 0; color: #38bdf8;">{len(users)}</h2>
        </div>
        """, unsafe_type=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <small style="color: #64748b;">ACTIVE WINDOWS</small>
            <h2 style="margin: 5px 0 0 0; color: #38bdf8;">{len(weeks)} Weeks</h2>
        </div>
        """, unsafe_type=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <small style="color: #64748b;">DRIFT ANOMALIES</small>
            <h2 style="margin: 5px 0 0 0; color: #ef4444;">{anomalies_detected}</h2>
        </div>
        """, unsafe_type=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <small style="color: #64748b;">IDENTITY OVERLAPS</small>
            <h2 style="margin: 5px 0 0 0; color: #f59e0b;">{credential_sharing_alerts}</h2>
        </div>
        """, unsafe_type=True)

    # Display Alerts
    st.markdown("<br><h3>Active Anomaly Feed</h3>", unsafe_type=True)
    if alerts_html:
        for alert in alerts_html:
            st.markdown(alert, unsafe_type=True)
    else:
        st.success("🟢 No active behavioral anomalies or identity collisions detected.")

# --- TAB 2: IDENTITY SIMILARITY (BSI) ---
with tab_similarity:
    st.header(f"Behavioral Similarity Index (BSI) Matrix - Week {selected_week}")
    st.markdown("Evaluates user-to-user cosine resemblance. High scores ($>0.98$) denote overlapping behaviors.")
    
    # Calculate similarity matrix
    week_users = [u for u in users if selected_week in signatures[u]]
    bsi_matrix = []
    
    for u1 in week_users:
        row = []
        for u2 in week_users:
            bsi = CyberDNAEngine.calculate_bsi(signatures[u1][selected_week], signatures[u2][selected_week])
            row.append(bsi)
        bsi_matrix.append(row)
        
    bsi_df = pd.DataFrame(bsi_matrix, index=week_users, columns=week_users)
    
    # Plotly Heatmap
    fig_heat = px.imshow(
        bsi_df,
        text_auto=".3f",
        aspect="auto",
        color_continuous_scale="Viridis",
        labels=dict(x="User B", y="User A", color="Similarity (BSI)"),
        title=f"Cohort Similarity Grid (Week {selected_week})"
    )
    fig_heat.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#e2e8f0',
        width=900,
        height=600
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# --- TAB 3: TEMPORAL DRIFT EXPLORER (BDS) ---
with tab_drift:
    st.header("Behavioral Drift (BDS) Timeline")
    st.markdown("Tracks the Euclidean evolution of users' signatures from their Week 1 baseline.")
    
    drift_data = []
    for user in users:
        dbs_w1 = signatures[user][1]
        for w in weeks:
            if w not in signatures[user]:
                continue
            bds = CyberDNAEngine.calculate_bds(dbs_w1, signatures[user][w])
            drift_data.append({
                'User': user,
                'Week': w,
                'Drift (BDS)': bds
            })
            
    drift_df = pd.DataFrame(drift_data)
    
    # Line Chart
    fig_line = px.line(
        drift_df,
        x='Week',
        y='Drift (BDS)',
        color='User',
        markers=True,
        title="Weekly Behavioral Drift Score (BDS) from Baseline",
        labels={'Drift (BDS)': 'Behavioral Drift Score (BDS)', 'Week': 'Assessment Week'}
    )
    # Add horizontal threshold lines
    fig_line.add_hline(y=0.2, line_dash="dash", line_color="#f59e0b", annotation_text="Moderate Drift Limit")
    fig_line.add_hline(y=0.6, line_dash="dash", line_color="#ef4444", annotation_text="Severe Anomaly Threshold")
    
    fig_line.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#e2e8f0',
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)')
    )
    st.plotly_chart(fig_line, use_container_width=True)

# --- TAB 4: PROFILE FEATURE DETAILS ---
with tab_profiles:
    st.header("DBS Profile Feature Inspector")
    st.markdown("Inspect raw and scaled feature breakdowns of a chosen profile.")
    
    selected_user = st.selectbox("Select User Profile", users)
    
    # Load user features
    user_feats = raw_feats[raw_feats['user'] == selected_user].sort_values('time_window')
    
    st.subheader(f"Weekly Raw Metrics for {selected_user}")
    st.dataframe(user_feats)
    
    # Plot feature distribution
    # Reshape for bar chart
    melted_feats = pd.melt(
        user_feats, 
        id_vars=['user', 'time_window'], 
        value_vars=['login_freq', 'active_hours', 'avg_session', 'email_freq', 'vocab_diversity', 'contact_diversity', 'reciprocity'],
        var_name='Feature', 
        value_name='Raw Value'
    )
    
    fig_bar = px.bar(
        melted_feats,
        x='Feature',
        y='Raw Value',
        color='time_window',
        barmode='group',
        title=f"Feature Metric Comparisons for {selected_user} by Week",
        labels={'time_window': 'Week'}
    )
    fig_bar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#e2e8f0'
    )
    st.plotly_chart(fig_bar, use_container_width=True)
