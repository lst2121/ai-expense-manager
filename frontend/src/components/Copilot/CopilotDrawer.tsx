import { useState, useRef, useEffect } from 'react';
import {
  Bot,
  Send,
  X,
  Sparkles,
  CheckCircle,
  Plus,
  Check,
  Languages,
  Paperclip,
  Camera,
  FileText,
  CheckCircle2,
  ArrowRight,
  Receipt,
  Tag,
  Calendar,
  CreditCard,
  Copy,
  ThumbsUp,
  ThumbsDown,
  Download,
  Table as TableIcon,
  PanelLeft,
  Settings,
  ChevronDown,
  Edit2,
  Bell,
  BellRing,
  AlertTriangle,
  ShieldCheck,
} from 'lucide-react';
import {
  streamCopilotChat,
  createTransaction,
  ingestDocument,
  fetchDynamicSuggestions,
  submitChatFeedback,
  fetchSessionDetail,
  fetchNotifications,
  dismissNotification,
} from '../../services/api';
import type { ChartSpec, ExpenseIntent, FinancialInsightData, AppNotification } from '../../services/api';
import { RechartsCard } from '../Charts/RechartsCard';
import { FinancialInsightCard } from '../Cards/FinancialInsightCard';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  toolsUsed?: Array<{ tool: string; status: 'running' | 'done'; input?: any }>;
  chartSpec?: ChartSpec;
  intent?: ExpenseIntent;
  intentAdded?: boolean;
  intentDismissed?: boolean;
  isEditingIntent?: boolean;
  financialInsight?: FinancialInsightData;
  receiptWidget?: {
    vendor_name: string;
    date: string;
    total_amount: number;
    payment_method: string;
    category: string;
    confidence_score?: number;
    invoice_number?: string;
  };
  receiptAdded?: boolean;
  isStreaming?: boolean;
  userQuery?: string;
  feedbackGiven?: 'thumbs_up' | 'thumbs_down';
}

export interface CopilotDrawerProps {
  isOpen?: boolean;
  onClose?: () => void;
  onTransactionLogged?: () => void;
  isStandalone?: boolean;
  sessionId?: string | null;
  onSessionUpdated?: () => void;
  onNewChat?: () => void;
  isSidebarOpen?: boolean;
  onToggleSidebar?: () => void;
  onOpenSettings?: () => void;
  activeSessionTitle?: string;
  provider?: 'deepseek' | 'gemini';
  setProvider?: (p: 'deepseek' | 'gemini') => void;
  language?: 'en' | 'hi';
  setLanguage?: (l: 'en' | 'hi') => void;
  initialInput?: string | null;
  onSessionCreated?: (id: string) => void;
}

const AVAILABLE_EXPENSE_CATEGORIES = [
  'dining',
  'groceries',
  'shopping',
  'home & furniture',
  'electronics',
  'transportation',
  'utilities',
  'healthcare',
  'entertainment',
  'rent',
  'general',
];

const AVAILABLE_PAYMENT_METHODS = [
  'UPI',
  'Cash',
  'Credit Card',
  'Debit Card',
  'Net Banking',
];

