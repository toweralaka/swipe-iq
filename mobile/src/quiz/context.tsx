import * as SecureStore from 'expo-secure-store';
import { ACCOUNT_KEY } from '../auth/session-actions';
import { forCandidate } from './request';
import { useCallback, createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { useSession } from '../auth/session';
import { apiBaseUrl, studentRequest } from '../api/student';
import { quizDrafts } from './device';
import { type Result } from './types';
import { type DraftLease } from './drafts';
const Context=createContext<{lease:DraftLease|null;error:string;recent:Result|null;remember:(result:Result)=>void;request:(path:string,body?:unknown)=>Promise<unknown>}|null>(null);
export function QuizProvider({children}:{children:ReactNode}) {
 const {candidate,authorize}=useSession(); const [lease,setLease]=useState<DraftLease|null>(null);const [error,setError]=useState('');const [recent,setRecent]=useState<{owner:string;result:Result}|null>(null);
 let owner='';try{if(candidate)owner=apiBaseUrl()+'|'+candidate.id;}catch{/* The feed shows setup errors before quiz navigation. */}
 const request=useCallback((path:string,body?:unknown)=>authorize(credential=>forCandidate(candidate?.id,credential,()=>SecureStore.getItemAsync(ACCOUNT_KEY),()=>studentRequest(path,credential,body))),[authorize,candidate?.id]);
 useEffect(()=>{let active=true;if(owner)void quizDrafts.activate(owner).then(value=>{if(active){setLease(value);setError('');}},problem=>{if(active)setError(problem.message);});return()=>{active=false;};},[owner]);
 return <Context.Provider key={owner} value={{recent:recent?.owner===owner?recent.result:null,remember:result=>setRecent({owner,result}),lease:lease?.owner===owner?lease:null,error,request}}>{children}</Context.Provider>;
}
export function useQuiz(){const value=useContext(Context);if(!value)throw new Error('Quiz provider missing.');return {...value,store:quizDrafts};}
