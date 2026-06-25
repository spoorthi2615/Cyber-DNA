import React from 'react';
import { Hexagon } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';

export default function BSISimilarityTab({ data }) {
  const bsiData = data.dashboard_illustrative_data?.bsi_distribution || [];

  return (
    <div className="flex flex-col gap-6">
      <div className="bg-[#10b981]/10 border border-[#10b981]/30 rounded p-4 text-sm text-[#10b981] flex items-center justify-between">
        <span className="font-semibold">Derived Behavioral Similarity Distribution</span>
        <span className="text-xs uppercase tracking-widest text-slate-400">Analyst Inspection View</span>
      </div>

      <div className="glass-panel p-6 space-y-6">
        <div className="flex items-center gap-2 mb-4">
          <Hexagon size={20} className="text-[#10b981]" />
          <h2 className="text-xl font-bold text-slate-200">Cohort BSI Distribution</h2>
        </div>

        <p className="text-sm text-slate-400 italic border-l-2 border-slate-700 pl-3">
          This visualization is used to illustrate how identity similarity can be inspected within the dashboard and is not part of the Phase 11 benchmark table.
        </p>

        <div className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bsiData} margin={{ top: 20, right: 30, left: 0, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
              <XAxis 
                dataKey="range" 
                stroke="#64748b" 
                tick={{ fill: '#94a3b8', fontSize: 11 }} 
                angle={-45} 
                textAnchor="end"
              />
              <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc' }}
                cursor={{ fill: '#1e293b', opacity: 0.4 }}
              />
              
              <Bar dataKey="benign_pairs" name="Benign Pairs" stackId="a" fill="#0ea5e9" radius={[0, 0, 0, 0]} />
              <Bar dataKey="malicious_pairs" name="Malicious Pairs (Collision)" stackId="a" fill="#ef4444" radius={[4, 4, 0, 0]}>
                {bsiData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.range === "0.90-1.00" || entry.range === "0.80-0.90" ? '#ef4444' : '#f59e0b'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
