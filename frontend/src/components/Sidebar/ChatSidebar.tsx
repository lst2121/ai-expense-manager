import React, { useState } from 'react';
import {
  MessageSquarePlus,
  Pin,
  Trash2,
  Edit2,
  Check,
  X,
  Settings,
  TrendingDown,
  Globe2,
  AlertCircle,
  Building,
  PanelLeftClose,
  PanelLeft,
  LogOut,
  LogIn,
} from 'lucide-react';
import type { ChatSessionItem } from '../../services/api';

interface ChatSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  sessions: ChatSessionItem[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onPinSession: (id: string, isPinned: boolean) => void;
  onRenameSession: (id: string, newTitle: string) => void;
  onDeleteSession: (id: string) => void;
  onOpenSettings: () => void;
  onQuickAction: (prompt: string) => void;
  provider: 'deepseek' | 'gemini';
  currentUser?: { id: string; email: string; full_name: string } | null;
  onOpenAuth?: () => void;
  onSignOut?: () => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  isOpen,
  onToggle,
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onPinSession,
  onRenameSession,
  onDeleteSession,
  onOpenSettings,
  onQuickAction,
  provider: _provider,
  currentUser = null,
  onOpenAuth,
  onSignOut,
}) => {
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const handleStartRename = (e: React.MouseEvent, s: ChatSessionItem) => {
    e.stopPropagation();
    setEditingSessionId(s.id);
    setEditTitle(s.title);
  };

  const handleSaveRename = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      onRenameSession(id, editTitle.trim());
    }
    setEditingSessionId(null);
  };

  const handleCancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(null);
  };

  // Chronological grouping
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const yesterdayStart = todayStart - 86400000;
  const sevenDaysStart = todayStart - 7 * 86400000;

  const pinnedSessions = sessions.filter((s) => s.is_pinned);
  const unpinnedSessions = sessions.filter((s) => !s.is_pinned);

  const todaySessions: ChatSessionItem[] = [];
  const yesterdaySessions: ChatSessionItem[] = [];
  const pastWeekSessions: ChatSessionItem[] = [];
  const olderSessions: ChatSessionItem[] = [];

  unpinnedSessions.forEach((s) => {
    const time = s.updated_at ? new Date(s.updated_at).getTime() : 0;
    if (time >= todayStart) {
      todaySessions.push(s);
    } else if (time >= yesterdayStart) {
      yesterdaySessions.push(s);
    } else if (time >= sevenDaysStart) {
      pastWeekSessions.push(s);
    } else {
      olderSessions.push(s);
    }
  });

  const renderSessionItem = (s: ChatSessionItem) => {
    const isActive = s.id === activeSessionId;
    const isEditing = s.id === editingSessionId;

    return (
      <div
        key={s.id}
        onClick={() => !isEditing && onSelectSession(s.id)}
        className={`group relative flex items-center justify-between px-3 py-2 rounded-xl text-xs transition cursor-pointer ${
          isActive
            ? 'bg-slate-800/90 text-white font-medium border border-slate-700/60 shadow-sm'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
        }`}
      >
        {isEditing ? (
          <div className="flex items-center gap-1.5 w-full" onClick={(e) => e.stopPropagation()}>
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              autoFocus
              className="w-full bg-slate-900 border border-indigo-500 rounded px-2 py-1 text-xs text-white outline-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSaveRename(e as any, s.id);
                if (e.key === 'Escape') handleCancelRename(e as any);
              }}
            />
            <button
              onClick={(e) => handleSaveRename(e, s.id)}
              className="p-1 hover:text-emerald-400 text-slate-300"
            >
              <Check className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleCancelRename}
              className="p-1 hover:text-rose-400 text-slate-300"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2 truncate pr-2">
              <span className="truncate">{s.title || 'Untitled Thread'}</span>
            </div>

            {/* Hover Actions */}
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onPinSession(s.id, !s.is_pinned);
                }}
                title={s.is_pinned ? 'Unpin' : 'Pin to top'}
                className={`p-1 rounded hover:bg-slate-700/80 transition ${
                  s.is_pinned ? 'text-indigo-400' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Pin className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={(e) => handleStartRename(e, s)}
                title="Rename thread"
                className="p-1 rounded hover:bg-slate-700/80 text-slate-400 hover:text-slate-200 transition"
              >
                <Edit2 className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(s.id);
                }}
                title="Delete thread"
                className="p-1 rounded hover:bg-slate-700/80 text-slate-400 hover:text-rose-400 transition"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </>
        )}
      </div>
    );
  };

  if (!isOpen) {
    return (
      <div className="fixed top-4 left-4 z-40">
        <button
          onClick={onToggle}
          title="Open Sidebar"
          className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 shadow-xl transition"
        >
          <PanelLeft className="w-5 h-5" />
        </button>
      </div>
    );
  }

  return (
    <aside className="w-72 h-screen flex-shrink-0 bg-slate-950 border-r border-slate-800/80 flex flex-col justify-between select-none z-40 transition-all">
      {/* Top Header */}
      <div className="p-4 border-b border-slate-900 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
            <Building className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-tight flex items-center gap-1.5">
              Nivo
              <span className="text-[10px] font-normal px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                AI
              </span>
            </h2>
            <p className="text-[10px] text-slate-400">Personal Wealth Copilot</p>
          </div>
        </div>

        <button
          onClick={onToggle}
          title="Close Sidebar"
          className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-900 rounded-lg transition"
        >
          <PanelLeftClose className="w-4 h-4" />
        </button>
      </div>

      {/* New Chat Primary Action */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full py-2.5 px-3.5 rounded-xl bg-slate-850 hover:bg-slate-800 border border-slate-700/70 text-slate-200 hover:text-white font-medium text-xs flex items-center justify-center gap-2 shadow-sm transition"
        >
          <MessageSquarePlus className="w-4 h-4 text-indigo-400" />
          <span>New Analysis / Chat</span>
        </button>
      </div>

      {/* Quick Analysis Actions */}
      <div className="px-3 py-1 space-y-1">
        <p className="px-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
          Quick Actions
        </p>
        <button
          onClick={() => onQuickAction('🔥 Roast my spending habits mercilessly! Show my worst impulse buys and dining addictions')}
          className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs text-amber-300 hover:text-amber-200 hover:bg-amber-500/10 transition text-left"
        >
          <span className="text-sm">🔥</span>
          <span className="truncate font-medium">Roast My Spending</span>
        </button>
        <button
          onClick={() => onQuickAction('Audit my unreconciled expenses and find discrepancies')}
          className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs text-slate-300 hover:text-white hover:bg-slate-900/80 transition text-left"
        >
          <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
          <span className="truncate">Audit Unreconciled</span>
        </button>
        <button
          onClick={() => onQuickAction('Calculate my monthly burn rate and spending trajectory for 2026')}
          className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs text-slate-300 hover:text-white hover:bg-slate-900/80 transition text-left"
        >
          <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
          <span className="truncate">Monthly Burn Rate</span>
        </button>
        <button
          onClick={() => onQuickAction('What are current inflation trends and RBI repo rates in India?')}
          className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs text-slate-300 hover:text-white hover:bg-slate-900/80 transition text-left"
        >
          <Globe2 className="w-3.5 h-3.5 text-sky-400" />
          <span className="truncate">Market & Inflation</span>
        </button>
      </div>

      {/* Sessions Scrollable Feed */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-4 custom-scrollbar">
        {/* Pinned Section */}
        {pinnedSessions.length > 0 && (
          <div className="space-y-1">
            <p className="px-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1">
              <Pin className="w-3 h-3 text-indigo-400" />
              Pinned
            </p>
            {pinnedSessions.map(renderSessionItem)}
          </div>
        )}

        {/* Chronological Sections */}
        {todaySessions.length > 0 && (
          <div className="space-y-1">
            <p className="px-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
              Today
            </p>
            {todaySessions.map(renderSessionItem)}
          </div>
        )}

        {yesterdaySessions.length > 0 && (
          <div className="space-y-1">
            <p className="px-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
              Yesterday
            </p>
            {yesterdaySessions.map(renderSessionItem)}
          </div>
        )}

        {pastWeekSessions.length > 0 && (
          <div className="space-y-1">
            <p className="px-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
              Previous 7 Days
            </p>
            {pastWeekSessions.map(renderSessionItem)}
          </div>
        )}

        {olderSessions.length > 0 && (
          <div className="space-y-1">
            <p className="px-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
              Older
            </p>
            {olderSessions.map(renderSessionItem)}
          </div>
        )}

        {sessions.length === 0 && (
          <div className="p-4 text-center text-slate-600 text-xs">
            No past conversations yet. Ask your copilot anything above!
          </div>
        )}
      </div>

      {/* Bottom User Profile & Settings */}
      <div className="p-3 border-t border-slate-900 bg-slate-950/60">
        {currentUser ? (
          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-900/60 border border-slate-800/60 gap-1.5">
            <div
              onClick={onOpenAuth}
              className="flex items-center gap-2.5 cursor-pointer hover:opacity-80 transition flex-1 min-w-0"
              title="Click to manage account / profile"
            >
              <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-xs font-bold text-indigo-300 flex-shrink-0">
                {currentUser.full_name
                  .split(' ')
                  .map((n) => n[0])
                  .join('')
                  .slice(0, 2)
                  .toUpperCase()}
              </div>
              <div className="truncate">
                <p className="text-xs font-semibold text-slate-200 truncate">{currentUser.full_name}</p>
                <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                  <span>Household Ledger • Active</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-0.5 flex-shrink-0">
              <button
                onClick={onOpenSettings}
                title="Copilot Settings"
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
              >
                <Settings className="w-4 h-4" />
              </button>
              <button
                onClick={onSignOut}
                title="Sign Out"
                data-testid="sidebar-signout-btn"
                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 rounded-lg transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-900/60 border border-slate-800/60 gap-2">
            <div
              onClick={onOpenAuth}
              className="flex items-center gap-2.5 cursor-pointer hover:opacity-80 transition flex-1 min-w-0"
              title="Click to sign in"
            >
              <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-400 flex-shrink-0">
                <LogIn className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="truncate">
                <p className="text-xs font-semibold text-slate-200">Sign In</p>
                <p className="text-[10px] text-slate-400">Private ledger access</p>
              </div>
            </div>

            <button
              onClick={onOpenAuth}
              title="Sign In"
              data-testid="sidebar-signin-btn"
              className="px-2.5 py-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 rounded-lg transition flex items-center gap-1"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Login</span>
            </button>
          </div>
        )}
      </div>
    </aside>
  );
};
