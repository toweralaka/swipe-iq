import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, Text, View, type ViewToken } from 'react-native';
import { router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import { useSession } from '../auth/session';
import { Action, Page, styles } from '../components/ui';
import { useFeed } from '../feed/context';
import { readLesson, type ReadResult } from '../feed/repository';
import { MediaCard } from '../feed/media';
import type { Card, Lesson } from '../feed/types';
export default function LessonScreen() {
  const { id } = useLocalSearchParams<{ id: string }>(); const { candidate } = useSession(); const { repository, revision, error } = useFeed();
  if (!candidate) return <Page><Text style={styles.text}>Sign in to read lessons.</Text><Action title="Go to sign-in" onPress={() => router.replace('/')} /></Page>;
  if (!/^\d+$/.test(id ?? '')) return <Page><Text style={styles.text}>Choose a lesson from the topic list.</Text></Page>;
  if (!repository) return <Page>{error ? <Text style={styles.text}>{error}</Text> : <ActivityIndicator />}</Page>;
  return <LessonBody key={id + ':' + revision} id={Number(id)} />;
}
function LessonBody({ id }: { id: number }) {
  const { repository } = useFeed(); const [result, setResult] = useState<ReadResult<Lesson> | null>(null); const [error, setError] = useState(''); const [attempt, setAttempt] = useState(0);
  const [visible, setVisible] = useState<string | null>(null); const [focused, setFocused] = useState(false);
  useFocusEffect(useCallback(() => { setFocused(true); return () => setFocused(false); }, []));
  const viewable = useCallback(({ viewableItems }: { viewableItems: ViewToken<Card>[] }) => { setVisible(viewableItems.find(item => item.isViewable)?.item.identity ?? null); }, []);
  useEffect(() => { let active = true; void readLesson(repository!, id).then(value => { if (active) { setResult(value); setError(''); } }, problem => { if (active) { setResult(null); setError(problem.message); } }); return () => { active = false; }; }, [repository, id, attempt]);
  if (error) return <Page><Text style={styles.text}>{error}</Text><Action title="Retry" onPress={() => { setError(''); setAttempt(v => v + 1); }} /><Action title="Choose another lesson" onPress={() => router.back()} /></Page>;
  if (!result) return <Page><ActivityIndicator accessibilityLabel="Loading lesson text" /></Page>;
  const lesson = result.value;
  return <FlatList style={{ backgroundColor: '#F4F7F1' }} contentContainerStyle={{ padding: 24, gap: 24, paddingBottom: 48 }} data={lesson.cards} keyExtractor={card => card.identity} onViewableItemsChanged={viewable} viewabilityConfig={{ viewAreaCoveragePercentThreshold: 1 }}
    ListHeaderComponent={<View style={{ gap: 16 }}><Text style={styles.message}>{lesson.topic.subject.examination.name} · {lesson.topic.subject.name} · {lesson.topic.name}</Text><Text style={styles.title}>{lesson.title}</Text><Text style={styles.text}>{lesson.objective}</Text>
      {result.offline && <Text style={styles.message}>Offline: reading a saved lesson. Publication changes will be checked when you reconnect.</Text>}
      {!result.saved && <Text style={styles.message}>The text could not be saved. Check free space on your phone.</Text>}
    </View>}
    renderItem={({ item }) => <View style={{ padding: 20, backgroundColor: '#fff', borderRadius: 16, gap: 20 }}><Text style={styles.message}>Card {item.position} of {lesson.cards.length}</Text><Text style={styles.text}>{item.text}</Text>{item.media && <MediaCard media={item.media} version={lesson.id} active={focused && visible === item.identity} />}</View>}
    ListFooterComponent={<Text style={styles.message}>End of lesson. Use Back to choose another.</Text>} />;
}
