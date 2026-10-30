import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  ArrowUpDown,
  CheckCircle2,
  Clock,
  ChevronLeft,
  ChevronRight,
  Plus,
  X,
  CreditCard,
  Building2,
} from 'lucide-react';
import { fetchTransactions, createTransaction } from '../../services/api';
import type { TransactionItem } from '../../services/api';

const CATEGORY_COLORS: Record<string, string> = {
  subscriptions: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  transportation: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  entertainment: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
  healthcare: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  utilities: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  rent: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  groceries: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  dining: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
};

interface TransactionTableProps {
  onTransactionCreated?: () => void;
}

export const TransactionTable: React.FC<TransactionTableProps> = ({ onTransactionCreated }) => {
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [limit] = useState(15);
  const [category, setCategory] = useState('all');
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');
  const [loading, setLoading] = useState(true);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newDesc, setNewDesc] = useState('');
  const [newAmount, setNewAmount] = useState('');
  const [newCategory, setNewCategory] = useState('subscriptions');
  const [newVendor, setNewVendor] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await fetchTransactions({
        page,
        limit,
        category,
        search,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setTransactions(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [page, category, sortBy, sortOrder]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadData();
  };

  const toggleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
    setPage(1);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDesc || !newAmount) return;

    setIsSubmitting(true);
    try {
      await createTransaction({
        description: newDesc,
        amount: parseFloat(newAmount),
        category: newCategory,
        vendor_name: newVendor || undefined,
      });
      setIsModalOpen(false);
      setNewDesc('');
      setNewAmount('');
      setNewVendor('');
      loadData();
      if (onTransactionCreated) onTransactionCreated();
    } catch (err) {
      alert(`Error recording transaction: ${err}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      {/* Header & Controls */}
      <div className="p-4 sm:p-5 border-b border-slate-800 flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <span>Household Expenses & Disbursements</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-normal">
              {total} Total
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Verified family payment records with automatic budget tracking
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Search bar */}
          <form onSubmit={handleSearchSubmit} className="relative flex-1 sm:w-60">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search memo, vendor..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </form>

          {/* Category Dropdown */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
              className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="all" className="bg-slate-900">All Categories</option>
              <option value="subscriptions" className="bg-slate-900">Subscriptions</option>
              <option value="transportation" className="bg-slate-900">Transportation</option>
              <option value="entertainment" className="bg-slate-900">Entertainment</option>
              <option value="healthcare" className="bg-slate-900">Healthcare</option>
              <option value="utilities" className="bg-slate-900">Utilities</option>
              <option value="rent" className="bg-slate-900">Rent</option>
              <option value="groceries" className="bg-slate-900">Groceries</option>
              <option value="dining" className="bg-slate-900">Dining</option>
            </select>
          </div>

          {/* New Transaction Button */}
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Entry</span>
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase font-medium">
              <th className="py-3 px-4 cursor-pointer hover:text-white" onClick={() => toggleSort('date')}>
                <div className="flex items-center gap-1">
                  <span>Date</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4">Description / Memo</th>
              <th className="py-3 px-4">Vendor</th>
              <th className="py-3 px-4">Category</th>
              <th className="py-3 px-4">Category Code</th>
              <th className="py-3 px-4 cursor-pointer hover:text-white text-right" onClick={() => toggleSort('total_amount')}>
                <div className="flex items-center justify-end gap-1">
                  <span>Amount</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {loading ? (
              [...Array(6)].map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td colSpan={7} className="py-4 px-4 bg-slate-900/30"></td>
                </tr>
              ))
            ) : transactions.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500">
                  No transactions match the selected filters.
                </td>
              </tr>
            ) : (
              transactions.map((tx) => {
                const catColor = CATEGORY_COLORS[tx.category.toLowerCase()] || 'bg-slate-800 text-slate-300 border-slate-700';
                return (
                  <tr key={tx.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 text-slate-300 whitespace-nowrap font-mono">
                      {tx.date}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-100">{tx.description}</div>
                      <div className="text-[11px] text-slate-500 flex items-center gap-1.5 mt-0.5">
                        <CreditCard className="w-3 h-3" />
                        <span>{tx.payment_method}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-300 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <Building2 className="w-3 h-3 text-slate-500" />
                        <span>{tx.vendor_name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-[11px] font-medium border ${catColor}`}>
                        {tx.category}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400 font-mono">
                      <span className="text-slate-300">{tx.account_code}</span>
                      <span className="text-[10px] text-slate-500 ml-1">({tx.account_name.split(' ')[0]})</span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-semibold text-slate-100 whitespace-nowrap">
                      ₹{tx.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-center whitespace-nowrap">
                      {tx.is_reconciled ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Reconciled</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] text-amber-400 font-medium">
                          <Clock className="w-3 h-3" />
                          <span>Pending</span>
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <div>
          Showing Page <span className="font-semibold text-slate-200">{page}</span> of <span className="font-semibold text-slate-200">{totalPages}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(p - 1, 1))}
            disabled={page === 1}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-950 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            <span>Previous</span>
          </button>
          <button
            onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
            disabled={page === totalPages}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-950 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <span>Next</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* New Transaction Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md p-6 shadow-2xl relative">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-base font-bold text-white mb-1">Record New Expense</h3>
            <p className="text-xs text-slate-400 mb-4">
              Instantly logs the expense and updates your family ledger and spend reports.
            </p>

            <form onSubmit={handleCreateSubmit} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Description / Memo</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. AWS Cloud Infrastructure"
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Amount (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="0.00"
                    value={newAmount}
                    onChange={(e) => setNewAmount(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
                  >
                    <option value="dining">Food & Dining (Swiggy/Zomato)</option>
                    <option value="groceries">Groceries & Ration (Blinkit/Zepto)</option>
                    <option value="utilities">Bills & Utilities (Electricity/Gas/Wi-Fi)</option>
                    <option value="transportation">Transport & Fuel (Petrol/Ola/Uber)</option>
                    <option value="rent">House Rent & Society</option>
                    <option value="healthcare">Health & Pharmacy</option>
                    <option value="entertainment">Entertainment & OTT</option>
                    <option value="subscriptions">Education & Subscriptions</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Vendor Name (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Amazon Web Services Inc."
                  value={newVendor}
                  onChange={(e) => setNewVendor(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="pt-3 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-800 text-slate-300 hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium disabled:opacity-50"
                >
                  {isSubmitting ? 'Posting...' : 'Post to Ledger'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

