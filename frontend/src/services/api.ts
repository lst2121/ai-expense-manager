export interface KpiData {
  total_spend: number;
  monthly_variance: number;
  burn_rate: number;
  top_category: string;
  active_accounts: number;
  total_transactions: number;
  average_transaction: number;
  monthly_trend: Array<{ month: string; spend: number; count: number }>;
  category_distribution: Array<{ category: string; amount: number; count: number; percentage: number }>;
}

export interface TransactionItem {
  id: number;
  date: string;
  description: string;
  total_amount: number;
  payment_method: string;
  category: string;
  is_reconciled: boolean;
  notes: string;
  vendor_name: string;
  account_name: string;
  account_code: string;
}

export interface TransactionResponse {
  items: TransactionItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface AccountItem {
  id: number;
  code: string;
  name: string;
  type: string;
  description: string;
}

export interface ChartSpec {
  __chart__: boolean;
  chart_type: 'bar' | 'area' | 'pie' | 'line';
  title: string;
  description?: string;
  x_key: string;
  y_keys: string[];
  data: Array<Record<string, any>>;
}

export interface ExpenseIntent {
  amount: number;
  item: string;
  category: string;
  vendor?: string;
  payment_method?: string;
}

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

export interface AppNotification {
  id: string;
  type: 'anomaly' | 'briefing' | 'task';
  title: string;
  message: string;
  date: string;
  severity: 'high' | 'normal' | 'info';
  action_label?: string;
  action_prompt?: string;
  read: boolean;
}

export function getAuthHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const token = localStorage.getItem('auth_token') || localStorage.getItem('nivo_auth_token');
  const userStr = localStorage.getItem('nivo_user');
  const isSignedOut = localStorage.getItem('nivo_signed_out') === 'true';
  let userId = isSignedOut ? 'guest' : 'usr-lokender-2026';
  if (userStr) {
    try {
      const u = JSON.parse(userStr);
      if (u.id) userId = u.id;
    } catch (e) {}
  }
  const headers: Record<string, string> = {
    'X-User-Id': userId,
    ...extraHeaders,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export interface ReceiptWidgetData {
  widget_type: 'receipt_card';
  receipt: {
    vendor_name: string;
    date: string;
    total_amount: number;
    payment_method: string;
    category: string;
    confidence_score?: number;
    invoice_number?: string;
  };
}

const API_BASE = '/api';

export async function fetchKpis(): Promise<KpiData> {
  const res = await fetch(`${API_BASE}/analytics/kpis`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to fetch KPIs: ${res.statusText}`);
  return res.json();
}

export async function fetchTransactions(params: {
  page?: number;
  limit?: number;
  category?: string;
  search?: string;
  sort_by?: string;
  sort_order?: string;
}): Promise<TransactionResponse> {
  const query = new URLSearchParams();
  if (params.page) query.set('page', params.page.toString());
  if (params.limit) query.set('limit', params.limit.toString());
  if (params.category && params.category !== 'all') query.set('category', params.category);
  if (params.search) query.set('search', params.search);
  if (params.sort_by) query.set('sort_by', params.sort_by);
  if (params.sort_order) query.set('sort_order', params.sort_order);

  const res = await fetch(`${API_BASE}/transactions?${query.toString()}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to fetch transactions: ${res.statusText}`);
  return res.json();
}

export async function fetchAccounts(): Promise<AccountItem[]> {
  const res = await fetch(`${API_BASE}/accounts`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to fetch accounts: ${res.statusText}`);
  return res.json();
}

export async function createTransaction(payload: {
  description: string;
  category: string;
  amount: number;
  vendor_name?: string;
  date?: string;
  payment_method?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/transactions`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to create transaction: ${res.statusText}`);
  return res.json();
}

export interface StreamHandlers {
  onSession?: (data: { thread_id: string; session_id?: string; provider: string; language?: string }) => void;
  onToken: (token: string) => void;
  onToolStart?: (tool: string, input: any) => void;
  onToolEnd?: (tool: string, summary: string) => void;
  onChart?: (spec: ChartSpec) => void;
  onIntent?: (intent: ExpenseIntent) => void;
  onWidget?: (data: any) => void;
  onInsight?: (insight: FinancialInsightData) => void;
  onDone?: () => void;
  onError?: (error: string) => void;
}

export async function streamCopilotChat(
  message: string,
  threadId: string | null,
  provider: string = 'deepseek',
  handlers: StreamHandlers,
  signal?: AbortSignal,
  language: string = 'en',
  sessionId?: string | null
): Promise<void> {
  const maxRetries = 2;
  let attempt = 0;

  while (attempt <= maxRetries) {
    try {
      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          message,
          thread_id: threadId,
          session_id: sessionId || threadId,
          provider,
          language,
        }),
        signal,
      });

