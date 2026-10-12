import { useState } from 'react';
import { ActivityIndicator, Text } from 'react-native';
import { Link, router } from 'expo-router';
import { useSession } from '../auth/session';
import { studentRequest } from '../api/student';
import { Action, Input, Page, styles } from '../components/ui';

export default function Home() {
  const { candidate, ready, error, refresh, logout } = useSession();
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  async function requestLink() {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) { setMessage('Enter a valid email address.'); return; }
    setBusy(true); setMessage('');
    try {
      await studentRequest('auth/request-link/', undefined, { email: email.trim() });
      setMessage('If this address is invited, a login link will arrive shortly. Open it on this phone and confirm sign-in. Check spam if needed. Links expire after 15 minutes.');
    } catch (problem) { setMessage(problem instanceof Error ? problem.message : 'Request failed. Try again.'); }
    finally { setBusy(false); }
  }
  async function signOut() {
    setBusy(true); setMessage('');
    try { await logout(); }
    catch { setMessage('Sign-out could not finish. Check your connection and retry.'); }
    finally { setBusy(false); }
  }

  return <Page>
    <Text style={styles.title}>A fresh way to revise Biology.</Text>
    {!ready ? <ActivityIndicator accessibilityLabel="Restoring sign-in" /> : error ? <>
      <Text style={styles.text}>{error}</Text><Action title="Retry" onPress={() => { void refresh(); }} />
    </> : candidate ? <>
      <Text style={styles.text}>Signed in as {candidate.email}</Text>
      <Text style={styles.text}>Your student account is ready. The lesson feed and exam selection arrive in the next milestone.</Text>
      <Action title={busy ? 'Signing out…' : 'Sign out'} onPress={() => { void signOut(); }} disabled={busy} />
    </> : <>
      <Text style={styles.text}>Enter your invited email address. We’ll send you a link so you can sign in without a password.</Text>
      <Input accessibilityLabel="Email address" placeholder="you@example.com" textContentType="emailAddress" autoComplete="email" keyboardType="email-address" autoCapitalize="none" autoCorrect={false} value={email} onChangeText={setEmail} editable={!busy} />
      <Action title={busy ? 'Requesting…' : 'Send login link'} onPress={() => { void requestLink(); }} disabled={busy} />
      {__DEV__ && <Action title="Test a local login link" onPress={() => router.push('/login')} />}
    </>}
    {!!message && <Text accessibilityLiveRegion="polite" style={styles.message}>{message}</Text>}
    <Link href="/connection" style={styles.message}>Check server connection</Link>
  </Page>;
}
