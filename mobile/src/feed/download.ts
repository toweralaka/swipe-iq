import { ApiError, NetworkError } from '../api/student.ts';
import type { Media } from './types.ts';
import type { MediaBytes } from './repository.ts';
type FetchFile = (url: string, options: { headers: Record<string, string>; signal: AbortSignal; redirect: 'error' }) => Promise<{ ok: boolean; status: number; headers: { get: (key: string) => string | null }; arrayBuffer: () => Promise<ArrayBuffer> }>;
export async function downloadMedia(media: Media, base: string, credential: string, fetchFile: FetchFile): Promise<MediaBytes> {
  if (media.url !== '/api/v1/media/' + media.id + '/') throw new Error('Invalid media address.');
  const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 30000);
  try {
    const response = await fetchFile(base + media.url, { headers: { Authorization: 'Bearer ' + credential }, signal: controller.signal, redirect: 'error' });
    if (!response.ok) throw new ApiError(response.status, response.status === 401 ? 'Sign in again to load this file.' : 'This file could not be loaded. Try again or read the text instead.');
    const length = response.headers.get('Content-Length');
    if (length && Number(length) !== media.byte_size) throw new Error('The file size has changed. Refresh this lesson.');
    const mime = response.headers.get('Content-Type')?.split(';')[0];
    const formats: Record<string, MediaBytes['extension']> = { 'image/png': 'png', 'image/jpeg': 'jpg', 'audio/mpeg': 'mp3', 'audio/wav': 'wav', 'audio/x-wav': 'wav', 'video/mp4': 'mp4' };
    const extension = formats[mime ?? ''];
    if (!extension || (media.kind === 'image' && !['png', 'jpg'].includes(extension)) || (media.kind === 'audio' && !['mp3', 'wav'].includes(extension)) || (media.kind === 'video' && extension !== 'mp4')) throw new Error('Unsupported file format. Read the text instead.');
    const bytes = new Uint8Array(await response.arrayBuffer());
    if (bytes.length !== media.byte_size) throw new Error('The file did not finish loading. Try again.');
    return { bytes, extension };
  } catch (error) {
    if (controller.signal.aborted) throw new NetworkError('The file took too long to load. Try again or read the text.');
    if (error instanceof TypeError) throw new NetworkError('Could not download this file. Check your connection and try again.');
    throw error;
  } finally { clearTimeout(timeout); }
}
