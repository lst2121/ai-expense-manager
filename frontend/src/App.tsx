import { useState, useEffect } from 'react';
import { ChatSidebar } from './components/Sidebar/ChatSidebar';
import { CopilotDrawer } from './components/Copilot/CopilotDrawer';
import { SettingsModal } from './components/Settings/SettingsModal';
import { AuthModal } from './components/Auth/AuthModal';
import {
  fetchChatSessions,
  updateChatSession,
  deleteChatSession,
  getAuthHeaders,
} from './services/api';
import type { ChatSessionItem } from './services/api';

export function App() {
  const [sessions, setSessions] = useState<ChatSessionItem[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<{ id: string; email: string; full_name: string } | null>(() => {
    const isSignedOut = localStorage.getItem('nivo_signed_out') === 'true';
    if (isSignedOut) return null;
    const saved = localStorage.getItem('nivo_user');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {}
    }
    return {
      id: 'usr-lokender-2026',
      email: 'lokender@nivo.ai',
      full_name: 'Lokender Singh',
    };
  });
  const [provider, setProvider] = useState<'deepseek' | 'gemini'>('deepseek');
  const [language, setLanguage] = useState<'en' | 'hi'>('en');
  const [pendingPrompt, setPendingPrompt] = useState<string | null>(null);

  // Load chat threads from PostgreSQL
  const loadSessions = async () => {
    try {
      const list = await fetchChatSessions();
      setSessions(list);
      // If there are sessions and no active session selected, pick the most recent
      if (list.length > 0 && !activeSessionId) {
        setActiveSessionId(list[0].id);
      } else if (list.length === 0) {
        setActiveSessionId(null);
      }
    } catch (err) {
      console.error('Failed to load chat sessions:', err);
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('nivo_auth_token');
    localStorage.removeItem('nivo_user');
    localStorage.setItem('nivo_signed_out', 'true');
    setCurrentUser(null);
    setActiveSessionId(null);
    setSessions([]);
  };

  const handleLoginSuccess = (user: { id: string; email: string; full_name: string }, token: string) => {
    localStorage.removeItem('nivo_signed_out');
    setCurrentUser(user);
    localStorage.setItem('nivo_user', JSON.stringify(user));
    if (token) {
      localStorage.setItem('nivo_auth_token', token);
      localStorage.setItem('auth_token', token);
    }
    setActiveSessionId(null);
    loadSessions();
  };

  useEffect(() => {
    const verifyAuth = async () => {
      const isSignedOut = localStorage.getItem('nivo_signed_out') === 'true';
      const token = localStorage.getItem('nivo_auth_token') || localStorage.getItem('auth_token');
      if (isSignedOut && !token) {
        setCurrentUser(null);
        return;
      }
      try {
        const res = await fetch('/api/auth/me', {
          headers: getAuthHeaders(),
        });
        if (res.ok) {
          const data = await res.json();
          if (data.authenticated && data.user) {
            setCurrentUser(data.user);
            localStorage.setItem('nivo_user', JSON.stringify(data.user));
            localStorage.removeItem('nivo_signed_out');
          } else if (isSignedOut) {
            setCurrentUser(null);
          }
        }
      } catch (e) {}
    };
    verifyAuth();
    loadSessions();
  }, []);

  const handleNewChat = () => {
    setActiveSessionId(null);
    setPendingPrompt(null);
  };

  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
  };

  const handlePinSession = async (id: string, isPinned: boolean) => {
    await updateChatSession(id, { is_pinned: isPinned });
    await loadSessions();
  };

  const handleRenameSession = async (id: string, newTitle: string) => {
    await updateChatSession(id, { title: newTitle });
    await loadSessions();
  };

  const handleDeleteSession = async (id: string) => {
    await deleteChatSession(id);
    if (activeSessionId === id) {
      const remaining = sessions.filter((s) => s.id !== id);
      setActiveSessionId(remaining.length > 0 ? remaining[0].id : null);
    }
    await loadSessions();
  };

  const activeSession = sessions.find((s) => s.id === activeSessionId);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#090d16] text-slate-100 font-sans">
      {/* ChatGPT / Perplexity Collapsible Left Sidebar */}
      <ChatSidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onPinSession={handlePinSession}
        onRenameSession={handleRenameSession}
        onDeleteSession={handleDeleteSession}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onQuickAction={(prompt) => {
          setPendingPrompt(prompt);
          if (!activeSessionId && sessions.length === 0) {
            handleNewChat();
          }
        }}
        provider={provider}
        currentUser={currentUser}
        onOpenAuth={() => setIsAuthOpen(true)}
        onSignOut={handleSignOut}
      />

      {/* Main Full-Screen Generative Conversational Canvas */}
      <main className="flex-1 h-screen flex flex-col min-w-0 overflow-hidden relative">
        <CopilotDrawer
          isOpen={true}
          isStandalone={true}
          sessionId={activeSessionId}
          onSessionUpdated={loadSessions}
          onNewChat={handleNewChat}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          onOpenSettings={() => setIsSettingsOpen(true)}
          activeSessionTitle={activeSession?.title}
          provider={provider}
          setProvider={setProvider}
          language={language}
          setLanguage={setLanguage}
          initialInput={pendingPrompt}
          onSessionCreated={(newId) => setActiveSessionId(newId)}
        />
      </main>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        provider={provider}
        setProvider={setProvider}
        language={language}
        setLanguage={setLanguage}
      />

      {/* Auth & Multi-Tenancy Modal */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        currentUser={currentUser}
        onLoginSuccess={handleLoginSuccess}
        onSignOut={handleSignOut}
      />
    </div>
  );
}
export default App;
