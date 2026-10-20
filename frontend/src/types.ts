export interface Product {
 id:string; name:string; category:string; price_inr:number; cpu_label:string; cpu_tier:number;
 ram_gb:number; storage_gb:number; storage_type:string; gpu_label:string; gpu_tier:number;
 dedicated_gpu:boolean|null; vram_gb:number|null; weight_kg:number|null; battery_hours:number|null;
 use_case_tags:string[]; feature_tags:string[]; is_synthetic:boolean;
}
export interface Requirements {
 category:string; use_cases:string[]; budget_max_inr:number|null; no_budget:boolean;
 min_ram_gb:number|null; min_storage_gb:number|null; require_dedicated_gpu:boolean|null;
 max_weight_kg:number|null; min_battery_hours:number|null; required_features:string[];
 preferences:string[]; ml_mode:string|null; conflicts:string[]; provenance:Record<string,string>;
 pending_budget:number|null;
}
export interface Recommendation {
 product:Product; score:number; score_components:Record<string,number>;
 reasons:string[]; trade_offs:string[]; unknowns:string[];
}
export interface Turn {
 conversation_id:string; response_type:'clarification'|'recommendations'|'no_match'|'informational';
 assistant_message:string; requirements:Requirements; state_version:number;
 recommendations:Recommendation[];
 evidence:{changed_fields:string[];eligible_count:number;searched:boolean;hard_filters:Record<string,unknown>;
 budget_proposal:{field:string;current:number;proposed:number;product_id:string;status:string}|null;ranking:string};
 mode:'live'|'demo'|'test';
}
export interface Message {id:string;role:'user'|'assistant';content:string;sequence:number;created_at:string;response:Turn|null}
export interface Conversation {id:string;requirements:Requirements;state_version:number;created_at:string;updated_at:string;messages:Message[];latest_response:Turn|null}
export interface Meta {name:string;catalogue:string;mode:string;provider:string;model:string|null;llm_configured:boolean}
export const money=(value:number)=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(value);
export const label=(s:string)=>s.replaceAll('_',' ');
