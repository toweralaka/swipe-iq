import { useState } from 'react';
import { ActivityIndicator, Text } from 'react-native';
import { Link, Redirect, router } from 'expo-router';
import { useSession } from '../auth/session';
import { studentRequest } from '../api/student';
import { Action, Input, Page, styles } from '../components/ui';
export default function Home() {
 const { candidate, ready, error, refresh } = useSession();
 const [email, setEmail] = useState(''); const [busy, setBusy] = useState(false); const [message, setMessage] = useState('');
 async function requestLink() {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) { setMessage('Enter a valid email address.'); return; }
  setBusy(true); setMessage('');
  try { await studentRequest('auth/request-link/', undefined, { email: email.trim() }); setMessage('If this address is invited, a login link will arrive shortly. Open it on this phone and confirm sign-in. Check spam if needed. Links expire after 15 minutes.'); }
  catch(problem) { setMessage(problem instanceof Error ? problem.message : 'Could not send a link. Try again.'); }
  finally { setBusy(false); }
 }
 if (ready && candidate && !error) return <Redirect href="/subjects" />;
 return <Page><Text style={[styles.message,{fontWeight:'800',letterSpacing:3}]}>SWIPE-IQ ✳</Text><Text style={styles.title}>A little scroll.{ '\n' }A big aha.</Text><Text style={styles.text}>Biology with a sense of humour. Take a breather, find your mix, and let curiosity do its thing.</Text>
 {!ready ? <ActivityIndicator accessibilityLabel="Restoring sign-in" /> : error ? <><Text style={styles.text}>{error}</Text><Action title="Retry" onPress={() => { void refresh(); }} /></> : <><Text style={styles.text}>Enter your invited email. We’ll send a link—no password to remember.</Text><Input accessibilityLabel="Email address" placeholder="you@example.com" textContentType="emailAddress" autoComplete="email" keyboardType="email-address" autoCapitalize="none" autoCorrect={false} value={email} onChangeText={setEmail} editable={!busy} /><Action title={busy ? 'Sending…' : 'Send my login link'} onPress={() => { void requestLink(); }} disabled={busy} />{__DEV__ && <Action title="Test a local login link" onPress={() => router.push('/login')} />}</>}
 {!!message && <Text accessibilityLiveRegion="polite" style={styles.message}>{message}</Text>}<Link href="/connection" style={styles.message}>Check server connection</Link></Page>;
}
