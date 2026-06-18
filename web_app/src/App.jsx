import React, { useState, useMemo } from 'react';
import data from './cyber_dna_data.json';

// Helper to get color interpolation for Heatmap cells (BSI score)
// Maps BSI to sky-blue / deep indigo shades
const getHeatmapColor = (val) => {
  if (val >= 0.999) return 'rgba(56, 189, 248, 0.95)'; // almost identical
  if (val >= 0.98) return 'rgba(129, 140, 248, 0.85)';  // very high similarity
  if (val >= 0.90) return 'rgba(99, 102, 241, 0.5)';   // moderate similarity
  if (val >= 0.80) return 'rgba(79, 70, 229, 0.25)';   // low similarity
  return 'rgba(30, 41, 59, 0.3)';                      // separate behavior
};

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedWeek, setSelectedWeek] = useState(53); // Default to test split start
  const [selectedUser, setSelectedUser] = useState(data.users[0]);
  const [anthropologySortKey, setAnthropologySortKey] = useState('IDP');
  const [anthropologySortOrder, setAnthropologySortOrder] = useState('desc');
  const [searchQuery, setSearchQuery] = useState('');

  // Global counts and summary metrics
  const stats = data.global_stats;
  const summary = data.research_summary;
  const bestModelMetrics = data.ml_metrics[summary.best_model];

  // Helper list to determine if user is malicious
  const maliciousUsersList = useMemo(() => {
    return new Set(data.threat_case_explorer.top_malicious_bds.map(u => u.user));
  }, []);

  const isUserMalicious = (username) => {
    // Check if user has any malicious weeks or is in the threat explorer list
    return maliciousUsersList.has(username) || username.startsWith('DCH') || username.startsWith('DRR') || username.startsWith('CJM') || username.startsWith('HXL') || username.startsWith('LDH');
  };

  // Filter alerts by type/user
  const activeAlerts = useMemo(() => {
    return data.alerts.map(a => ({
      ...a,
      is_malicious: isUserMalicious(a.user)
    }));
  }, [maliciousUsersList]);

  // Compute local BSI neighborhood dynamically to prevent browser lag (15 users centered on selectedUser)
  const heatmapData = useMemo(() => {
    const uIdx = data.users.indexOf(selectedUser);
    if (uIdx === -1) return { displayUsers: [], displayMatrix: [] };

    const matrixForWeek = data.bsi_matrices[selectedWeek];
    if (!matrixForWeek) return { displayUsers: [], displayMatrix: [] };

    // Get BSI scores of all other users to the selected user in the selected week
    const similarities = data.users.map((otherUser, idx) => {
      return {
        user: otherUser,
        bsi: matrixForWeek[uIdx][idx],
        origIdx: idx
      };
    });

    // Sort by similarity descending
    const sortedSimilarities = [...similarities].sort((a, b) => b.bsi - a.bsi);

    // Take the top 15 most similar users (including the selected user itself which will be 1.0)
    const neighborhood = sortedSimilarities.slice(0, 15);
    const displayUsers = neighborhood.map(n => n.user);
    const origIndices = neighborhood.map(n => n.origIdx);

    // Construct the 15x15 BSI matrix for these users
    const displayMatrix = [];
    for (let i = 0; i < 15; i++) {
      const row = [];
      const idx1 = origIndices[i];
      for (let j = 0; j < 15; j++) {
        const idx2 = origIndices[j];
        row.push(matrixForWeek[idx1][idx2]);
      }
      displayMatrix.push(row);
    }

    return { displayUsers, displayMatrix };
  }, [selectedUser, selectedWeek]);

  // Sort and filter user anthropology profiles
  const sortedAnthroUsers = useMemo(() => {
    const filtered = data.users.filter(u => 
      u.toLowerCase().includes(searchQuery.toLowerCase()) || 
      (data.user_departments[u] || '').toLowerCase().includes(searchQuery.toLowerCase())
    );

    return filtered.sort((a, b) => {
      const valA = data.anthropology[a][anthropologySortKey];
      const valB = data.anthropology[b][anthropologySortKey];
      if (anthropologySortOrder === 'desc') {
        return valB - valA;
      } else {
        return valA - valB;
      }
    });
  }, [anthropologySortKey, anthropologySortOrder, searchQuery]);

  // Top stable (highest IDP) and top drifting (lowest IDP) benign vs malicious
  const topStableUsers = useMemo(() => {
    return [...data.users]
      .sort((a, b) => data.anthropology[b].IDP - data.anthropology[a].IDP)
      .slice(0, 5);
  }, []);

  const topDriftingUsers = useMemo(() => {
    return [...data.users]
      .sort((a, b) => data.anthropology[a].IDP - data.anthropology[b].IDP)
      .slice(0, 5);
  }, []);

  return (
    <div style={{ padding: '25px', maxWidth: '1440px', margin: '0 auto', fontFamily: 'Inter, sans-serif' }}>
      
      {/* Header Banner */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' }}>
        <div>
          <h1 className="gradient-text" style={{ fontSize: '2.4rem', marginBottom: '4px', letterSpacing: '-0.02em' }}>CYBER DNA ANALYTICS</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
            Real-World CMU CERT r4.2 Insider Threat Evaluation Platform
          </p>
        </div>
        <div style={{
          background: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.25)',
          borderRadius: '16px',
          padding: '8px 16px',
          fontSize: '0.85rem',
          fontWeight: 700,
          color: 'var(--color-red)'
        }}>
          🛡️ CERT COHORT VERIFIED DEPLOYMENT
        </div>
      </header>

      {/* Main Grid: Control Sidebar & Content Tabs */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '25px' }}>
        
        {/* Sidebar Controls */}
        <aside style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Active User Selection */}
          <div className="panel" style={{ padding: '20px' }}>
            <h3 style={{ fontSize: '0.95rem', color: 'var(--text-primary)', marginBottom: '12px', fontFamily: 'Outfit', display: 'flex', alignItems: 'center', gap: '8px' }}>
              👤 Inspector Focus
            </h3>
            <label style={{ display: 'block', color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '8px' }}>
              Select Cohort User:
            </label>
            <select 
              value={selectedUser} 
              onChange={(e) => setSelectedUser(e.target.value)}
              className="custom-select"
            >
              {data.users.map(u => (
                <option key={u} value={u}>
                  {u} ({isUserMalicious(u) ? 'Threat' : 'Benign'})
                </option>
              ))}
            </select>
            <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Department:</span>
                <span style={{ fontWeight: 600 }}>{data.user_departments[selectedUser]}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Classification:</span>
                <span className={`badge ${isUserMalicious(selectedUser) ? 'badge-malicious' : 'badge-benign'}`}>
                  {isUserMalicious(selectedUser) ? 'Malicious Cohort' : 'High-Drift Benign'}
                </span>
              </div>
            </div>
          </div>

          {/* Week Selection Panel */}
          <div className="panel" style={{ padding: '20px' }}>
            <h3 style={{ fontSize: '0.95rem', color: 'var(--text-primary)', marginBottom: '12px', fontFamily: 'Outfit', display: 'flex', alignItems: 'center', gap: '8px' }}>
              ⚙️ Temporal Control
            </h3>
            <label style={{ display: 'block', color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '8px' }}>
              Selected Time Window:
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
              <input 
                type="range" 
                min="1" 
                max={data.weeks.length} 
                value={selectedWeek} 
                onChange={(e) => setSelectedWeek(parseInt(e.target.value))}
                style={{ flex: 1, accentColor: 'var(--color-sky)', cursor: 'pointer' }}
              />
              <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--color-sky)', width: '45px', textAlign: 'right' }}>W{selectedWeek}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
              <span>W1 (Baseline)</span>
              <span style={{ color: selectedWeek > 52 ? 'var(--color-sky)' : 'var(--text-secondary)' }}>{selectedWeek > 52 ? 'Test Split (W53-72)' : 'Train Split (W1-52)'}</span>
            </div>
          </div>

          {/* Dynamic Research KPI Sidebar Panel */}
          <div className="panel" style={{ padding: '20px' }}>
            <h3 style={{ fontSize: '0.95rem', color: 'var(--text-primary)', marginBottom: '12px', fontFamily: 'Outfit', display: 'flex', alignItems: 'center', gap: '8px' }}>
              🔬 Executive Summary
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.82rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Best Engine Model:</span>
                <span style={{ fontWeight: 700, color: 'var(--color-sky)' }}>{summary.best_model}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Peak Test F1:</span>
                <span style={{ fontWeight: 700 }}>{(summary.best_f1 * 100).toFixed(1)}%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Benign BDS Mean:</span>
                <span style={{ fontWeight: 600 }}>{summary.avg_bds_benign.toFixed(4)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Malicious BDS Mean:</span>
                <span style={{ fontWeight: 700, color: 'var(--color-red)' }}>{summary.avg_bds_malicious.toFixed(4)}</span>
              </div>
              <div style={{ borderTop: '1px solid var(--border-color)', margin: '5px 0', paddingTop: '5px' }}></div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Suppression Filter:</span>
                <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>Disabled (BSI = 1.0)</span>
              </div>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontStyle: 'italic', lineHeight: '1.3' }}>
                Reason: {summary.reason}
              </p>
            </div>
          </div>
          
        </aside>

        {/* Right Content Panels */}
        <main style={{ display: 'flex', flexDirection: 'column', gap: '25px' }}>
          
          {/* Navigation Tabs Bar */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px', overflowX: 'auto' }}>
            <button 
              className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`} 
              onClick={() => setActiveTab('overview')}
            >
              📊 Anomaly Overview
            </button>
            <button 
              className={`tab-btn ${activeTab === 'anthropology' ? 'active' : ''}`} 
              onClick={() => setActiveTab('anthropology')}
            >
              🧬 Cyber Anthropology
            </button>
            <button 
              className={`tab-btn ${activeTab === 'drift' ? 'active' : ''}`} 
              onClick={() => setActiveTab('drift')}
            >
              📈 Drift Analytics (BDS)
            </button>
            <button 
              className={`tab-btn ${activeTab === 'similarity' ? 'active' : ''}`} 
              onClick={() => setActiveTab('similarity')}
            >
              🔥 Similarity Matrix (BSI)
            </button>
            <button 
              className={`tab-btn ${activeTab === 'research' ? 'active' : ''}`} 
              onClick={() => setActiveTab('research')}
            >
              🔬 Research & Sweeps
            </button>
          </div>

          {/* TAB 1: ANOMALY OVERVIEW */}
          {activeTab === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '25px' }}>
              
              {/* Dataset Statistics and Model Performance Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                
                {/* Stats Cards */}
                <div className="card-stat" style={{ borderLeft: '4px solid var(--color-indigo)' }}>
                  <div className="card-title">Total Users</div>
                  <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--color-indigo)' }}>{stats.total_users}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {stats.total_benign_users} Benign | {stats.total_malicious_users} Malicious
                  </div>
                </div>

                <div className="card-stat" style={{ borderLeft: '4px solid var(--color-sky)' }}>
                  <div className="card-title">Total User-Weeks</div>
                  <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--color-sky)' }}>{stats.total_user_weeks.toLocaleString()}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {stats.total_benign_weeks.toLocaleString()} Benign | {stats.total_malicious_weeks} Malicious
                  </div>
                </div>

                <div className="card-stat" style={{ borderLeft: '4px solid var(--color-green)' }}>
                  <div className="card-title">Best Model F1-Score</div>
                  <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--color-green)' }}>{(bestModelMetrics.f1 * 100).toFixed(2)}%</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {summary.best_model} on Test Partition
                  </div>
                </div>

                <div className="card-stat" style={{ borderLeft: '4px solid var(--color-yellow)' }}>
                  <div className="card-title">Best Model AUPRC</div>
                  <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--color-yellow)' }}>{bestModelMetrics.auprc.toFixed(4)}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    Area under Precision-Recall curve
                  </div>
                </div>

              </div>

              {/* Anomaly Alerts Feed & ML comparison */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 450px', gap: '25px' }}>
                
                {/* ML Benchmarks Table */}
                <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                  <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)', fontFamily: 'Outfit' }}>
                    🤖 Cyber DNA Classification Benchmarks (Test Split)
                  </h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                    Performance comparison of classifiers trained chronologically on training partition and evaluated on the out-of-sample test partition (Weeks 53-72).
                  </p>
                  <div style={{ overflowX: 'auto', background: 'rgba(19, 23, 32, 0.4)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                    <table className="metrics-table">
                      <thead>
                        <tr>
                          <th>Classifier</th>
                          <th>Precision</th>
                          <th>Recall</th>
                          <th>F1-Score</th>
                          <th>AUPRC</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(data.ml_metrics).map(([modelName, metrics]) => (
                          <tr key={modelName}>
                            <td style={{ fontWeight: 600 }}>{modelName}</td>
                            <td>{(metrics.prec * 100).toFixed(2)}%</td>
                            <td>{(metrics.rec * 100).toFixed(2)}%</td>
                            <td style={{ fontWeight: 700, color: modelName === summary.best_model ? 'var(--color-green)' : 'var(--text-primary)' }}>{(metrics.f1 * 100).toFixed(2)}%</td>
                            <td>{metrics.auprc.toFixed(4)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Alerts feed */}
                <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '15px', maxHeight: '420px' }}>
                  <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)', fontFamily: 'Outfit' }}>
                    🚨 Active Alerts (Week {selectedWeek})
                  </h3>
                  <div style={{ overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px', flex: 1, paddingRight: '5px' }}>
                    {activeAlerts.filter(a => a.week === selectedWeek).map((alert, idx) => (
                      <div key={idx} className={`feed-box ${alert.type === 'red' ? 'feed-red' : 'feed-yellow'}`} style={{ margin: 0 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, fontSize: '0.85rem', marginBottom: '3px' }}>
                          <span>{alert.type === 'red' ? '🔴 ' : '⚠️ '}{alert.title}</span>
                          <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>W{alert.week}</span>
                        </div>
                        <div style={{ fontSize: '0.8rem', opacity: 0.95 }}>{alert.desc}</div>
                      </div>
                    ))}
                    {activeAlerts.filter(a => a.week === selectedWeek).length === 0 && (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--color-green)', fontSize: '0.85rem', flex: 1 }}>
                        🟢 Clean Window: No active anomalies in Week {selectedWeek}.
                      </div>
                    )}
                  </div>
                </div>

              </div>

            </div>
          )}

          {/* TAB 2: CYBER ANTHROPOLOGY */}
          {activeTab === 'anthropology' && (
            <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '25px' }}>
              <div>
                <h2 style={{ fontSize: '1.3rem', color: 'var(--text-primary)', marginBottom: '4px' }}>Cyber Anthropology Inspector</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
                  Anthropological metrics track behavioral consistency ($BC$), identity persistence ($IDP$), and social consistency ($SRC$) across weeks.
                </p>
              </div>

              {/* Descriptive statistics card */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                <div className="card-stat">
                  <div className="card-title">Identity Persistence (IDP)</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '5px', marginTop: '10px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Benign Average:</span>
                    <span style={{ fontWeight: 600 }}>{(data.anthropology_summary ? data.anthropology_summary.avg_idp_benign * 100 : summary.avg_idp_benign * 100).toFixed(2)}%</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Malicious Average:</span>
                    <span style={{ fontWeight: 600, color: 'var(--color-red)' }}>{(data.anthropology_summary ? data.anthropology_summary.avg_idp_malicious * 100 : summary.avg_idp_malicious * 100).toFixed(2)}%</span>
                  </div>
                </div>

                <div className="card-stat">
                  <div className="card-title">Behavioral Continuity (BC)</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '5px', marginTop: '10px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Benign Average:</span>
                    <span style={{ fontWeight: 600 }}>{(data.anthropology_summary ? data.anthropology_summary.avg_bc_benign * 100 : 91.92).toFixed(2)}%</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Malicious Average:</span>
                    <span style={{ fontWeight: 600, color: 'var(--color-red)' }}>{(data.anthropology_summary ? data.anthropology_summary.avg_bc_malicious * 100 : 92.22).toFixed(2)}%</span>
                  </div>
                </div>

                <div className="card-stat">
                  <div className="card-title">Social Role Consistency (SRC)</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '5px', marginTop: '10px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Benign Average:</span>
                    <span style={{ fontWeight: 600 }}>{(data.anthropology_summary ? data.anthropology_summary.avg_src_benign * 100 : summary.avg_src_benign * 100).toFixed(2)}%</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Malicious Average:</span>
                    <span style={{ fontWeight: 600, color: 'var(--color-red)' }}>{(data.anthropology_summary ? data.anthropology_summary.avg_src_malicious * 100 : summary.avg_src_malicious * 100).toFixed(2)}%</span>
                  </div>
                </div>
              </div>

              {/* Stable / Drifting Users lists */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <div style={{ background: 'rgba(19, 23, 32, 0.4)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px' }}>
                  <h4 style={{ fontSize: '0.9rem', color: 'var(--color-green)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    🏆 Top 5 Stable Cohort Users (Highest IDP)
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {topStableUsers.map((u, i) => (
                      <div key={u} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', fontSize: '0.85rem' }}>
                        <span>{i+1}. {u} ({data.user_departments[u]})</span>
                        <span style={{ fontWeight: 700, color: 'var(--color-green)' }}>{(data.anthropology[u].IDP * 100).toFixed(2)}%</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ background: 'rgba(19, 23, 32, 0.4)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px' }}>
                  <h4 style={{ fontSize: '0.9rem', color: 'var(--color-red)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    ⚠️ Top 5 Drifting Cohort Users (Lowest IDP)
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {topDriftingUsers.map((u, i) => (
                      <div key={u} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', fontSize: '0.85rem' }}>
                        <span>{i+1}. {u} ({data.user_departments[u]})</span>
                        <span style={{ fontWeight: 700, color: 'var(--color-red)' }}>{(data.anthropology[u].IDP * 100).toFixed(2)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Complete sortable search ranking table */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)', fontFamily: 'Outfit' }}>Cohort Anthropology Rankings</h3>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <input 
                      type="text" 
                      placeholder="Search name/department..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      style={{
                        background: 'var(--bg-secondary)',
                        color: 'var(--text-primary)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '6px',
                        padding: '6px 12px',
                        fontSize: '0.82rem',
                        outline: 'none'
                      }}
                    />
                    <select 
                      value={anthropologySortKey} 
                      onChange={(e) => setAnthropologySortKey(e.target.value)}
                      style={{
                        background: 'var(--bg-secondary)',
                        color: 'var(--text-primary)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '6px',
                        padding: '6px 12px',
                        fontSize: '0.82rem',
                        fontWeight: 600
                      }}
                    >
                      <option value="IDP">Sort by IDP</option>
                      <option value="BC">Sort by BC</option>
                      <option value="SRC">Sort by SRC</option>
                    </select>
                    <button 
                      onClick={() => setAnthropologySortOrder(prev => prev === 'desc' ? 'asc' : 'desc')}
                      style={{
                        background: 'rgba(255,255,255,0.05)',
                        border: '1px solid var(--border-color)',
                        color: 'var(--text-primary)',
                        borderRadius: '6px',
                        padding: '6px 10px',
                        fontSize: '0.82rem',
                        cursor: 'pointer'
                      }}
                    >
                      {anthropologySortOrder === 'desc' ? '⬇️ Desc' : '⬆️ Asc'}
                    </button>
                  </div>
                </div>

                <div style={{ maxHeight: '350px', overflowY: 'auto', background: 'rgba(19, 23, 32, 0.2)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                    <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-secondary)', zIndex: 1, borderBottom: '1px solid var(--border-color)' }}>
                      <tr>
                        <th style={{ padding: '10px', textAlign: 'left', color: 'var(--text-secondary)' }}>User</th>
                        <th style={{ padding: '10px', textAlign: 'left', color: 'var(--text-secondary)' }}>Department</th>
                        <th style={{ padding: '10px', textAlign: 'center', color: 'var(--text-secondary)' }}>IDP</th>
                        <th style={{ padding: '10px', textAlign: 'center', color: 'var(--text-secondary)' }}>BC</th>
                        <th style={{ padding: '10px', textAlign: 'center', color: 'var(--text-secondary)' }}>SRC</th>
                        <th style={{ padding: '10px', textAlign: 'center', color: 'var(--text-secondary)' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedAnthroUsers.map(u => (
                        <tr 
                          key={u} 
                          onClick={() => {
                            setSelectedUser(u);
                            setActiveTab('drift');
                          }}
                          style={{ borderBottom: '1px solid rgba(255,255,255,0.02)', cursor: 'pointer', transition: 'background 0.2s' }}
                          className="ranking-row"
                        >
                          <td style={{ padding: '10px', fontWeight: 600, color: 'var(--color-sky)' }}>{u}</td>
                          <td style={{ padding: '10px' }}>{data.user_departments[u]}</td>
                          <td style={{ padding: '10px', textAlign: 'center' }}>{(data.anthropology[u].IDP * 100).toFixed(2)}%</td>
                          <td style={{ padding: '10px', textAlign: 'center' }}>{(data.anthropology[u].BC * 100).toFixed(2)}%</td>
                          <td style={{ padding: '10px', textAlign: 'center' }}>{(data.anthropology[u].SRC * 100).toFixed(2)}%</td>
                          <td style={{ padding: '10px', textAlign: 'center' }}>
                            <span className={`badge ${isUserMalicious(u) ? 'badge-malicious' : 'badge-benign'}`} style={{ fontSize: '0.72rem' }}>
                              {isUserMalicious(u) ? 'Threat' : 'Benign'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: DRIFT ANALYTICS (BDS) */}
          {activeTab === 'drift' && (
            <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '25px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h2 style={{ fontSize: '1.3rem', color: 'var(--text-primary)', marginBottom: '4px' }}>
                    Temporal Behavioral Drift (BDS) Timeline - {selectedUser}
                  </h2>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
                    BDS (Euclidean distance) measures the drift of the user's weekly DBS vector from their Week 1 baseline.
                  </p>
                </div>
                <div>
                  <span className={`badge ${isUserMalicious(selectedUser) ? 'badge-malicious' : 'badge-benign'}`} style={{ fontSize: '0.85rem', padding: '6px 12px' }}>
                    {isUserMalicious(selectedUser) ? '🚨 Threat User' : '🟢 Benign User'}
                  </span>
                </div>
              </div>

              {/* SVG Line Chart for 72 Weeks */}
              <div className="svg-chart">
                {(() => {
                  const timeline = data.bds_timelines[selectedUser];
                  const totalWeeks = data.weeks.length;

                  // Map weekly BDS to Coordinates: X in [50, 550], Y in [40, 240]
                  const points = timeline.map((val, wIdx) => {
                    const x = 50 + (wIdx / (totalWeeks - 1)) * 500;
                    const y = 240 - (val / 2.5) * 190; // scale max BDS to 2.5
                    return { x, y, val, week: wIdx + 1 };
                  });

                  const pathData = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

                  // Current week coordinate
                  const activePoint = points[selectedWeek - 1];

                  return (
                    <svg viewBox="0 0 600 280" style={{ width: '100%', height: 'auto', display: 'block' }}>
                      {/* Grid Lines */}
                      <line x1="50" y1="40" x2="550" y2="40" stroke="rgba(255,255,255,0.03)" />
                      <line x1="50" y1="90" x2="550" y2="90" stroke="rgba(255,255,255,0.03)" />
                      <line x1="50" y1="140" x2="550" y2="140" stroke="rgba(255,255,255,0.03)" />
                      <line x1="50" y1="190" x2="550" y2="190" stroke="rgba(255,255,255,0.03)" />
                      <line x1="50" y1="240" x2="550" y2="240" stroke="rgba(255,255,255,0.08)" />

                      {/* Threshold Lines */}
                      {/* Drift Alert Threshold (BDS = 0.6) -> Y = 240 - (0.6 / 2.5) * 190 = 194.4 */}
                      <line x1="50" y1="194.4" x2="550" y2="194.4" stroke="rgba(239, 68, 68, 0.4)" strokeDasharray="3,3" strokeWidth="1" />
                      <text x="52" y="190" fill="var(--color-red)" fontSize="7" fontWeight="bold">DRIFT ALERT THRESHOLD (BDS = 0.6)</text>

                      {/* Y-Axis Labels */}
                      <text x="42" y="44" fill="var(--text-secondary)" fontSize="8" textAnchor="end">2.5</text>
                      <text x="42" y="94" fill="var(--text-secondary)" fontSize="8" textAnchor="end">2.0</text>
                      <text x="42" y="144" fill="var(--text-secondary)" fontSize="8" textAnchor="end">1.25</text>
                      <text x="42" y="194.4" fill="var(--text-secondary)" fontSize="8" textAnchor="end">0.6</text>
                      <text x="42" y="244" fill="var(--text-secondary)" fontSize="8" textAnchor="end">0.0</text>

                      {/* X-Axis Labels (Tick every 10 weeks) */}
                      {[1, 10, 20, 30, 40, 50, 60, 72].map(w => {
                        const x = 50 + ((w - 1) / (totalWeeks - 1)) * 500;
                        return (
                          <g key={w}>
                            <line x1={x} y1="240" x2={x} y2="244" stroke="rgba(255,255,255,0.2)" />
                            <text x={x} y="254" fill="var(--text-secondary)" fontSize="8" textAnchor="middle">W{w}</text>
                          </g>
                        );
                      })}

                      {/* Training / Testing Split Marker */}
                      {/* Week 52 -> X = 50 + (51 / 71) * 500 = 409.15 */}
                      <line x1="409.15" y1="30" x2="409.15" y2="240" stroke="rgba(56, 189, 248, 0.25)" strokeDasharray="4,4" />
                      <text x="404" y="38" fill="var(--color-sky)" fontSize="7" textAnchor="end" fontWeight="bold">TRAIN SPLIT</text>
                      <text x="414" y="38" fill="var(--color-sky)" fontSize="7" textAnchor="start" fontWeight="bold">TEST SPLIT (OUT-OF-SAMPLE)</text>

                      {/* Main BDS line */}
                      <path d={pathData} fill="none" stroke={isUserMalicious(selectedUser) ? 'var(--color-red)' : 'var(--color-sky)'} strokeWidth="2" />

                      {/* Draw single highlighted dot for active selectedWeek */}
                      {activePoint && (
                        <g>
                          <line x1={activePoint.x} y1="40" x2={activePoint.x} y2="240" stroke="rgba(255,255,255,0.06)" />
                          <circle cx={activePoint.x} cy={activePoint.y} r="6" fill={isUserMalicious(selectedUser) ? 'var(--color-red)' : 'var(--color-sky)'} stroke="#ffffff" strokeWidth="2" />
                          <text x={activePoint.x + 8} y={activePoint.y - 8} fill="#ffffff" fontSize="9" fontWeight="bold" background="black">
                            W{selectedWeek}: {activePoint.val.toFixed(4)}
                          </text>
                        </g>
                      )}
                    </svg>
                  );
                })()}
              </div>

              {/* Layout for active week metrics vs historical table */}
              <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: '20px' }}>
                
                {/* Active Week Parameters */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                  <h3 style={{ fontSize: '0.95rem', color: 'var(--text-primary)', fontFamily: 'Outfit' }}>
                    📊 W{selectedWeek} Feature Signatures:
                  </h3>
                  {(() => {
                    const feats = data.raw_features[selectedUser][selectedWeek];
                    if (!feats) return <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>No data for week {selectedWeek}</div>;
                    return (
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.82rem' }}>
                        <div className="card-stat" style={{ padding: '12px' }}>
                          <div className="card-title" style={{ fontSize: '0.7rem' }}>Logins Count</div>
                          <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>{feats.login_freq}</div>
                        </div>
                        <div className="card-stat" style={{ padding: '12px' }}>
                          <div className="card-title" style={{ fontSize: '0.7rem' }}>Active Hours %</div>
                          <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>{(feats.active_hours * 100).toFixed(0)}%</div>
                        </div>
                        <div className="card-stat" style={{ padding: '12px' }}>
                          <div className="card-title" style={{ fontSize: '0.7rem' }}>Session Length</div>
                          <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>{feats.avg_session.toFixed(1)} hrs</div>
                        </div>
                        <div className="card-stat" style={{ padding: '12px' }}>
                          <div className="card-title" style={{ fontSize: '0.7rem' }}>Emails Sent</div>
                          <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>{feats.email_freq}</div>
                        </div>
                        <div className="card-stat" style={{ padding: '12px' }}>
                          <div className="card-title" style={{ fontSize: '0.7rem' }}>Lexical Diversity</div>
                          <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>{(feats.vocab_diversity * 100).toFixed(1)}%</div>
                        </div>
                        <div className="card-stat" style={{ padding: '12px' }}>
                          <div className="card-title" style={{ fontSize: '0.7rem' }}>Reply Lag</div>
                          <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>{feats.response_time.toFixed(1)} hrs</div>
                        </div>
                        <div className="card-stat" style={{ padding: '12px' }}>
                          <div className="card-title" style={{ fontSize: '0.7rem' }}>Contact range</div>
                          <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>{feats.contact_diversity}</div>
                        </div>
                        <div className="card-stat" style={{ padding: '12px' }}>
                          <div className="card-title" style={{ fontSize: '0.7rem' }}>Reciprocity</div>
                          <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>{feats.reciprocity.toFixed(2)}</div>
                        </div>
                      </div>
                    );
                  })()}
                </div>

                {/* Historical Table */}
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <h3 style={{ fontSize: '0.95rem', color: 'var(--text-primary)', marginBottom: '10px', fontFamily: 'Outfit' }}>
                    Timeline History (BDS & Activity)
                  </h3>
                  <div style={{ overflowY: 'auto', maxHeight: '180px', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                      <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-secondary)', zIndex: 1, borderBottom: '1px solid var(--border-color)' }}>
                        <tr>
                          <th style={{ padding: '6px 10px' }}>Week</th>
                          <th style={{ padding: '6px 10px' }}>BDS Drift</th>
                          <th style={{ padding: '6px 10px' }}>Logins</th>
                          <th style={{ padding: '6px 10px' }}>Daytime Ratio</th>
                          <th style={{ padding: '6px 10px' }}>Session hrs</th>
                          <th style={{ padding: '6px 10px' }}>Emails</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.weeks.map(w => {
                          const bdsVal = data.bds_timelines[selectedUser][w - 1];
                          const feats = data.raw_features[selectedUser][w];
                          return (
                            <tr 
                              key={w} 
                              onClick={() => setSelectedWeek(w)}
                              style={{ 
                                borderBottom: '1px solid rgba(255,255,255,0.02)', 
                                cursor: 'pointer',
                                background: w === selectedWeek ? 'rgba(56, 189, 248, 0.08)' : 'transparent' 
                              }}
                            >
                              <td style={{ padding: '6px 10px', fontWeight: 700, color: 'var(--color-sky)' }}>W{w}</td>
                              <td style={{ padding: '6px 10px', color: bdsVal >= 0.6 ? 'var(--color-red)' : 'var(--text-primary)', fontWeight: bdsVal >= 0.6 ? 700 : 400 }}>
                                {bdsVal.toFixed(4)}
                              </td>
                              <td style={{ padding: '6px 10px' }}>{feats.login_freq}</td>
                              <td style={{ padding: '6px 10px' }}>{(feats.active_hours * 100).toFixed(0)}%</td>
                              <td style={{ padding: '6px 10px' }}>{feats.avg_session.toFixed(1)}</td>
                              <td style={{ padding: '6px 10px' }}>{feats.email_freq}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

              </div>

            </div>
          )}

          {/* TAB 4: SIMILARITY ANALYTICS (BSI) */}
          {activeTab === 'similarity' && (
            <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '25px' }}>
              <div>
                <h2 style={{ fontSize: '1.3rem', color: 'var(--text-primary)', marginBottom: '4px' }}>
                  Dynamic Similarity Heatmap - Week {selectedWeek}
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
                  A localized 15x15 BSI cosine similarity heatmap centered on <strong>{selectedUser}</strong> and their top matches. This dynamic slicing prevents browser rendering lag.
                </p>
              </div>

              {/* Heatmap Grid & Legend */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '25px', alignItems: 'start' }}>
                
                {/* 15x15 Grid */}
                <div style={{ overflowX: 'auto' }}>
                  <table className="heatmap-table">
                    <thead>
                      <tr>
                        <th className="heatmap-hdr" style={{ width: '60px' }}></th>
                        {heatmapData.displayUsers.map(u => (
                          <th key={u} className="heatmap-hdr" style={{ fontSize: '0.72rem', transform: 'rotate(-45deg)', height: '45px', verticalAlign: 'bottom' }}>
                            {u}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {heatmapData.displayUsers.map((u1, i) => (
                        <tr key={u1}>
                          <td className="heatmap-hdr" style={{ textAlign: 'right', paddingRight: '8px', fontSize: '0.75rem', fontWeight: 700 }}>{u1}</td>
                          {heatmapData.displayUsers.map((u2, j) => {
                            const val = heatmapData.displayMatrix[i][j];
                            const isFocus = u1 === selectedUser || u2 === selectedUser;
                            return (
                              <td 
                                key={u2} 
                                className="heatmap-cell"
                                onClick={() => {
                                  setSelectedUser(u1);
                                }}
                                style={{ 
                                  backgroundColor: getHeatmapColor(val),
                                  color: val > 0.90 ? '#ffffff' : 'var(--text-primary)',
                                  fontSize: '0.72rem',
                                  padding: '10px 4px',
                                  border: isFocus ? '1px solid rgba(255, 255, 255, 0.4)' : 'none'
                                }}
                                title={`BSI between ${u1} and ${u2} in W${selectedWeek}: ${val}`}
                              >
                                {val.toFixed(3)}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Similarity sidebar */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                  
                  {/* Top matches list */}
                  <div style={{ background: 'rgba(19, 23, 32, 0.4)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px' }}>
                    <h4 style={{ fontSize: '0.85rem', color: 'var(--color-sky)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      🔗 Top Matches for {selectedUser}
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {heatmapData.displayUsers.slice(1, 6).map((u, i) => {
                        const val = heatmapData.displayMatrix[0][i+1];
                        return (
                          <div 
                            key={u} 
                            onClick={() => setSelectedUser(u)}
                            style={{ 
                              display: 'flex', 
                              justifyContent: 'space-between', 
                              padding: '8px', 
                              background: 'rgba(255,255,255,0.02)', 
                              borderRadius: '6px', 
                              fontSize: '0.8rem',
                              cursor: 'pointer'
                            }}
                          >
                            <span>{u} ({data.user_departments[u] || 'Unknown'})</span>
                            <span style={{ fontWeight: 700, color: 'var(--color-sky)' }}>{val.toFixed(4)}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Credential sharing warnings */}
                  <div style={{ background: 'rgba(19, 23, 32, 0.4)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px' }}>
                    <h4 style={{ fontSize: '0.85rem', color: 'var(--color-yellow)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      ⚠️ High Similarity Pairs (W{selectedWeek})
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '180px', overflowY: 'auto' }}>
                      {data.alerts
                        .filter(a => a.week === selectedWeek && a.type === 'yellow')
                        .map((alert, i) => (
                          <div key={i} style={{ padding: '6px', background: 'rgba(245, 158, 11, 0.05)', border: '1px solid rgba(245, 158, 11, 0.15)', borderRadius: '6px', fontSize: '0.75rem' }}>
                            {alert.desc}
                          </div>
                        ))}
                      {data.alerts.filter(a => a.week === selectedWeek && a.type === 'yellow').length === 0 && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'center', padding: '10px' }}>
                          No shared behavior collisions detected in Week {selectedWeek}.
                        </div>
                      )}
                    </div>
                  </div>

                </div>

              </div>

            </div>
          )}

          {/* TAB 5: RESEARCH RESULTS & sweeps */}
          {activeTab === 'research' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '25px' }}>
              
              {/* Layout for Tables vs Key Findings */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '25px', alignItems: 'start' }}>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '25px' }}>
                  
                  {/* Ablation study */}
                  <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)', fontFamily: 'Outfit' }}>
                      🔬 Ablation Study Results
                    </h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                      Ablative tests of the Cyber DNA features, showing how temporal drift (BDS) and anthropology metrics affect the XGBoost test split results.
                    </p>
                    <div style={{ overflowX: 'auto', background: 'rgba(19, 23, 32, 0.4)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                      <table className="metrics-table" style={{ fontSize: '0.8rem' }}>
                        <thead>
                          <tr>
                            <th>Configuration</th>
                            <th>Precision</th>
                            <th>Recall</th>
                            <th>F1-Score</th>
                            <th>AUPRC</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(data.ablation_metrics).map(([config, met]) => (
                            <tr key={config}>
                              <td style={{ fontWeight: 600 }}>{config}</td>
                              <td>{(met.prec * 100).toFixed(2)}%</td>
                              <td>{(met.rec * 100).toFixed(2)}%</td>
                              <td style={{ fontWeight: 700, color: 'var(--color-sky)' }}>{(met.f1 * 100).toFixed(2)}%</td>
                              <td>{met.auprc.toFixed(4)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Calibration Sweep */}
                  <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)', fontFamily: 'Outfit' }}>
                      🎛️ Z-score filter Calibration sweeps
                    </h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                      Joint calibration sweep of the Departmental Similarity Filter Z-score threshold at $BSI &gt; 0.85$ (13-feature XGBoost model).
                    </p>
                    <div style={{ overflowX: 'auto', background: 'rgba(19, 23, 32, 0.4)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                      <table className="metrics-table" style={{ fontSize: '0.8rem' }}>
                        <thead>
                          <tr>
                            <th>Z-Threshold</th>
                            <th>Precision</th>
                            <th>Recall</th>
                            <th>F1-Score</th>
                            <th>Suppressed</th>
                            <th>Benign Suppressed</th>
                            <th>Malicious Suppressed</th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.calibration_sweep.map(row => (
                            <tr key={row.z_threshold}>
                              <td style={{ fontWeight: 700, color: 'var(--color-sky)' }}>Z = {row.z_threshold.toFixed(1)}</td>
                              <td>{(row.precision * 100).toFixed(1)}%</td>
                              <td>{(row.recall * 100).toFixed(1)}%</td>
                              <td style={{ fontWeight: 700, color: row.z_threshold === 0.0 ? 'var(--color-green)' : 'var(--text-primary)' }}>{(row.f1 * 100).toFixed(2)}%</td>
                              <td>{row.suppressed_total}</td>
                              <td>{row.suppressed_benign}</td>
                              <td>{row.suppressed_malicious}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                </div>

                {/* Key Findings Panel */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  
                  {/* Key Findings Card */}
                  <div className="panel" style={{ borderLeft: '4px solid var(--color-sky)', padding: '20px' }}>
                    <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)', marginBottom: '12px', fontFamily: 'Outfit' }}>
                      📌 Key Findings Summary
                    </h3>
                    <ul style={{ paddingLeft: '18px', margin: 0, display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                      <li>
                        <strong style={{ color: 'var(--text-primary)' }}>BDS Drift Discrepancy:</strong> Malicious weeks exhibit significantly higher drift ($0.1898$) than benign weeks ($0.1341$).
                      </li>
                      <li>
                        <strong style={{ color: 'var(--text-primary)' }}>Anthropology Precision:</strong> Including anthropology consistency gauges ($IDP$/$BC$/$SRC$) increased precision from $20.7\%$ to <strong style={{ color: 'var(--color-green)' }}>$36.3\%$</strong>, reducing false alarms.
                      </li>
                      <li>
                        <strong style={{ color: 'var(--text-primary)' }}>Suppression Failure:</strong> Departmental Z-score filter suppressed all true alerts. Disabling it (setting BSI = 1.0) preserves F1.
                      </li>
                      <li>
                        <strong style={{ color: 'var(--text-primary)' }}>XGBoost Primacy:</strong> XGBoost achieved the best overall performance ($F_1 = 16.17\%$).
                      </li>
                    </ul>
                  </div>

                  {/* Suppression Explanation Card */}
                  <div className="panel" style={{ padding: '20px' }}>
                    <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)', marginBottom: '10px', fontFamily: 'Outfit' }}>
                      ⚠️ why suppression was disabled
                    </h3>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                      In corporate structures, different departments (software engineering, management, HR) share highly uniform baseline habits (login schedules, email volume). 
                      <br /><br />
                      This overlapping behavior makes BSI cosine similarity very high (&gt; 0.95) between any user and *any other* department centroid, rendering the Z-score filter overly permissive and suppressing legitimate threat signals.
                    </p>
                  </div>

                </div>

              </div>

              {/* Threat Case Explorer Panel */}
              <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)', fontFamily: 'Outfit' }}>
                  🔎 Threat Case Explorer
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  Deep-dive exploration of the highest-drift and highest-similarity user profiles across the entire CMU CERT evaluation split.
                </p>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
                  
                  {/* Malicious BDS */}
                  <div style={{ background: 'rgba(19, 23, 32, 0.4)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '15px' }}>
                    <h4 style={{ fontSize: '0.82rem', color: 'var(--color-red)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      🔴 Top Malicious Users (max BDS)
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '220px', overflowY: 'auto' }}>
                      {data.threat_case_explorer.top_malicious_bds.map((item, idx) => (
                        <div 
                          key={item.user} 
                          onClick={() => {
                            setSelectedUser(item.user);
                            setSelectedWeek(item.week);
                            setActiveTab('drift');
                          }}
                          style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer' }}
                        >
                          <span>{idx+1}. {item.user} (W{item.week})</span>
                          <span style={{ fontWeight: 700, color: 'var(--color-red)' }}>{item.max_bds.toFixed(3)}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Benign BDS */}
                  <div style={{ background: 'rgba(19, 23, 32, 0.4)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '15px' }}>
                    <h4 style={{ fontSize: '0.82rem', color: 'var(--color-sky)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      🟢 Top Benign Users (max BDS)
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '220px', overflowY: 'auto' }}>
                      {data.threat_case_explorer.top_benign_bds.map((item, idx) => (
                        <div 
                          key={item.user} 
                          onClick={() => {
                            setSelectedUser(item.user);
                            setSelectedWeek(item.week);
                            setActiveTab('drift');
                          }}
                          style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer' }}
                        >
                          <span>{idx+1}. {item.user} (W{item.week})</span>
                          <span style={{ fontWeight: 700, color: 'var(--color-sky)' }}>{item.max_bds.toFixed(3)}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* BSI matches */}
                  <div style={{ background: 'rgba(19, 23, 32, 0.4)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '15px' }}>
                    <h4 style={{ fontSize: '0.82rem', color: 'var(--color-yellow)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      ⚠️ Top Similarity Pairs (BSI)
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '220px', overflowY: 'auto' }}>
                      {data.threat_case_explorer.top_bsi_pairs.map((item, idx) => (
                        <div 
                          key={idx} 
                          onClick={() => {
                            setSelectedUser(item.user1);
                            setSelectedWeek(item.week);
                            setActiveTab('similarity');
                          }}
                          style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer' }}
                        >
                          <span>{idx+1}. {item.user1} &amp; {item.user2} (W{item.week})</span>
                          <span style={{ fontWeight: 700, color: 'var(--color-yellow)' }}>{item.bsi.toFixed(4)}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                </div>
              </div>

            </div>
          )}

        </main>
      </div>
    </div>
  );
}
