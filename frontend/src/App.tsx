import { useCallback, useEffect, useRef, useState } from 'react';
import { Leaf, ArrowRight, RefreshCw } from 'lucide-react';
import { api, ApiError } from './api/client';
import type { Conversation, ConversationSummary, Meta } from './types';
import { ConversationSidebar } from './components/ConversationSidebar';
import { ChatPanel } from './components/ChatPanel';
import { RequirementsPanel } from './components/RequirementsPanel';
import { ProductCard } from './components/ProductCard';
import { ComparisonPanel } from './components/ComparisonPanel';

// Active conversation key (legacy, preserved)
const ACTIVE_KEY = 'clearchoice.conversation.v1';
// Browser registry of all known conversation IDs
const REGISTRY_KEY = 'clearchoice.conversations.v1';

function loadRegistry(): string[] {
  try {
    const raw = localStorage.getItem(REGISTRY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    // Validate and deduplicate
    return [...new Set(parsed.filter((id: unknown) => typeof id === 'string' && id.length === 36))];
  } catch {
    return [];
  }
}

function saveRegistry(ids: string[]) {
  try {
    localStorage.setItem(REGISTRY_KEY, JSON.stringify(ids));
  } catch { /* quota exceeded — ignore */ }
}

function addToRegistry(id: string) {
  const current = loadRegistry();
  if (!current.includes(id)) {
    saveRegistry([id, ...current]);
  }
}

function removeFromRegistry(id: string) {
  saveRegistry(loadRegistry().filter(i => i !== id));
}

export default function App() {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [pendingText, setPendingText] = useState('');

  // Sidebar state
  const [summaries, setSummaries] = useState<ConversationSummary[]>([]);
  const [sidebarLoading, setSidebarLoading] = useState(false);
  const [sidebarError, setSidebarError] = useState('');

  const pending = useRef<{ text: string; id: string } | null>(null);
  const started = useRef(false);
  // Request token to prevent stale loads from overwriting active conversation
  const loadToken = useRef(0);

  // On first mount, import legacy active-conversation ID into registry
  useEffect(() => {
    const legacy = localStorage.getItem(ACTIVE_KEY);
    if (legacy) addToRegistry(legacy);
  }, []);

  const loadSidebar = useCallback(async () => {
    const ids = loadRegistry();
    if (ids.length === 0) { setSummaries([]); return; }
    setSidebarLoading(true);
    setSidebarError('');
    try {
      const result = await api.summaries(ids);
      // Remove stale IDs (returned fewer than requested)
      const found = new Set(result.map(s => s.id));
      const stale = ids.filter(id => !found.has(id));
      stale.forEach(removeFromRegistry);
      setSummaries(result);
    } catch {
      setSidebarError('history_error');
    } finally {
      setSidebarLoading(false);
    }
  }, []);

  async function initialize() {
    setLoading(true); setError('');
    try {
      const info = await api.meta(); setMeta(info);
      const stored = localStorage.getItem(ACTIVE_KEY);
      let c: Conversation;
      if (stored) {
        try {
          c = await api.get(stored);
        } catch (e) {
          if (e instanceof ApiError && e.status === 404) {
            removeFromRegistry(stored);
            c = await api.create();
            setNotice('The previous conversation was not found. A new one is ready.');
          } else throw e;
        }
      } else {
        c = await api.create();
      }
      localStorage.setItem(ACTIVE_KEY, c.id);
      addToRegistry(c.id);
      setConversation(c);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
    void loadSidebar();
  }

  useEffect(() => {
    if (!started.current) { started.current = true; void initialize(); }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function newConversation() {
    if (busy || loading) return;
    // Reuse current conversation if it has no messages
    if (conversation && conversation.messages.length === 0) {
      setDraft(''); setError(''); setNotice('');
      return;
    }
    setLoading(true);
    try {
      const c = await api.create();
      localStorage.setItem(ACTIVE_KEY, c.id);
      addToRegistry(c.id);
      setConversation(c);
      pending.current = null;
      setDraft(''); setError(''); setNotice('');
      void loadSidebar();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function openConversation(id: string) {
    if (busy || loading) return;
    if (id === conversation?.id) return;
    const token = ++loadToken.current;
    setLoading(true); setError(''); setNotice('');
    pending.current = null; setDraft('');
    try {
      const c = await api.get(id);
      if (token !== loadToken.current) return; // stale — another load started
      localStorage.setItem(ACTIVE_KEY, c.id);
      setConversation(c);
    } catch (e) {
      if (token !== loadToken.current) return;
      if (e instanceof ApiError && e.status === 404) {
        removeFromRegistry(id);
        setSummaries(prev => prev.filter(s => s.id !== id));
        setError('That conversation no longer exists. It may have been cleared from the database.');
      } else {
        setError((e as Error).message);
      }
    } finally {
      if (token === loadToken.current) setLoading(false);
    }
  }

  async function send(customText?: string) {
    const text = (customText ?? draft).trim();
    if (!text || !conversation || busy || loading) return;
    if (!pending.current || pending.current.text !== text)
      pending.current = { text, id: crypto.randomUUID() };
    setBusy(true); setPendingText(text); setError(''); setNotice('');
    try {
      await api.send(conversation.id, text, pending.current.id);
      const updated = await api.get(conversation.id);
      setConversation(updated);
      setDraft(''); pending.current = null;

      // Request title generation if this is the first turn
      const isFirstTurn = updated.messages.filter(m => m.role === 'user').length === 1;
      if (isFirstTurn && updated.title_status === 'pending') {
        // Fire-and-forget; never blocks the UI
        api.generateTitle(updated.id).then(t => {
          if (t.title) {
            setSummaries(prev =>
              prev.map(s => s.id === updated.id ? { ...s, title: t.title, title_status: t.title_status } : s)
            );
          }
        }).catch(() => { /* title generation failure is non-fatal */ });
      }
    } catch (e) {
      setError((e as Error).message);
      if (e instanceof ApiError && e.code === 'state_conflict') {
        try { setConversation(await api.get(conversation.id)); } catch { /* original error remains */ }
      }
    } finally {
      setBusy(false);
    }
  }

  const turn = conversation?.latest_response;
  const cards = turn?.recommendations || [];
  const totalCatalogue = meta?.catalogue_size ?? 40;
  const eligibleCount = turn?.evidence.eligible_count ?? cards.length;

  return (
    <div className="app app--with-sidebar">
      <ConversationSidebar
        summaries={summaries}
        activeId={conversation?.id ?? null}
        loading={sidebarLoading}
        error={sidebarError}
        onNew={newConversation}
        onSelect={openConversation}
        onRetry={loadSidebar}
        busy={busy || loading}
      />

      <div className="app-body">
        <header className="header">
          <a href="#" className="brand" aria-label="ClearChoice home">
            <span className="brand-icon"><Leaf size={22}/></span>ClearChoice
            <span className="brand-sub">LAPTOP ADVISOR</span>
          </a>
          {conversation && <span className="header-title">{conversation.title ?? 'New chat'}</span>}
        </header>

        <main>
          <div className="intro">
            <div>
              <span className="eyebrow">LESS GUESSWORK. BETTER FIT.</span>
              <h1>A laptop that fits <em>your life.</em></h1>
              <p>Tell us what matters. We'll compare the options and make the trade-offs clear.</p>
            </div>
            <div className="catalogue-badge">
              <span className="status-dot"/>Synthetic catalogue
              <span>For assessment demonstration</span>
            </div>
          </div>

          {meta?.mode === 'demo' && (
            <div className="notice mode-banner">Demo mode · A limited rule parser is active. Live AI interpretation requires Groq configuration.</div>
          )}
          {meta?.mode === 'live' && !meta.llm_configured && (
            <div className="notice mode-banner">Live AI is not configured yet. Add the Groq API key to the backend environment and restart it.</div>
          )}
          {error && (
            <div className="error-banner" role="alert">
              <span>{error}</span>
              {!conversation && <button onClick={initialize}><RefreshCw size={14}/>Retry connection</button>}
            </div>
          )}
          {notice && <p className="notice" role="status">{notice}</p>}
          {loading && <p className="small muted" role="status">Loading your conversation…</p>}

          <div className="workspace">
            <ChatPanel
              messages={conversation?.messages || []}
              draft={draft}
              setDraft={setDraft}
              send={() => void send()}
              onQuickSend={(opt) => void send(opt)}
              busy={busy}
              disabled={loading || !conversation}
              pendingText={pendingText}
            />
            <RequirementsPanel state={conversation?.requirements} changed={turn?.evidence.changed_fields || []}/>
          </div>

          <section className="results" aria-live="polite">
            <div className="results-title">
              <div>
                <span className="eyebrow">YOUR SHORTLIST</span>
                <h2>{
                  cards.length
                    ? `Showing ${cards.length} of ${eligibleCount} eligible laptop${eligibleCount === 1 ? '' : 's'} (${totalCatalogue} in catalogue)`
                    : turn?.response_type === 'no_match'
                      ? 'No match for these requirements.'
                      : turn?.response_type === 'clarification' && (turn?.evidence.changed_fields.length ?? 0) > 0
                        ? 'Requirements updated — answer above to see revised shortlist.'
                        : 'Good choices start with your needs.'
                }</h2>
              </div>
              {!!cards.length && <span className="small muted">Top {cards.length} shortlist <ArrowRight size={15}/></span>}
            </div>
            {cards.length
              ? <><div className="product-grid">{cards.map((item, i) => <ProductCard key={`${turn?.state_version}-${item.product.id}`} item={item} index={i}/>)}</div><ComparisonPanel items={cards}/></>
              : <div className="empty-results">{
                  turn?.response_type === 'no_match'
                    ? 'Your limits remain in place. Continue the conversation to decide whether any requirement should change.'
                    : turn?.response_type === 'clarification' && (turn?.evidence.changed_fields.length ?? 0) > 0
                      ? 'Your requirements have changed. Answer the clarification question above to generate your updated shortlist.'
                      : 'Your recommendations will appear here once we have enough information to search the catalogue.'
                }</div>
            }
          </section>
        </main>

        <footer>
          <span>ClearChoice</span>
          <p>All products, prices, and performance tiers are synthetic. Battery figures are estimates. No purchases are made here.</p>
        </footer>
      </div>
    </div>
  );
}
