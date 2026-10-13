export type EventKind='view'|'dare_shown'|'dare_accepted';
export class DailyEvents {
 private sent=new Set<string>();private pending=new Map<string,Promise<void>>();
 private request:(path:string,body?:unknown)=>Promise<unknown>;private now:()=>number;
 constructor(request:(path:string,body?:unknown)=>Promise<unknown>,now:()=>number=Date.now){this.request=request;this.now=now;}
 track(version:number,identity:string,kind:EventKind):Promise<void>{
  const day=new Date(this.now()+3600000).toISOString().slice(0,10),key=day+':'+version+':'+identity+':'+kind;
  if(this.sent.has(key))return Promise.resolve();const existing=this.pending.get(key);if(existing)return existing;
  const action=Promise.resolve().then(()=>this.request('engagement/events/',{version,card_identity:identity,kind})).then(()=>{this.sent.add(key);if(this.sent.size>1000)this.sent.delete(this.sent.values().next().value!);}).catch(()=>{/* Best effort only; nothing is saved or queued offline. */}).finally(()=>{this.pending.delete(key);});
  this.pending.set(key,action);return action;
 }
}
