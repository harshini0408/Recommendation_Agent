import type { Conversation, ConversationSummary, Meta, Product, TitleOut, Turn } from '../types';
const BASE=(import.meta.env.VITE_API_BASE_URL||'http://localhost:8000').replace(/\/$/,'');
export class ApiError extends Error {constructor(message:string,public status:number,public code:string){super(message)}}
async function request<T>(path:string,init?:RequestInit):Promise<T>{
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),75000);
 try{
  const response=await fetch(`${BASE}/api/v1${path}`,{...init,signal:controller.signal,headers:{'Content-Type':'application/json',...init?.headers}});
  const body=await response.json();
  if(!response.ok)throw new ApiError(body.error?.message||'Request failed.',response.status,body.error?.code||'request_failed');
  return body as T;
 }catch(error){
  if(error instanceof ApiError)throw error;
  throw new ApiError('Unable to reach the backend, or the request timed out. Check that the server is running, then retry.',0,'connection_error');
 }finally{clearTimeout(timer)}
}
export const api={
 meta:()=>request<Meta>('/meta'),
 create:()=>request<Conversation>('/conversations',{method:'POST'}),
 get:(id:string)=>request<Conversation>(`/conversations/${id}`),
 send:(id:string,content:string,client_message_id:string)=>request<Turn>(`/conversations/${id}/messages`,{method:'POST',body:JSON.stringify({content,client_message_id})}),
 product:(id:string)=>request<Product>(`/products/${encodeURIComponent(id)}`),
 summaries:(ids:string[])=>request<ConversationSummary[]>('/conversations/summaries',{method:'POST',body:JSON.stringify({ids})}),
 generateTitle:(id:string)=>request<TitleOut>(`/conversations/${id}/title`,{method:'POST'}),
};
