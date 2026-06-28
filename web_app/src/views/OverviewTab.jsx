import React from 'react';
import { Users, Clock, AlertTriangle, Crosshair } from 'lucide-react';
import StatCard from '../components/ui/StatCard';

export default function OverviewTab({ baseline, final }) {
  return (
    <div className="flex flex-col gap-6">
      {/* Stat Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          icon={Users} title="Cohort Users" value="1,000" subtitle="Profiled CERT employees" 
          iconColor="text-[#0ea5e9]" valueColor="text-slate-100" 
        />
        <StatCard 
          icon={Clock} title="User-Weeks Logged" value="67,167" subtitle="18-month behavior logs" 
          iconColor="text-[#8b5cf6]" valueColor="text-slate-100" 
        />
        <StatCard 
          icon={AlertTriangle} title="Threat Incidence" value="322" subtitle="Target alert weeks (0.48%)" 
          iconColor="text-[#ef4444]" valueColor="text-[#ef4444]" 
        />
        <StatCard 
          icon={Crosshair} title="Final Model F1" value={`${(final.f1 * 100).toFixed(2)}%`} subtitle="Leakage-Free Validation" 
          iconColor="text-[#10b981]" valueColor="text-glow-success" borderClass="border-[#10b981]/30"
        />
      </div>

      {/* Main Compare Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-2">
        <div className="glass-panel p-8">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-8 h-8 rounded bg-slate-800 flex items-center justify-center text-slate-400 font-bold">A</div>
            <h3 className="text-xl font-bold text-slate-200">Baseline Verified</h3>
          </div>
          
          <div className="grid grid-cols-2 gap-8">
            <div>
              <div className="text-xs font-bold text-slate-500 tracking-widest mb-2">F1-SCORE</div>
              <div className="text-3xl font-black text-slate-300">{(baseline.f1 * 100).toFixed(2)}%</div>
            </div>
            <div>
              <div className="text-xs font-bold text-slate-500 tracking-widest mb-2">RECALL</div>
              <div className="text-3xl font-black text-slate-300">{(baseline.recall * 100).toFixed(2)}%</div>
            </div>
            <div>
              <div className="text-xs font-bold text-slate-500 tracking-widest mb-2">PRECISION</div>
              <div className="text-2xl font-bold text-slate-400">{(baseline.precision * 100).toFixed(2)}%</div>
            </div>
            <div>
              <div className="text-xs font-bold text-slate-500 tracking-widest mb-2">AUPRC</div>
              <div className="text-2xl font-bold text-slate-400">{baseline.auprc.toFixed(4)}</div>
            </div>
          </div>
          
          <div className="mt-8 pt-6 border-t border-slate-800 text-sm text-slate-400">
            <span className="font-mono">TP:{baseline.tp} | FP:{baseline.fp} | FN:{baseline.fn}</span> &bull; {baseline.num_features} Features
          </div>
        </div>

        <div className="glass-panel p-8 border-[#0ea5e9]/30 bg-gradient-to-br from-[#111827] to-[#0ea5e9]/10 relative">
          <div className="absolute top-0 right-0 w-64 h-64 bg-[#0ea5e9]/10 rounded-full blur-[80px] -mr-10 -mt-10 pointer-events-none"></div>
          
          <div className="flex items-center gap-3 mb-8 relative z-10">
            <div className="w-8 h-8 rounded bg-[#0ea5e9] flex items-center justify-center text-white font-bold shadow-[0_0_15px_rgba(14,165,233,0.5)]">E</div>
            <h3 className="text-xl font-bold text-white">Full Phase 11 <span className="text-[#0ea5e9] text-sm ml-2 px-2 py-1 bg-[#0ea5e9]/10 rounded border border-[#0ea5e9]/30 uppercase tracking-widest">Final</span></h3>
          </div>
          
          <div className="grid grid-cols-2 gap-8 relative z-10">
            <div>
              <div className="text-xs font-bold text-[#0ea5e9] tracking-widest mb-2">F1-SCORE</div>
              <div className="text-3xl font-black text-glow-primary">{(final.f1 * 100).toFixed(2)}%</div>
            </div>
            <div>
              <div className="text-xs font-bold text-[#0ea5e9] tracking-widest mb-2">RECALL</div>
              <div className="text-3xl font-black text-glow-primary">{(final.recall * 100).toFixed(2)}%</div>
            </div>
            <div>
              <div className="text-xs font-bold text-slate-400 tracking-widest mb-2">PRECISION</div>
              <div className="text-2xl font-bold text-slate-300">{(final.precision * 100).toFixed(2)}%</div>
            </div>
            <div>
              <div className="text-xs font-bold text-slate-400 tracking-widest mb-2">AUPRC</div>
              <div className="text-2xl font-bold text-slate-300">{final.auprc.toFixed(4)}</div>
            </div>
          </div>
          
          <div className="mt-8 pt-6 border-t border-[#0ea5e9]/20 text-sm text-[#0ea5e9] relative z-10">
            <span className="font-mono">TP:{final.tp} | FP:{final.fp} | FN:{final.fn}</span> &bull; {final.num_features} Features
          </div>
        </div>
      </div>
    </div>
  );
}
