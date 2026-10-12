import { useLocalSearchParams } from 'expo-router';
import { LessonList } from '../feed/list';
export default function Browse() {
 const params = useLocalSearchParams<{ exam?: string; subject?: string; topic?: string }>();
 return params.topic ? <LessonList stage="unit" selection={params.topic} /> : params.subject ? <LessonList stage="topic" selection={params.subject} /> : params.exam ? <LessonList stage="subject" selection={params.exam} /> : <LessonList stage="exam" />;
}
