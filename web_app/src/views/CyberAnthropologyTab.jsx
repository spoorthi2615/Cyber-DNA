import React from 'react';
import { Activity, Hexagon, Clock } from 'lucide-react';
import StatCard from '../components/ui/StatCard';

export default function CyberAnthropologyTab({ data }) {
  const idpMetrics = data.idpMetrics || { value: '94.2%', subtitle: 'Identity Distinguishability' };
  const bcMetrics = data.bcMetrics || { value: '88.7%', subtitle: 'Behavioral Consistency' };
  const srcMetrics = data.srcMetrics || { value: '91.5%', subtitle: 'Source Reliability' };

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
        <StatCard
          icon={Activity}
          title="IDP"
          value={idpMetrics.value}
          subtitle={idpMetrics.subtitle}
          iconColor="text-[#0ea5e9]"
          valueColor="text-slate-100"
        />
        <StatCard
          icon={Hexagon}
          title="BC"
          value={bcMetrics.value}
          subtitle={bcMetrics.subtitle}
          iconColor="text-[#8b5cf6]"
          valueColor="text-slate-100"
        />
        <StatCard
          icon={Clock}
          title="SRC"
          value={srcMetrics.value}
          subtitle={srcMetrics.subtitle}
          iconColor="text-[#10b981]"
          valueColor="text-slate-100"
        />
      </div>
      
      <div className="glass-panel p-6 border-slate-800">
        <h3 className="text-lg font-bold mb-4 text-slate-300">Anthropological Insights</h3>
        <p className="text-sm text-slate-400 leading-relaxed mb-4">
          The Cyber DNA framework leverages these three core metrics to continuously authenticate users. IDP (Identity Distinguishability Pattern) isolates unique user quirks. BC (Behavioral Consistency) measures the stability of those quirks over time. SRC (Source Reliability Context) validates the environmental factors of the session.
        </p>
      </div>
    </div>
  );
}
