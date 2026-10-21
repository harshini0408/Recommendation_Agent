import { useEffect,useRef } from 'react';
import { ArrowUp, Sparkles, User } from 'lucide-react';
import type { Message } from '../types';
interface Props {messages:Message[];draft:string;setDraft:(v:string)=>void;send:()=>void;onQuickSend?:(v:string)=>void;busy:boolean;disabled:boolean;pendingText?:string}
export function ChatPanel({messages,draft,setDraft,send,onQuickSend,busy,disabled,pendingText}:Props){
 const bottom=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  bottom.current?.scrollIntoView({behavior:'smooth',block:'nearest'});
 },[messages,busy]);
 const examples=['A laptop for programming under ₹80,000','A lightweight laptop for college','Compare laptops for local machine learning'];
 const lastMsg=messages.length?messages[messages.length-1]:null;
 const isMlClarification=lastMsg?.role==='assistant'&&(lastMsg.response?.requirements.clarification_field==='ml_mode'||(lastMsg.content.toLowerCase().includes('local')&&lastMsg.content.toLowerCase().includes('cloud')));
 return <section className="chat panel"><div className="chat-top"><div><span className="eyebrow">YOUR LAPTOP ADVISOR</span><h2>Let’s find the right fit.</h2></div><span className="small muted">One conversation. Clear choices.</span></div>
 <div className="messages" aria-live="polite">
 {!messages.length&&<div className="welcome"><div className="assistant-icon"><Sparkles size={22}/></div><h3>What do you need your next laptop to do?</h3><p>I’ll help you narrow down the options, keep track of your needs, and explain the trade-offs.</p><div className="examples">{examples.map(x=><button disabled={busy||disabled} key={x} onClick={()=>setDraft(x)}>{x}<span>↗</span></button>)}</div></div>}
 {messages.map(m=><div className={`message ${m.role}`} key={m.id}><div className="avatar">{m.role==='assistant'?<Sparkles size={15}/>:<User size={15}/>}</div><div><span className="speaker">{m.role==='assistant'?'ClearChoice':'You'}</span><p>{m.content}</p></div></div>)}
 {busy&&<><div className="message user"><div className="avatar"><User size={15}/></div><div><span className="speaker">You</span><p>{pendingText}</p></div></div><div className="thinking"><span/> Checking your request…</div></>}
 <div ref={bottom}/></div>
 {isMlClarification&&!busy&&<div className="quick-replies" role="group" aria-label="Suggested responses">{['Local','Cloud','Both','Not sure'].map(opt=><button key={opt} type="button" className="quick-reply-btn" disabled={busy||disabled} onClick={()=>{if(onQuickSend)onQuickSend(opt);else{setDraft(opt);send();}}}>{opt}</button>)}</div>}
 <form className="composer" onSubmit={e=>{e.preventDefault();send()}}><label className="sr-only" htmlFor="message">Your message</label><textarea id="message" value={draft} onChange={e=>setDraft(e.target.value)} disabled={busy||disabled} maxLength={4000} rows={2} placeholder="Tell me your use case, budget, or what you’d like to change…" onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();send()}}}/><button className="send" type="submit" aria-label="Send message" disabled={!draft.trim()||busy||disabled}><ArrowUp size={20}/></button></form>
 <div className="composer-note">Enter to send · Shift + Enter for a new line</div></section>
}
