export type HealthResponse = { status: 'ok'; service: 'swipe-iq-api' };

export async function checkHealth(): Promise<HealthResponse> {
  const baseUrl = process.env.EXPO_PUBLIC_API_URL?.trim().replace(/\/+$/, '');
  if (!baseUrl || !/^https?:\/\//.test(baseUrl)) {
    throw new Error('Set EXPO_PUBLIC_API_URL in mobile/.env to your computer’s API address, then restart Expo.');
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(baseUrl + '/api/v1/health/', { signal: controller.signal });
    if (!response.ok) throw new Error('The API returned HTTP ' + response.status + '. Check the backend terminal.');
    const data: unknown = await response.json();
    if (!data || typeof data !== 'object' || !('status' in data) || !('service' in data)
      || data.status !== 'ok' || data.service !== 'swipe-iq-api') {
      throw new Error('The server returned an unexpected response. Check the API address.');
    }
    return { status: 'ok', service: 'swipe-iq-api' };
  } catch (error) {
    if (controller.signal.aborted) throw new Error('Connection timed out. Check Wi-Fi, the API address, and the backend.');
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
