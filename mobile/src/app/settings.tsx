import { useState } from 'react';
import { Text } from 'react-native';
import { Redirect, router } from 'expo-router';
import { useSession } from '../auth/session';
import { useFeed } from '../feed/context';
import { Action, Page, styles } from '../components/ui';
export default function Settings() {
 const { candidate, ready, logout } = useSession(); const { dataSaver, toggleDataSaver, clearCache } = useFeed(); const [busy, setBusy] = useState(false); const [message, setMessage] = useState('');
 if (ready && !candidate) return <Redirect href="/" />;
 async function act(operation: () => Promise<void>, done: string) { setBusy(true); setMessage(''); try { await operation(); setMessage(done); } catch(problem) { setMessage(problem instanceof Error ? problem.message : 'Could not finish. Try again.'); } finally { setBusy(false); } }
 return <Page><Text style={styles.title}>Your space</Text><Text style={styles.text}>{candidate?.email}</Text>
 <Action title="My progress" onPress={() => router.push('/progress')} />
 <Action title="Change my subjects" disabled={busy} onPress={() => router.replace('/subjects')} />
 <Text style={styles.text}>Data saver is {dataSaver ? 'on. Files wait for you to tap Load.' : 'off. Visible images load automatically.'} Audio and video always wait for Play.</Text>
 <Action title={dataSaver ? 'Turn data saver off' : 'Turn data saver on'} disabled={busy} onPress={() => { void act(toggleDataSaver, 'Setting saved.'); }} />
 <Text style={styles.text}>Posts and loaded files share up to 100 MB on this phone. Older items go first. Clearing them also resets your subject picks. Unfinished quiz answers are kept. Signing out removes unfinished answers.</Text>
 <Action title="Clear saved posts and files" disabled={busy} onPress={() => { void act(clearCache, 'Saved copies and subject picks cleared.'); }} />
 <Action title={busy ? 'Please wait…' : 'Sign out'} disabled={busy} onPress={() => { void act(logout, 'Signed out.'); }} />
 {!!message && <Text accessibilityLiveRegion="polite" style={styles.message}>{message}</Text>}
 </Page>;
}
