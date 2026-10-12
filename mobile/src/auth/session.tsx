import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import { studentRequest, type Candidate } from '../api/student';
import { confirmCandidate, logoutCandidate, restoreCandidate } from './session-actions';

type SessionContext = {
  candidate: Candidate | null; ready: boolean; error: string; refresh: () => Promise<void>;
  confirm: (token: string) => Promise<void>; logout: () => Promise<void>;
};
const Context = createContext<SessionContext | null>(null);
const RECOVERY = 'Could not restore sign-in. Check your connection and tap Retry.';

export function SessionProvider({ children }: { children: ReactNode }) {
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    void restoreCandidate(SecureStore, studentRequest).then(
      account => { if (active) { setCandidate(account); setReady(true); } },
      () => { if (active) { setError(RECOVERY); setReady(true); } },
    );
    return () => { active = false; };
  }, []);

  async function refresh() {
    setReady(false); setError('');
    try { setCandidate(await restoreCandidate(SecureStore, studentRequest)); }
    catch { setError(RECOVERY); }
    finally { setReady(true); }
  }
  async function confirm(token: string) {
    setCandidate(await confirmCandidate(SecureStore, studentRequest, token)); setError('');
  }
  async function logout() {
    await logoutCandidate(SecureStore, studentRequest); setCandidate(null); setError('');
  }
  return <Context.Provider value={{ candidate, ready, error, refresh, confirm, logout }}>{children}</Context.Provider>;
}
export function useSession() {
  const session = useContext(Context);
  if (!session) throw new Error('Session provider is missing.');
  return session;
}
