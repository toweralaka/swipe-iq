import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import { loginTokenFromLink, loginRouteFromPath } from '../src/auth/login-link.ts';
process.env.NODE_ENV = 'test';
const { ApiError, studentRequest } = await import('../src/api/student.ts');
const { SESSION_KEY, restoreCandidate, confirmCandidate, logoutCandidate } = await import('../src/auth/session-actions.ts');
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
  const state = { value: initial };
  return { state, async getItemAsync(key) { assert.equal(key, SESSION_KEY); return state.value; },
    async setItemAsync(key, value) { assert.equal(key, SESSION_KEY); state.value = value; },
    async deleteItemAsync(key) { assert.equal(key, SESSION_KEY); state.value = null; } };
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
  assert.deepEqual(await restoreCandidate(secure, async (path, saved) => { assert.equal(saved, credential); return { id: 1, email: 'student@example.com' }; }), { id: 1, email: 'student@example.com' });
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
  const result = await confirmCandidate(secure, async (path) => { calls.push(path); return path === 'auth/exchange/' ? { credential } : { id: 1, email: 'student@example.com' }; }, token);
  assert.equal(result.id, 1);
  assert.equal(secure.state.value, credential);
  assert.deepEqual(calls, ['auth/exchange/', 'auth/me/']);
});

test('secure-storage failure attempts server revocation and never reports success', async () => {
  const secure = storage(null);
  secure.setItemAsync = async () => { throw new Error('storage unavailable'); };
  const calls = [];
  await assert.rejects(confirmCandidate(secure, async (path) => { calls.push(path); return path === 'auth/exchange/' ? { credential } : { id: 1, email: 'student@example.com' }; }, token), /storage unavailable/);
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
