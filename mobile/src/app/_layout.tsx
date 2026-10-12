import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SessionProvider } from '../auth/session';

export default function Layout() {
  return <SessionProvider><StatusBar style="dark" /><Stack screenOptions={{ headerStyle: { backgroundColor: '#F4F7F1' }, headerTintColor: '#16352B' }}>
    <Stack.Screen name="index" options={{ title: 'Swipe-IQ' }} />
    <Stack.Screen name="login" options={{ title: 'Confirm sign-in' }} />
    <Stack.Screen name="connection" options={{ title: 'Connection check' }} />
  </Stack></SessionProvider>;
}
