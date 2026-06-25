import React from 'react';
import { Hexagon } from 'lucide-react';

export default function Navbar({ finalF1, baselineF1, finalPrecision, finalRecall, rawMaliciousCount, trainWeeks, testWeeks }) {
  return (
    <nav className="border-b border-slate-800 bg-[#0a0f1a]/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-[1400px] mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Hexagon size={28} className="text-[#0ea5e9] animate-[pulse_4s_ease-in-out_infinite]" />
          <div>
            <div className="text-xl font-black tracking-widest text-slate-100 flex items-center gap-2">
              CYBER DNA
            </div>
            <div className="text-[0.65rem] tracking-[0.2em] text-[#0ea5e9] uppercase font-semibold">
              Behavioral Classifier Engine
            </div>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="hidden md:flex gap-6 items-center">
          <div className="flex flex-col items-end">
            <span className="text-[0.65rem] text-slate-500 font-bold uppercase tracking-wider">Cohort Size</span>
            <span className="text-sm text-slate-300 font-mono">1,000 Users</span>
          </div>
          <div className="h-6 w-px bg-slate-800"></div>
          <div className="flex flex-col items-end">
            <span className="text-[0.65rem] text-slate-500 font-bold uppercase tracking-wider">Span</span>
            <span className="text-sm text-slate-300 font-mono">72 Weeks</span>
          </div>
          <div className="h-6 w-px bg-slate-800"></div>
          <div className="flex flex-col items-end">
            <span className="text-[0.65rem] text-slate-500 font-bold uppercase tracking-wider">Imbalance</span>
            <span className="text-sm text-[#ef4444] font-mono">0.48% Malicious</span>
          </div>
          <div className="h-6 w-px bg-slate-800"></div>
          <div className="flex flex-col items-end">
            <span className="text-[0.65rem] text-slate-500 font-bold uppercase tracking-wider">Raw Malicious Users</span>
            <span className="text-sm text-[#f59e0b] font-mono font-bold">{rawMaliciousCount}</span>
          </div>
          <div className="h-6 w-px bg-slate-800"></div>
          <div className="flex flex-col items-end">
            <span className="text-[0.65rem] text-slate-500 font-bold uppercase tracking-wider">Train / Test Weeks</span>
            <span className="text-sm text-slate-300 font-mono">{trainWeeks} / {testWeeks}</span>
          </div>
          <div className="h-6 w-px bg-slate-800"></div>
          <div className="flex flex-col items-end">
            <span className="text-[0.65rem] text-slate-500 font-bold uppercase tracking-wider">Baseline F1</span>
            <span className="text-sm text-[#0ea5e9] font-mono font-bold">{(baselineF1 * 100).toFixed(2)}%</span>
          </div>
          <div className="h-6 w-px bg-slate-800"></div>
          <div className="flex flex-col items-end">
            <span className="text-[0.65rem] text-slate-500 font-bold uppercase tracking-wider">Precision</span>
            <span className="text-sm text-[#10b981] font-mono font-bold">{(finalPrecision * 100).toFixed(2)}%</span>
          </div>
          <div className="h-6 w-px bg-slate-800"></div>
          <div className="flex flex-col items-end">
            <span className="text-[0.65rem] text-slate-500 font-bold uppercase tracking-wider">Recall</span>
            <span className="text-sm text-[#ef4444] font-mono font-bold">{(finalRecall * 100).toFixed(2)}%</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
