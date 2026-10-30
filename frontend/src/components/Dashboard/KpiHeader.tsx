import React from 'react';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Layers,
  PieChart,
  Wallet,
  Receipt,
} from 'lucide-react';
import type { KpiData } from '../../services/api';

interface KpiHeaderProps {
  kpis: KpiData | null;
  loading: boolean;
}

export const KpiHeader: React.FC<KpiHeaderProps> = ({ kpis, loading }) => {
  if (loading || !kpis) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 rounded-xl bg-slate-900/60 border border-slate-800 animate-pulse p-4" />
        ))}
      </div>
    );
  }

  const isPositiveVariance = kpis.monthly_variance >= 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* 1. Total Spend */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Spend (YTD)</span>
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400">
            <DollarSign className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-white tracking-tight">
            ₹{kpis.total_spend.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className="flex items-center gap-1.5 mt-1.5 text-xs text-slate-400">
            <Receipt className="w-3.5 h-3.5 text-slate-500" />
            <span>{kpis.total_transactions} verified payments</span>
          </div>
        </div>
      </div>

      {/* 2. Monthly Variance */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Monthly Variance</span>
          <div
            className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              isPositiveVariance ? 'bg-amber-500/10 text-amber-400' : 'bg-emerald-500/10 text-emerald-400'
            }`}
          >
            {isPositiveVariance ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          </div>
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-white tracking-tight">
            {isPositiveVariance ? `+${kpis.monthly_variance}%` : `${kpis.monthly_variance}%`}
          </div>
          <div className="flex items-center gap-1.5 mt-1.5 text-xs text-slate-400">
            <span>Vs. prior closing month</span>
          </div>
        </div>
      </div>

      {/* 3. Monthly Burn Rate */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Monthly Burn Rate</span>
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400">
            <Wallet className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-white tracking-tight">
            ₹{kpis.burn_rate.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className="flex items-center gap-1.5 mt-1.5 text-xs text-slate-400">
            <span>Avg ₹{kpis.average_transaction.toFixed(2)} / tx</span>
          </div>
        </div>
      </div>

      {/* 4. Top Category & Accounts */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Primary Outflow</span>
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
            <PieChart className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-emerald-400 tracking-tight truncate">
            {kpis.top_category}
          </div>
          <div className="flex items-center gap-1.5 mt-1.5 text-xs text-slate-400">
            <Layers className="w-3.5 h-3.5 text-slate-500" />
            <span>Across {kpis.active_accounts} expense categories</span>
          </div>
        </div>
      </div>
    </div>
  );
};

