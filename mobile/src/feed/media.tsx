import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, AppState, Image, Pressable, Text, View } from 'react-native';
import { useFocusEffect } from 'expo-router';
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import { useVideoPlayer, VideoView } from 'expo-video';
import { useEvent } from 'expo';
import { styles } from '../components/ui';
import { useFeed } from './context';
import { captionAt, captionsFrom } from './captions';
import type { Media } from './types';
function MediaAction({ title, onPress, disabled = false, compact = false }: { title: string; onPress: () => void; disabled?: boolean; compact?: boolean }) {
 return <Pressable accessibilityRole="button" disabled={disabled} onPress={onPress} style={{ backgroundColor: '#172723', borderRadius: compact ? 12 : 16, padding: compact ? 11 : 16, opacity: disabled ? 0.5 : 1, alignItems: 'center' }}><Text style={{ color: '#fff', fontWeight: '800', fontSize: compact ? 14 : 17 }}>{title}</Text></Pressable>;
}
function usePauseWhenHidden(pause: () => void, active: boolean) {
  const allowed = useRef(false);
  useEffect(() => { allowed.current = active && AppState.currentState === 'active'; if (!allowed.current) pause(); }, [active, pause]);
  useFocusEffect(useCallback(() => {
    allowed.current = active && AppState.currentState === 'active';
    return () => { allowed.current = false; pause(); };
  }, [active, pause]));
  useEffect(() => {
    const sub = AppState.addEventListener('change', state => { allowed.current = active && state === 'active'; if (!allowed.current) pause(); });
    return () => sub.remove();
  }, [active, pause]);
  return useCallback(() => allowed.current, []);
}
function Audio({ uri, active, compact = false }: { uri: string; active: boolean; compact?: boolean }) {
  const player = useAudioPlayer(uri); const status = useAudioPlayerStatus(player);
  const pause = useCallback(() => player.pause(), [player]); const canPlay = usePauseWhenHidden(pause, active);
  const [error, setError] = useState('');
  async function toggle() {
    try {
      setError('');
      if (status.playing) player.pause();
      else {
        if (status.didJustFinish || (status.duration > 0 && status.currentTime >= status.duration - 0.1)) await player.seekTo(0);
        if (canPlay()) player.play();
      }
    } catch { setError('This audio could not play. You can still read its transcript.'); }
  }
  return <View style={{ gap: compact ? 5 : 12 }}><Text style={styles.text}>{Math.floor(status.currentTime)} / {Math.floor(status.duration)} seconds</Text>
    <MediaAction compact={compact} title={status.playing ? 'Pause audio' : 'Play audio'} disabled={!active || !status.isLoaded} onPress={() => { void toggle(); }} />
    {!!error && <Text style={styles.text}>{error}</Text>}
    {status.isBuffering && <ActivityIndicator accessibilityLabel="Preparing audio" />}
  </View>;
}
function Video({ uri, active, captions, compact = false }: { uri: string; active: boolean; captions: string; compact?: boolean }) {
  const player = useVideoPlayer(uri, p => { p.loop = false; p.timeUpdateEventInterval = 0.25; });
  const playing = useEvent(player, 'playingChange', { isPlaying: player.playing });
  const status = useEvent(player, 'statusChange', { status: player.status });
  const time = useEvent(player, 'timeUpdate', { currentTime: 0, currentLiveTimestamp: null, currentOffsetFromLive: null, bufferedPosition: 0 });
  const pause = useCallback(() => player.pause(), [player]); usePauseWhenHidden(pause, active);
  const caption = captionAt(captionsFrom(captions), time.currentTime);
  return <View style={{ gap: compact ? 5 : 12 }}><VideoView player={player} style={{ height: compact ? 110 : 220, width: '100%' }} nativeControls={false} allowsPictureInPicture={false} fullscreenOptions={{ enable: false }} contentFit="contain" />
    {!!caption && <Text numberOfLines={compact ? 2 : undefined} style={[styles.text, { backgroundColor: '#16352B', color: '#fff', padding: 12 }]}>{caption}</Text>}
    {!compact && <Text style={styles.text}>{Math.floor(time.currentTime)} seconds</Text>}
    <MediaAction compact={compact} title={playing.isPlaying ? 'Pause video' : 'Play video'} disabled={!active || status.status !== 'readyToPlay'} onPress={() => { if (playing.isPlaying) player.pause(); else { if (player.currentTime >= player.duration - 0.1) player.replay(); player.play(); } }} />
    {status.status === 'loading' && <ActivityIndicator accessibilityLabel="Preparing video" />}
    {status.status === 'error' && <Text style={styles.text}>This video could not play. You can still read the text below.</Text>}
  </View>;
}
export function MediaCard({ media, version, active, compact = false }: { media: Media; version: number; active: boolean; compact?: boolean }) {
  const { repository, dataSaver } = useFeed(); const [uri, setUri] = useState(''); const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const load = useCallback(async () => { if (!repository) return; setBusy(true); setError(''); try { setUri(await repository.media(version, media)); } catch (problem) { setError(problem instanceof Error ? problem.message : 'Could not load this file.'); } finally { setBusy(false); } }, [repository, version, media]);
  useEffect(() => { if (media.kind === 'image' && !dataSaver && active && !uri && !busy && !error) { void Promise.resolve().then(load); } }, [media.kind, dataSaver, active, uri, busy, error, load]);
  return <View style={{ gap: compact ? 6 : 14 }}><Text style={[styles.message, compact && { fontSize: 12, lineHeight: 18 }]}>{media.kind.toUpperCase()} · {(media.byte_size / 1000).toFixed(0)} KB{media.duration_seconds ? ' · ' + media.duration_seconds + ' seconds' : ''}</Text>
    {!compact && media.kind === 'image' && <Text style={styles.text}>{media.alt_text}</Text>}
    {!uri && <MediaAction compact={compact} title={busy ? 'Loading…' : 'Load ' + media.kind} disabled={busy || !active} onPress={() => { void load(); }} />}
    {busy && <ActivityIndicator accessibilityLabel="Loading media" />}
    {!!error && <Text accessibilityLiveRegion="polite" style={styles.text}>{error}</Text>}
    {!!uri && media.kind === 'image' && <Image source={{ uri }} accessibilityLabel={media.alt_text} resizeMode="contain" style={{ width: '100%', height: compact ? 110 : 240 }} onError={() => { setUri(''); setError('This image could not open. Read its description above or try again.'); }} />}
    {!!uri && media.kind === 'audio' && <Audio uri={uri} active={active} compact={compact} />}
    {!!uri && media.kind === 'video' && <Video uri={uri} active={active} captions={media.captions_vtt} compact={compact} />}
    {!compact && !!media.transcript && <><Text style={styles.message}>Read instead</Text><Text style={styles.text}>{media.transcript}</Text></>}
    {!compact && !!media.attribution && <Text style={styles.message}>Source: {media.attribution}</Text>}
  </View>;
}
