import { resultFrom, type Result } from './types.ts';
import { QuizDrafts, submission, type DraftLease } from './drafts.ts';
export async function submitQuiz(store:QuizDrafts,lease:DraftLease,version:number,request:(body:unknown)=>Promise<unknown>):Promise<{result:Result;cleanupFailed:boolean}> {
 const draft=await store.lock(lease,version);
 const result=resultFrom(await request(submission(draft)));
 if(result.version!==version)throw new Error('The result belongs to another quiz. Retry your saved submission.');
 let cleanupFailed=false;try{await store.remove(lease,version);}catch{cleanupFailed=true;}
 return {result,cleanupFailed};
}
