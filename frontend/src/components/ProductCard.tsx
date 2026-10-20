import { useState } from 'react';
import { CheckCircle2, Laptop, ChevronDown } from 'lucide-react';
import type { Recommendation,Product } from '../types';
import { money } from '../types';
import { api } from '../api/client';
export function ProductCard({item,index}:{item:Recommendation;index:number}){
 const p=item.product;const [detail,setDetail]=useState<Product|null>(null);const [open,setOpen]=useState(false);const [error,setError]=useState('');
 async function toggle(){if(open){setOpen(false);return}try{const row=await api.product(p.id);setDetail(row);setOpen(true);setError('')}catch(e){setError((e as Error).message)}}
 return <article className="product-card"><div className="product-art"><span className="rank">{index===0?'01 · Top match':'02 · Alternative'}</span><Laptop size={76} strokeWidth={1}/><span className="synthetic">SYNTHETIC CATALOGUE</span></div><div className="product-body"><span className="eyebrow">{p.id}</span><h3>{p.name.replace(' (Synthetic)','')}</h3><div className="price">{money(p.price_inr)}</div><div className="specs"><span>{p.ram_gb} GB RAM</span><span>{p.storage_gb} GB SSD</span><span>{p.weight_kg!==null?`${p.weight_kg} kg`:'Weight unknown'}</span></div>
 <h4>Why it fits</h4><ul className="fit-list">{item.reasons.map(x=><li key={x}><CheckCircle2 size={14}/><span>{x}</span></li>)}</ul>
 <h4>The trade-off</h4>{item.trade_offs.length?<ul className="tradeoffs">{item.trade_offs.map(x=><li key={x}>{x}</li>)}</ul>:<p className="small muted">No additional disadvantage identified by the available comparison rules. Review the specifications and unknowns.</p>}
 {!!item.unknowns.length&&<p className="unknown small">{item.unknowns.join(' ')}</p>}
 <details className="score"><summary>How this was ranked</summary><p>Heuristic suitability score: {item.score.toFixed(3)}. This is not a probability or benchmark.</p>{Object.entries(item.score_components).map(([k,v])=><div key={k}>{k}: {v.toFixed(3)} contribution</div>)}</details>
 <button className="detail-button" onClick={toggle}>{open?'Hide':'View'} catalogue details <ChevronDown size={14}/></button>{error&&<p role="alert" className="error-text">{error}</p>}
 {open&&detail&&<dl className="detail-grid"><dt>CPU</dt><dd>{detail.cpu_label}</dd><dt>Graphics</dt><dd>{detail.gpu_label}</dd><dt>VRAM</dt><dd>{detail.vram_gb===null?'Unknown':`${detail.vram_gb} GB`}</dd><dt>Battery estimate</dt><dd>{detail.battery_hours===null?'Unknown':`${detail.battery_hours} h (synthetic)`}</dd><dt>Features</dt><dd>{detail.feature_tags.join(', ')}</dd></dl>}
 </div></article>
}
