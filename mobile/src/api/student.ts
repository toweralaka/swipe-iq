export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) { super(message); this.status = status; }
}

export async function studentRequest(path: string, credential?: string, body?: unknown): Promise<unknown> {
  const base = process.env.EXPO_PUBLIC_API_URL?.trim().replace(/\/+$/, '');
  if (!base || !/^https?:\/\//.test(base)) throw new Error('Configure the API address, then restart the app.');
  if (!__DEV_SAFE__ && !base.startsWith('https://')) throw new Error('Sign-in requires an HTTPS API in preview builds.');
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(base + '/api/v1/' + path, {
      method: body === undefined ? 'GET' : 'POST', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', ...(credential ? { Authorization: 'Bearer ' + credential } : {}) },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    if (!response.ok) {
      const message = response.status === 429 ? 'Too many requests. Wait 15 minutes before trying again.'
        : response.status === 401 ? 'Your session has expired. Sign in again.'
        : response.status === 403 || response.status === 400 ? 'This link is invalid, expired, or already used. Request a new one.'
        : 'The server could not complete this request. Try again.';
      throw new ApiError(response.status, message);
    }
    return response.status === 204 ? null : await response.json();
  } catch (error) {
    if (controller.signal.aborted) throw new Error('Connection timed out. Check your connection and try again.');
    if (error instanceof ApiError) throw error;
    throw new Error('Cannot reach the server. Check your connection and try again.');
  } finally { clearTimeout(timer); }
}

// Node tests have no React Native global; production bundles must require HTTPS.
const __DEV_SAFE__ = typeof __DEV__ !== 'undefined' ? __DEV__ : process.env.NODE_ENV === 'test';

export type Candidate = { id: number; email: string };
export function candidateFrom(data: unknown): Candidate {
  if (!data || typeof data !== 'object' || !('id' in data) || !('email' in data)
    || typeof data.id !== 'number' || typeof data.email !== 'string') throw new Error('Unexpected account response. Try again.');
  return { id: data.id, email: data.email };
}

export function sessionFrom(data: unknown): string {
  if (!data || typeof data !== 'object' || !('credential' in data) || typeof data.credential !== 'string'
    || !/^[A-Za-z0-9_-]{43}$/.test(data.credential)) throw new Error('Unexpected sign-in response. Request a new link.');
  return data.credential;
}
