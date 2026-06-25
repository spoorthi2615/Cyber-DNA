import React, { useState } from 'react';
import { Activity, Beaker, FileSearch, Terminal, Hexagon } from 'lucide-react';
import data from './cyber_dna_data.json';

// Components
import Navbar from './components/layout/Navbar';
import OverviewTab from './views/OverviewTab';
import AblationTab from './views/AblationTab';
import FeatureImportanceTab from './views/FeatureImportanceTab';
import ResearchResultsTab from './views/ResearchResultsTab';
import CyberAnthropologyTab from './views/CyberAnthropologyTab';
import TemporalDriftTab from './views/TemporalDriftTab';
import BSISimilarityTab from './views/BSISimilarityTab';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');

  const { final_summary, baseline_vs_final, ablation_results, feature_importance, key_findings } = data;
  const { baseline, final } = baseline_vs_final;
  // Additional stats for header
  const rawMaliciousCount = 70;
  const trainWeeks = 49867;
  const testWeeks = 17300;
  
  // Format data for Recharts
  const chartData = ablation_results.map(row => ({
    name: row.configuration.replace('Baseline + ', '+ ').replace('Expanded Cyber DNA Model', 'Final'),
    Precision: parseFloat((row.precision * 100).toFixed(2)),
    F1: parseFloat((row.f1 * 100).toFixed(2)),
    Recall: parseFloat((row.recall * 100).toFixed(2))
  }));

  return (
    <div className="min-h-screen bg-cyber-bg pb-12">
      <Navbar finalF1={final.f1} baselineF1={baseline.f1} finalPrecision={final.precision} finalRecall={final.recall} rawMaliciousCount={rawMaliciousCount} trainWeeks={trainWeeks} testWeeks={testWeeks} />

      <div className="max-w-[1400px] mx-auto px-6 mt-8">
        {/* Navigation Tabs */}
        <div className="flex overflow-x-auto mb-8 border-b border-slate-800">
          <button className={`nav-tab ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}
            >
              <Activity size={18} /> Overview
            </button>
            <button className={`nav-tab ${activeTab === 'ablation' ? 'active' : ''}`} onClick={() => setActiveTab('ablation')}
            >
              <Beaker size={18} /> Ablation Study
            </button>
            <button className={`nav-tab ${activeTab === 'features' ? 'active' : ''}`} onClick={() => setActiveTab('features')}
            >
              <FileSearch size={18} /> Feature Importance
            </button>
            <button className={`nav-tab ${activeTab === 'research' ? 'active' : ''}`} onClick={() => setActiveTab('research')}
            >
              <Terminal size={18} /> Research Results
            </button>
            <button className={`nav-tab ${activeTab === 'anthropology' ? 'active' : ''}`} onClick={() => setActiveTab('anthropology')}
            >
              <Hexagon size={18} /> Cyber Anthropology
            </button>
            <button className={`nav-tab ${activeTab === 'drift' ? 'active' : ''}`} onClick={() => setActiveTab('drift')}
            >
              <Activity size={18} /> Temporal Drift
            </button>
            <button className={`nav-tab ${activeTab === 'bsi' ? 'active' : ''}`} onClick={() => setActiveTab('bsi')}
            >
              <FileSearch size={18} /> BSI Similarity
            </button>
        </div>

        <main className="fade-in-up">
          {activeTab === 'overview' && (
            <OverviewTab baseline={baseline} final={final} />
          )}

          {activeTab === 'ablation' && (
            <AblationTab ablation_results={ablation_results} baseline={baseline} final={final} chartData={chartData} />
          )}

          {activeTab === 'features' && (
            <FeatureImportanceTab feature_importance={feature_importance} />
          )}

          {activeTab === 'research' && (
            <ResearchResultsTab final={final} key_findings={key_findings} />
          )}

          {activeTab === 'anthropology' && (
            <CyberAnthropologyTab data={data} />
          )}

          {activeTab === 'drift' && (
            <TemporalDriftTab data={data} />
          )}

          {activeTab === 'bsi' && (
            <BSISimilarityTab data={data} />
          )}
        </main>
      </div>
    </div>
  );
}
