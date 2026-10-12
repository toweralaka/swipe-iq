import { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { checkHealth } from './src/api/health';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('Ready to check the connection.');
  const [connected, setConnected] = useState(false);

  async function connect() {
    setLoading(true);
    setConnected(false);
    setMessage('Connecting…');
    try {
      await checkHealth();
      setConnected(true);
      setMessage('Connected to Swipe-IQ API.');
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Connection failed.';
      setMessage(detail + ' Make sure the phone and computer are on the same Wi-Fi, then try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.container}>
      <StatusBar style="dark" />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.eyebrow}>SWIPE-IQ</Text>
        <Text style={styles.title}>A fresh way to revise Biology.</Text>
        <Text style={styles.description}>Short lessons, useful practice, and friendly challenges are coming next.</Text>
        <View style={styles.card}>
          <Text style={styles.heading}>Connection check</Text>
          <Text accessibilityLiveRegion="polite" style={[styles.message, connected && styles.success]}>{message}</Text>
          {loading && <ActivityIndicator accessibilityLabel="Checking API connection" color="#145A46" />}
          <Pressable accessibilityRole="button" disabled={loading} onPress={connect}
            style={({ pressed }) => [styles.button, (pressed || loading) && styles.dimmed]}>
            <Text style={styles.buttonText}>{loading ? 'Checking…' : 'Check connection'}</Text>
          </Pressable>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F4F7F1' },
  content: { flexGrow: 1, justifyContent: 'center', padding: 28, paddingTop: 64, paddingBottom: 48 },
  eyebrow: { color: '#145A46', fontWeight: '800', letterSpacing: 3, marginBottom: 18 },
  title: { fontSize: 34, fontWeight: '800', color: '#16352B', marginBottom: 16 },
  description: { fontSize: 18, lineHeight: 28, color: '#4E6057', marginBottom: 32 },
  card: { backgroundColor: '#FFFFFF', padding: 24, borderRadius: 20, gap: 18 },
  heading: { fontSize: 20, fontWeight: '700', color: '#16352B' },
  message: { fontSize: 16, lineHeight: 24, color: '#4E6057' },
  success: { color: '#145A46' },
  button: { backgroundColor: '#145A46', padding: 16, borderRadius: 12, alignItems: 'center' },
  buttonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
  dimmed: { opacity: 0.65 },
});
