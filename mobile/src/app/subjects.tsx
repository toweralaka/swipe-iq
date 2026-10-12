import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, Text, View } from 'react-native';
import { Redirect, router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSession } from '../auth/session';
import { useFeed } from '../feed/context';
import { apiBaseUrl } from '../api/student';
import { pageFrom, subjectFrom, nextPath, type Subject, type ListPage } from '../feed/types';
import type { ReadResult } from '../feed/repository';
import { Chip, look, palette } from '../feed/theme';
export default function Subjects() {
 const { candidate, ready } = useSession(); const { repository, revision, error } = useFeed();
 if (ready && !candidate) return <Redirect href="/" />;
 if (!repository) return <SafeAreaView style={look.screen}><View style={{ padding: 24 }}>{error ? <Text style={look.copy}>{error}</Text> : <ActivityIndicator />}</View></SafeAreaView>;
 return <Choices key={revision} />;
}
function Choices() {
 const { repository } = useFeed(); const [subjects, setSubjects] = useState<Subject[]>([]); const [selected, setSelected] = useState<number[]>([]);
 const [busy, setBusy] = useState(true); const [saving, setSaving] = useState(false); const [error, setError] = useState(''); const [offline, setOffline] = useState(false); const [attempt, setAttempt] = useState(0);
 useEffect(() => {
  let active = true;
  async function load() {
   const remembered = await repository!.selection(); let path: string | null = 'subjects/'; const all: Subject[] = []; let saved = false;
   for(let page = 0; path && page < 10; page++) {
    const response: ReadResult<ListPage<Subject>> = await repository!.read(path, value => pageFrom(value, subjectFrom)); all.push(...response.value.results); saved ||= response.offline;
    path = response.value.next ? nextPath(response.value.next, apiBaseUrl(), 'subjects/') : null;
   }
   if(active) { setSubjects(all); setSelected(remembered.filter(id => all.some(subject => subject.id === id))); setOffline(saved); setBusy(false); setError(''); }
  }
  void load().catch(problem => { if(active) { setBusy(false); setError(problem.message); } }); return () => { active = false; };
 }, [repository, attempt]);
 function toggle(id: number) { setSelected(old => old.includes(id) ? old.filter(v => v !== id) : old.length < 20 ? [...old,id] : old); }
 async function start() {
  setSaving(true); setError('');
  try { await repository!.saveSelection(selected); router.replace({ pathname: '/feed', params: { subjects: selected.join(',') } }); }
  catch { setError('Could not save your picks. Check free space and try again.'); setSaving(false); }
 }
 return <SafeAreaView style={look.screen}><ScrollView contentContainerStyle={{ padding: 24, gap: 24, flexGrow: 1 }}>
  <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}><Text style={look.eyebrow}>SWIPE-IQ / YOUR MIX</Text><Chip label="Settings" onPress={() => router.push('/settings')} /></View>
  <View style={{ backgroundColor: palette.lime, borderRadius: 32, padding: 28, gap: 12 }}><Text style={{ fontSize: 44 }}>✳</Text><Text style={look.headline}>Pick your{ '\n' }kind of fun.</Text><Text style={look.copy}>A little Biology. A little banter. Choose what lands in your feed.</Text></View>
  <View style={{ gap: 8 }}><Text style={[look.copy, { fontWeight: '800', color: palette.ink }]}>Your subjects</Text><Text style={look.copy}>Pick 1–20 subjects. You can change your mix anytime.</Text></View>
  {busy && <ActivityIndicator accessibilityLabel="Loading subjects" />}
  {offline && <Text style={look.copy}>Offline · showing saved subjects.</Text>}
  {subjects.map(subject => { const checked = selected.includes(subject.id); return <Pressable key={subject.id} accessibilityRole="checkbox" accessibilityState={{ checked, disabled: saving }} disabled={saving} onPress={() => toggle(subject.id)} style={{ backgroundColor: checked ? palette.ink : '#fff', borderRadius: 22, padding: 22, borderWidth: 1, borderColor: checked ? palette.ink : '#D9DFD5', flexDirection: 'row', alignItems: 'center', gap: 16 }}>
   <View style={{ width: 28, height: 28, borderRadius: 8, backgroundColor: checked ? palette.lime : '#EDF0E8', alignItems: 'center', justifyContent: 'center' }}><Text style={{ fontSize: 20, fontWeight: '900', color: palette.ink }}>{checked ? '✓' : ''}</Text></View>
   <Text style={{ flex: 1, fontSize: 20, fontWeight: '800', color: checked ? '#fff' : palette.ink }}>{subject.name} ({subject.examination.name})</Text>
  </Pressable>; })}
  {!busy && !error && !subjects.length && <Text style={look.copy}>Your feed is waiting for its first post. Ask the admin to publish reviewed content in an active exam.</Text>}
  {!!error && <><Text accessibilityLiveRegion="polite" style={look.copy}>{error}</Text><Chip label="Try again" onPress={() => { setBusy(true); setAttempt(v => v + 1); }} /></>}
  <View style={{ flex: 1 }} /><Pressable accessibilityRole="button" disabled={busy || saving || !selected.length} onPress={() => { void start(); }} style={[look.cta, (!selected.length || busy || saving) && { opacity: 0.45 }]}><Text style={look.ctaText}>{saving ? 'Opening your mix…' : selected.length ? 'Let’s scroll  ↗' : 'Pick a subject to start'}</Text></Pressable>
 </ScrollView></SafeAreaView>;
}
