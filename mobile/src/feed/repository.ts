import { ApiError, NetworkError } from '../api/student.ts';
import { ViewedCache, type Lease } from '../cache/store.ts';
import { lessonFrom, feedPageFrom, type Media } from './types.ts';
export type ReadResult<T> = { value: T; saved: boolean; offline: boolean };
export type MediaBytes = { bytes: Uint8Array; extension: 'png' | 'jpg' | 'mp3' | 'wav' | 'mp4' };
export class FeedRepository {
  private unavailable = new Set<string>();
  private cache: ViewedCache; private lease: Lease;
  private request: (path: string, body?: unknown) => Promise<unknown>;
  private download: (media: Media) => Promise<MediaBytes>;
  constructor(cache: ViewedCache, lease: Lease, request: (path: string, body?: unknown) => Promise<unknown>, download: (media: Media) => Promise<MediaBytes>) { this.cache = cache; this.lease = lease; this.request = request; this.download = download; }
  async read<T>(path: string, parse: (data: unknown) => T): Promise<ReadResult<T>> {
    const key = 'json:' + path;
    try {
      const value = parse(await this.request(path));
      if (this.unavailable.has(path)) throw new ApiError(404, 'This lesson is no longer available. Refresh the lesson list.');
      let saved = true;
      try { await this.cache.put(this.lease, key, new TextEncoder().encode(JSON.stringify(value))); } catch { saved = false; }
      return { value, saved, offline: false };
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) await this.forgetLesson(path);
      if (!(error instanceof NetworkError)) throw error;
      const bytes = await this.cache.read(this.lease, key);
      if (!bytes) throw new NetworkError('You are offline and this lesson or list is not saved yet. Connect and try again.');
      return { value: parse(JSON.parse(new TextDecoder().decode(bytes))), saved: true, offline: true };
    }
  }
  async selection(): Promise<number[]> {
    const bytes = await this.cache.read(this.lease, 'selection:subjects');
    if (!bytes) return [];
    try { const value = JSON.parse(new TextDecoder().decode(bytes)); return Array.isArray(value) && value.length <= 20 && value.every(id => Number.isSafeInteger(id) && id > 0) ? value : []; } catch { return []; }
  }
  async saveSelection(ids: number[]) {
    await this.cache.put(this.lease, 'selection:subjects', new TextEncoder().encode(JSON.stringify(ids)));
  }
  async feed(path: string) {
    const result = await this.read(path, feedPageFrom);
    result.value.results = result.value.results.filter(lesson => !this.unavailable.has('units/' + lesson.id + '/'));
    if (!result.offline) for (const lesson of result.value.results) {
      try { await this.cache.put(this.lease, 'json:units/' + lesson.id + '/', new TextEncoder().encode(JSON.stringify(lesson))); } catch { result.saved = false; }
    }
    return result;
  }
  async media(version: number, media: Media): Promise<string> {
    const path = 'units/' + version + '/';
    if (this.unavailable.has(path)) throw new ApiError(404, 'This lesson is no longer available.');
    const key = 'media:' + version + ':' + media.id;
    const saved = await this.cache.file(this.lease, key);
    if (saved) return saved;
    const data = await this.download(media);
    if (this.unavailable.has(path)) throw new ApiError(404, 'This lesson is no longer available.');
    if (data.bytes.length !== media.byte_size) throw new Error('The file did not finish loading. Try again.');
    return this.cache.put(this.lease, key, data.bytes, data.extension);
  }
  async forgetLesson(path: string) {
    if (/^units\/\d+\/$/.test(path)) this.unavailable.add(path);
    await this.cache.remove(this.lease, 'json:' + path);
    const match = /^units\/(\d+)\/$/.exec(path);
    if (match) for (const key of await this.cache.keys(this.lease, 'media:' + match[1] + ':')) await this.cache.remove(this.lease, key);
  }
  async recheckSavedLessons() {
    const keys = (await this.cache.keys(this.lease, 'json:units/')).filter(key => /^json:units\/\d+\/$/.test(key));
    if (!keys.length) return;
    const ids = keys.map(key => Number(key.split('/')[1]));
    const data = await this.request('units/availability/', { version_ids: ids }) as { available_ids?: unknown };
    if (!Array.isArray(data.available_ids) || !data.available_ids.every(id => typeof id === 'number')) throw new Error('Could not check saved lessons.');
    const available = new Set(data.available_ids);
    const unavailable = ids.filter(id => !available.has(id));
    for (const id of unavailable) await this.forgetLesson('units/' + id + '/');
    if (unavailable.length) {
      // Old selection/list pages may still name a removed lesson; fetch them again.
      for (const key of await this.cache.keys(this.lease, 'json:')) if (!/^json:units\/\d+\/$/.test(key)) await this.cache.remove(this.lease, key);
    }
  }
}
export const readLesson = (repository: FeedRepository, id: number) => repository.read('units/' + id + '/', lessonFrom);
