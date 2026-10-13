import { Pressable, StyleSheet, Text } from 'react-native';
export const palette = { ink: '#172723', cream: '#F7F6EE', lime: '#D8FA72', muted: '#53615C', dark: '#101E1A' };
export function Chip({ label, onPress, dark = false, disabled = false, selected }: { label: string; onPress: () => void; dark?: boolean; disabled?:boolean; selected?:boolean }) {
 return <Pressable accessibilityRole="button" accessibilityState={{disabled,selected}} disabled={disabled} onPress={onPress} style={[look.chip, disabled && {opacity:0.5}, dark && { backgroundColor: '#ffffff14', borderColor: '#ffffff44' }]}><Text style={[look.chipText, dark && { color: '#fff' }]}>{label}</Text></Pressable>;
}
export const look = StyleSheet.create({
 screen: { flex: 1, backgroundColor: palette.cream },
 eyebrow: { fontSize: 12, fontWeight: '800', letterSpacing: 2, color: palette.muted },
 headline: { fontSize: 44, lineHeight: 48, fontWeight: '900', letterSpacing: -2, color: palette.ink },
 copy: { fontSize: 17, lineHeight: 25, color: palette.muted },
 chip: { borderRadius: 24, paddingHorizontal: 16, paddingVertical: 11, borderWidth: 1, borderColor: '#D1D8CE', backgroundColor: '#fff' },
 chipText: { fontSize: 14, fontWeight: '700', color: palette.ink },
 cta: { backgroundColor: palette.ink, borderRadius: 20, padding: 20, alignItems: 'center' },
 ctaText: { color: palette.lime, fontSize: 18, fontWeight: '800' },
});
