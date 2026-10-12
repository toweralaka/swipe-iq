import { useEffect, useState } from 'react';
import { ActivityIndicator, Text } from 'react-native';
import { router } from 'expo-router';
import { apiBaseUrl } from '../api/student';
import { useSession } from '../auth/session';
import { Action, Page, styles } from '../components/ui';
import { useFeed } from './context';
import { examFrom, subjectFrom, topicFrom, unitFrom, pageFrom, nextPath } from './types';
import type { ReadResult } from './repository';
import type { Exam, Subject, Topic, Unit, ListPage } from './types';
type Row = { id: number; label: string; path: string };
export function LessonList({ stage, selection }: { stage: 'exam' | 'subject' | 'topic' | 'unit'; selection?: string }) {
  const { candidate } = useSession(); const { repository, error: openingError, revision } = useFeed();
  if (!candidate) return <Page><Text style={styles.text}>Sign in to open lessons.</Text><Action title="Go to sign-in" onPress={() => router.replace('/')} /></Page>;
  if (!repository) return <Page>{openingError ? <Text style={styles.text}>{openingError}</Text> : <ActivityIndicator accessibilityLabel="Opening saved lessons" />}</Page>;
  const path = stage === 'exam' ? 'examinations/' : stage === 'subject' ? 'subjects/?examination=' + encodeURIComponent(selection ?? '') : stage === 'topic' ? 'topics/?subject=' + encodeURIComponent(selection ?? '') : 'units/?topic=' + encodeURIComponent(selection ?? '');
  return <Rows key={path + ':' + revision} path={path} stage={stage} />;
}
function Rows({ path, stage }: { path: string; stage: 'exam' | 'subject' | 'topic' | 'unit' }) {
  const { repository } = useFeed();
  const [rows, setRows] = useState<Row[]>([]); const [next, setNext] = useState<string | null>(null);
  const [busy, setBusy] = useState(true); const [error, setError] = useState(''); const [offline, setOffline] = useState(false); const [saved, setSaved] = useState(true);
  type Item = Exam | Subject | Topic | Unit;
  function parse(data: unknown): ListPage<Item> { return stage === 'exam' ? pageFrom(data, examFrom) : stage === 'subject' ? pageFrom(data, subjectFrom) : stage === 'topic' ? pageFrom(data, topicFrom) : pageFrom(data, unitFrom); }
  function accept(result: ReadResult<ListPage<Item>>, append: boolean) {
    const incoming = result.value.results.map(v => {
      if ('code' in v) return { id: v.id, label: v.name, path: '/browse?exam=' + encodeURIComponent(v.code) };
      if ('examination' in v) return { id: v.id, label: v.examination.name + ' · ' + v.name, path: '/browse?subject=' + v.id };
      if ('subject' in v) return { id: v.id, label: v.subject.examination.name + ' · ' + v.subject.name + ' · ' + v.name, path: '/browse?topic=' + v.id };
      return { id: v.id, label: v.title, path: '/lesson?id=' + v.id };
    });
    setRows(old => append ? [...old, ...incoming.filter(v => !old.some(row => row.id === v.id))] : incoming);
    setNext(result.value.next); setOffline(old => append ? old || result.offline : result.offline); setSaved(result.saved); setBusy(false); setError('');
  }
  useEffect(() => {
    let active = true;
    if (repository) void repository.read(path, parse).then(result => { if (active) accept(result, false); }, problem => { if (active) { setError(problem.message); setBusy(false); } });
    return () => { active = false; };
    // This screen is remounted when its path or the connection check changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [repository, path]);
  function load(append: boolean) {
    setBusy(true); setError('');
    try { const target = append && next ? nextPath(next, apiBaseUrl(), path) : path;
      void repository!.read(target, parse).then(result => accept(result, append), problem => { setError(problem.message); setBusy(false); });
    } catch (problem) { setError(problem instanceof Error ? problem.message : 'Could not open the next page.'); setBusy(false); }
  }
  return <Page><Text style={styles.title}>{stage === 'exam' ? 'Choose your exam' : stage === 'subject' ? 'Choose a subject' : stage === 'topic' ? 'Choose a topic' : 'Choose a lesson'}</Text>
    {offline && <Text style={styles.message}>Offline: showing a saved list. Connect and refresh to check for changes.</Text>}
    {!saved && <Text style={styles.message}>This list could not be saved on the phone.</Text>}
    {rows.map(row => <Action key={row.id} title={row.label} onPress={() => router.push(row.path as '/browse')} />)}
    {busy && <ActivityIndicator accessibilityLabel="Loading lessons" />}
    {!busy && !error && rows.length === 0 && <Text style={styles.text}>No published lessons here yet. Ask the admin to publish a reviewed lesson.</Text>}
    {!!error && <Text accessibilityLiveRegion="polite" style={styles.text}>{error}</Text>}
    {!busy && next && <Action title="Load more" onPress={() => load(true)} />}
    {!busy && <Action title={error ? 'Retry' : 'Refresh list'} onPress={() => load(false)} />}
    {!busy && !next && rows.length > 0 && <Text style={styles.message}>You have reached the end of this list.</Text>}
  </Page>;
}
