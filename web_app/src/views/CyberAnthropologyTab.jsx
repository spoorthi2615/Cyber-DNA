import React from 'react';
import { Activity, Hexagon, Clock } from 'lucide-react';
import StatCard from '../components/ui/StatCard';

export default function CyberAnthropologyTab({ data }) {
  // Use the verified baseline thresholds directly from the dashboard_illustrative_data
  const metrics = data.dashboard_illustrative_data?.anthropology_summary || {
    idp: { benign_threshold: '≥ 0.90', malicious_threshold: '< 0.75' },
    bc:  { benign_threshold: '≥ 0.90', malicious_threshold: '< 0.70' },
    src: { benign_threshold: 'High', malicious_threshold: 'Low' }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Disclaimer / Label for clarity */}
      <div className="bg-[#0ea5e9]/10 border border-[#0ea5e9]/30 rounded p-4 text-sm text-[#0ea5e9] flex items-center justify-between">
        <span className="font-semibold">Verified Benchmark Interpretation</span>
        <span className="text-xs uppercase tracking-widest text-slate-400">Cyber DNA Final Report</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          icon={Activity}
          title="Identity Persistence (IDP)"
          value={metrics.idp.benign_threshold}
          subtitle={`Malicious Drop: ${metrics.idp.malicious_threshold}`}
          iconColor="text-[#0ea5e9]"
          valueColor="text-slate-100"
        />
        <StatCard
          icon={Hexagon}
          title="Behavioral Continuity (BC)"
          value={metrics.bc.benign_threshold}
          subtitle={`Malicious Drop: ${metrics.bc.malicious_threshold}`}
          iconColor="text-[#8b5cf6]"
          valueColor="text-slate-100"
        />
        <StatCard
          icon={Clock}
          title="Social Role Consistency (SRC)"
          value={metrics.src.definition || "Context Monitor"}
          subtitle="Measures Role Isolation"
          iconColor="text-[#10b981]"
          valueColor="text-slate-100"
        />
      </div>
      
      <div className="glass-panel p-6 border-slate-800">
        <h3 className="text-lg font-bold mb-4 text-slate-300">Anthropological Insights</h3>
        <p className="text-sm text-slate-400 leading-relaxed mb-4">
          The Phase 11 evaluation verified that benign users maintain high Identity Persistence (IDP) and Behavioral Continuity (BC). Conversely, malicious actors display a marked transition shock during active attack phases, significantly dropping their scores and distinguishing them from normal operations. Social Role Consistency (SRC) validates these environmental deviations.
        </p>
        <p className="text-sm text-slate-400 italic border-l-2 border-slate-700 pl-3">
          Thresholds shown here are documented benchmark criteria from the Cyber Anthropology evaluation design and are used to interpret user stability patterns; they are not separate Phase 11 cohort-average outputs.
        </p>
      </div>
    </div>
  );
}
