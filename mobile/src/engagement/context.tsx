import { createContext, useContext, useMemo, type ReactNode } from 'react';
import { useCandidateRequest } from '../auth/candidate-request';
import { LikeController } from './likes';
import { DailyEvents } from './events';
const Context=createContext<{like:(version:number,identity:string)=>LikeController;events:DailyEvents}|null>(null);
export function EngagementProvider({children}:{children:ReactNode}){
 // The existing request wrapper binds the credential to the signed-in account.
 const request=useCandidateRequest();
 const value=useMemo(()=>{const likes=new Map<string,LikeController>();return {events:new DailyEvents(request),like(version:number,identity:string){const key=version+':'+identity;let controller=likes.get(key);if(!controller){controller=new LikeController('units/'+version+'/cards/'+identity+'/like/',request);likes.set(key,controller);if(likes.size>200)likes.delete(likes.keys().next().value!);}return controller;}};},[request]);
 return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useEngagement(){const value=useContext(Context);if(!value)throw new Error('Engagement provider missing.');return value;}
