import { useEffect, useState } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';
import { Redirect, router, useLocalSearchParams } from 'expo-router';
import { useSession } from '../auth/session';
import { useQuiz } from '../quiz/context';
import { resultFrom, uuid, type Result } from '../quiz/types';
import { Action, Page, styles } from '../components/ui';
export default function ResultScreen(){const {id,warning}=useLocalSearchParams<{id:string;warning:string}>();const {candidate,ready}=useSession();const {request,recent}=useQuiz();const [result,setResult]=useState<Result|null>(recent?.id===id?recent:null),[error,setError]=useState(''),[retry,setRetry]=useState(0);
 useEffect(()=>{let active=true;if(candidate&&uuid(id)&&recent?.id!==id)void request('attempts/'+id+'/').then(value=>{if(active){setResult(resultFrom(value));setError('');}}).catch(problem=>{if(active)setError(problem.message);});return()=>{active=false;};
 },[id,candidate,retry,request,recent]);
 if(ready&&!candidate)return <Redirect href="/"/>;
 return <Page>{!uuid(id)?<Text style={styles.text}>Open a result from your progress page.</Text>:result?<><Text style={styles.title}>{result.score} / {result.total} ✦</Text><Text style={styles.text}>{result.context.title} · {result.is_first?'First play':'Practice '+result.number}</Text>{warning==='1'&&<Text style={styles.message}>Score saved on the server. The phone could not clear the saved answers. Retrying them will show this same result.</Text>}{result.results.map(q=><View key={q.question_id} style={{gap:10}}><Text style={styles.text}>{q.position}. {q.prompt}</Text><Text style={styles.message}>{q.is_correct?'Got it!':'An aha for next time.'} Your pick: {q.choices[q.selected_choice]}</Text><Text style={styles.text}>Correct answer: {q.choices[q.correct_choice]}</Text><Text style={styles.text}>{q.explanation}</Text></View>)}<Action title="Play again" onPress={()=>router.replace({pathname:'/quiz',params:{version:result.version}})}/><Action title="My progress" onPress={()=>router.push('/progress')}/></>:!error&&<ActivityIndicator/>}{!!error&&<><Text style={styles.message}>{error}</Text><Action title="Try again" onPress={()=>setRetry(v=>v+1)}/></>}<Action title="Back" onPress={()=>router.back()}/></Page>;
}
