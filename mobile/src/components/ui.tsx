import { Pressable, ScrollView, StyleSheet, Text, type TextInputProps, TextInput } from 'react-native';
import { type ReactNode } from 'react';

export function Page({ children }: { children: ReactNode }) {
  return <ScrollView contentContainerStyle={styles.page} keyboardShouldPersistTaps="handled">{children}</ScrollView>;
}
export function Action({ title, onPress, disabled = false }: { title: string; onPress: () => void; disabled?: boolean }) {
  return <Pressable accessibilityRole="button" disabled={disabled} onPress={onPress} style={[styles.button, disabled && { opacity: 0.5 }]}><Text style={styles.buttonText}>{title}</Text></Pressable>;
}
export function Input(props: TextInputProps) { return <TextInput {...props} style={styles.input} />; }
export const styles = StyleSheet.create({
  page: { flexGrow: 1, padding: 24, paddingBottom: 48, gap: 20, backgroundColor: '#F4F7F1' },
  title: { fontSize: 30, fontWeight: '800', color: '#16352B' },
  text: { fontSize: 17, lineHeight: 26, color: '#4E6057' },
  message: { fontSize: 16, lineHeight: 24, color: '#145A46' },
  input: { backgroundColor: '#fff', borderColor: '#61756A', borderWidth: 1, borderRadius: 12, padding: 16, fontSize: 17 },
  button: { backgroundColor: '#145A46', borderRadius: 12, padding: 16, alignItems: 'center' },
  buttonText: { fontSize: 17, color: '#fff', fontWeight: '700' },
});
