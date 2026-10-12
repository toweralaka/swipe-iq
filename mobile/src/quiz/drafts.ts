import { choice, uuid, type Choice, type Quiz } from './types.ts';
export type Draft = { version: number; submission_id: string; question_ids: number[]; answers: Record<string,Choice>; pending: boolean };
export type DraftDisk = { read: () => Promise<string | null>; write: (data:string) => Promise<void>; clear: () => Promise<void> };
export type DraftLease = { owner: string; generation: number };
type State = { owner: string; drafts: Draft[] };
const clone = <T,>(value:T):T => JSON.parse(JSON.stringify(value));
export class QuizDrafts {
 private disk:DraftDisk; private state:State={owner:'',drafts:[]}; private loaded=false; private generation=0; private queue:Promise<unknown>=Promise.resolve();
 constructor(disk:DraftDisk) { this.disk=disk; }
 private serial<T>(action:()=>Promise<T>):Promise<T> { const promise=this.queue.then(action); this.queue=promise.catch(()=>{}); return promise; }
 private async load() {
  if(this.loaded)return; const raw=await this.disk.read();
  if(raw) {
   let data:State; try { data=JSON.parse(raw) as State; } catch { throw new Error('Saved quiz answers could not be read. They have not been removed.'); }
   if(raw.length>64000 || !data || typeof data.owner!=='string' || !Array.isArray(data.drafts) || data.drafts.length>20 || !data.drafts.every(d=>Number.isSafeInteger(d.version)&&d.version>0&&uuid(d.submission_id)&&typeof d.pending==='boolean'&&Array.isArray(d.question_ids)&&d.question_ids.length===3&&new Set(d.question_ids).size===3&&d.question_ids.every(id=>Number.isSafeInteger(id)&&id>0)&&d.answers&&(!d.pending||d.question_ids.every(id=>['a','b','c','d'].includes(d.answers[id])))&&Object.entries(d.answers).every(([id,c])=>d.question_ids.includes(Number(id))&&['a','b','c','d'].includes(c)))) throw new Error('Saved quiz answers could not be read. They have not been removed.');
   this.state=data;
  }
  this.loaded=true;
 }
 private check(lease:DraftLease) { if(lease.owner!==this.state.owner || lease.generation!==this.generation)throw new Error('The signed-in account changed. Reopen the quiz.'); }
 private async persist(next:State) { await this.disk.write(JSON.stringify(next)); this.state=next; }
 activate(owner:string):Promise<DraftLease> { return this.serial(async()=>{await this.load();if(owner!==this.state.owner){await this.disk.clear();this.generation++;await this.persist({owner,drafts:[]});}return {owner,generation:this.generation};}); }
 clear():Promise<void> { return this.serial(async()=>{this.generation++;await this.disk.clear();this.state={owner:'',drafts:[]};this.loaded=true;}); }
 begin(lease:DraftLease,quiz:Quiz):Promise<Draft> { return this.serial(async()=>{
  await this.load();this.check(lease);const ids=quiz.questions.map(q=>q.id);const existing=this.state.drafts.find(d=>d.version===quiz.version);
  if(existing){if(JSON.stringify(existing.question_ids)!==JSON.stringify(ids))throw new Error('This quiz changed. Your saved answers were kept.');return clone(existing);}
  if(this.state.drafts.length>=20)throw new Error('You have 20 unfinished quizzes. Finish one before starting another.');
  const draft:Draft={version:quiz.version,submission_id:quiz.submission_id,question_ids:ids,answers:{},pending:false};await this.persist({...this.state,drafts:[...this.state.drafts,draft]});return clone(draft);
 }); }
 answer(lease:DraftLease,version:number,id:number,selected:Choice):Promise<Draft> { return this.serial(async()=>{
  this.check(lease);const next=clone(this.state),draft=next.drafts.find(d=>d.version===version);if(!draft||!draft.question_ids.includes(id))throw new Error('Open the quiz again.');if(draft.pending)throw new Error('Retry your saved submission before changing answers.');draft.answers[id]=choice(selected);await this.persist(next);return clone(draft);
 }); }
 lock(lease:DraftLease,version:number):Promise<Draft> { return this.serial(async()=>{
  this.check(lease);const next=clone(this.state),draft=next.drafts.find(d=>d.version===version);if(!draft||draft.question_ids.some(id=>!draft.answers[id]))throw new Error('Pick an answer for all three questions first.');draft.pending=true;await this.persist(next);return clone(draft);
 }); }
 remove(lease:DraftLease,version:number):Promise<void> {return this.serial(async()=>{this.check(lease);await this.persist({...this.state,drafts:this.state.drafts.filter(d=>d.version!==version)});});}
 list(lease:DraftLease):Promise<Draft[]> {return this.serial(async()=>{await this.load();this.check(lease);return clone(this.state.drafts);});}
 get(lease:DraftLease,version:number):Promise<Draft|null> {return this.serial(async()=>{await this.load();this.check(lease);const draft=this.state.drafts.find(d=>d.version===version);return draft?clone(draft):null;});}
}
export function submission(draft:Draft) { return {version:draft.version,submission_id:draft.submission_id,answers:draft.question_ids.map(id=>({question_id:id,choice:draft.answers[id]}))}; }
