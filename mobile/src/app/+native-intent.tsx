import { loginRouteFromPath } from '../auth/login-link';

export function redirectSystemPath({ path }: { path: string; initial: boolean }) {
  // Routing only presents confirmation; it never consumes the login token.
  return loginRouteFromPath(path, process.env.EXPO_PUBLIC_LOGIN_HOST, __DEV__);
}