export const CopilotDrawer: React.FC<CopilotDrawerProps> = ({
  isOpen = true,
  onClose,
  onTransactionLogged,
  isStandalone = true,
  sessionId = null,
  onSessionUpdated,
  onNewChat,
  isSidebarOpen = true,
  onToggleSidebar,
  onOpenSettings,
  activeSessionTitle,
  provider: externalProvider,
  setProvider: externalSetProvider,
  language: externalLanguage,
  setLanguage: externalSetLanguage,
  initialInput,
  onSessionCreated,
}) => {
  const [internalLanguage, setInternalLanguage] = useState<'en' | 'hi'>('en');
  const language = externalLanguage ?? internalLanguage;
  const setLanguage = externalSetLanguage ?? setInternalLanguage;

  const [internalProvider, setInternalProvider] = useState<'deepseek' | 'gemini'>('deepseek');
  const provider = externalProvider ?? internalProvider;
  const setProvider = externalSetProvider ?? setInternalProvider;

  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);
  const modelDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modelDropdownRef.current && !modelDropdownRef.current.contains(event.target as Node)) {
        setIsModelDropdownOpen(false);
      }
    };
    if (isModelDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isModelDropdownOpen]);

  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      content:
        "Hi! I'm Nivo, your personal wealth copilot. Ask me about your monthly spending, 2026 expense projections, category breakdowns, or upload your bank statements and bills!",
    },
  ]);
  const [input, setInput] = useState('');

  useEffect(() => {
    if (initialInput) {
      setInput(initialInput);
    }
  }, [initialInput]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(sessionId);

  const [dynamicSuggestions, setDynamicSuggestions] = useState<string[]>([]);
  const [expandedToolMsgIds, setExpandedToolMsgIds] = useState<Set<string>>(new Set());
  const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);
  const [activeFeedbackMsgId, setActiveFeedbackMsgId] = useState<string | null>(null);

  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const notifDropdownRef = useRef<HTMLDivElement>(null);

  const loadNotifications = async () => {
    try {
      const res = await fetchNotifications();
      setNotifications(res.notifications || []);
    } catch (e) {}
  };

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutsideNotif = (event: MouseEvent) => {
      if (notifDropdownRef.current && !notifDropdownRef.current.contains(event.target as Node)) {
        setIsNotifOpen(false);
      }
    };
    if (isNotifOpen) {
      document.addEventListener('mousedown', handleClickOutsideNotif);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutsideNotif);
    };
  }, [isNotifOpen]);

  const handleDismissNotif = async (notifId: string) => {
    await dismissNotification(notifId);
    setNotifications((prev) => prev.filter((n) => n.id !== notifId));
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const activeStreamSessionIdRef = useRef<string | null>(null);
  const isStreamingRef = useRef(isStreaming);
  useEffect(() => {
    isStreamingRef.current = isStreaming;
  }, [isStreaming]);

  // Restore session messages from PostgreSQL when sessionId changes
  useEffect(() => {
    if (!sessionId) {
      setThreadId(null);
      activeStreamSessionIdRef.current = null;
      setMessages([
        {
          id: 'welcome',
          sender: 'assistant',
          content:
            language === 'hi'
              ? 'नमस्ते! मैं निवो (Nivo) हूँ, आपका पर्सनल वेल्थ कोपायलट। मुझसे अपने मासिक बजट, 2026 के खर्चों के रुझान या बैंक स्टेटमेंट के बारे में पूछें!'
              : "Hi! I'm Nivo, your personal wealth copilot. Ask me about your monthly spending, 2026 expense projections, category breakdowns, or upload your bank statements and bills!",
        },
      ]);
      return;
    }

    // Guard against race conditions: If this sessionId change was triggered by our own active streaming session, do not wipe!
    if (activeStreamSessionIdRef.current === sessionId || (isStreamingRef.current && threadId === sessionId)) {
      setThreadId(sessionId);
      return;
    }

    setThreadId(sessionId);
    fetchSessionDetail(sessionId).then((detail) => {
      // Do not overwrite if user started streaming while request was in flight
      if (isStreamingRef.current && activeStreamSessionIdRef.current === sessionId) return;

      if (detail && detail.messages && detail.messages.length > 0) {
        const loadedMessages: Message[] = detail.messages.map((m) => {
          const insightItem = m.tool_calls?.find((t: any) => t.insight)?.insight;
          return {
            id: m.id,
            sender: m.role,
            content: m.content,
            chartSpec: m.chart_spec || undefined,
            financialInsight: insightItem || undefined,
            toolsUsed: m.tool_calls
              ? m.tool_calls.map((t: any) => ({
                  tool: t.tool || 'Analysis Tool',
                  status: 'done' as const,
                  input: t.input,
                }))
              : undefined,
            userQuery: m.role === 'assistant' ? undefined : m.content,
          };
        });
        setMessages(loadedMessages);
      } else if (!isStreamingRef.current) {
        setMessages([
          {
            id: 'welcome',
            sender: 'assistant',
            content:
              language === 'hi'
                ? 'नमस्ते! मैं निवो (Nivo) हूँ, आपका पर्सनल वेल्थ कोपायलट। मुझसे अपने मासिक बजट, 2026 के खर्चों के रुझान या बैंक स्टेटमेंट के बारे में पूछें!'
                : "Hi! I'm Nivo, your personal wealth copilot. Ask me about your monthly spending, 2026 expense projections, category breakdowns, or upload your bank statements and bills!",
          },
        ]);
      }
    });
  }, [sessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  // Load dynamic ledger-aware prompt suggestions on mount and language switch
  useEffect(() => {
    if (isOpen) {
      fetchDynamicSuggestions(language).then((sugs) => {
        if (sugs && sugs.length > 0) {
          setDynamicSuggestions(sugs);
        }
      });
    }
  }, [isOpen, language]);

  // Handle language switch
  const handleLanguageChange = (newLang: 'en' | 'hi') => {
    setLanguage(newLang);
    const greeting =
      newLang === 'hi'
        ? 'नमस्ते! मैं निवो (Nivo) हूँ, आपका पर्सनल वेल्थ कोपायलट। मुझसे अपने मासिक बजट, 2026 के खर्चों के रुझान या बैंक स्टेटमेंट के बारे में पूछें!'
        : "Hi! I'm Nivo, your personal wealth copilot. Ask me about your monthly spending, 2026 expense projections, category breakdowns, or upload your bank statements and bills!";

    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        content: greeting,
      },
    ]);
  };

  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [stagedFile, setStagedFile] = useState<File | null>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setStagedFile(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  const handleInputPaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    const pastedText = e.clipboardData?.getData('text');
    // If user pastes large text (> 800 characters or > 15 lines), stage as file like ChatGPT
    if (pastedText && (pastedText.length > 800 || pastedText.split('\n').length > 15)) {
      e.preventDefault();
      const blob = new Blob([pastedText], { type: 'text/plain' });
      const file = new File([blob], 'pasted_content.txt', { type: 'text/plain' });
      setStagedFile(file);
    }
  };

  // Helper to extract [Action: <label>] chips from text
  const extractActionChips = (content: string) => {
    const matches: string[] = [];
    const regex = /`?\s*\[Action:\s*([^\]]+)\]\s*`?/gi;
    let match;
    while ((match = regex.exec(content)) !== null) {
      const cleanLabel = match[1].replace(/[`"']/g, '').trim();
      if (cleanLabel) {
        matches.push(cleanLabel);
      }
    }
    return matches;
  };

  // Strip [Action: ...] and legacy persona tags from displayed text body and normalize quotation artifacts
  const cleanMessageContent = (content: string) => {
    // Strip legacy [Persona: ...] tags
    let text = content.replace(/\[Persona:\s*[^\]]+\]/gi, '').trim();
    // Strip all [Action: ...] tags, whether bare, wrapped in backticks, brackets or quotes
    text = text.replace(/`?\s*\[Action:[^\]]*\]\s*`?/gi, '').trim();
    // Strip <financial_insight> ... </financial_insight> tags and any in-progress insight stream
    text = text.replace(/<financial_insight>[\s\S]*?<\/financial_insight>/gi, '').trim();
    text = text.replace(/<financial_insight>[\s\S]*$/gi, '').trim();
    // Strip doubled quotes
    text = text.replace(/""([^""]+)""/g, '"$1"');
    // Strip empty backtick spans or backticks surrounding whitespace
    text = text.replace(/`\s*`/g, '').trim();
    // Strip lines that contain nothing except backticks, dashes, asterisks or whitespace
    text = text.replace(/^[ \t]*[`\s\-_*~]+[ \t]*$/gm, '').trim();
    // Strip stray isolated backticks at start or end of text or tokens
    text = text.replace(/(?:^|\s+)`(?:\s+|$)/g, ' ').trim();
    text = text.replace(/`+$/g, '').trim();
    text = text.replace(/^`+/g, '').trim();
    return text;
  };

  // Renders financial amounts in a bespoke monospace currency badge
  const renderCurrencyBadges = (rawText: string): React.ReactNode => {
    // Normalize unwanted whitespace before punctuation e.g. "₹60,962 ." -> "₹60,962."
    const cleanedText = rawText.replace(/\s+([.,;:?!])/g, '$1');
    const parts = cleanedText.split(/(₹[\d,]+(?:\.\d{1,2})?(?:\s*(?:L|Cr|Lakh|k|K))?)/g);
    if (parts.length === 1) return cleanedText;

    return parts.map((part, pIdx) => {
      if (part.startsWith('₹') && /\d/.test(part)) {
        return (
          <span
            key={pIdx}
            className="inline-flex items-baseline font-mono font-semibold text-emerald-300 bg-slate-900/95 border border-slate-700/70 px-1.5 py-0.5 mx-0.5 rounded text-[11.5px] tracking-tight shadow-xs select-text align-baseline"
          >
            {part}
          </span>
        );
      }
      return part;
    });
  };

  const renderInlineMarkdown = (text: string): React.ReactNode => {
    const tokens = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g);

    return tokens.map((token, i) => {
      if (token.startsWith('**') && token.endsWith('**') && token.length > 4) {
        return (
          <strong key={i} className="font-semibold text-white tracking-wide">
            {renderCurrencyBadges(token.slice(2, -2))}
          </strong>
        );
      }
      if (token.startsWith('`') && token.endsWith('`') && token.length > 2) {
        const codeContent = token.slice(1, -1).trim();
        if (!codeContent) {
          return null;
        }
        return (
          <code
            key={i}
            className="px-1.5 py-0.5 mx-0.5 rounded bg-slate-800 border border-slate-700/60 font-mono text-[11px] text-indigo-300"
          >
            {codeContent}
          </code>
        );
      }
      if (token.startsWith('*') && token.endsWith('*') && token.length > 2) {
        return (
          <em key={i} className="italic text-slate-300">
            {renderCurrencyBadges(token.slice(1, -1))}
          </em>
        );
      }
      return renderCurrencyBadges(token);
    });
  };

  const toggleToolExpand = (msgId: string) => {
    setExpandedToolMsgIds((prev) => {
      const next = new Set(prev);
      if (next.has(msgId)) next.delete(msgId);
      else next.add(msgId);
      return next;
    });
  };

  const getToolFriendlyName = (toolName: string, lang: 'en' | 'hi') => {
    switch (toolName) {
      case 'get_current_datetime':
        return lang === 'hi' ? 'तारीख व वित्तीय तिमाही की जाँच...' : 'Checking date & fiscal quarter...';
      case 'run_financial_query':
        return lang === 'hi' ? 'बहीखाता डेटाबेस में खोज...' : 'Querying ledger database...';
      case 'get_expense_summary':
        return lang === 'hi' ? 'खर्च श्रेणियों का विश्लेषण...' : 'Aggregating category totals...';
      case 'web_search':
        return lang === 'hi' ? 'बाज़ार डेटा की खोज...' : 'Sourcing live market data...';
      case 'generate_chart_spec':
        return lang === 'hi' ? 'चार्ट विज़ुअलाइज़ेशन तैयार...' : 'Generating chart visualization...';
      case 'project_future_expenses':
        return lang === 'hi' ? 'भविष्य के बजट का अनुमान...' : 'Forecasting budget trajectory...';
      default:
        return lang === 'hi' ? 'प्रक्रिया जारी है...' : 'Processing financial data...';
    }
  };

  const handleCopyMessage = (msgId: string, content: string) => {
    const cleaned = cleanMessageContent(content);
    navigator.clipboard.writeText(cleaned);
    setCopiedMsgId(msgId);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  const handleFeedback = async (
    msgId: string,
    rating: 'thumbs_up' | 'thumbs_down',
    userQuery?: string,
    assistantResponse?: string,
    category?: string
  ) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === msgId ? { ...m, feedbackGiven: rating } : m))
    );
    setActiveFeedbackMsgId(null);
    await submitChatFeedback({
      message_id: msgId,
      thread_id: threadId,
      rating,
      category,
      user_query: userQuery,
      assistant_response: cleanMessageContent(assistantResponse || ''),
    });
  };

  interface TableData {
    headers: string[];
    rows: string[][];
    rawMarkdown: string;
  }

  const parseMarkdownBlocks = (content: string) => {
    const tableRegex = /(?:^|\n)\|([^\n]+)\|\r?\n\|[-:\s|]+\|\r?\n((?:\|[^\n]+\|\r?\n?)+)/g;
    const blocks: Array<{ type: 'text' | 'table'; content?: string; table?: TableData }> = [];
    let lastIndex = 0;
    let match;

    while ((match = tableRegex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        const textPart = content.slice(lastIndex, match.index).trim();
        if (textPart) blocks.push({ type: 'text', content: textPart });
      }

      const headerLine = match[1];
      const rowsBlock = match[2];
      const headers = headerLine.split('|').map((h) => h.trim()).filter((h) => h.length > 0);
      const rows = rowsBlock
        .trim()
        .split('\n')
        .map((line) =>
          line
            .replace(/^\||\|$/g, '')
            .split('|')
            .map((cell) => cell.trim())
        )
        .filter((row) => row.length > 0);

      blocks.push({
        type: 'table',
        table: {
          headers,
          rows,
          rawMarkdown: match[0].trim(),
        },
      });

      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < content.length) {
      const textPart = content.slice(lastIndex).trim();
      if (textPart) blocks.push({ type: 'text', content: textPart });
    }

    return blocks.length > 0 ? blocks : [{ type: 'text' as const, content }];
  };

  const RichTableCard: React.FC<{ table: TableData }> = ({ table }) => {
    const [copied, setCopied] = useState(false);

    // Strips markdown artifacts (e.g. **जुलाई** -> जुलाई) from table cells
    const cleanCell = (cell: string) => {
      return cell.replace(/\*\*/g, '').replace(/""/g, '"').trim();
    };

    const isNumeric = (val: string) => {
      const cleaned = cleanCell(val);
      return /^[\s₹$€£,.\d%+-]+$/.test(cleaned) && /\d/.test(cleaned);
    };

    // Determines whether an entire column represents financial amounts, rates, or counts
    const isColumnNumeric = (colIdx: number) => {
      const header = cleanCell(table.headers[colIdx] || '').toLowerCase();
      if (
        header.includes('amount') ||
        header.includes('राशि') ||
        header.includes('spend') ||
        header.includes('total') ||
        header.includes('खर्च') ||
        header.includes('औसत') ||
        header.includes('debit') ||
        header.includes('credit') ||
        header.includes('balance') ||
        header.includes('price') ||
        header.includes('cost') ||
        header.includes('rate') ||
        header.includes('txns') ||
        header.includes('लेनदेन') ||
        header.includes('%')
      ) {
        return true;
      }
      let numericCount = 0;
      for (const row of table.rows) {
        const val = row[colIdx] || '';
        if (
          val.includes('₹') ||
          val.includes('$') ||
          val.includes('€') ||
          isNumeric(val) ||
          /\d+[\d,.]*/.test(val)
        ) {
          numericCount++;
        }
      }
      return table.rows.length > 0 && numericCount / table.rows.length >= 0.5;
    };

    const handleCopy = () => {
      const tsv = [
        table.headers.map(cleanCell).join('\t'),
        ...table.rows.map((r) => r.map(cleanCell).join('\t')),
      ].join('\n');
      navigator.clipboard.writeText(tsv);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    };

    const handleDownloadCsv = () => {
      const csvContent = [
        table.headers.map((h) => `"${cleanCell(h).replace(/"/g, '""')}"`).join(','),
        ...table.rows.map((r) => r.map((c) => `"${cleanCell(c).replace(/"/g, '""')}"`).join(',')),
      ].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `financial_table_${Date.now()}.csv`;
      link.click();
      URL.revokeObjectURL(url);
    };

    return (
      <div className="my-2.5 rounded-xl border border-slate-800 bg-slate-950/90 overflow-hidden shadow-lg">
        <div className="px-3 py-2 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-[11px]">
            <TableIcon className="w-3.5 h-3.5" />
            <span>{language === 'hi' ? 'वित्तीय डेटा तालिका' : 'Financial Overview Table'}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={handleCopy}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[10px] transition"
              title="Copy table to clipboard"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3 text-emerald-400" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy</span>
                </>
              )}
            </button>
            <button
              type="button"
              onClick={handleDownloadCsv}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[10px] transition"
              title="Download table as CSV"
            >
              <Download className="w-3 h-3" />
              <span>CSV</span>
            </button>
          </div>
        </div>
        <div className="overflow-x-auto no-scrollbar">
          <table className="w-full text-[11px] text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800/80 bg-slate-900/40">
                {table.headers.map((h, hIdx) => {
                  const isNum = isColumnNumeric(hIdx);
                  return (
                    <th
                      key={hIdx}
                      className={`px-3 py-2 font-semibold text-slate-400 uppercase tracking-wider text-[10px] ${
                        isNum ? 'text-right' : 'text-left'
                      }`}
                    >
                      {cleanCell(h)}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {table.rows.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-slate-900/30 transition-colors">
                  {row.map((cell, cIdx) => {
                    const isNum = isColumnNumeric(cIdx);
                    return (
                      <td
                        key={cIdx}
                        className={`px-3 py-2 text-slate-200 whitespace-nowrap ${
                          isNum
                            ? 'text-right font-mono font-medium text-emerald-300/90'
                            : 'text-left'
                        }`}
                      >
                        {cleanCell(cell)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  // Render message with collapsible <details> accordion support, rich tables, and streaming cursor
  const renderFormattedMessage = (content: string, isStreaming?: boolean) => {
    const cleaned = cleanMessageContent(content);
    const detailsRegex = /<details>[\s\S]*?<summary>([\s\S]*?)<\/summary>([\s\S]*?)<\/details>/i;
    const match = detailsRegex.exec(cleaned);

    let mainPart = cleaned;
    let summaryText = '';
    let detailsBody = '';

    if (match) {
      mainPart = cleaned.replace(detailsRegex, '').trim();
      summaryText = match[1].trim();
      detailsBody = match[2].trim();
    }

    const blocks = parseMarkdownBlocks(mainPart);

    return (
      <div className="space-y-2">
        {blocks.map((block, idx) => {
          if (block.type === 'table' && block.table) {
            return <RichTableCard key={idx} table={block.table} />;
          }

          const lines = (block.content || '').split('\n');

          return (
            <div key={idx} className="space-y-1.5 leading-relaxed text-slate-200">
              {lines.map((line, lIdx) => {
                const trimmed = line.trim();
                if (!trimmed) {
                  return <div key={lIdx} className="h-1.5" />;
                }

                // Suppress lines that consist purely of residual backticks or punctuation artifacts
                const residualAlphanum = trimmed.replace(/[`\s\-_*~]/g, '');
                if (!residualAlphanum && trimmed.includes('`')) {
                  return null;
                }

                // Clean doubled quotes at line boundaries
                let cleanLine = line.replace(/^""(.*)""$/, '$1');

                // Header 3 (###) or Section Header
                if (cleanLine.startsWith('### ')) {
                  return (
                    <h4
                      key={lIdx}
                      className="font-bold text-slate-100 text-xs mt-2.5 mb-1 text-indigo-300/90 flex items-center gap-1.5"
                    >
                      <span className="w-1 h-3 rounded-full bg-indigo-500" />
                      {renderInlineMarkdown(cleanLine.slice(4))}
                    </h4>
                  );
                }
                if (cleanLine.startsWith('## ')) {
                  return (
                    <h3
                      key={lIdx}
                      className="font-bold text-white text-sm mt-3 mb-1 flex items-center gap-2"
                    >
                      <span className="w-1.5 h-3.5 rounded-full bg-indigo-500" />
                      {renderInlineMarkdown(cleanLine.slice(3))}
                    </h3>
                  );
                }

                // Standalone bold header lines e.g. **महीने-वार विवरण** or **By merchant:**
                if (/^\*\*[^*:]+:\*\*\s*$/.test(cleanLine) || /^\*\*[^*]+\*\*\s*$/.test(cleanLine)) {
                  const headerTitle = cleanLine.replace(/\*\*/g, '').trim();
                  return (
                    <div
                      key={lIdx}
                      className="font-semibold text-slate-100 text-xs mt-2.5 mb-0.5 text-indigo-300/90 flex items-center gap-1.5"
                    >
                      <span className="w-1 h-2.5 rounded-full bg-indigo-400" />
                      <span>{headerTitle}</span>
                    </div>
                  );
                }

                // Numbered list item: 1. or 2.
                const numMatch = cleanLine.match(/^(\s*)(\d+)\.\s+(.+)$/);
                if (numMatch) {
                  return (
                    <div key={lIdx} className="flex items-start gap-2 pl-1.5">
                      <span className="font-mono text-indigo-400 font-medium text-[11px] select-none min-w-[16px]">
                        {numMatch[2]}.
                      </span>
                      <span className="flex-1">{renderInlineMarkdown(numMatch[3])}</span>
                    </div>
                  );
                }

                // Bullet point: - or * or •
                const bulletMatch = cleanLine.match(/^(\s*)([-*•])\s+(.+)$/);
                if (bulletMatch) {
                  return (
                    <div key={lIdx} className="flex items-start gap-2 pl-2">
                      <span className="text-indigo-400 mt-1.5 text-[6px] select-none">●</span>
                      <span className="flex-1">{renderInlineMarkdown(bulletMatch[3])}</span>
                    </div>
                  );
                }

                return (
                  <p key={lIdx}>
                    {renderInlineMarkdown(cleanLine)}
                    {isStreaming &&
                      idx === blocks.length - 1 &&
                      lIdx === lines.length - 1 && (
                        <span className="inline-block w-1.5 h-3 ml-1 bg-indigo-400 animate-pulse rounded-sm align-middle" />
                      )}
                  </p>
                );
              })}
            </div>
          );
        })}

        {match && (
          <details className="group mt-2.5 rounded-xl border border-slate-800 bg-slate-950/80 p-2.5 text-xs transition">
            <summary className="cursor-pointer font-medium text-slate-300 hover:text-indigo-400 flex items-center justify-between select-none">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                {summaryText}
              </span>
              <span className="text-[10px] text-slate-500 group-open:rotate-180 transition-transform">▼</span>
            </summary>
            <div className="mt-2 pt-2 border-t border-slate-800/80 font-mono text-[11px] text-slate-300 whitespace-pre-wrap overflow-x-auto">
              {detailsBody}
            </div>
          </details>
        )}
      </div>
    );
  };



  const handleConfirmReceipt = async (msgId: string, receipt: any) => {
    try {
      await createTransaction({
        description: receipt.vendor_name || 'Receipt Expense',
        amount: receipt.total_amount,
        category: receipt.category,
        vendor_name: receipt.vendor_name,
        payment_method: receipt.payment_method || 'UPI',
        date: receipt.date,
      });

      setMessages((prev) =>
        prev.map((m) =>
          m.id === msgId ? { ...m, receiptAdded: true } : m
        )
      );

      const confirmMsg: Message = {
        id: Date.now().toString(),
        sender: 'assistant',
        content:
          language === 'hi'
            ? `✔ सफलतापूर्वक दर्ज किया गया: **₹${receipt.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}** (${receipt.vendor_name}, ${receipt.category.toUpperCase()})। आपका बहीखाता अपडेट हो गया है!`
            : `✔ Recorded **₹${receipt.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}** for **${receipt.vendor_name}** under **${receipt.category.toUpperCase()}** via ${receipt.payment_method}. Your ledger and charts have been refreshed!`,
      };
      setMessages((prev) => [...prev, confirmMsg]);
      if (onTransactionLogged) {
        onTransactionLogged();
      }
    } catch (err) {
      console.error('Failed to record receipt transaction:', err);
    }
  };

  const handleConfirmAddExpense = async (msgId: string, intent: ExpenseIntent) => {
    try {
      await createTransaction({
        description: intent.item,
        amount: intent.amount,
        category: intent.category,
        vendor_name: intent.vendor,
        payment_method: intent.payment_method || 'UPI',
      });

      // Mark intent as added in message
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msgId ? { ...m, intentAdded: true, isEditingIntent: false } : m
        )
      );

      // Add confirmation reply
      const confirmMsg: Message = {
        id: Date.now().toString(),
        sender: 'assistant',
        content:
          language === 'hi'
            ? `✔ दर्ज किया गया: **₹${intent.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}** (${intent.item}) श्रेणी **${intent.category.toUpperCase()}** माध्यम ${intent.payment_method || 'UPI'}। आपका बजट रिफ्रेश हो गया है!`
            : `✔ Recorded **₹${intent.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}** for **${intent.item}** under **${intent.category.toUpperCase()}** via ${intent.payment_method || 'UPI'}. Your household ledger and charts have been refreshed!`,
      };
      setMessages((prev) => [...prev, confirmMsg]);

      if (onTransactionLogged) {
        onTransactionLogged();
      }
    } catch (err) {
      alert(`Error recording expense: ${err}`);
    }
  };

  const handleDismissIntent = (msgId: string) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === msgId ? { ...m, intentDismissed: true, isEditingIntent: false } : m
      )
    );
  };

  const handleToggleEditIntent = (msgId: string) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === msgId ? { ...m, isEditingIntent: !m.isEditingIntent } : m
      )
    );
  };

  const handleUpdateIntentCategory = (msgId: string, newCategory: string) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === msgId && m.intent
          ? { ...m, intent: { ...m.intent, category: newCategory } }
          : m
      )
    );
  };

  const handleUpdateIntentPayment = (msgId: string, newPaymentMethod: string) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === msgId && m.intent
          ? { ...m, intent: { ...m.intent, payment_method: newPaymentMethod } }
          : m
      )
    );
  };

  const handleSend = async (messageText?: string) => {
    const rawText = messageText !== undefined ? messageText : input;
    const textToSend = rawText.trim();
    const currentStagedFile = stagedFile;

    // Reject if neither text nor file is present, or if streaming
    if ((!textToSend && !currentStagedFile) || isStreaming) return;

    // Conversational follow-up: detect if user typed "cash", "credit card", "debit card", "upi"
    // to mutate an unconfirmed pending expense intent
    const lowerTrimmed = textToSend.toLowerCase().replace(/^(?:it was\s+|paid\s+(?:in|by|via|with)?\s*)/i, '').trim();
    let matchedMethod: string | undefined = undefined;
    if (lowerTrimmed === 'cash' || lowerTrimmed === 'by cash' || lowerTrimmed === 'in cash') {
      matchedMethod = 'Cash';
    } else if (lowerTrimmed === 'upi' || lowerTrimmed === 'gpay' || lowerTrimmed === 'phonepe' || lowerTrimmed === 'paytm') {
      matchedMethod = 'UPI';
    } else if (lowerTrimmed === 'card' || lowerTrimmed === 'credit' || lowerTrimmed === 'credit card' || lowerTrimmed === 'cc') {
      matchedMethod = 'Credit Card';
    } else if (lowerTrimmed === 'debit' || lowerTrimmed === 'debit card' || lowerTrimmed === 'dc') {
      matchedMethod = 'Debit Card';
    } else if (lowerTrimmed === 'net banking' || lowerTrimmed === 'netbanking' || lowerTrimmed === 'bank transfer') {
      matchedMethod = 'Net Banking';
    } else {
      matchedMethod = AVAILABLE_PAYMENT_METHODS.find(
        (pm) => pm.toLowerCase() === lowerTrimmed || pm.toLowerCase() === lowerTrimmed.replace(/\s+/g, '')
      );
    }
    if (!currentStagedFile && matchedMethod) {
      const pendingMsgIndex = [...messages].reverse().findIndex((m) => m.intent && !m.intentAdded && !m.intentDismissed);
      if (pendingMsgIndex !== -1) {
        const actualIndex = messages.length - 1 - pendingMsgIndex;
        const targetMsg = messages[actualIndex];
        setInput('');
        setMessages((prev) =>
          prev.map((m) =>
            m.id === targetMsg.id && m.intent
              ? { ...m, intent: { ...m.intent, payment_method: matchedMethod } }
              : m
          ).concat([
            {
              id: Date.now().toString(),
              sender: 'user',
              content: textToSend,
            },
            {
              id: (Date.now() + 1).toString(),
              sender: 'assistant',
              content:
                language === 'hi'
                  ? `समझ गया! **${targetMsg.intent?.item}** के लिए भुगतान माध्यम बदलकर **${matchedMethod}** कर दिया गया है। दर्ज करने के लिए ऊपर **[Approve & Record]** पर क्लिक करें।`
                  : `Got it! Updated payment method for **${targetMsg.intent?.item}** to **${matchedMethod}**. Tap **[Approve & Record]** above to commit it.`,
            }
          ])
        );
        return;
      }
    }

    setStagedFile(null);
    setInput('');

    // Case 1: Staged file WITH accompanying user prompt
    if (currentStagedFile && textToSend) {
      const userMsgId = Date.now().toString();
      const assistantMsgId = (Date.now() + 1).toString();

      setMessages((prev) => [
        ...prev,
        {
          id: userMsgId,
          sender: 'user',
          content: `📎 **[${currentStagedFile.name}]**\n\n${textToSend}`,
        },
        {
          id: assistantMsgId,
          sender: 'assistant',
          content: '',
          isStreaming: true,
          userQuery: textToSend,
          toolsUsed: [{ tool: 'ingest_document', status: 'running', input: { file: currentStagedFile.name } }],
        },
      ]);
      setIsStreaming(true);

      try {
        const ingestRes = await ingestDocument(currentStagedFile, undefined, threadId || sessionId);
        const activeSid = ingestRes.session_id || threadId || sessionId;
        if (activeSid && (!sessionId || sessionId !== activeSid)) {
          setThreadId(activeSid);
          onSessionCreated?.(activeSid);
        }

        abortControllerRef.current = new AbortController();
        await streamCopilotChat(
          textToSend,
          activeSid,
          provider,
          {
            onSession: (data) => {
              activeStreamSessionIdRef.current = data.session_id || null;
              setThreadId(data.thread_id);
              if (data.session_id && data.session_id !== sessionId) {
                onSessionCreated?.(data.session_id);
              }
            },
            onToken: (token) => {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, content: msg.content + token } : msg
                )
              );
            },
            onToolStart: (tool, toolInput) => {
              setMessages((prev) =>
                prev.map((msg) => {
                  if (msg.id !== assistantMsgId) return msg;
                  const existing = msg.toolsUsed || [];
                  return {
                    ...msg,
                    toolsUsed: [...existing, { tool, status: 'running', input: toolInput }],
                  };
                })
              );
            },
            onToolEnd: (tool) => {
              setMessages((prev) =>
                prev.map((msg) => {
                  if (msg.id !== assistantMsgId) return msg;
                  const updatedTools = (msg.toolsUsed || []).map((t) =>
                    t.tool === tool ? { ...t, status: 'done' as const } : t
                  );
                  return { ...msg, toolsUsed: updatedTools };
                })
              );
            },
            onChart: (spec) => {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, chartSpec: spec } : msg
                )
              );
            },
            onIntent: (intent) => {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, intent } : msg
                )
              );
            },
            onWidget: (widgetData) => {
              if (widgetData.widget_type === 'receipt_card' && widgetData.receipt) {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId ? { ...msg, receiptWidget: widgetData.receipt } : msg
                  )
                );
              }
            },
            onInsight: (insight) => {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, financialInsight: insight } : msg
                )
              );
            },
            onDone: () => {
              activeStreamSessionIdRef.current = null;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, isStreaming: false } : msg
                )
              );
              setIsStreaming(false);
              onSessionUpdated?.();
            },
            onError: (err) => {
              activeStreamSessionIdRef.current = null;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId
                    ? { ...msg, isStreaming: false, content: msg.content + `\n\n*(Notice: ${err})*` }
                    : msg
                )
              );
              setIsStreaming(false);
              onSessionUpdated?.();
            },
          },
          abortControllerRef.current.signal,
          language,
          activeSid
        );
      } catch (err: any) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? { ...msg, isStreaming: false, content: `Error processing file: ${err.message}` }
              : msg
          )
        );
        setIsStreaming(false);
      }
      return;
    }

    // Case 2: File only (no text prompt) -> Standard document analysis & receipt extraction
    if (currentStagedFile && !textToSend) {
      const userMsgId = Date.now().toString();
      const assistantMsgId = (Date.now() + 1).toString();

      setMessages((prev) => [
        ...prev,
        {
          id: userMsgId,
          sender: 'user',
          content: `Uploaded document: ${currentStagedFile.name}`,
        },
        {
          id: assistantMsgId,
          sender: 'assistant',
          content: 'Analyzing document and extracting transaction details...',
          isStreaming: true,
        },
      ]);
      setIsUploading(true);

      try {
        const res = await ingestDocument(currentStagedFile, undefined, threadId || sessionId);
        if (res.session_id && (!sessionId || sessionId !== res.session_id)) {
          setThreadId(res.session_id);
          onSessionCreated?.(res.session_id);
        }
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  isStreaming: false,
                  content: res.summary || 'Document analysis completed.',
                  receiptWidget: res.receipt,
                }
              : msg
          )
        );
        onSessionUpdated?.();
      } catch (err: any) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  isStreaming: false,
                  content: `Could not extract transaction: ${err.message}`,
                }
              : msg
          )
        );
      } finally {
        setIsUploading(false);
      }
      return;
    }

    // Case 3: Standard text query
    const userMsgId = Date.now().toString();
    const assistantMsgId = (Date.now() + 1).toString();

    const newMessages: Message[] = [
      ...messages,
      { id: userMsgId, sender: 'user', content: textToSend },
      {
        id: assistantMsgId,
        sender: 'assistant',
        content: '',
        isStreaming: true,
        userQuery: textToSend,
        toolsUsed: [],
      },
    ];

    setMessages(newMessages);
    setIsStreaming(true);

    abortControllerRef.current = new AbortController();

    try {
      await streamCopilotChat(
        textToSend,
        threadId,
        provider,
        {
          onSession: (data) => {
            activeStreamSessionIdRef.current = data.session_id || null;
            setThreadId(data.thread_id);
            if (data.session_id && data.session_id !== sessionId) {
              onSessionCreated?.(data.session_id);
            }
          },
          onToken: (token) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? { ...msg, content: msg.content + token }
                  : msg
              )
            );
          },
          onToolStart: (tool, toolInput) => {
            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id !== assistantMsgId) return msg;
                const existing = msg.toolsUsed || [];
                return {
                  ...msg,
                  toolsUsed: [...existing, { tool, status: 'running', input: toolInput }],
                };
              })
            );
          },
          onToolEnd: (tool) => {
            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id !== assistantMsgId) return msg;
                const updatedTools = (msg.toolsUsed || []).map((t) =>
                  t.tool === tool ? { ...t, status: 'done' as const } : t
                );
                return { ...msg, toolsUsed: updatedTools };
              })
            );
          },
          onChart: (spec) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId ? { ...msg, chartSpec: spec } : msg
              )
            );
          },
          onIntent: (intent) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId ? { ...msg, intent } : msg
              )
            );
          },
          onWidget: (widgetData) => {
            if (widgetData.widget_type === 'receipt_card' && widgetData.receipt) {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, receiptWidget: widgetData.receipt } : msg
                )
              );
            }
          },
          onInsight: (insight) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId ? { ...msg, financialInsight: insight } : msg
              )
            );
          },
          onDone: () => {
            activeStreamSessionIdRef.current = null;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId ? { ...msg, isStreaming: false } : msg
              )
            );
            setIsStreaming(false);
            onSessionUpdated?.();
          },
          onError: (err) => {
            activeStreamSessionIdRef.current = null;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? {
                      ...msg,
                      isStreaming: false,
                      content:
                        msg.content +
                        `\n\n*(Notice: ${err})*`,
                    }
                  : msg
              )
            );
            setIsStreaming(false);
            onSessionUpdated?.();
          },
        },
        abortControllerRef.current.signal,
        language,
        sessionId
      );
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  isStreaming: false,
                  content:
                    msg.content ||
                    (language === 'hi'
                      ? 'वित्तीय रिकॉर्ड का विश्लेषण करने में समस्या आई।'
                      : 'Encountered an issue analyzing financial records.'),
                }
              : msg
          )
        );
      }
      setIsStreaming(false);
    }
  };

  const handleClearHistory = () => {
    if (abortControllerRef.current) abortControllerRef.current.abort();
    setThreadId(null);
    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        content:
          language === 'hi'
            ? 'सत्र रीसेट हो गया है। आप अपने बजट या खर्चों के बारे में कुछ भी पूछ सकते हैं।'
            : 'Session refreshed. Ask any question about your household budget, or type an expense like "3500 pizza" to log it.',
      },
    ]);
  };

  if (!isOpen) return null;

  return (
    <div
      className={
        isStandalone
          ? 'flex-1 h-screen flex flex-col bg-[#090d16] text-slate-100 overflow-hidden relative'
          : 'fixed inset-y-0 right-0 z-50 w-full sm:w-[480px] lg:w-[540px] bg-slate-950 border-l border-slate-800 shadow-2xl flex flex-col'
      }
    >
      {/* Header */}
      {isStandalone ? (
        <div className="h-16 px-6 border-b border-slate-800/80 bg-slate-950/40 backdrop-blur-md flex items-center justify-between flex-shrink-0 z-10">
          <div className="flex items-center gap-3">
            {onToggleSidebar && (
              <button
                onClick={onToggleSidebar}
                title={isSidebarOpen ? 'Collapse Sidebar' : 'Expand Sidebar'}
                className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 transition"
              >
                <PanelLeft className="w-5 h-5" />
              </button>
            )}
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-white tracking-tight truncate max-w-[260px]">
                  {activeSessionTitle || (language === 'hi' ? 'नई चर्चा' : 'New Analysis')}
                </h2>

                {/* Model Selection Dropdown */}
                <div ref={modelDropdownRef} className="relative">
                  <button
                    type="button"
                    onClick={() => setIsModelDropdownOpen((prev) => !prev)}
                    title="Select AI Model"
                    className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-slate-900 border border-slate-700/80 text-[10.5px] text-indigo-300 font-mono hover:border-indigo-500/50 hover:bg-slate-800 transition cursor-pointer"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                    <span>{provider === 'deepseek' ? 'DeepSeek-V3' : 'Gemini 2.5 Flash'}</span>
                    <ChevronDown className="w-3 h-3 text-slate-400" />
                  </button>

                  {isModelDropdownOpen && (
                    <div className="absolute left-0 mt-1.5 w-48 rounded-xl bg-slate-900 border border-slate-700/80 shadow-2xl p-1 z-50 animate-in fade-in slide-in-from-top-1">
                      <div className="px-2 py-1 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                        AI Model Engine
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setProvider('deepseek');
                          setIsModelDropdownOpen(false);
                        }}
                        className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs flex items-center justify-between transition cursor-pointer ${
                          provider === 'deepseek'
                            ? 'bg-indigo-600/20 text-indigo-300 font-semibold border border-indigo-500/30'
                            : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                        }`}
                      >
                        <div>
                          <div className="font-mono text-xs">DeepSeek-V3</div>
                          <div className="text-[10px] text-slate-400 font-normal">Deep Financial Reasoning</div>
                        </div>
                        {provider === 'deepseek' && <Check className="w-3.5 h-3.5 text-indigo-400" />}
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setProvider('gemini');
                          setIsModelDropdownOpen(false);
                        }}
                        className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs flex items-center justify-between mt-0.5 transition cursor-pointer ${
                          provider === 'gemini'
                            ? 'bg-indigo-600/20 text-indigo-300 font-semibold border border-indigo-500/30'
                            : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                        }`}
                      >
                        <div>
                          <div className="font-mono text-xs">Gemini 2.5 Flash</div>
                          <div className="text-[10px] text-slate-400 font-normal">Multimodal & High Speed</div>
                        </div>
                        {provider === 'gemini' && <Check className="w-3.5 h-3.5 text-indigo-400" />}
                      </button>
                    </div>
                  )}
                </div>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Nivo • Personal Wealth Copilot
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Language Selector */}
            <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs">
              <button
                onClick={() => handleLanguageChange('en')}
                className={`px-2.5 py-1 rounded font-medium transition ${
                  language === 'en'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                EN
              </button>
              <button
                onClick={() => handleLanguageChange('hi')}
                className={`px-2.5 py-1 rounded font-medium transition ${
                  language === 'hi'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                हिन्दी
              </button>
            </div>

            <button
              onClick={onNewChat || handleClearHistory}
              title="New Chat Session"
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 text-xs font-medium transition"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Chat</span>
            </button>

            {/* Notification Bell */}
            <div className="relative" ref={notifDropdownRef}>
              <button
                type="button"
                onClick={() => setIsNotifOpen(!isNotifOpen)}
                title="Financial Notifications & Anomaly Alerts"
                className="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                {notifications.some((n) => !n.read) ? (
                  <BellRing className="w-4 h-4 text-amber-400 animate-pulse" />
                ) : (
                  <Bell className="w-4 h-4" />
                )}
                {notifications.some((n) => !n.read) && (
                  <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-amber-500 ring-2 ring-slate-900" />
                )}
              </button>

              {/* Notification Popover Drawer */}
              {isNotifOpen && (
                <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl bg-slate-900/95 border border-slate-800 shadow-2xl p-4 text-xs z-50 backdrop-blur-xl animate-fade-in space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                    <div className="flex items-center gap-1.5 font-semibold text-white">
                      <Bell className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Ledger Alerts & Briefings</span>
                    </div>
                    <span className="text-[10px] text-slate-400">
                      {notifications.length} active
                    </span>
                  </div>

                  {notifications.length === 0 ? (
                    <div className="py-6 text-center text-slate-400">
                      <ShieldCheck className="w-8 h-8 mx-auto mb-2 text-emerald-400/60" />
                      <p className="text-xs font-medium text-slate-300">All Normal & In Balance</p>
                      <p className="text-[10px] text-slate-500 mt-0.5">No spending anomalies or pending briefings.</p>
                    </div>
                  ) : (
                    <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                      {notifications.map((notif) => (
                        <div
                          key={notif.id}
                          className={`p-3 rounded-xl border ${
                            notif.severity === 'high'
                              ? 'bg-amber-950/20 border-amber-500/30'
                              : 'bg-slate-800/50 border-slate-700/50'
                          } space-y-2`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <span className="font-semibold text-white text-[11px] flex items-center gap-1.5">
                              {notif.severity === 'high' ? (
                                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                              ) : (
                                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                              )}
                              {notif.title}
                            </span>
                            <button
                              type="button"
                              onClick={() => handleDismissNotif(notif.id)}
                              className="text-[10px] text-slate-500 hover:text-slate-300 transition"
                            >
                              ✕
                            </button>
                          </div>

                          <p className="text-[11px] text-slate-300 leading-relaxed">
                            {notif.message}
                          </p>

                          {notif.action_prompt && (
                            <div className="pt-1 flex justify-end">
                              <button
                                type="button"
                                onClick={() => {
                                  setIsNotifOpen(false);
                                  handleSend(notif.action_prompt);
                                }}
                                className="px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-[10px] flex items-center gap-1 transition"
                              >
                                <span>{notif.action_label || 'Investigate'}</span>
                                <ArrowRight className="w-3 h-3" />
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {onOpenSettings && (
              <button
                onClick={onOpenSettings}
                title="Copilot Settings"
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <Settings className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60 backdrop-blur-sm">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <span>Financial AI Assistant</span>
              </h3>
              <p className="text-[11px] text-slate-400">Context-Aware Spend & Budget Planner</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        <div className="max-w-3xl mx-auto w-full space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[92%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-[#1e2430] border border-slate-700/60 text-slate-100 rounded-tr-sm shadow-sm'
                  : 'bg-slate-900/90 border border-slate-800/80 text-slate-200 rounded-tl-sm shadow-sm'
              }`}
            >
              {/* Single Morphing Tool Status Pill & Expandable Completed History */}
              {msg.toolsUsed && msg.toolsUsed.length > 0 && (
                <div className="mb-2.5">
                  {msg.isStreaming ? (
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-850 border border-slate-700/60 text-[11px] text-slate-300 shadow-sm animate-pulse">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                      <span className="font-medium">
                        {getToolFriendlyName(
                          msg.toolsUsed[msg.toolsUsed.length - 1].tool,
                          language
                        )}
                      </span>
                    </div>
                  ) : (
                    <div>
                      <button
                        type="button"
                        onClick={() => toggleToolExpand(msg.id)}
                        className="inline-flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 hover:text-slate-200 hover:border-slate-700 transition select-none group"
                      >
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="font-medium text-slate-300">
                          {language === 'hi'
                            ? `${msg.toolsUsed.length} विश्लेषण चरण पूर्ण`
                            : `Completed ${msg.toolsUsed.length} analysis step${msg.toolsUsed.length > 1 ? 's' : ''}`}
                        </span>
                        <span className="text-[10px] text-slate-500 group-hover:text-slate-300 transition-transform">
                          {expandedToolMsgIds.has(msg.id) ? '▲' : '▼'}
                        </span>
                      </button>
                      {expandedToolMsgIds.has(msg.id) && (
                        <div className="mt-2 pl-3 border-l-2 border-indigo-500/40 space-y-1.5 py-1 bg-slate-950/40 rounded-r-lg">
                          {msg.toolsUsed.map((t, idx) => (
                            <div key={idx} className="text-[10px] text-slate-400 flex items-center gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                              <span className="text-slate-300 font-medium">
                                {getToolFriendlyName(t.tool, language)}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Message text content */}
              {renderFormattedMessage(msg.content, msg.isStreaming)}

              {/* Streaming Indicator */}
              {msg.isStreaming && !msg.content && (
                <div className="flex items-center gap-1.5 text-slate-400 py-1">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
                  <span>
                    {language === 'hi'
                      ? 'डेटा और बजट का विश्लेषण हो रहा है...'
                      : 'Analyzing records and budget...'}
                  </span>
                </div>
              )}

              {/* Generative UI: Interactive Receipt Ingestion Card */}
              {msg.receiptWidget && (
                <div className="mt-3 p-3.5 rounded-xl bg-slate-950/90 border border-emerald-500/30 shadow-lg space-y-2.5">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs">
                      <Receipt className="w-4 h-4" />
                      <span>{msg.receiptWidget.vendor_name || 'Receipt Expense'}</span>
                    </div>
                    {msg.receiptWidget.invoice_number && (
                      <span className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
                        <FileText className="w-3 h-3 text-slate-500" />
                        #{msg.receiptWidget.invoice_number}
                      </span>
                    )}
                  </div>

                  <div className="flex items-baseline justify-between">
                    <div className="text-lg font-bold text-white tracking-tight">
                      ₹{msg.receiptWidget.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-[10px] font-medium text-indigo-300 capitalize">
                        <Tag className="w-3 h-3" />
                        {msg.receiptWidget.category}
                      </span>
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-800 text-[10px] text-slate-300">
                        <CreditCard className="w-3 h-3 text-slate-400" />
                        {msg.receiptWidget.payment_method || 'UPI'}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400">
                    <span className="inline-flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-slate-500" />
                      {msg.receiptWidget.date || 'Today'}
                    </span>

                    {msg.receiptAdded ? (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Recorded to Ledger
                      </span>
                    ) : (
                      <button
                        onClick={() => handleConfirmReceipt(msg.id, msg.receiptWidget)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs shadow-md transition transform active:scale-95"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Approve & Record</span>
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* 1-Click Conversational Expense Intent Action Card */}
              {msg.intent && (
                <div className="mt-3 p-3.5 rounded-xl bg-slate-950/95 border border-indigo-500/30 space-y-2.5 shadow-md">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="font-bold text-white text-sm flex items-center gap-2">
                        <span>₹{msg.intent.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 capitalize">
                          {msg.intent.category}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {msg.intent.item} • {msg.intent.payment_method || 'UPI'}
                      </div>
                    </div>

                    {msg.intentAdded ? (
                      <span className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-medium flex items-center gap-1">
                        <Check className="w-3.5 h-3.5" />
                        Added
                      </span>
                    ) : msg.intentDismissed ? (
                      <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-400 text-[11px] flex items-center gap-1">
                        <X className="w-3 h-3" />
                        Dismissed
                      </span>
                    ) : (
                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => handleToggleEditIntent(msg.id)}
                          title="Edit category or payment method"
                          className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDismissIntent(msg.id)}
                          title="Dismiss expense"
                          className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleConfirmAddExpense(msg.id, msg.intent!)}
                          className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center gap-1.5 transition shadow-sm"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Approve & Record</span>
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Inline Category & Payment Method Editor */}
                  {msg.isEditingIntent && !msg.intentAdded && !msg.intentDismissed && (
                    <div className="pt-2.5 border-t border-slate-800/80 flex flex-wrap items-center gap-3 text-xs">
                      <div className="flex items-center gap-1.5">
                        <span className="text-slate-400 text-[11px]">Category:</span>
                        <select
                          value={msg.intent.category}
                          onChange={(e) => handleUpdateIntentCategory(msg.id, e.target.value)}
                          className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white outline-none capitalize cursor-pointer focus:border-indigo-500"
                        >
                          {AVAILABLE_EXPENSE_CATEGORIES.map((cat) => (
                            <option key={cat} value={cat} className="capitalize">
                              {cat}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="flex items-center gap-1.5">
                        <span className="text-slate-400 text-[11px]">Paid via:</span>
                        <select
                          value={msg.intent.payment_method || 'UPI'}
                          onChange={(e) => handleUpdateIntentPayment(msg.id, e.target.value)}
                          className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white outline-none cursor-pointer focus:border-indigo-500"
                        >
                          {AVAILABLE_PAYMENT_METHODS.map((pm) => (
                            <option key={pm} value={pm}>
                              {pm}
                            </option>
                          ))}
                        </select>
                      </div>

                      <button
                        type="button"
                        onClick={() => handleToggleEditIntent(msg.id)}
                        className="ml-auto px-2.5 py-1 rounded text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
                      >
                        Done
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Inline Interactive Chart Spec */}
              {msg.chartSpec && (
                <div className="mt-3">
                  <RechartsCard spec={msg.chartSpec} />
                </div>
              )}

              {/* Financial Insight & Calculation Card */}
              {msg.financialInsight && (
                <div className="mt-3">
                  <FinancialInsightCard
                    data={msg.financialInsight}
                    onAction={(action) => handleSend(action)}
                  />
                </div>
              )}

              {/* Interactive Action Chips */}
              {msg.sender === 'assistant' && extractActionChips(msg.content).length > 0 && (
                <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex flex-wrap gap-1.5">
                  {extractActionChips(msg.content).map((chip, chipIdx) => (
                    <button
                      key={chipIdx}
                      onClick={() => handleSend(chip)}
                      disabled={isStreaming}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-900/90 hover:bg-slate-800 border border-slate-700/60 text-[11px] font-medium text-slate-300 hover:text-white transition disabled:opacity-50 group shadow-sm"
                    >
                      <span>{chip}</span>
                      <ArrowRight className="w-3 h-3 text-slate-400 group-hover:text-white group-hover:translate-x-0.5 transition-all" />
                    </button>
                  ))}
                </div>
              )}

              {/* Message Action Bar: Copy and Quality Feedback */}
              {msg.sender === 'assistant' && !msg.isStreaming && (
                <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center justify-between text-slate-400 text-[11px]">
                  <button
                    type="button"
                    onClick={() => handleCopyMessage(msg.id, msg.content)}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded hover:bg-slate-800 hover:text-slate-200 transition"
                    title="Copy message"
                  >
                    {copiedMsgId === msg.id ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-400" />
                        <span className="text-[10px] text-emerald-400 font-medium">Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        <span className="text-[10px]">Copy</span>
                      </>
                    )}
                  </button>

                  <div className="flex items-center gap-1 relative">
                    <button
                      type="button"
                      onClick={() => handleFeedback(msg.id, 'thumbs_up', msg.userQuery, msg.content)}
                      className={`p-1 rounded hover:bg-slate-800 transition ${
                        msg.feedbackGiven === 'thumbs_up'
                          ? 'text-emerald-400 bg-emerald-500/10'
                          : 'hover:text-slate-200'
                      }`}
                      title="Helpful response"
                    >
                      <ThumbsUp className="w-3 h-3" />
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        setActiveFeedbackMsgId(activeFeedbackMsgId === msg.id ? null : msg.id)
                      }
                      className={`p-1 rounded hover:bg-slate-800 transition ${
                        msg.feedbackGiven === 'thumbs_down'
                          ? 'text-rose-400 bg-rose-500/10'
                          : 'hover:text-slate-200'
                      }`}
                      title="Report issue"
                    >
                      <ThumbsDown className="w-3 h-3" />
                    </button>

                    {/* Dislike Feedback Popover */}
                    {activeFeedbackMsgId === msg.id && (
                      <div className="absolute right-0 bottom-7 z-50 w-52 p-2.5 rounded-xl bg-slate-900 border border-slate-700 shadow-2xl text-[10px] space-y-1.5">
                        <div className="font-semibold text-slate-200 px-1">What went wrong?</div>
                        {[
                          { id: 'inaccurate_math', label: 'Inaccurate numbers / math' },
                          { id: 'too_wordy', label: 'Too wordy or technical' },
                          { id: 'misunderstood', label: 'Misunderstood my question' },
                          { id: 'broken_chart', label: 'Chart or table issue' },
                        ].map((opt) => (
                          <button
                            key={opt.id}
                            type="button"
                            onClick={() =>
                              handleFeedback(
                                msg.id,
                                'thumbs_down',
                                msg.userQuery,
                                msg.content,
                                opt.id
                              )
                            }
                            className="w-full text-left px-2 py-1 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition"
                          >
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        </div>
        <div ref={messagesEndRef} />
      </div>

      {/* Dynamic Contextual Prompts (Shown on cold start or when starting chat) */}
      {messages.length <= 1 && dynamicSuggestions.length > 0 && (
        <div className="px-4 py-2 bg-slate-950 border-t border-slate-900/60">
          <div className="max-w-3xl mx-auto w-full flex items-center gap-1.5 overflow-x-auto text-[11px] no-scrollbar">
            {dynamicSuggestions.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(p)}
                disabled={isStreaming}
                className="whitespace-nowrap px-3 py-1.5 rounded-full bg-slate-900 hover:bg-slate-800 border border-slate-800/80 text-slate-300 hover:text-white transition disabled:opacity-40 shadow-sm"
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/60 backdrop-blur-md">
        <div className="max-w-3xl mx-auto w-full">
          {/* Hidden File Inputs for Document Ingestion */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept=".pdf,.csv,.xlsx,.xls,image/*,application/pdf,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
            className="hidden"
          />
          <input
            type="file"
            ref={cameraInputRef}
            onChange={handleFileSelect}
            accept="image/*"
            capture="environment"
            className="hidden"
          />

          {/* Staged File Pill Preview */}
          {stagedFile && (
            <div className="flex items-center gap-2 px-3 py-1.5 mb-2.5 bg-slate-900/95 border border-slate-700/80 rounded-xl w-fit text-xs text-slate-200 shadow-lg animate-in fade-in slide-in-from-bottom-1">
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              <span className="font-medium max-w-[220px] truncate">{stagedFile.name}</span>
              <span className="text-[10px] text-slate-400 font-mono">({formatFileSize(stagedFile.size)})</span>
              <button
                type="button"
                onClick={() => setStagedFile(null)}
                className="ml-1 p-0.5 rounded-full hover:bg-slate-800 text-slate-400 hover:text-white transition"
                title="Remove attached file"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-2xl p-1.5 shadow-xl focus-within:border-indigo-500/80 transition"
          >
            <div className="flex items-center gap-0.5 text-slate-400 pl-1">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading || isStreaming}
                title="Upload Statement (PDF, CSV, Excel) or Receipt"
                className="p-2 rounded-xl hover:bg-slate-800 hover:text-white transition disabled:opacity-40"
              >
                {isUploading ? (
                  <Sparkles className="w-4 h-4 text-indigo-400 animate-spin" />
                ) : (
                  <Paperclip className="w-4 h-4" />
                )}
              </button>
              <button
                type="button"
                onClick={() => cameraInputRef.current?.click()}
                disabled={isUploading || isStreaming}
                title="Capture Photo of Receipt"
                className="p-2 rounded-xl hover:bg-slate-800 hover:text-white transition disabled:opacity-40"
              >
                <Camera className="w-4 h-4" />
              </button>
            </div>

            <input
              type="text"
              placeholder={
                stagedFile
                  ? language === 'hi'
                    ? `फ़ाइल '${stagedFile.name}' के बारे में प्रश्न पूछें या एंटर दबाएं...`
                    : `Ask a question about '${stagedFile.name}' or press Enter to analyze...`
                  : isStreaming
                  ? language === 'hi'
                    ? 'उत्तर आ रहा है... (अपना अगला प्रश्न यहाँ लिखें)'
                    : 'AI is streaming... (Type your next question)'
                  : language === 'hi'
                  ? "पूछें जैसे '2026 का खर्च प्रोजेक्ट करो', '3500 pizza', या कोई संदेश पेस्ट करें..."
                  : "Ask a question, paste your message, or type e.g. '3500 pizza'..."
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onPaste={handleInputPaste}
              className="flex-1 bg-transparent px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={isStreaming || isUploading || (!input.trim() && !stagedFile)}
              title={isStreaming ? "AI is responding..." : "Send message"}
              className="bg-indigo-600 hover:bg-indigo-500 text-white p-2.5 rounded-xl disabled:opacity-40 transition shadow-md shadow-indigo-600/30 flex items-center justify-center min-w-[36px]"
            >
              {isStreaming ? (
                <span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin block" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </form>
          <div className="mt-2 text-[10px] text-slate-500 flex items-center justify-between px-1">
            <span className="flex items-center gap-1">
              <Languages className="w-3 h-3 text-slate-400" />
              <span>Bilingual • Natural Hinglish Supported</span>
            </span>
            <span className="text-emerald-400 font-medium">● Context-Aware AI Engine Active</span>
          </div>
        </div>
      </div>
    </div>
  );
};
