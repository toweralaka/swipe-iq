import { useEffect, useState } from 'react';
import { ActivityIndicator, Text } from 'react-native';
import { Redirect, router } from 'expo-router';
import { useSession } from '../auth/session';
import { type Draft } from '../quiz/drafts';
import { useQuiz } from '../quiz/context';
import { attemptFrom, progressFrom, type Attempt, type Progress } from '../quiz/types';
import { nextPath } from '../feed/types';
import { apiBaseUrl } from '../api/student';
import { Action, Page, styles } from '../components/ui';
export default function ProgressScreen(){const {candidate,ready}=useSession();const {request,store,lease,error:storeError}=useQuiz();const [drafts,setDrafts]=useState<Draft[]>([]);const [progress,setProgress]=useState<Progress|null>(null),[attempts,setAttempts]=useState<Attempt[]>([]),[next,setNext]=useState<string|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0),[busy,setBusy]=useState(false);
 useEffect(()=>{let active=true;if(!candidate)return;void Promise.all([request('progress/'),request('attempts/')]).then(([summary,history])=>{const page=history as {results:unknown[];next:string|null};if(active){setProgress(progressFrom(summary));setAttempts(page.results.map(attemptFrom));setNext(page.next);setError('');}}).catch(problem=>{if(active)setError(problem.message);});return()=>{active=false;};
 },[candidate,retry,request]);
 useEffect(()=>{let active=true;if(lease)void store.list(lease).then(value=>{if(active)setDrafts(value);}).catch(()=>{});return()=>{active=false;};},[lease,store,retry]);
 async function more(){if(!next||busy)return;setBusy(true);try{const path=nextPath(next,apiBaseUrl(),'attempts/');const page=await request(path) as {results:unknown[];next:string|null};setAttempts(old=>[...old,...page.results.map(attemptFrom)]);setNext(page.next);setError('');}catch(problem){setError(problem instanceof Error?problem.message:'Could not load more.');}finally{setBusy(false);}}
 if(ready&&!candidate)return <Redirect href="/"/>;
 return <Page><Text style={styles.title}>Look what stuck ✦</Text><Text style={styles.text}>Only you can see this page. Playing is optional.</Text>{drafts.map((draft,index)=><Action key={draft.version} title={(draft.pending?'Retry saved dare':'Resume dare')+' '+(index+1)+' · '+Object.keys(draft.answers).length+'/3 picks saved'} onPress={()=>router.push({pathname:'/quiz',params:{version:draft.version}})}/>)}{!!storeError&&<Text style={styles.message}>{storeError}</Text>}{progress?<><Text style={styles.text}>{progress.completed_units} posts tried · {progress.total_attempts} plays</Text><Text style={styles.text}>First-play score: {progress.first_attempt_percentage===null?'No completed plays yet':progress.first_attempt_percentage+'%'}</Text><Text style={styles.text}>These are optional plays, not posts you must finish. Playing again stays in your history and does not raise your first-play score.</Text>{attempts.map(attempt=><Action key={attempt.id} title={attempt.context.title+' · '+attempt.score+'/3 · '+(attempt.is_first?'First play':'Practice '+attempt.number)} onPress={()=>router.push({pathname:'/result',params:{id:attempt.id}})}/>)}{next&&<Action title={busy?'Loading…':'More plays'} disabled={busy} onPress={()=>{void more();}}/>}</>:!error&&<ActivityIndicator/>}{!!error&&<Text style={styles.message}>{error}</Text>}<Action title="Refresh" onPress={()=>setRetry(v=>v+1)}/></Page>;
}
