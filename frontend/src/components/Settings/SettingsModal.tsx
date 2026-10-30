import React from 'react';
import { X, Cpu, Globe, ShieldCheck, Database, Sliders } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  provider: 'deepseek' | 'gemini';
  setProvider: (p: 'deepseek' | 'gemini') => void;
  language: 'en' | 'hi';
  setLanguage: (l: 'en' | 'hi') => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  provider,
  setProvider,
  language,
  setLanguage,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/80 bg-slate-950/40">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Sliders className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100">Copilot Settings</h3>
              <p className="text-[11px] text-slate-400">Model intelligence and ledger preferences</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 text-sm">
          {/* AI Provider */}
          <div>
            <label className="text-xs font-medium text-slate-300 flex items-center gap-2 mb-2">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              Intelligence Engine
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setProvider('deepseek')}
                className={`p-3 rounded-xl border text-left transition flex flex-col justify-between ${
                  provider === 'deepseek'
                    ? 'border-indigo-500/80 bg-indigo-500/10 text-slate-100 shadow-sm'
                    : 'border-slate-800 bg-slate-950/40 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="font-semibold text-xs text-white">DeepSeek Flash</span>
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">High-speed financial reasoning & code</p>
              </button>

              <button
                type="button"
                onClick={() => setProvider('gemini')}
                className={`p-3 rounded-xl border text-left transition flex flex-col justify-between ${
                  provider === 'gemini'
                    ? 'border-indigo-500/80 bg-indigo-500/10 text-slate-100 shadow-sm'
                    : 'border-slate-800 bg-slate-950/40 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="font-semibold text-xs text-white">Gemini 2.5 Flash</span>
                  <span className="w-2 h-2 rounded-full bg-sky-400"></span>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">Google multimodal & broad search</p>
              </button>
            </div>
          </div>

          {/* Primary Language */}
          <div>
            <label className="text-xs font-medium text-slate-300 flex items-center gap-2 mb-2">
              <Globe className="w-3.5 h-3.5 text-indigo-400" />
              Interface & Response Language
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setLanguage('en')}
                className={`py-2 px-3 rounded-xl border text-xs font-medium transition ${
                  language === 'en'
                    ? 'border-indigo-500 bg-indigo-500/10 text-white'
                    : 'border-slate-800 bg-slate-950/40 text-slate-400 hover:border-slate-700'
                }`}
              >
                English (Indian Rupee ₹)
              </button>
              <button
                type="button"
                onClick={() => setLanguage('hi')}
                className={`py-2 px-3 rounded-xl border text-xs font-medium transition ${
                  language === 'hi'
                    ? 'border-indigo-500 bg-indigo-500/10 text-white'
                    : 'border-slate-800 bg-slate-950/40 text-slate-400 hover:border-slate-700'
                }`}
              >
                हिन्दी / Hinglish (₹)
              </button>
            </div>
          </div>

          {/* Ledger & Security Note */}
          <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/80 space-y-2 text-xs text-slate-400">
            <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Read-Only Guard Rails Active</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              Analytical queries run strictly read-only against PostgreSQL 17 with balanced double-entry validation (SUM Debit = SUM Credit).
            </p>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
            <div className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5" />
              <span>6,455 Seeded Transactions</span>
            </div>
            <span>v2.2.0 • Standalone OS</span>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-950/60 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-sm transition"
          >
            Save & Close
          </button>
        </div>
      </div>
    </div>
  );
};
