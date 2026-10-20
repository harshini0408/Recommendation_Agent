import { useEffect,useRef,useState } from 'react';
import { Plus, Leaf, ArrowRight, RefreshCw } from 'lucide-react';
import { api,ApiError } from './api/client';
import type { Conversation,Meta } from './types';
import { ChatPanel } from './components/ChatPanel';
import { RequirementsPanel } from './components/RequirementsPanel';
import { ProductCard } from './components/ProductCard';
import { ComparisonPanel } from './components/ComparisonPanel';
const STORAGE='clearchoice.conversation.v1';
export default function App(){
 const [conversation,setConversation]=useState<Conversation|null>(null);
 const [meta,setMeta]=useState<Meta|null>(null);const [draft,setDraft]=useState('');
 const [busy,setBusy]=useState(false);const [loading,setLoading]=useState(true);
 const [error,setError]=useState('');const [notice,setNotice]=useState('');
 const [pendingText,setPendingText]=useState('');
 const pending=useRef<{text:string;id:string}|null>(null);
 const started=useRef(false);
 async function initialize(){
  setLoading(true);setError('');
  try{
   const info=await api.meta();setMeta(info);
   const stored=localStorage.getItem(STORAGE);let c:Conversation;
   if(stored){try{c=await api.get(stored)}catch(e){if(e instanceof ApiError&&e.status===404){c=await api.create();setNotice('The previous conversation was not found. A new one is ready.')}else throw e}}
   else c=await api.create();
   localStorage.setItem(STORAGE,c.id);setConversation(c);
  }catch(e){setError((e as Error).message)}finally{setLoading(false)}
 }
 useEffect(()=>{if(!started.current){started.current=true;void initialize()}},[]);
 async function newConversation(){if(busy||loading)return;setLoading(true);try{const c=await api.create();setConversation(c);localStorage.setItem(STORAGE,c.id);pending.current=null;setDraft('');setError('');setNotice('')}catch(e){setError((e as Error).message)}finally{setLoading(false)}}
 async function send(){
  const text=draft.trim();if(!text||!conversation||busy||loading)return;
  if(!pending.current||pending.current.text!==text)pending.current={text,id:crypto.randomUUID()};
  setBusy(true);setPendingText(text);setError('');setNotice('');
  try{
   await api.send(conversation.id,text,pending.current.id);
   // Refresh is authoritative; if it fails, keep the request ID for safe retry.
   const updated=await api.get(conversation.id);setConversation(updated);setDraft('');pending.current=null;
  }catch(e){
   setError((e as Error).message);
   if(e instanceof ApiError&&e.code==='state_conflict'){
    try{setConversation(await api.get(conversation.id))}catch{/* original error remains visible */}
   }
  }finally{setBusy(false)}
 }
 const turn=conversation?.latest_response;const cards=turn?.recommendations||[];
 return <div className="app"><header className="header"><a href="#" className="brand" aria-label="ClearChoice home"><span className="brand-icon"><Leaf size={22}/></span>ClearChoice<span className="brand-sub">LAPTOP ADVISOR</span></a><button className="new-button" onClick={newConversation} disabled={busy||loading}><Plus size={16}/>New conversation</button></header>
 <main><div className="intro"><div><span className="eyebrow">LESS GUESSWORK. BETTER FIT.</span><h1>A laptop that fits <em>your life.</em></h1><p>Tell us what matters. We’ll compare the options and make the trade-offs clear.</p></div><div className="catalogue-badge"><span className="status-dot"/>Synthetic catalogue<span>For assessment demonstration</span></div></div>
 {meta?.mode==='demo'&&<div className="notice mode-banner">Demo mode · A limited rule parser is active. Live AI interpretation requires Groq configuration.</div>}
 {meta?.mode==='live'&&!meta.llm_configured&&<div className="notice mode-banner">Live AI is not configured yet. Add the Groq API key to the backend environment and restart it.</div>}
 {error&&<div className="error-banner" role="alert"><span>{error}</span>{!conversation&&<button onClick={initialize}><RefreshCw size={14}/>Retry connection</button>}</div>}
 {notice&&<p className="notice" role="status">{notice}</p>}
 {loading&&<p className="small muted" role="status">Loading your conversation…</p>}
 <div className="workspace"><ChatPanel messages={conversation?.messages||[]} draft={draft} setDraft={setDraft} send={send} busy={busy} disabled={loading||!conversation} pendingText={pendingText}/><RequirementsPanel state={conversation?.requirements} changed={turn?.evidence.changed_fields||[]}/></div>
 <section className="results" aria-live="polite"><div className="results-title"><div><span className="eyebrow">YOUR SHORTLIST</span><h2>{cards.length?'The options worth a closer look.':turn?.response_type==='no_match'?'No match for these requirements.':'Good choices start with your needs.'}</h2></div>{!!cards.length&&<span className="small muted">{cards.length} option{cards.length===1?'':'s'} <ArrowRight size={15}/></span>}</div>
 {cards.length?<><div className="product-grid">{cards.map((item,i)=><ProductCard key={`${turn?.state_version}-${item.product.id}`} item={item} index={i}/>)}</div><ComparisonPanel items={cards}/></>:<div className="empty-results">{turn?.response_type==='no_match'?'Your limits remain in place. Continue the conversation to decide whether any requirement should change.':'Your recommendations will appear here once we have enough information to search the catalogue.'}</div>}
 </section></main><footer><span>ClearChoice</span><p>All products, prices, and performance tiers are synthetic. Battery figures are estimates. No purchases are made here.</p></footer></div>
}
