import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import { checkHealth } from '../src/api/health.ts';

const originalFetch = globalThis.fetch;
const originalUrl = process.env.EXPO_PUBLIC_API_URL;
afterEach(() => {
  globalThis.fetch = originalFetch;
  if (originalUrl === undefined) delete process.env.EXPO_PUBLIC_API_URL;
  else process.env.EXPO_PUBLIC_API_URL = originalUrl;
});

test('missing configuration fails before making a request', async () => {
  delete process.env.EXPO_PUBLIC_API_URL;
  globalThis.fetch = () => { throw new Error('Unexpected request'); };
  await assert.rejects(checkHealth(), /Set EXPO_PUBLIC_API_URL/);
});

test('configured API base produces the versioned health request', async () => {
  process.env.EXPO_PUBLIC_API_URL = 'http://192.168.1.10:8000/';
  globalThis.fetch = async (url) => {
    assert.equal(url, 'http://192.168.1.10:8000/api/v1/health/');
    return Response.json({ status: 'ok', service: 'swipe-iq-api' });
  };
  assert.deepEqual(await checkHealth(), { status: 'ok', service: 'swipe-iq-api' });
});

test('HTTP failure is not reported as a connection success', async () => {
  process.env.EXPO_PUBLIC_API_URL = 'http://localhost:8000';
  globalThis.fetch = async () => new Response('', { status: 503 });
  await assert.rejects(checkHealth(), /HTTP 503/);
});

test('a different service or malformed response is rejected', async () => {
  process.env.EXPO_PUBLIC_API_URL = 'http://localhost:8000';
  for (const body of [null, {}, { status: 'ok', service: 'other-service' }]) {
    globalThis.fetch = async () => Response.json(body);
    await assert.rejects(checkHealth(), /unexpected response/);
  }
});

test('network failure can be followed by a successful retry', async () => {
  process.env.EXPO_PUBLIC_API_URL = 'http://localhost:8000';
  globalThis.fetch = async () => { throw new TypeError('Network request failed'); };
  await assert.rejects(checkHealth(), /Network request failed/);
  globalThis.fetch = async () => Response.json({ status: 'ok', service: 'swipe-iq-api' });
  assert.equal((await checkHealth()).status, 'ok');
});
