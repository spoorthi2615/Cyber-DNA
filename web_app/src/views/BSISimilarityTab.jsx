import React from 'react';
import { Hexagon } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function BSISimilarityTab({ data }) {
  const bsiData = data.bsiData || [
    { label: 'Role Similarity', value: 45 },
    { label: 'Temporal Similarity', value: 25 },
    { label: 'Resource Similarity', value: 20 },
    { label: 'Location Similarity', value: 10 }
  ];
  
  const COLORS = ['#0ea5e9', '#10b981', '#ef4444', '#f59e0b', '#8b5cf6'];
  
  return (
    <div className="glass-panel p-6 space-y-6 mt-4">
      <div className="flex items-center gap-2 mb-4">
        <Hexagon size={20} className="text-[#8b5cf6]" />
        <h2 className="text-xl font-bold text-slate-200">BSI Similarity Breakdown</h2>
      </div>
      <div className="h-[350px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={bsiData} dataKey="value" nameKey="label" outerRadius={120} label>
              {bsiData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc' }} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
