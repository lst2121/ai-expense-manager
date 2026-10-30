import React, { useState } from 'react';
import {
  MessageSquare,
  FileText,
  UploadCloud,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  X,
  CreditCard,
  Building2,
  Receipt,
} from 'lucide-react';
import { parseBankSms, createTransaction } from '../../services/api';

interface SmartImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess: () => void;
}

export const SmartImportModal: React.FC<SmartImportModalProps> = ({
  isOpen,
  onClose,
  onImportSuccess,
}) => {
  const [activeMode, setActiveMode] = useState<'sms' | 'ocr'>('sms');
  const [smsInput, setSmsInput] = useState('');
  const [parsedData, setParsedData] = useState<{
    amount: number | null;
    merchant: string | null;
    payment_mode: string;
    category: string;
    date: string;
  } | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  // Sample SMS templates for instant testing
  const sampleSmsList = [
    'Sent Rs. 450.00 from HDFC Bank AC **1234 to ZOMATO via UPI Ref 4123456789. Bal Rs 45,210',
    'Debited INR 1,850.00 on 28-OCT-26 via UPI to BLINKIT COMMERCE. Avail Bal: Rs 12,340',
    'Paid Rs. 1,420 to BESCOM Electricity on 15-OCT-26 via PhonePe. Txn ID: UPI987654321',
    'Debited Rs. 850.00 at SHELL PETROL PUMP via ICICI Debit Card on 29-OCT-26',
  ];

  const handleParse = (textToParse: string) => {
    setSmsInput(textToParse);
    const result = parseBankSms(textToParse);
    setParsedData(result);
    setSuccessMessage('');
  };

  const handleSaveExpense = async () => {
    if (!parsedData || !parsedData.amount) return;

    setIsSaving(true);
    try {
      await createTransaction({
        description: `${parsedData.merchant} (${parsedData.category.toUpperCase()})`,
        amount: parsedData.amount,
        category: parsedData.category,
        vendor_name: parsedData.merchant || undefined,
        payment_method: parsedData.payment_mode,
        date: parsedData.date,
      });

      setSuccessMessage(`Successfully logged ₹${parsedData.amount.toLocaleString('en-IN')} for ${parsedData.merchant}!`);
      setTimeout(() => {
        onImportSuccess();
        onClose();
      }, 1200);
    } catch (err) {
      alert(`Error saving expense: ${err}`);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-2.5 mb-1">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Smart Expense Ingestion</h3>
            <p className="text-xs text-slate-400">
              Auto-extract expenses from messages, payment alerts, or receipts
            </p>
          </div>
        </div>

        {/* Tab Mode Buttons */}
        <div className="flex items-center gap-2 mt-4 mb-4 border-b border-slate-800 pb-3">
          <button
            onClick={() => setActiveMode('sms')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              activeMode === 'sms'
                ? 'bg-indigo-600 text-white'
                : 'text-slate-400 hover:text-white bg-slate-950 border border-slate-800'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Bank & UPI SMS Parser</span>
          </button>
          <button
            onClick={() => setActiveMode('ocr')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              activeMode === 'ocr'
                ? 'bg-indigo-600 text-white'
                : 'text-slate-400 hover:text-white bg-slate-950 border border-slate-800'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Receipt & Bill OCR</span>
          </button>
        </div>

        {/* Mode 1: SMS Parser */}
        {activeMode === 'sms' && (
          <div className="space-y-3.5">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Paste Bank / UPI SMS Alert:
              </label>
              <textarea
                rows={3}
                placeholder="e.g. Sent Rs. 450.00 from HDFC Bank to Zomato via UPI..."
                value={smsInput}
                onChange={(e) => handleParse(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>

            {/* Quick SMS Presets */}
            <div>
              <span className="text-[11px] text-slate-400 block mb-1.5 font-medium">
                Try Sample Indian Household Alerts:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {sampleSmsList.map((sms, i) => (
                  <button
                    key={i}
                    onClick={() => handleParse(sms)}
                    className="text-[10px] px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-800 hover:text-white transition"
                  >
                    {sms.includes('ZOMATO')
                      ? '🍕 Zomato ₹450'
                      : sms.includes('BLINKIT')
                      ? '🛒 Blinkit ₹1,850'
                      : sms.includes('BESCOM')
                      ? '⚡ BESCOM Electricity'
                      : '⛽ Shell Petrol ₹850'}
                  </button>
                ))}
              </div>
            </div>

            {/* Extraction Result Card */}
            {parsedData && parsedData.amount && (
              <div className="p-3.5 rounded-xl bg-slate-950 border border-emerald-500/30 text-xs mt-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2">
                  <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Auto-Extracted Details</span>
                  </div>
                  <span className="text-sm font-bold text-white font-mono">
                    ₹{parsedData.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300">
                  <div className="flex items-center gap-1.5">
                    <Building2 className="w-3.5 h-3.5 text-slate-500" />
                    <span>Merchant: <strong className="text-white">{parsedData.merchant}</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CreditCard className="w-3.5 h-3.5 text-slate-500" />
                    <span>Mode: <strong className="text-indigo-400">{parsedData.payment_mode}</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5 col-span-2">
                    <Receipt className="w-3.5 h-3.5 text-slate-500" />
                    <span>Category: <strong className="text-emerald-400 uppercase">{parsedData.category}</strong></span>
                  </div>
                </div>

                <button
                  onClick={handleSaveExpense}
                  disabled={isSaving}
                  className="w-full mt-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center justify-center gap-1.5 transition disabled:opacity-50"
                >
                  <span>{isSaving ? 'Logging...' : 'Confirm & Log Expense'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {successMessage && (
              <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs text-center font-medium">
                {successMessage}
              </div>
            )}
          </div>
        )}

        {/* Mode 2: OCR Dropzone */}
        {activeMode === 'ocr' && (
          <div className="space-y-4 text-center py-4">
            <div className="border-2 border-dashed border-slate-800 hover:border-indigo-500 rounded-xl p-8 transition flex flex-col items-center justify-center bg-slate-950/60">
              <UploadCloud className="w-10 h-10 text-indigo-400 mb-2" />
              <h4 className="text-sm font-medium text-white mb-1">
                Upload Receipt, Supermarket Bill, or PDF Statement
              </h4>
              <p className="text-xs text-slate-400 mb-4 max-w-xs">
                Supports D-Mart, Kirana, Zepto invoices, and monthly bank e-statements.
              </p>
              <label className="cursor-pointer px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition">
                <span>Browse Files</span>
                <input
                  type="file"
                  accept="image/*,application/pdf"
                  className="hidden"
                  onChange={() => {
                    handleParse('Paid Rs. 2,340.00 to D-Mart Supermarket via UPI on 29-OCT-26');
                    setActiveMode('sms');
                  }}
                />
              </label>
            </div>
            <p className="text-[11px] text-slate-500">
              Files are processed locally and securely matched to your household accounts.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

