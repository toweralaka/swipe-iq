import { useCallback } from 'react';
import * as SecureStore from 'expo-secure-store';
import { studentRequest } from '../api/student';
import { useSession } from './session';
import { ACCOUNT_KEY } from './session-actions';
import { forCandidate } from './request-binding';
export function useCandidateRequest(){
 const {candidate,authorize}=useSession();
 return useCallback((path:string,body?:unknown)=>authorize(credential=>forCandidate(candidate?.id,credential,()=>SecureStore.getItemAsync(ACCOUNT_KEY),()=>studentRequest(path,credential,body))),[authorize,candidate?.id]);
}
