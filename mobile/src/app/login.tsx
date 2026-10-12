import { useState } from 'react';
import { Text } from 'react-native';
import { Link, router, useLocalSearchParams } from 'expo-router';
import { useSession } from '../auth/session';
import { loginTokenFromLink } from '../auth/login-link';
import { Action, Input, Page, styles } from '../components/ui';

export default function LoginRoute() {
  const params = useLocalSearchParams<{ token?: string }>();
  const incoming = typeof params.token === 'string' && /^[A-Za-z0-9_-]{43}$/.test(params.token) ? params.token : null;
  return <Login key={incoming ?? 'no-link'} incoming={incoming} />;
}

function Login({ incoming }: { incoming: string | null }) {
  const { confirm, ready, candidate } = useSession();
  const [token, setToken] = useState<string | null>(incoming);
  const [localLink, setLocalLink] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  async function signIn() {
    if (!token || busy) return;
    setBusy(true); setMessage('');
    try { await confirm(token); setToken(null); router.replace('/'); }
    catch (problem) { setToken(null); setMessage(problem instanceof Error ? problem.message : 'Sign-in failed. Request a new link.'); }
    finally { setBusy(false); }
  }
  function readLocalLink() {
    const parsed = loginTokenFromLink(localLink, process.env.EXPO_PUBLIC_LOGIN_HOST, true);
    setLocalLink(''); setToken(parsed);
    setMessage(parsed ? '' : 'This login link is invalid. Request a new one.');
  }
  return <Page>
    <Text style={styles.title}>Confirm your sign-in</Text>
    {candidate && <Text style={styles.text}>Currently signed in as {candidate.email}. Confirming another link will switch accounts.</Text>}
    {token ? <>
      <Text style={styles.text}>Only continue if you requested this email link for your own account.</Text>
      <Action title={busy ? 'Signing in…' : 'Confirm sign-in'} onPress={() => { void signIn(); }} disabled={busy || !ready} />
    </> : <Text style={styles.text}>Open the latest login link from your email. If it has expired or was already used, request another one.</Text>}
    {__DEV__ && !token && <>
      <Text style={styles.text}>Local development: paste the complete link from the private email outbox.</Text>
      <Input accessibilityLabel="Local login link" placeholder="Paste local email link" secureTextEntry autoCapitalize="none" autoCorrect={false} value={localLink} onChangeText={setLocalLink} editable={!busy} />
      <Action title="Read local link" onPress={readLocalLink} disabled={busy} />
    </>}
    {!!message && <Text accessibilityLiveRegion="polite" style={styles.message}>{message}</Text>}
    {!busy && <Link replace href="/" style={styles.message}>Cancel or request a new link</Link>}
  </Page>;
}
