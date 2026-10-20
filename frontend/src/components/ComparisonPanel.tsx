import type { Recommendation } from '../types';
import { money } from '../types';
export function ComparisonPanel({items}:{items:Recommendation[]}){
 if(items.length<2)return null;
 const rows:[string,(i:Recommendation)=>string][]=[['Price',i=>money(i.product.price_inr)],['Memory',i=>`${i.product.ram_gb} GB`],['Storage',i=>`${i.product.storage_gb} GB`],['Weight',i=>i.product.weight_kg===null?'Unknown':`${i.product.weight_kg} kg`],['Graphics',i=>i.product.gpu_label],['Battery estimate',i=>i.product.battery_hours===null?'Unknown':`${i.product.battery_hours} h (synthetic)`]];
 return <details className="comparison panel"><summary>Compare the details side by side</summary><div className="table-scroll"><table><thead><tr><th scope="col">Specification</th>{items.map(i=><th scope="col" key={i.product.id}>{i.product.name.replace(' (Synthetic)','')}</th>)}</tr></thead><tbody>{rows.map(([label,value])=><tr key={label}><th scope="row">{label}</th>{items.map(i=><td key={i.product.id}>{value(i)}</td>)}</tr>)}</tbody></table></div></details>
}
