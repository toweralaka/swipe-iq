export type Exam = { id: number; code: string; name: string };
export type Subject = { id: number; name: string; examination: Exam };
export type Topic = { id: number; name: string; subject: Subject };
export type Unit = { id: number; unit_key: string; number: number; title: string; objective: string; topic: Topic };
export type Media = { id: string; kind: 'image' | 'audio' | 'video'; byte_size: number; duration_seconds: number | null; alt_text: string; transcript: string; captions_vtt: string; attribution: string; url: string };
export type Card = { identity: string; position: number; text: string; media: Media | null };
export type Lesson = Unit & { cards: Card[] };
export type ListPage<T> = { count: number; next: string | null; results: T[] };
function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('The lesson data could not be read. Try again.');
  return value as Record<string, unknown>;
}
function text(value: unknown): string { if (typeof value !== 'string') throw new Error('Missing lesson text.'); return value; }
function id(value: unknown): number { if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 1) throw new Error('Invalid lesson number.'); return value; }
export function examFrom(value: unknown): Exam { const v = record(value); return { id: id(v.id), code: text(v.code), name: text(v.name) }; }
export function subjectFrom(value: unknown): Subject { const v = record(value); return { id: id(v.id), name: text(v.name), examination: examFrom(v.examination) }; }
export function topicFrom(value: unknown): Topic { const v = record(value); return { id: id(v.id), name: text(v.name), subject: subjectFrom(v.subject) }; }
export function unitFrom(value: unknown): Unit { const v = record(value); return { id: id(v.id), unit_key: text(v.unit_key), number: id(v.number), title: text(v.title), objective: text(v.objective), topic: topicFrom(v.topic) }; }
export function mediaFrom(value: unknown): Media {
  const v = record(value); const key = text(v.id); const kind = v.kind;
  if (!/^[0-9a-f-]{36}$/i.test(key) || !['image', 'audio', 'video'].includes(String(kind)) || v.url !== '/api/v1/media/' + key + '/') throw new Error('Invalid media address.');
  const size = id(v.byte_size); const max = kind === 'image' ? 250_000 : kind === 'audio' ? 1_000_000 : 5_000_000;
  if (size > max) throw new Error('This file is too large for the app.');
  return { id: key, kind: kind as Media['kind'], byte_size: size, duration_seconds: v.duration_seconds == null ? null : id(v.duration_seconds), alt_text: text(v.alt_text), transcript: text(v.transcript), captions_vtt: text(v.captions_vtt), attribution: text(v.attribution), url: text(v.url) };
}
export function lessonFrom(value: unknown): Lesson {
  const v = record(value);
  if (!Array.isArray(v.cards) || v.cards.length < 1 || v.cards.length > 3) throw new Error('This lesson has no readable cards.');
  return { ...unitFrom(v), cards: v.cards.map((value, i) => { const c = record(value); if (c.position !== i + 1) throw new Error('Cards are out of order.'); return { identity: text(c.identity), position: id(c.position), text: text(c.text), media: c.media == null ? null : mediaFrom(c.media) }; }) };
}
export function pageFrom<T>(value: unknown, parse: (item: unknown) => T): ListPage<T> {
  const v = record(value);
  if (!Array.isArray(v.results) || typeof v.count !== 'number' || v.count < 0 || (v.next !== null && typeof v.next !== 'string')) throw new Error('The list could not be read.');
  return { count: v.count, next: v.next as string | null, results: v.results.map(parse) };
}
export function nextPath(url: string, base: string, currentPath: string): string {
  const target = new URL(url, base); const origin = new URL(base);
  if (target.origin !== origin.origin || target.username || target.password || target.hash || target.pathname !== '/api/v1/' + currentPath.split('?')[0]) throw new Error('The next page address is invalid.');
  const filters = new URLSearchParams(currentPath.split('?')[1]);
  for (const [key, value] of filters) if (key !== 'page' && target.searchParams.get(key) !== value) throw new Error('The next page belongs to a different list.');
  return target.pathname.slice('/api/v1/'.length) + target.search;
}
