import { Directory, File, Paths } from 'expo-file-system';
import { ViewedCache, type Disk } from './store';

// Only this app-owned folder is cleared, never the whole phone cache.
const root = new Directory(Paths.cache, 'swipe-iq-viewed-v1');
function directory() { root.create({ idempotent: true, intermediates: true }); return root; }
const disk: Disk = {
  async read(name) { const file = new File(directory(), name); return file.exists ? await file.bytes() : null; },
  async write(name, bytes) { const file = new File(directory(), name); file.write(bytes); },
  async remove(name) { const file = new File(directory(), name); if (file.exists) file.delete(); },
  async clear() { if (root.exists) root.delete(); directory(); },
  async files() { return directory().list().map(file => file.name); },
  async size(name) { const file = new File(directory(), name); return file.exists ? file.size : 0; },
  uri(name) { return new File(root, name).uri; },
};
export const viewedCache = new ViewedCache(disk);
export const clearViewedContent = () => viewedCache.clear();
