import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import { loginTokenFromLink, loginRouteFromPath } from '../src/auth/login-link.ts';
process.env.NODE_ENV = 'test';
const { ApiError, NetworkError, studentRequest } = await import('../src/api/student.ts');
const { SESSION_KEY, ACCOUNT_KEY, clearSession, restoreCandidate, confirmCandidate, logoutCandidate } = await import('../src/auth/session-actions.ts');
const originalFetch = globalThis.fetch;
const originalUrl = process.env.EXPO_PUBLIC_API_URL;
afterEach(() => {
  globalThis.fetch = originalFetch;
  if (originalUrl === undefined) delete process.env.EXPO_PUBLIC_API_URL;
  else process.env.EXPO_PUBLIC_API_URL = originalUrl;
});
const token = 'a'.repeat(43);
const credential = 's'.repeat(43);
function storage(initial = credential) {
  const state = { value: initial, account: null };
  return { state, async getItemAsync(key) { return key === SESSION_KEY ? state.value : state.account; },
    async setItemAsync(key, value) { if (key === SESSION_KEY) state.value = value; else state.account = value; },
    async deleteItemAsync(key) { if (key === SESSION_KEY) state.value = null; else state.account = null; } };
}

test('trusted fragment links parse without consuming tokens; foreign and malformed links fail', () => {
  assert.equal(loginTokenFromLink('https://login.example.com/login#token=' + token, 'login.example.com'), token);
  for (const link of ['https://evil.example/login#token=' + token, 'https://login.example.com/login?token=' + token,
    'https://login.example.com/login#token=bad', 'https://login.example.com/login#token=' + token + '&token=' + token,
    'https://user:pass@login.example.com/login#token=' + token, 'swipeiq://login#token=' + token]) {
    assert.equal(loginTokenFromLink(link, 'login.example.com'), null);
  }
  assert.equal(loginTokenFromLink('http://192.168.1.10:8000/login#token=' + token, undefined, true), token);
});

test('exchange sends secret in POST body and session uses Authorization header', async () => {
  process.env.EXPO_PUBLIC_API_URL = 'https://api.example.com/';
  globalThis.fetch = async (url, options) => {
    assert.equal(url, 'https://api.example.com/api/v1/auth/exchange/');
    assert.equal(options.method, 'POST');
    assert.deepEqual(JSON.parse(options.body), { token });
    return Response.json({ credential });
  };
  assert.deepEqual(await studentRequest('auth/exchange/', undefined, { token }), { credential });
  globalThis.fetch = async (url, options) => {
    assert.equal(options.headers.Authorization, 'Bearer ' + credential);
    return new Response(null, { status: 204 });
  };
  assert.equal(await studentRequest('auth/logout/', credential, {}), null);
});

test('server errors do not leak response secrets and rate limits offer recovery', async () => {
  process.env.EXPO_PUBLIC_API_URL = 'https://api.example.com';
  for (const status of [400, 401, 403, 429, 500]) {
    globalThis.fetch = async () => new Response('private token: ' + token, { status });
    await assert.rejects(studentRequest('auth/exchange/', undefined, { token }), error => error instanceof ApiError && error.status === status && !error.message.includes(token));
  }
});

test('session restores from secure storage and expired session is cleared', async () => {
  const secure = storage();
  assert.deepEqual(await restoreCandidate(secure, async (path, saved) => { assert.equal(saved, credential); return { id: 1, email: 'student@example.com', expires_at: new Date(Date.now() + 86400000).toISOString() }; }), { id: 1, email: 'student@example.com' });
  assert.equal(await restoreCandidate(secure, async () => { throw new ApiError(401, 'expired'); }), null);
  assert.equal(secure.state.value, null);
});

test('offline restore and failed logout preserve credential for recovery', async () => {
  const secure = storage();
  const offline = async () => { throw new Error('offline'); };
  await assert.rejects(restoreCandidate(secure, offline), /offline/);
  await assert.rejects(logoutCandidate(secure, offline), /offline/);
  assert.equal(secure.state.value, credential);
});

