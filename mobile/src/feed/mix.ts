import type { Lesson, Card } from './types.ts';
export type Post = { key: string; lesson: Lesson; card: Card };
export function subjectIds(value: string): number[] {
  const parts = value.split(',');
  if (!value || parts.length > 20 || !parts.every(v => /^[1-9][0-9]*$/.test(v) && Number(v) <= 2147483647)) throw new Error('Pick between 1 and 20 subjects.');
  return [...new Set(parts.map(Number))].sort((a,b) => a-b);
}
export function feedPath(ids: number[], search = '') {
  const subjects = subjectIds(ids.join(',')); const q = search.trim();
  if (q && q.split(/\s+/).length > 10) throw new Error('Use 10 words or fewer in your search.');
  if (q.length > 120) throw new Error('Keep your search under 120 characters.');
  return 'feed/?subjects=' + subjects.join(',') + (q ? '&q=' + encodeURIComponent(q) : '');
}
export function postsFrom(lessons: Lesson[]): Post[] {
  return lessons.flatMap(lesson => lesson.cards.map(card => ({ key: lesson.id + ':' + card.identity, lesson, card })));
}
export function mergePosts(previous: Post[], incoming: Post[]): Post[] {
  const keys = new Set(previous.map(post => post.key)); return [...previous, ...incoming.filter(post => { if(keys.has(post.key)) return false; keys.add(post.key); return true; })];
}
