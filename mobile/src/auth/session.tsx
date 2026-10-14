import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import { ApiError, studentRequest, type Candidate } from '../api/student';
import { SESSION_KEY, ACCOUNT_KEY, clearSession, confirmCandidate, logoutCandidate, restoreCandidate } from './session-actions';

import { clearViewedContent } from '../cache/device';
import { clearQuizDrafts } from '../quiz/device';
async function clearAccountContent() { const outcomes=await Promise.allSettled([clearViewedContent(),clearQuizDrafts()]); const failed=outcomes.find(result=>result.status==='rejected'); if(failed?.status==='rejected') throw failed.reason; }

type SessionContext = {
  candidate: Candidate | null; ready: boolean; error: string; refresh: () => Promise<void>;
  authorize: <T>(operation: (credential: string) => Promise<T>) => Promise<T>;
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
    void restoreCandidate(SecureStore, studentRequest, clearAccountContent).then(
      account => { if (active) { setCandidate(account); setReady(true); } },
      () => { if (active) { setError(RECOVERY); setReady(true); } },
    );
    return () => { active = false; };
  }, []);

  const authorize = useCallback(async <T,>(operation: (credential: string) => Promise<T>): Promise<T> => {
    const credential = await SecureStore.getItemAsync(SESSION_KEY);
    try {
      if (!credential) throw new ApiError(401, 'Sign in again to open lessons.');
      return await operation(credential);
    } catch (problem) {
      if (problem instanceof ApiError && problem.status === 401 && await SecureStore.getItemAsync(SESSION_KEY) === credential) {
        try { await clearSession(SecureStore, clearAccountContent); }
        finally { setCandidate(null); setError(''); }
      }
      throw problem;
    }
  }, []);

  useEffect(() => {
    let active = true; let timer: ReturnType<typeof setTimeout> | undefined;
    if (candidate) void SecureStore.getItemAsync(ACCOUNT_KEY).then(value => {
      if (!active || !value) return;
      const saved = JSON.parse(value) as { expiresAt: number };
      const expire = () => { void clearSession(SecureStore, clearAccountContent).finally(() => { if (active) setCandidate(null); }).catch(() => {}); };
      // Recheck daily so the timer stays within the platform's timer range.
      const schedule = () => { if (!Number.isFinite(saved.expiresAt)) { expire(); return; } const remaining = saved.expiresAt - Date.now(); if (remaining <= 0) expire(); else timer = setTimeout(schedule, Math.min(remaining, 86400000)); };
      schedule();
    }).catch(() => {});
    return () => { active = false; if (timer) clearTimeout(timer); };
  }, [candidate]);

  async function refresh() {
    setReady(false); setError('');
    try { setCandidate(await restoreCandidate(SecureStore, studentRequest, clearAccountContent)); }
    catch { setError(RECOVERY); }
    finally { setReady(true); }
  }
  async function confirm(token: string) {
    setCandidate(await confirmCandidate(SecureStore, studentRequest, token, clearAccountContent)); setError('');
  }
  async function logout() {
    try { await logoutCandidate(SecureStore, studentRequest, clearAccountContent); }
    finally { if (!await SecureStore.getItemAsync(SESSION_KEY)) { setCandidate(null); setError(''); } }
  }
  return <Context.Provider value={{ candidate, ready, error, refresh, confirm, logout, authorize }}>{children}</Context.Provider>;
}
export function useSession() {
  const session = useContext(Context);
  if (!session) throw new Error('Session provider is missing.');
  return session;
}
