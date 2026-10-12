export function loginTokenFromLink(input: string, host: string | undefined, development = false): string | null {
  try {
    const url = new URL(input.trim());
    const trustedHttps = url.protocol === 'https:' && !!host && url.host === host && url.pathname === '/login';
    const localLink = development && ((url.protocol === 'http:' && url.pathname === '/login')
      || (url.protocol === 'swipeiq:' && url.hostname === 'login'));
    if ((!trustedHttps && !localLink) || url.username || url.password || url.search) return null;
    const params = new URLSearchParams(url.hash.slice(1));
    if (Array.from(params.keys()).length !== 1) return null;
    const token = params.get('token');
    return token && /^[A-Za-z0-9_-]{43}$/.test(token) ? token : null;
  } catch { return null; }
}

export function loginRouteFromPath(path: string, host: string | undefined, development = false): string {
  const token = loginTokenFromLink(path, host, development);
  if (token) return '/login?token=' + encodeURIComponent(token);
  try {
    const url = new URL(path);
    return url.pathname === '/login' || url.hostname === 'login' ? '/login' : '/';
  } catch { return path.startsWith('/login') ? '/login' : '/'; }
}
