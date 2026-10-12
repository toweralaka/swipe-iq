import { Stack } from 'expo-router';
import { FeedProvider } from '../feed/context';
import { StatusBar } from 'expo-status-bar';
import { SessionProvider } from '../auth/session';

export default function Layout() {
  return <SessionProvider><FeedProvider><StatusBar style="dark" /><Stack screenOptions={{ headerStyle: { backgroundColor: '#F4F7F1' }, headerTintColor: '#16352B' }}>
    <Stack.Screen name="index" options={{ title: 'Swipe-IQ' }} />
    <Stack.Screen name="login" options={{ title: 'Confirm sign-in' }} />
    <Stack.Screen name="connection" options={{ title: 'Connection check' }} />
  <Stack.Screen name="browse" options={{ title: 'Find lessons' }} /><Stack.Screen name="lesson" options={{ title: 'Biology lesson' }} /><Stack.Screen name="subjects" options={{ headerShown: false }} /><Stack.Screen name="feed" options={{ headerShown: false }} /><Stack.Screen name="settings" options={{ title: 'Your space' }} /></Stack></FeedProvider></SessionProvider>;
}
