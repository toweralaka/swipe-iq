import { ApiError, NetworkError, candidateFrom, sessionFrom, type Candidate } from '../api/student.ts';

export const SESSION_KEY = 'swipe-iq-session-v1';
export const ACCOUNT_KEY = 'swipe-iq-account-v1';
const noop = async () => {};
function snapshot(data: unknown): { candidate: Candidate; expiresAt: number } {
  const candidate = candidateFrom(data);
  const expiresAt = data && typeof data === 'object' && 'expires_at' in data && typeof data.expires_at === 'string' ? Date.parse(data.expires_at) : NaN;
  if (!Number.isFinite(expiresAt)) throw new Error('Sign in again to use saved lessons offline.');
  return { candidate, expiresAt };
}
export async function clearSession(storage: Storage, clearContent: () => Promise<void>) {
  try { await clearContent(); }
  finally { await storage.deleteItemAsync(SESSION_KEY); await storage.deleteItemAsync(ACCOUNT_KEY); }
}
export type Storage = {
  getItemAsync: (key: string) => Promise<string | null>;
  setItemAsync: (key: string, value: string) => Promise<void>;
  deleteItemAsync: (key: string) => Promise<void>;
};
export type Request = (path: string, credential?: string, body?: unknown) => Promise<unknown>;

export async function restoreCandidate(storage: Storage, request: Request, clearContent = noop): Promise<Candidate | null> {
  const credential = await storage.getItemAsync(SESSION_KEY);
  if (!credential) { await clearSession(storage, clearContent); return null; }
  try {
    const data = await request('auth/me/', credential);
    const saved = snapshot(data);
    await storage.setItemAsync(ACCOUNT_KEY, JSON.stringify({ ...saved, binding: credential }));
    return saved.candidate;
  }
  catch (problem) {
    if (problem instanceof ApiError && problem.status === 401) {
      await clearSession(storage, clearContent); return null;
    }
    if (problem instanceof NetworkError) {
      const saved = await storage.getItemAsync(ACCOUNT_KEY);
      if (saved) {
        try {
          const data = JSON.parse(saved) as { candidate: Candidate; expiresAt: number; binding: string };
          if (data.binding === credential && data.expiresAt > Date.now()) return candidateFrom(data.candidate);
          if (data.expiresAt <= Date.now()) { await clearSession(storage, clearContent); return null; }
        } catch { /* Invalid local account data is not a sign-in. */ }
      }
      throw new NetworkError('Connect to the internet to restore sign-in.');
    }
    throw problem;
  }
}

export async function confirmCandidate(storage: Storage, request: Request, token: string, clearContent = noop): Promise<Candidate> {
  const credential = sessionFrom(await request('auth/exchange/', undefined, { token }));
  try {
    const saved = snapshot(await request('auth/me/', credential));
    await clearContent();
    await storage.setItemAsync(ACCOUNT_KEY, JSON.stringify({ ...saved, binding: credential }));
    await storage.setItemAsync(SESSION_KEY, credential);
    return saved.candidate;
  } catch (problem) {
    try { await request('auth/logout/', credential, {}); } catch { /* Server expiry still applies. */ }
    throw problem;
  }
}

export async function logoutCandidate(storage: Storage, request: Request, clearContent = noop): Promise<void> {
  const credential = await storage.getItemAsync(SESSION_KEY);
  if (credential) {
    try { await request('auth/logout/', credential, {}); }
    catch (problem) { if (!(problem instanceof ApiError && problem.status === 401)) throw problem; }
  }
  await clearSession(storage, clearContent);
}
