import React from 'react';
import { Clock } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function TemporalDriftTab({ data }) {
  const driftData = data.driftData || [
    { week: 'W1', value: 10 },
    { week: 'W10', value: 30 },
    { week: 'W20', value: 45 },
    { week: 'W30', value: 60 }
  ];

  return (
    <div className="glass-panel p-6 space-y-6 mt-4">
      <div className="flex items-center gap-2 mb-4">
        <Clock size={20} className="text-[#0ea5e9]" />
        <h2 className="text-xl font-bold text-slate-200">Temporal Drift (BDS Evolution)</h2>
      </div>
      <div className="h-[350px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={driftData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
            <XAxis dataKey="week" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
            <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} domain={[0, 100]} tickFormatter={val => `${val}%`} />
            <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc' }} />
            <Line type="monotone" dataKey="value" stroke="#0ea5e9" strokeWidth={3} dot={{ r: 4, fill: '#0ea5e9', stroke: '#0f172a', strokeWidth: 2 }} activeDot={{ r: 6 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
