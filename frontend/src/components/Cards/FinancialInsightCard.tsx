import React, { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Database,
  ArrowRight,
  Copy,
  Check,
  Info,
} from 'lucide-react';

export interface FinancialInsightData {
  title: string;
  status: 'unverified' | 'audited' | 'projected' | 'warning';
  status_label?: string;
  metric?: string;
  metric_label?: string;
  findings: string[];
  recommended_action?: {
    label: string;
    payload?: string;
  };
  calculation?: {
    formula?: string;
    accounts_involved?: string[];
    sql_query?: string;
    execution_time_ms?: number;
    notes?: string;
  };
}

interface FinancialInsightCardProps {
  data: FinancialInsightData;
  onAction?: (actionText: string) => void;
}

export const FinancialInsightCard: React.FC<FinancialInsightCardProps> = ({
  data,
  onAction,
}) => {
  const [isCalculationsOpen, setIsCalculationsOpen] = useState(false);
  const [hasCopiedSql, setHasCopiedSql] = useState(false);

  const getStatusStyle = () => {
    switch (data.status) {
      case 'unverified':
        return {
          badge: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
          border: 'border-amber-500/30',
          bg: 'bg-amber-950/20',
          icon: <ShieldAlert className="w-4 h-4 text-amber-400" />,
          defaultLabel: 'Verification Required',
        };
      case 'audited':
        return {
          badge: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
          border: 'border-emerald-500/30',
          bg: 'bg-emerald-950/20',
          icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
          defaultLabel: 'Audited & Verified',
        };
      case 'warning':
        return {
          badge: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
          border: 'border-rose-500/30',
          bg: 'bg-rose-950/20',
          icon: <AlertTriangle className="w-4 h-4 text-rose-400" />,
          defaultLabel: 'Attention Needed',
        };
      case 'projected':
      default:
        return {
          badge: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
          border: 'border-sky-500/30',
          bg: 'bg-sky-950/20',
          icon: <TrendingUp className="w-4 h-4 text-sky-400" />,
          defaultLabel: 'Projection Estimate',
        };
    }
  };

  const statusStyle = getStatusStyle();

  const handleCopySql = () => {
    if (data.calculation?.sql_query) {
      navigator.clipboard.writeText(data.calculation.sql_query);
      setHasCopiedSql(true);
      setTimeout(() => setHasCopiedSql(false), 2000);
    }
  };

  return (
    <div
      className={`rounded-2xl border ${statusStyle.border} ${statusStyle.bg} bg-slate-900/90 backdrop-blur-md p-4 sm:p-5 shadow-xl space-y-4 transition-all`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-slate-800/80 border border-slate-700/60 shadow-sm">
            {statusStyle.icon}
          </div>
          <div>
            <h3 className="font-semibold text-white text-sm tracking-tight">{data.title}</h3>
            <span
              className={`inline-block mt-1 px-2.5 py-0.5 rounded-full text-[10px] font-medium border ${statusStyle.badge}`}
            >
              {data.status_label || statusStyle.defaultLabel}
            </span>
          </div>
        </div>

        {data.metric && (
          <div className="text-right">
            <div className="text-base sm:text-lg font-bold text-white tracking-tight">
              {data.metric}
            </div>
            {data.metric_label && (
              <div className="text-[10px] text-slate-400 uppercase tracking-wider">
                {data.metric_label}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Key Findings */}
      {data.findings && data.findings.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <div className="text-[11px] font-medium text-slate-300 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-indigo-400" />
            <span>Key Ledger Findings:</span>
          </div>
          <ul className="space-y-1.5 pl-2 text-xs text-slate-300">
            {data.findings.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">•</span>
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommended Action */}
      {data.recommended_action && (
        <div className="pt-2 flex items-center justify-between gap-3 border-t border-slate-800/80">
          <div className="text-[11px] text-slate-400">
            Recommended Next Step:
          </div>
          <button
            onClick={() => onAction && onAction(data.recommended_action?.payload || data.recommended_action?.label || '')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-md shadow-indigo-600/20 transition transform active:scale-95"
          >
            <span>{data.recommended_action.label}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Expandable "How this was calculated" SQL Evidence Accordion */}
      {data.calculation && (
        <div className="pt-2 border-t border-slate-800/60">
          <button
            type="button"
            onClick={() => setIsCalculationsOpen(!isCalculationsOpen)}
            className="w-full flex items-center justify-between text-[11px] font-medium text-slate-400 hover:text-slate-200 transition py-1"
          >
            <div className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-indigo-400" />
              <span>How this was calculated (Double-Entry Ledger Audit)</span>
            </div>
            {isCalculationsOpen ? (
              <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            )}
          </button>

          {isCalculationsOpen && (
            <div className="mt-2.5 p-3 rounded-xl bg-slate-950/90 border border-slate-800 space-y-2.5 text-xs animate-fade-in font-mono">
              {data.calculation.formula && (
                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-0.5">
                    Accounting Formula
                  </div>
                  <div className="text-slate-200 text-[11px] bg-slate-900 px-2.5 py-1.5 rounded-lg border border-slate-800/80">
                    {data.calculation.formula}
                  </div>
                </div>
              )}

              {data.calculation.accounts_involved && data.calculation.accounts_involved.length > 0 && (
                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">
                    Chart of Accounts Involved
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {data.calculation.accounts_involved.map((acc, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded-md bg-slate-800/80 text-slate-300 border border-slate-700/50 text-[10px]"
                      >
                        {acc}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {data.calculation.sql_query && (
                <div>
                  <div className="flex items-center justify-between text-[10px] text-slate-400 uppercase tracking-wider mb-1">
                    <span>Ledger SQL Verification</span>
                    <button
                      type="button"
                      onClick={handleCopySql}
                      className="inline-flex items-center gap-1 text-[10px] text-slate-400 hover:text-white hover:underline lowercase font-sans"
                    >
                      {hasCopiedSql ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-400" />
                          <span className="text-emerald-400">copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>copy sql</span>
                        </>
                      )}
                    </button>
                  </div>
                  <pre className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-[10.5px] text-slate-300 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                    <code>{data.calculation.sql_query}</code>
                  </pre>
                </div>
              )}

              <div className="flex items-center justify-between pt-1 text-[10px] text-slate-500 font-sans border-t border-slate-900">
                <span>PostgreSQL 17 • Verified Double-Entry Balance</span>
                {data.calculation.execution_time_ms !== undefined && (
                  <span>Runtime: {data.calculation.execution_time_ms} ms</span>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
