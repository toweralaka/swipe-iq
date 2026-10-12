export type Cue = { start: number; end: number; text: string };
function seconds(value: string): number { const parts = value.trim().split(':').map(Number); return parts.reduce((sum, v) => sum * 60 + v, 0); }
export function captionsFrom(vtt: string): Cue[] {
  return vtt.replace(/\r/g, '').split(/\n\n+/).flatMap(block => {
    const lines = block.split('\n'); const timing = lines.findIndex(line => line.includes(' --> '));
    if (timing < 0) return [];
    const [a, b] = lines[timing].split(' --> '); const start = seconds(a); const end = seconds(b.split(' ')[0]);
    return Number.isFinite(start) && Number.isFinite(end) && end > start ? [{ start, end, text: lines.slice(timing + 1).join('\n').replace(/<[^>]*>/g, '') }] : [];
  });
}
export function captionAt(cues: Cue[], time: number) { return cues.filter(cue => cue.start <= time && time < cue.end).map(cue => cue.text).join('\n'); }
