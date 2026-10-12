import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ViewedCache, CacheChanged } from '../src/cache/store.ts';
import { FeedRepository } from '../src/feed/repository.ts';
import { ApiError, NetworkError } from '../src/api/student.ts';
import { nextPath, lessonFrom, pageFrom, examFrom } from '../src/feed/types.ts';
import { downloadMedia } from '../src/feed/download.ts';
import { feedPath, subjectIds, postsFrom, mergePosts } from '../src/feed/mix.ts';
import { captionsFrom, captionAt } from '../src/feed/captions.ts';
function disk() { const data = new Map(); return { data, async read(k) { return data.get(k) ?? null; }, async write(k,v) { data.set(k,v); }, async remove(k) { data.delete(k); }, async clear() { data.clear(); }, uri(k) { return 'file:///' + k; }, async files() { return [...data.keys()]; }, async size(k) { return data.get(k)?.length ?? 0; } }; }
const bytes = size => new Uint8Array(size).fill(65);
const media = { id: 'a'.repeat(8) + '-aaaa-aaaa-aaaa-' + 'a'.repeat(12), kind: 'image', byte_size: 3, duration_seconds: null, alt_text: 'A cell', transcript: '', captions_vtt: '', attribution: 'teacher' };
media.url = '/api/v1/media/' + media.id + '/';
const exam = { id: 1, code: 'jamb', name: 'JAMB' };
const lesson = { id: 1, unit_key: 'cell', number: 1, title: 'Cell', objective: 'Know cells', topic: { id: 1, name: 'Cells', subject: { id: 1, name: 'Biology', examination: exam } }, cards: [{ identity: 'one', position: 1, text: 'Cell lesson', media }] };
async function setup(request = async () => lesson, download = async () => ({ bytes: bytes(3), extension: 'png' })) { const drive = disk(); const cache = new ViewedCache(drive, 10000); const lease = await cache.activate('user1'); return { drive, cache, lease, repository: new FeedRepository(cache, lease, request, download) }; }
test('cache stays within its byte limit and removes the least recently used item', async () => {
 const drive = disk(); const cache = new ViewedCache(drive, 10000); const lease = await cache.activate('a');
 await cache.put(lease, 'a', bytes(3000)); await cache.put(lease, 'b', bytes(3000)); await cache.read(lease, 'a'); await cache.put(lease, 'c', bytes(3000));
 assert.equal(await cache.read(lease, 'b'), null); assert.equal((await cache.read(lease, 'a')).length, 3000); assert.ok([...drive.data.values()].reduce((n,v)=>n+v.length,0) <= 10000);
 await assert.rejects(cache.put(lease, 'huge', bytes(10001)), /large/);
});
test('account change and clear reject late writes from old requests', async () => {
 const { cache, lease } = await setup(); await cache.put(lease,'private',bytes(10)); const next = await cache.activate('user2'); assert.equal(await cache.read(next,'private'),null);
 await assert.rejects(cache.put(lease,'late',bytes(10)),CacheChanged); await cache.clear(); await assert.rejects(cache.put(next,'late',bytes(10)),CacheChanged);
});
test('restart removes unfinished files and detects missing or corrupt saved files', async () => {
 const { drive, cache, lease } = await setup(); await cache.put(lease,'text',bytes(10)); drive.data.set('unfinished.mp4',bytes(20));
 const restarted = new ViewedCache(drive,10000); const live = await restarted.activate('user1'); assert.equal(drive.data.has('unfinished.mp4'),false);
 const file = JSON.parse(new TextDecoder().decode(drive.data.get('index.json'))).entries[0].file; drive.data.delete(file); assert.equal(await restarted.read(live,'text'),null);
 drive.data.set('index.json',new TextEncoder().encode('broken')); const recovered = new ViewedCache(drive,10000); const owner = await recovered.activate('user1'); assert.equal(await recovered.read(owner,'text'),null);
});
test('file-write failure removes partial data and invalidates old work', async () => {
 const { drive, cache, lease } = await setup(); const write = drive.write; drive.write = async (k,v) => { await write(k,v); throw new Error('disk full'); };
 await assert.rejects(cache.put(lease,'x',bytes(30)),/disk full/); assert.equal(drive.data.size,0); await assert.rejects(cache.read(lease,'x'),CacheChanged);
});
test('network failures use saved text, while 401, 404 and server errors do not', async () => {
 let fail; const { repository } = await setup(async () => { if(fail) throw fail; return lesson; }); await repository.read('units/1/',lessonFrom);
 fail = new NetworkError('offline'); const saved = await repository.read('units/1/',lessonFrom); assert.equal(saved.offline,true); assert.equal(saved.value.title,'Cell');
 for (const status of [401,500,404]) { fail = new ApiError(status,'failure'); await assert.rejects(repository.read('units/1/',lessonFrom), e => e.status === status); }
 fail = new NetworkError('offline'); await assert.rejects(repository.read('units/1/',lessonFrom),/not saved/);
});
test('publication check removes withdrawn text, media and old selection lists', async () => {
 const { repository, cache, lease } = await setup(async path => path === 'units/availability/' ? { available_ids: [] } : lesson);
 await repository.read('units/1/',lessonFrom); await repository.media(1,media); await cache.put(lease,'json:examinations/',bytes(20)); await repository.recheckSavedLessons(); assert.deepEqual(await cache.keys(lease,''),[]);
});
test('an unfinished download is never cached', async () => {
 const { repository, cache, lease } = await setup(undefined,async () => ({ bytes: bytes(2), extension:'png' })); await assert.rejects(repository.media(1,media),/finish/); assert.deepEqual(await cache.keys(lease,'media:'),[]);
});
test('pagination cannot change server, path or selected topic', () => {
 const base = 'https://api.example.com'; const current = 'units/?topic=1'; assert.equal(nextPath(base+'/api/v1/units/?topic=1&page=2',base,current),'units/?topic=1&page=2');
 for(const url of ['https://evil.example/api/v1/units/?topic=1','/api/v1/auth/me/','/api/v1/units/?topic=2']) assert.throws(()=>nextPath(url,base,current));
});
test('lesson parser drops answer keys and rejects foreign media addresses', () => {
 assert.equal(lessonFrom({...lesson,questions:[{answer:'secret'}]}).questions,undefined); assert.throws(()=>lessonFrom({...lesson,cards:[{...lesson.cards[0],media:{...media,url:'https://evil.example/file'}}]}));
});
test('media download uses an auth header, blocks redirects and checks byte count', async () => {
 const fetcher = async (url,opts) => { assert.equal(url,'https://api.example.com'+media.url); assert.equal(opts.headers.Authorization,'Bearer secret'); assert.equal(opts.redirect,'error'); return new Response(bytes(3),{headers:{'Content-Type':'image/png','Content-Length':'3'}}); };
 assert.equal((await downloadMedia(media,'https://api.example.com','secret',fetcher)).extension,'png');
 await assert.rejects(downloadMedia(media,'https://api.example.com','secret',async()=>new Response(bytes(2),{headers:{'Content-Type':'image/png'}})),/finish|size|complete|match/);
});
test('video captions use cue times and are readable without markup', () => {
 const cues = captionsFrom('WEBVTT\n\n00:00:01.000 --> 00:00:03.000\n<b>A cell</b>\n\n00:00:03.000 --> 00:00:04.000\nNext'); assert.equal(captionAt(cues,0),''); assert.equal(captionAt(cues,2),'A cell'); assert.equal(captionAt(cues,3),'Next');
});

 test('saved selection pages keep their shape and page two works offline after it was viewed', async () => {
  let offline = false; const { repository } = await setup(async path => { if(offline) throw new NetworkError('offline'); return { count: 21, next: path.includes('page=2') ? null : 'https://api.example.com/api/v1/examinations/?page=2', results: [exam] }; });
  const parse = data => pageFrom(data,examFrom); await repository.read('examinations/',parse); await repository.read('examinations/?page=2',parse); offline = true;
  const first = await repository.read('examinations/',parse); const second = await repository.read(nextPath(first.value.next,'https://api.example.com','examinations/'),parse);
  assert.equal(second.offline,true); assert.equal(second.value.results[0].code,'jamb'); assert.equal(second.value.next,null);
 });

 test('a file started before a withdrawal cannot save itself afterwards', async () => {
  let finish; const pending = new Promise(resolve => { finish = resolve; }); const { repository, cache, lease } = await setup(undefined,async()=>pending);
  const loading = repository.media(1,media); await new Promise(resolve=>setImmediate(resolve)); await repository.forgetLesson('units/1/'); finish({ bytes:bytes(3),extension:'png' });
  await assert.rejects(loading,e=>e.status===404); assert.deepEqual(await cache.keys(lease,'media:'),[]);
 });

 test('subject selections are bounded and search cannot escape its selected-subject query', () => {
  assert.deepEqual(subjectIds('3,1,3'),[1,3]); assert.equal(feedPath([3,1],'membrane & page=99'),'feed/?subjects=1,3&q=membrane%20%26%20page%3D99');
  for(const ids of ['', '0', '-1', '1,bad', '1,'.repeat(21)]) assert.throws(()=>subjectIds(ids));
  assert.throws(()=>feedPath([1],'x'.repeat(121)));
 });
 test('feed cards retain their unit and stable identity and repeated pages do not duplicate posts', () => {
  const items = postsFrom([lesson]); assert.equal(items[0].lesson.id,1); assert.equal(items[0].card.text,'Cell lesson'); assert.equal(mergePosts(items,items).length,1);
 });
 test('subject picks are remembered for the account and cleared with its content', async () => {
  const { repository,cache,lease } = await setup(); await repository.saveSelection([1,2]); assert.deepEqual(await repository.selection(),[1,2]);
  const next = await cache.activate('another-account'); const other = new FeedRepository(cache,next,async()=>lesson,async()=>({bytes:bytes(3),extension:'png'})); assert.deepEqual(await other.selection(),[]); await assert.rejects(cache.read(lease,'selection:subjects'),CacheChanged);
 });
 test('cached mixed feeds can be opened offline and are purged when a version is withdrawn', async () => {
  let offline = false; const { repository,cache,lease } = await setup(async path => { if(offline) throw new NetworkError('offline'); return path === 'units/availability/' ? { available_ids: [] } : {count:1,next:null,results:[lesson]}; });
  const path = feedPath([1]); await repository.feed(path); offline = true; assert.equal((await repository.feed(path)).offline,true); offline = false; await repository.recheckSavedLessons(); assert.deepEqual(await cache.keys(lease,'json:'),[]);
 });
