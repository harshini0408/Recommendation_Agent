import { Check, SlidersHorizontal } from 'lucide-react';
import type { Requirements } from '../types';
import { money,label } from '../types';
export function RequirementsPanel({state,changed}:{state?:Requirements;changed:string[]}){
 const mandatory:[string,string][]=[];
 if(state?.min_ram_gb)mandatory.push(['min_ram_gb',`${state.min_ram_gb} GB RAM minimum`]);
 if(state?.min_storage_gb)mandatory.push(['min_storage_gb',`${state.min_storage_gb} GB storage minimum`]);
 if(state?.require_dedicated_gpu!==null&&state?.require_dedicated_gpu!==undefined)mandatory.push(['require_dedicated_gpu',state.require_dedicated_gpu?'Dedicated graphics required':'No dedicated graphics']);
 if(state?.max_weight_kg)mandatory.push(['max_weight_kg',`At most ${state.max_weight_kg} kg`]);
 if(state?.min_battery_hours)mandatory.push(['min_battery_hours',`At least ${state.min_battery_hours} h battery estimate`]);
 state?.required_features.forEach(x=>mandatory.push(['required_features',x]));
 return <aside className="requirements panel"><div className="panel-title"><SlidersHorizontal size={18}/><h2>Your requirements</h2></div>
 <p className="muted small">Updated as the conversation develops.</p>
 <div className={`budget ${changed.includes('budget_max_inr')?'changed':''}`}><span className="eyebrow">BUDGET CEILING</span><strong>{state?.budget_max_inr?money(state.budget_max_inr):state?.no_budget?'No fixed budget':'Not set yet'}</strong></div>
 <section><h3>Main use</h3><div className="tags">{state?.use_cases.length?state.use_cases.map(x=><span className="tag" key={x}>{label(x)}</span>):<span className="muted small">Tell us what you’ll use it for.</span>}</div>{state?.ml_mode&&<p className="small muted">ML experiments: {state.ml_mode}</p>}</section>
 <section><h3>Must have</h3>{mandatory.length?<ul className="check-list">{mandatory.map(([key,text],i)=><li className={changed.includes(key)?'changed':''} key={i}><Check size={14}/>{text}</li>)}</ul>:<p className="small muted">No additional hard constraints.</p>}</section>
 <section><h3>Nice to have</h3><div className="tags">{state?.preferences.length?state.preferences.map(x=><span className="tag light" key={x}>{label(x)}</span>):<span className="small muted">Optional preferences go here.</span>}</div></section>
 {!!state?.conflicts.length&&<div className="notice">{state.conflicts.map(x=><p key={x}>{x}</p>)}</div>}
 {state?.pending_budget&&<div className="notice">Budget change proposed: {money(state.pending_budget)}. Your current budget stays in place until you agree.</div>}
 <div className="privacy-note">Mandatory limits are checked against catalogue records before products are ranked.</div></aside>
}
