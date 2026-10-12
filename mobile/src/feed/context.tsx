import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { AppState } from 'react-native';
import { fetch as fetchFile } from 'expo/fetch';
import * as Network from 'expo-network';
import * as SecureStore from 'expo-secure-store';
import { apiBaseUrl, studentRequest } from '../api/student';
import { useSession } from '../auth/session';
import { clearViewedContent, viewedCache } from '../cache/device';
import { FeedRepository } from './repository';
import { downloadMedia } from './download';

type FeedContext = { repository: FeedRepository | null; error: string; dataSaver: boolean; toggleDataSaver: () => Promise<void>; clearCache: () => Promise<void>; revision: number; recheck: () => Promise<void> };
const Context = createContext<FeedContext | null>(null);
const PREF = 'swipe-iq-data-saver';
export function FeedProvider({ children }: { children: ReactNode }) {
  const { candidate, authorize } = useSession();
  const [current, setCurrent] = useState<{ owner: number; repository: FeedRepository } | null>(null);
  const [error, setError] = useState('');
  const [dataSaver, setDataSaver] = useState(true);
  const [revision, setRevision] = useState(0);
  const repository = current?.owner === candidate?.id ? current?.repository ?? null : null;
  const openRepository = useCallback(async (id: number) => {
    const base = apiBaseUrl();
    const lease = await viewedCache.activate(base + '|' + id);
    return new FeedRepository(viewedCache, lease,
      (path, body) => authorize(credential => studentRequest(path, credential, body)),
      media => authorize(credential => downloadMedia(media, base, credential, fetchFile)));
  }, [authorize]);
  useEffect(() => {
    let active = true;
    if (candidate) void openRepository(candidate.id).then(
      repo => { if (active) { setCurrent({ owner: candidate.id, repository: repo }); setError(''); } },
      () => { if (active) setError('Could not open saved lessons. Check the API address and free space on the phone.'); },
    );
    return () => { active = false; };
  }, [candidate, openRepository]);
  useEffect(() => {
    void SecureStore.getItemAsync(PREF).then(value => { if (value === 'off') setDataSaver(false); }).catch(() => {});
  }, []);
  const recheck = useCallback(async () => {
    if (!repository) return;
    try { await repository.recheckSavedLessons(); }
    finally { setRevision(value => value + 1); }
  }, [repository]);
  useEffect(() => {
    void recheck().catch(() => {});
    let wasConnected: boolean | undefined;
    const connection = Network.addNetworkStateListener(state => {
      const connected = state.isConnected;
      if (connected && wasConnected === false) void recheck().catch(() => {});
      wasConnected = connected;
    });
    const focus = AppState.addEventListener('change', state => { if (state === 'active') void recheck().catch(() => {}); });
    return () => { connection.remove(); focus.remove(); };
  }, [recheck]);
  async function toggleDataSaver() {
    const next = !dataSaver; await SecureStore.setItemAsync(PREF, next ? 'on' : 'off'); setDataSaver(next);
  }
  async function clearCache() {
    await clearViewedContent();
    if (candidate) setCurrent({ owner: candidate.id, repository: await openRepository(candidate.id) });
    setRevision(value => value + 1);
  }
  return <Context.Provider value={{ repository, error, dataSaver, toggleDataSaver, clearCache, revision, recheck }}>{children}</Context.Provider>;
}
export function useFeed() { const value = useContext(Context); if (!value) throw new Error('Feed provider missing.'); return value; }
