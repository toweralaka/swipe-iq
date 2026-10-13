import { useEffect, useMemo, useSyncExternalStore } from 'react';
import { AppState, Text, View } from 'react-native';
import { Chip, look } from '../feed/theme';
import { useEngagement } from './context';
import { type EventKind } from './events';
export function VisibleEvent({version,identity,kind,active}:{version:number;identity:string;kind:EventKind;active:boolean}){
 const {events}=useEngagement();
 useEffect(()=>{if(!active)return;let timer:ReturnType<typeof setTimeout>|undefined;function schedule(){if(timer)clearTimeout(timer);if(AppState.currentState==='active')timer=setTimeout(()=>{void events.track(version,identity,kind);},1000);}schedule();const subscription=AppState.addEventListener('change',schedule);return()=>{if(timer)clearTimeout(timer);subscription.remove();};},[events,version,identity,kind,active]);
 return null;
}
export function LikeButton({version,identity,active,offline}:{version:number;identity:string;active:boolean;offline:boolean}){
 const engagement=useEngagement();const controller=useMemo(()=>engagement.like(version,identity),[engagement,version,identity]);const state=useSyncExternalStore(controller.subscribe,controller.getSnapshot);
 useEffect(()=>{if(active&&!offline)void controller.load();},[active,offline,controller]);
 return <View style={{gap:4}}><Chip selected={state.liked===true} label={state.busy?'Checking…':state.liked?'♥ Liked':'♡ Like'} disabled={!active||offline||state.busy||state.liked===null||state.uncertain} onPress={()=>{void controller.change();}}/>{offline?<Text style={look.eyebrow}>Connect to like</Text>:!!state.error&&<><Text accessibilityLiveRegion="polite" style={look.copy}>{state.error}</Text><Chip label="Retry like check" disabled={!active||offline||state.busy} onPress={()=>{void controller.load();}}/></>}</View>;
}
