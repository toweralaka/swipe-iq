export const CACHE_LIMIT = 100_000_000;
const INDEX_RESERVE = 100_000;
const MAX_ENTRIES = 200;
export type Disk = {
  read: (file: string) => Promise<Uint8Array | null>;
  write: (file: string, bytes: Uint8Array) => Promise<void>;
  remove: (file: string) => Promise<void>;
  clear: () => Promise<void>;
  uri: (file: string) => string;
  files: () => Promise<string[]>;
  size: (file: string) => Promise<number>;
};
export type Lease = { owner: string; generation: number };
type Entry = { key: string; file: string; size: number; used: number };
type Index = { owner: string; entries: Entry[] };
export class CacheChanged extends Error {}
const encode = (data: unknown) => new TextEncoder().encode(JSON.stringify(data));
const safeFile = (value: string) => /^item-[0-9-]+\.(json|png|jpg|mp3|wav|mp4)$/.test(value);

export class ViewedCache {
  private disk: Disk;
  private limit: number;
  private index: Index = { owner: '', entries: [] };
  private loaded = false;
  private generation = 0;
  private clock = 0;
  private queue: Promise<unknown> = Promise.resolve();
  constructor(disk: Disk, limit = CACHE_LIMIT) { this.disk = disk; this.limit = limit; }
  private serial<T>(action: () => Promise<T>): Promise<T> {
    const work = this.queue.then(action);
    this.queue = work.catch(() => {});
    return work;
  }
  private async load() {
    if (this.loaded) return;
    try {
      const bytes = await this.disk.read('index.json');
      if (bytes) {
        const data = JSON.parse(new TextDecoder().decode(bytes)) as Index;
        if (typeof data.owner !== 'string' || !Array.isArray(data.entries) || data.entries.length > MAX_ENTRIES
          || !data.entries.every(e => typeof e.key === 'string' && e.key.length <= 300 && safeFile(e.file)
            && Number.isSafeInteger(e.size) && e.size > 0 && Number.isFinite(e.used))) throw new Error('Invalid cache');
        if (data.entries.reduce((n, e) => n + e.size, bytes.length) > this.limit) throw new Error('Cache too large');
        const retained = [];
        for (const entry of data.entries) {
          if (await this.disk.size(entry.file) === entry.size) retained.push(entry);
          else await this.disk.remove(entry.file);
        }
        data.entries = retained;
        const known = new Set(['index.json', ...retained.map(e => e.file)]);
        for (const file of await this.disk.files()) if (!known.has(file)) await this.disk.remove(file);
        this.index = data;
        this.clock = Math.max(0, ...data.entries.map(e => e.used));
      } else { await this.disk.clear(); }
    } catch { await this.disk.clear(); this.index = { owner: '', entries: [] }; }
    this.loaded = true;
  }
  private check(lease: Lease) {
    if (lease.owner !== this.index.owner || lease.generation !== this.generation) throw new CacheChanged('Saved content changed. Open the lesson again.');
  }
  private async save() {
    const data = encode(this.index);
    if (data.length > Math.min(INDEX_RESERVE, this.limit / 4)) throw new Error('Cache index too large');
    await this.disk.write('index.json', data);
  }
  activate(owner: string): Promise<Lease> {
    return this.serial(async () => {
      await this.load();
      if (owner !== this.index.owner) {
        await this.disk.clear(); this.generation++; this.index = { owner, entries: [] }; await this.save();
      }
      return { owner, generation: this.generation };
    });
  }
  clear(): Promise<void> {
    return this.serial(async () => {
      await this.load(); this.generation++;
      await this.disk.clear(); this.index = { owner: '', entries: [] }; await this.save();
    });
  }
  read(lease: Lease, key: string): Promise<Uint8Array | null> {
    return this.serial(async () => {
      await this.load(); this.check(lease);
      const entry = this.index.entries.find(e => e.key === key);
      if (!entry) return null;
      const data = await this.disk.read(entry.file);
      if (!data || data.length !== entry.size) { await this.dropEntry(entry); await this.save(); return null; }
      entry.used = ++this.clock; await this.save(); return data;
    });
  }
  file(lease: Lease, key: string): Promise<string | null> {
    return this.serial(async () => {
      await this.load(); this.check(lease);
      const entry = this.index.entries.find(e => e.key === key);
      if (!entry) return null;
      const bytes = await this.disk.read(entry.file);
      if (!bytes || bytes.length !== entry.size) { await this.dropEntry(entry); await this.save(); return null; }
      entry.used = ++this.clock; await this.save(); return this.disk.uri(entry.file);
    });
  }
  private async dropEntry(entry: Entry) {
    await this.disk.remove(entry.file); this.index.entries = this.index.entries.filter(e => e !== entry);
  }
  keys(lease: Lease, prefix: string): Promise<string[]> {
    return this.serial(async () => { await this.load(); this.check(lease); return this.index.entries.filter(e => e.key.startsWith(prefix)).map(e => e.key); });
  }
  remove(lease: Lease, key: string): Promise<void> {
    return this.serial(async () => {
      await this.load(); this.check(lease);
      const entry = this.index.entries.find(e => e.key === key);
      if (entry) { await this.dropEntry(entry); await this.save(); }
    });
  }
  put(lease: Lease, key: string, bytes: Uint8Array, extension: 'json' | 'png' | 'jpg' | 'mp3' | 'wav' | 'mp4' = 'json'): Promise<string> {
    return this.serial(async () => {
      await this.load(); this.check(lease);
      const reserve = Math.min(INDEX_RESERVE, this.limit / 4);
      if (!bytes.length || bytes.length > this.limit - reserve || key.length > 300) throw new Error('This item is too large to save.');
      const existing = this.index.entries.find(e => e.key === key);
      if (existing) await this.dropEntry(existing);
      while (this.index.entries.length && (this.index.entries.reduce((n, e) => n + e.size, bytes.length) > this.limit - reserve || this.index.entries.length >= MAX_ENTRIES)) {
        const oldest = this.index.entries.reduce((a, b) => a.used < b.used ? a : b);
        await this.dropEntry(oldest);
      }
      const file = 'item-' + Date.now() + '-' + (++this.clock) + '.' + extension;
      try {
        await this.disk.write(file, bytes);
        this.index.entries.push({ key, file, size: bytes.length, used: this.clock });
        await this.save(); return this.disk.uri(file);
      } catch (error) {
        await this.disk.clear(); this.index.entries = []; this.generation++; throw error;
      }
    });
  }
}
