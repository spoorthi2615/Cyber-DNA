import React from 'react';
import { Clock } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

export default function TemporalDriftTab({ data }) {
  const driftData = data.dashboard_illustrative_data?.temporal_drift || [];

  return (
    <div className="flex flex-col gap-6">
      <div className="bg-[#8b5cf6]/10 border border-[#8b5cf6]/30 rounded p-4 text-sm text-[#8b5cf6] flex items-center justify-between">
        <span className="font-semibold">Illustrative Behavioral Drift Profile</span>
        <span className="text-xs uppercase tracking-widest text-slate-400">Derived Analyst View</span>
      </div>

      <div className="glass-panel p-6 space-y-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Clock size={20} className="text-[#8b5cf6]" />
            <h2 className="text-xl font-bold text-slate-200">Temporal Drift (BDS Evolution)</h2>
          </div>
        </div>
        
        <p className="text-sm text-slate-400 italic border-l-2 border-slate-700 pl-3">
          This chart is intended to show how benign and malicious drift trajectories may diverge conceptually over time; it is not a separately benchmarked evaluation result.
        </p>

        <div className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={driftData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
              <XAxis dataKey="week" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc' }} />
              <Legend verticalAlign="top" height={36}/>
              
              <Line 
                name="Benign Cohort Average"
                type="monotone" 
                dataKey="benign_bds" 
                stroke="#0ea5e9" 
                strokeWidth={3} 
                dot={false}
              />
              <Line 
                name="Malicious Drift Spike"
                type="monotone" 
                dataKey="malicious_bds" 
                stroke="#ef4444" 
                strokeWidth={3} 
                strokeDasharray="5 5"
                dot={{ r: 4, fill: '#ef4444', stroke: '#0f172a', strokeWidth: 2 }} 
                activeDot={{ r: 6 }} 
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