      if (!response.ok) {
        throw new Error(`Chat stream request failed: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('ReadableStream not supported by browser environment.');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Robust SSE block split handling both CRLF and LF
        const blocks = buffer.split(/\r?\n\r?\n/);
        buffer = blocks.pop() || '';

        for (const block of blocks) {
          if (!block.trim()) continue;

          let eventType = 'message';
          const dataLines: string[] = [];

          for (const rawLine of block.split(/\r?\n/)) {
            const line = rawLine.trim();
            if (line.startsWith('event:')) {
              eventType = line.slice(6).trim();
            } else if (line.startsWith('data:')) {
              dataLines.push(line.slice(5).trim());
            }
          }

          const dataStr = dataLines.join('\n');
          if (!dataStr) continue;

          try {
            const parsed = JSON.parse(dataStr);

            if (eventType === 'token' && handlers.onToken) {
              handlers.onToken(parsed.token);
            } else if (eventType === 'tool_start' && handlers.onToolStart) {
              handlers.onToolStart(parsed.tool, parsed.input);
            } else if (eventType === 'tool_end' && handlers.onToolEnd) {
              handlers.onToolEnd(parsed.tool, parsed.summary);
            } else if (eventType === 'chart' && handlers.onChart) {
              handlers.onChart(parsed.spec);
            } else if (eventType === 'intent' && handlers.onIntent) {
              handlers.onIntent(parsed.intent);
            } else if (eventType === 'widget' && handlers.onWidget) {
              handlers.onWidget(parsed);
            } else if (eventType === 'insight' && handlers.onInsight) {
              handlers.onInsight(parsed.insight);
            } else if (eventType === 'session' && handlers.onSession) {
              handlers.onSession(parsed);
            } else if (eventType === 'done' && handlers.onDone) {
              handlers.onDone();
            } else if (eventType === 'error' && handlers.onError) {
              handlers.onError(parsed.error || parsed.message);
            }
          } catch (err) {
            console.warn('Failed to parse SSE JSON:', dataStr, err);
          }
        }
      }

      if (handlers.onDone) handlers.onDone();
      return; // Stream completed successfully
    } catch (err: any) {
      if (signal?.aborted) {
        throw err; // User clicked abort
      }
      attempt++;
      if (attempt > maxRetries) {
        throw err;
      }
      console.warn(`[WealthCopilot] SSE connection flicker. Reconnecting in 2s (attempt ${attempt}/${maxRetries})...`);
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }
}

/**
 * Parses Bank / UPI SMS and extracts structured financial information.
 * Supports HDFC, SBI, ICICI, Axis, Paytm, PhonePe, GPay.
 */
export function parseBankSms(smsText: string): {
  amount: number | null;
  merchant: string | null;
  payment_mode: string;
  category: string;
  date: string;
} {
  const text = smsText.trim();

  // Extract amount: e.g. Rs. 450, INR 1200, Rs 3500.50, debited by 500
  const amountMatch = text.match(/(?:Rs\.?|INR|debited\s*(?:by|for)?\s*(?:Rs\.?|INR)?)\s*([\d,]+(?:\.\d{1,2})?)/i);
  let amount: number | null = null;
  if (amountMatch) {
    const cleanNum = amountMatch[1].replace(/,/g, '');
    amount = parseFloat(cleanNum);
  }

  // Extract merchant / recipient: e.g. "to ZOMATO", "at STARBUCKS", "VPA swiggy@icici", "to BLINKIT"
  const merchantMatch = text.match(/(?:to|at|vpa|paid to|transfer to)\s+([A-Za-z0-9\s&'-]+?)(?:\s+(?:on|via|ref|using|avail|bal|a\/c)|[.,]|$)/i);
  let merchant = merchantMatch ? merchantMatch[1].trim() : 'Local Merchant';

  // Extract Payment Mode
  let payment_mode = 'UPI';
  if (/credit\s*card/i.test(text)) payment_mode = 'Credit Card';
  else if (/debit\s*card/i.test(text)) payment_mode = 'Debit Card';
  else if (/net\s*banking|neft|rtgs|imps/i.test(text)) payment_mode = 'NetBanking';
  else if (/upi|gpay|phonepe|paytm/i.test(text)) payment_mode = 'UPI';

  // Detect Category based on Indian household keywords
  const lowerMerchant = (merchant + ' ' + text).toLowerCase();
  let category = 'groceries';

  if (/zomato|swiggy|pizza|burger|chai|coffee|restaurant|bistro|dining|cafe|mcdonald|domino/i.test(lowerMerchant)) {
    category = 'dining';
  } else if (/blinkit|zepto|instamart|bigbasket|dmart|kirana|supermarket|vegetable|fruit|dairy|ration/i.test(lowerMerchant)) {
    category = 'groceries';
  } else if (/electricity|bescom|tata power|adani|water|gas|indane|hp gas|broadband|airtel|jio|vi|recharge/i.test(lowerMerchant)) {
    category = 'utilities';
  } else if (/uber|ola|rapido|petrol|fuel|shell|metro|indian oil|hpcl|bpcl|auto/i.test(lowerMerchant)) {
    category = 'transportation';
  } else if (/rent|maintenance|society|landlord|flat/i.test(lowerMerchant)) {
    category = 'rent';
  } else if (/netflix|hotstar|prime|spotify|youtube|bookmyshow|movie|cinema/i.test(lowerMerchant)) {
    category = 'entertainment';
  } else if (/apollo|pharmacy|chemist|hospital|clinic|1mg|doctor|medplus/i.test(lowerMerchant)) {
    category = 'healthcare';
  } else if (/school|tuition|fees|college|books|stationery/i.test(lowerMerchant)) {
    category = 'subscriptions'; // mapped to family/education account
  }

  return {
    amount,
    merchant,
    payment_mode,
    category,
    date: new Date().toISOString().split('T')[0],
  };
}

export async function ingestDocument(
  file?: File,
  rawText?: string,
  sessionId?: string | null
): Promise<{
  status: string;
  is_financial?: boolean;
  widget_type: string;
  receipt?: {
    vendor_name: string;
    date: string;
    total_amount: number;
    payment_method: string;
    category: string;
    confidence_score?: number;
  };
  summary: string;
  session_id?: string;
}> {
  const formData = new FormData();
  if (file) formData.append('file', file);
  if (rawText) formData.append('raw_text', rawText);
  if (sessionId) formData.append('session_id', sessionId);

  const res = await fetch(`${API_BASE}/chat/ingest`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
  });
  if (!res.ok) throw new Error(`Document ingestion failed: ${res.statusText}`);
  return res.json();
}

export async function fetchDynamicSuggestions(language: string = 'en'): Promise<string[]> {
  try {
    const res = await fetch(`${API_BASE}/chat/suggestions?language=${encodeURIComponent(language)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.suggestions || [];
  } catch (err) {
    console.warn('Failed to fetch dynamic suggestions:', err);
    return [];
  }
}

export interface FeedbackPayload {
  message_id: string;
  thread_id?: string | null;
  rating: 'thumbs_up' | 'thumbs_down';
  category?: string;
  comment?: string;
  user_query?: string;
  assistant_response?: string;
}

export async function submitChatFeedback(payload: FeedbackPayload): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/chat/feedback`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
    });
    return res.ok;
  } catch (err) {
    console.error('Failed to submit chat feedback:', err);
    return false;
  }
}

export interface ChatSessionItem {
  id: string;
  title: string;
  is_pinned: boolean;
  created_at: string | null;
  updated_at: string | null;
  message_count: number;
}

export interface ChatMessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  chart_spec?: ChartSpec | null;
  tool_calls?: any[] | null;
  created_at: string | null;
}

export interface ChatSessionDetail {
  id: string;
  title: string;
  is_pinned: boolean;
  created_at: string | null;
  updated_at: string | null;
  messages: ChatMessageItem[];
}

export async function fetchChatSessions(): Promise<ChatSessionItem[]> {
  try {
    const res = await fetch(`${API_BASE}/chat/sessions`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.sessions || [];
  } catch (err) {
    console.error('Failed to fetch chat sessions:', err);
    return [];
  }
}

export async function createChatSession(title?: string): Promise<ChatSessionItem | null> {
  try {
    const res = await fetch(`${API_BASE}/chat/sessions`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ title: title || 'New Conversation' }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.session || null;
  } catch (err) {
    console.error('Failed to create chat session:', err);
    return null;
  }
}

export async function fetchSessionDetail(sessionId: string): Promise<ChatSessionDetail | null> {
  try {
    const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.session || null;
  } catch (err) {
    console.error(`Failed to fetch session detail ${sessionId}:`, err);
    return null;
  }
}

export async function updateChatSession(
  sessionId: string,
  payload: { title?: string; is_pinned?: boolean }
): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
      method: 'PATCH',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
    });
    return res.ok;
  } catch (err) {
    console.error(`Failed to update session ${sessionId}:`, err);
    return false;
  }
}

export async function deleteChatSession(sessionId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    return res.ok;
  } catch (err) {
    console.error(`Failed to delete session ${sessionId}:`, err);
    return false;
  }
}

export async function fetchNotifications(): Promise<{ notifications: AppNotification[]; unread_count: number }> {
  try {
    const res = await fetch(`${API_BASE}/notifications`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) return { notifications: [], unread_count: 0 };
    return res.json();
  } catch (err) {
    console.warn('Failed to fetch notifications:', err);
    return { notifications: [], unread_count: 0 };
  }
}

export async function dismissNotification(notificationId: string): Promise<void> {
  try {
    await fetch(`${API_BASE}/notifications/dismiss`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ notification_id: notificationId }),
    });
  } catch (err) {
    console.warn('Failed to dismiss notification:', err);
  }
}

