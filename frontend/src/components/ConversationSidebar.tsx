import { useEffect,useRef,useState } from 'react';
import { Plus, MessageSquare, RefreshCw, Loader2, AlignLeft, X } from 'lucide-react';
import type { ConversationSummary } from '../types';
import { displayTitle } from '../types';

interface Props {
  summaries: ConversationSummary[];
  activeId: string | null;
  loading: boolean;
  error: string;
  onNew: () => void;
  onSelect: (id: string) => void;
  onRetry: () => void;
  busy: boolean;
}

export function ConversationSidebar({summaries,activeId,loading,error,onNew,onSelect,onRetry,busy}:Props){
  const [open,setOpen]=useState(false);
  const drawerRef=useRef<HTMLDivElement>(null);

  // Close drawer when clicking outside on mobile
  useEffect(()=>{
    function handleClick(e:MouseEvent){
      if(open && drawerRef.current && !drawerRef.current.contains(e.target as Node)){
        setOpen(false);
      }
    }
    document.addEventListener('mousedown',handleClick);
    return ()=>document.removeEventListener('mousedown',handleClick);
  },[open]);

  // Close drawer on Escape
  useEffect(()=>{
    function handleKey(e:KeyboardEvent){if(e.key==='Escape')setOpen(false);}
    document.addEventListener('keydown',handleKey);
    return ()=>document.removeEventListener('keydown',handleKey);
  },[]);

  function handleSelect(id:string){
    onSelect(id);
    setOpen(false);
  }

  const sidebarContent=(
    <>
      <div className="sidebar-header">
        <span className="sidebar-brand">Chats</span>
        <button
          className="sidebar-new"
          onClick={onNew}
          disabled={busy}
          aria-label="Start a new conversation"
          title="New chat"
        >
          <Plus size={16}/><span>New chat</span>
        </button>
      </div>

      <div className="sidebar-list" role="list" aria-label="Recent conversations">
        {loading && (
          <div className="sidebar-state">
            <Loader2 size={16} className="spin-icon"/><span>Loading history…</span>
          </div>
        )}
        {!loading && error && (
          <div className="sidebar-state sidebar-error">
            <span>Could not load history</span>
            <button className="sidebar-retry" onClick={onRetry}>
              <RefreshCw size={12}/>Retry
            </button>
          </div>
        )}
        {!loading && !error && summaries.length===0 && (
          <div className="sidebar-state sidebar-empty">
            <MessageSquare size={20}/>
            <span>No previous chats</span>
          </div>
        )}
        {!loading && !error && summaries.map(s=>{
          const isActive=s.id===activeId;
          const title=displayTitle(s);
          return (
            <button
              key={s.id}
              role="listitem"
              className={`sidebar-item${isActive?' sidebar-item--active':''}`}
              onClick={()=>handleSelect(s.id)}
              disabled={busy}
              aria-current={isActive?'page':undefined}
              aria-label={title}
              title={title}
            >
              <MessageSquare size={14} className="sidebar-item-icon"/>
              <span className="sidebar-item-title">{title}</span>
            </button>
          );
        })}
      </div>
    </>
  );

  return (
    <>
      {/* Mobile toggle button */}
      <button
        className="sidebar-toggle"
        onClick={()=>setOpen(v=>!v)}
        aria-label={open?'Close chat history':'Open chat history'}
        aria-expanded={open}
      >
        {open?<X size={20}/>:<AlignLeft size={20}/>}
      </button>

      {/* Mobile overlay */}
      {open && <div className="sidebar-overlay" aria-hidden="true" onClick={()=>setOpen(false)}/>}

      {/* Desktop sidebar — always visible; mobile drawer — conditional */}
      <aside
        ref={drawerRef}
        className={`sidebar${open?' sidebar--open':''}`}
        aria-label="Conversation history"
      >
        {sidebarContent}
      </aside>
    </>
  );
}
