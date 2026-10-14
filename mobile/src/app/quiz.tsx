import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, Text, View } from 'react-native';
import { Redirect, router, useLocalSearchParams } from 'expo-router';
import { useSession } from '../auth/session';
import { useQuiz } from '../quiz/context';
import { type Draft } from '../quiz/drafts';
import { quizFrom, type Quiz, type Choice } from '../quiz/types';
import { submitQuiz } from '../quiz/submit';
import { Action, Page, styles } from '../components/ui';
export default function QuickPlay() {
 const {version:raw}=useLocalSearchParams<{version:string}>();const version=Number(raw);
 const {candidate,ready}=useSession();const {store,lease,error:storeError,request,remember}=useQuiz();
 const [quiz,setQuiz]=useState<Quiz|null>(null),[draft,setDraft]=useState<Draft|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[reload,setReload]=useState(0);
 useEffect(()=>{let active=true;if(!lease||!Number.isSafeInteger(version)||version<1)return;
  void (async()=>{const saved=await store.get(lease,version);if(active)setDraft(saved);if(saved?.pending)return;
   const value=quizFrom(await request('units/'+version+'/quiz/'));const next=await store.begin(lease,value);if(active){setQuiz(value);setDraft(next);setError('');}
  })().catch(problem=>{if(active)setError(problem.message);});return()=>{active=false;};
 },[lease,store,version,reload,request]);
 if(ready&&!candidate)return <Redirect href="/"/>;
 if(!Number.isSafeInteger(version)||version<1)return <Page><Text style={styles.text}>Accept a dare from your feed.</Text></Page>;
 async function pick(id:number,choice:Choice){if(!lease)return;setBusy(true);setError('');try{setDraft(await store.answer(lease,version,id,choice));}catch(problem){setError(problem instanceof Error?problem.message:'Could not save that answer.');}finally{setBusy(false);}}
 async function submit(){if(!lease)return;setBusy(true);setError('');try{const {result,cleanupFailed}=await submitQuiz(store,lease,version,body=>request('attempts/',body));await store.get(lease,version);remember(result);router.replace({pathname:'/result',params:{id:result.id,warning:cleanupFailed?'1':''}});}catch(problem){setError(problem instanceof Error?problem.message:'Could not submit. Retry your saved answers.');try{setDraft(await store.get(lease,version));}catch{/* Session change already closes this screen. */}}finally{setBusy(false);}}
 return <Page><Text style={styles.title}>{quiz?.title??'Three picks. Feeling brave?'}</Text>
 <Text style={styles.text}>No timer, no pressure. Pick your answers or head back to scrolling.</Text>
 {!!(storeError||error)&&<Text accessibilityLiveRegion="polite" style={styles.message}>{storeError||error}</Text>}
 {draft?.pending ? <Text style={styles.text}>Your answers are saved. Retry to find out whether the server recorded them. Retrying counts this play only once.</Text> : quiz ? quiz.questions.map(question=><View key={question.id} style={{gap:12}}><Text style={styles.text}>{question.position}. {question.prompt}</Text>{(['a','b','c','d'] as Choice[]).map(c=><Pressable key={c} accessibilityRole="radio" accessibilityState={{checked:draft?.answers[question.id]===c,disabled:busy}} disabled={busy} onPress={()=>{void pick(question.id,c);}} style={[styles.input,{backgroundColor:draft?.answers[question.id]===c?'#D8FA72':'white'}]}><Text style={styles.text}>{c.toUpperCase()}. {question.choices[c]}</Text></Pressable>)}</View>) : !error&&!storeError&&<ActivityIndicator/>}
 {draft&&<><Text style={styles.message}>Answers stay on this phone until submission succeeds. Signing out removes unfinished answers.</Text><Action title={busy?'Please wait…':draft.pending?'Retry saved submission':'Show my score'} disabled={busy||draft.question_ids.some(id=>!draft.answers[id])} onPress={()=>{void submit();}}/></>}
 {!draft?.pending&&!!error&&<Action title="Try opening again" disabled={busy} onPress={()=>{setError('');setReload(v=>v+1);}}/>}
 </Page>;
}
