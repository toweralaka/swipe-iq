import { ApiError, candidateFrom, sessionFrom, type Candidate } from '../api/student.ts';

export const SESSION_KEY = 'swipe-iq-session-v1';
export type Storage = {
  getItemAsync: (key: string) => Promise<string | null>;
  setItemAsync: (key: string, value: string) => Promise<void>;
  deleteItemAsync: (key: string) => Promise<void>;
};
export type Request = (path: string, credential?: string, body?: unknown) => Promise<unknown>;

export async function restoreCandidate(storage: Storage, request: Request): Promise<Candidate | null> {
  const credential = await storage.getItemAsync(SESSION_KEY);
  if (!credential) return null;
  try { return candidateFrom(await request('auth/me/', credential)); }
  catch (problem) {
    if (problem instanceof ApiError && problem.status === 401) {
      await storage.deleteItemAsync(SESSION_KEY); return null;
    }
    throw problem;
  }
}

export async function confirmCandidate(storage: Storage, request: Request, token: string): Promise<Candidate> {
  const credential = sessionFrom(await request('auth/exchange/', undefined, { token }));
  try {
    const account = candidateFrom(await request('auth/me/', credential));
    await storage.setItemAsync(SESSION_KEY, credential);
    return account;
  } catch (problem) {
    try { await request('auth/logout/', credential, {}); } catch { /* Server expiry still applies. */ }
    throw problem;
  }
}

export async function logoutCandidate(storage: Storage, request: Request): Promise<void> {
  const credential = await storage.getItemAsync(SESSION_KEY);
  if (credential) {
    try { await request('auth/logout/', credential, {}); }
    catch (problem) { if (!(problem instanceof ApiError && problem.status === 401)) throw problem; }
  }
  await storage.deleteItemAsync(SESSION_KEY);
}