test('confirmation persists credential only after account verification', async () => {
  const secure = storage(null);
  const calls = [];
  const result = await confirmCandidate(secure, async (path) => { calls.push(path); return path === 'auth/exchange/' ? { credential } : { id: 1, email: 'student@example.com', expires_at: new Date(Date.now() + 86400000).toISOString() }; }, token);
  assert.equal(result.id, 1);
  assert.equal(secure.state.value, credential);
  assert.deepEqual(calls, ['auth/exchange/', 'auth/me/']);
});

test('secure-storage failure attempts server revocation and never reports success', async () => {
  const secure = storage(null);
  secure.setItemAsync = async () => { throw new Error('storage unavailable'); };
  const calls = [];
  await assert.rejects(confirmCandidate(secure, async (path) => { calls.push(path); return path === 'auth/exchange/' ? { credential } : { id: 1, email: 'student@example.com', expires_at: new Date(Date.now() + 86400000).toISOString() }; }, token), /storage unavailable/);
  assert.equal(calls.at(-1), 'auth/logout/');
  assert.equal(secure.state.value, null);
});

test('successful logout revokes on server before clearing secure storage', async () => {
  const secure = storage();
  await logoutCandidate(secure, async (path, saved, body) => {
    assert.equal(path, 'auth/logout/'); assert.equal(saved, credential);
    assert.deepEqual(body, {}); assert.equal(secure.state.value, credential); return null;
  });
  assert.equal(secure.state.value, null);
});

test('normal app launch stays at home and incoming login links only route to confirmation', () => {
  assert.equal(loginRouteFromPath('/', 'login.example.com'), '/');
  assert.equal(loginRouteFromPath('swipeiq:///', 'login.example.com', true), '/');
  assert.equal(loginRouteFromPath('https://login.example.com/login#token=' + token, 'login.example.com'), '/login?token=' + token);
  assert.equal(loginRouteFromPath('https://evil.example/login#token=' + token, 'login.example.com'), '/login');
});

 test('offline restart needs a verified account bound to the same unexpired credential', async () => {
  const secure = storage(); let cleared = 0; const clean = async () => { cleared++; };
  const me = async () => ({ id: 2, email: 'two@example.com', expires_at: new Date(Date.now() + 60000).toISOString() });
  await restoreCandidate(secure, me, clean);
  const offline = async () => { throw new NetworkError('offline'); };
  assert.equal((await restoreCandidate(secure, offline, clean)).id, 2);
  const data = JSON.parse(await secure.getItemAsync(ACCOUNT_KEY)); data.binding = 'different'; secure.state.account = JSON.stringify(data);
  await assert.rejects(restoreCandidate(secure, offline, clean), /Connect/);
  data.binding = credential; data.expiresAt = Date.now() - 1; secure.state.account = JSON.stringify(data);
  assert.equal(await restoreCandidate(secure, offline, clean), null); assert.equal(cleared, 1); assert.equal(secure.state.value, null);
 });
 test('clearing a session removes credentials even when file cleanup fails', async () => {
  const secure = storage(); await assert.rejects(clearSession(secure, async () => { throw new Error('disk'); }), /disk/); assert.equal(secure.state.value, null); assert.equal(secure.state.account, null);
 });

 test('a newly confirmed sign-in can reopen saved content offline', async () => {
  const secure = storage(null); let clean = 0;
  await confirmCandidate(secure, async path => path === 'auth/exchange/' ? { credential } : { id: 3, email: 'three@example.com', expires_at: new Date(Date.now() + 60000).toISOString() }, token, async () => { clean++; });
  assert.equal(clean, 1); assert.equal((await restoreCandidate(secure, async () => { throw new NetworkError('offline'); })).id, 3);
 });
