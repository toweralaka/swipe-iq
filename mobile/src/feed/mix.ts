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

export type FeedEntry = {kind:'post';key:string;post:Post}|{kind:'dare';key:string;post:Post};
// Reusing the server mix keeps dare positions steady while more pages arrive.
export function withDares(posts:Post[],mix:string):FeedEntry[]{
 let state=2166136261;for(const c of mix)state=Math.imul(state^c.charCodeAt(0),16777619)>>>0;
 const roll=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296;};
 let remaining=3+Math.floor(roll()*5);const entries:FeedEntry[]=[];const eligible:Post[]=[];
 for(const post of posts){entries.push({kind:'post',key:post.key,post});if(post.lesson.quiz_available)eligible.push(post);remaining=Math.max(0,remaining-1);
  if(remaining===0&&eligible.length){entries.push({kind:'dare',key:'dare:'+post.key,post:eligible[Math.floor(roll()*eligible.length)]});remaining=5+Math.floor(roll()*5);}
 }
 return entries;
}
