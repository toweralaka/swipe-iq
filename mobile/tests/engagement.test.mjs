import test from 'node:test';
import assert from 'node:assert/strict';
import { LikeController, likeFrom } from '../src/engagement/likes.ts';
import { DailyEvents } from '../src/engagement/events.ts';

test('like state changes only after confirmation and repeated taps send once',async()=>{
 let resolve;const calls=[];const controller=new LikeController('like/',async(path,body)=>{calls.push(body);if(!body)return {liked:false};return new Promise(done=>{resolve=done;});});await controller.load();const pending=controller.change();void controller.change();assert.equal(controller.getSnapshot().liked,false);assert.equal(controller.getSnapshot().busy,true);assert.equal(calls.length,2);assert.deepEqual(calls[1],{liked:true});resolve({liked:true});await pending;assert.equal(controller.getSnapshot().liked,true);assert.equal(controller.getSnapshot().busy,false);
});
test('a lost reply retains the last confirmed display and retry reads actual server state',async()=>{
 let server=false;const controller=new LikeController('like/',async(path,body)=>{if(body){server=body.liked;throw Error('Reply lost');}return {liked:server};});await controller.load();await controller.change();assert.equal(controller.getSnapshot().liked,false);assert.equal(controller.getSnapshot().uncertain,true);await controller.change();await controller.load();assert.equal(controller.getSnapshot().liked,true);assert.equal(controller.getSnapshot().uncertain,false);
});
test('unlike sends false and a rejected request never reports success',async()=>{
 let reject=false;const bodies=[];const controller=new LikeController('like/',async(path,body)=>{if(reject)throw Error('401');if(body)bodies.push(body);return {liked:body?body.liked:true};});await controller.load();await controller.change();assert.deepEqual(bodies,[{liked:false}]);assert.equal(controller.getSnapshot().liked,false);reject=true;await controller.change();assert.equal(controller.getSnapshot().liked,false);assert.ok(controller.getSnapshot().error);assert.equal(controller.getSnapshot().uncertain,true);
});
test('unreadable or failed initial state keeps liking disabled until a successful check',async()=>{
 let broken=true;const controller=new LikeController('like/',async()=>broken?{count:4}:{liked:false});await controller.load();assert.equal(controller.getSnapshot().liked,null);assert.equal(controller.getSnapshot().uncertain,true);await controller.change();broken=false;await controller.load();assert.equal(controller.getSnapshot().liked,false);assert.throws(()=>likeFrom({liked:'true'}));
});
test('account-specific controllers never inherit a previous account like',async()=>{
 const first=new LikeController('like/',async()=>({liked:true})),second=new LikeController('like/',async()=>({liked:false}));await first.load();assert.equal(second.getSnapshot().liked,null);await second.load();assert.equal(first.getSnapshot().liked,true);assert.equal(second.getSnapshot().liked,false);
});
test('daily events deduplicate inflight and confirmed deliveries but allow another Lagos day',async()=>{
 let calls=0,now=Date.parse('2026-10-12T22:59:00Z');const events=new DailyEvents(async(path,body)=>{assert.equal(path,'engagement/events/');assert.deepEqual(Object.keys(body).sort(),['card_identity','kind','version']);calls++;},()=>now);
 await Promise.all([events.track(1,'card','view'),events.track(1,'card','view')]);await events.track(1,'card','view');assert.equal(calls,1);await events.track(1,'card','dare_shown');assert.equal(calls,2);now=Date.parse('2026-10-12T23:01:00Z');await events.track(1,'card','view');assert.equal(calls,3);
});
test('failed events do not block scrolling or queue background retries',async()=>{
 let calls=0;const events=new DailyEvents(async()=>{calls++;throw Error('Offline');});await events.track(1,'card','view');await new Promise(resolve=>setImmediate(resolve));assert.equal(calls,1);await events.track(1,'card','view');assert.equal(calls,2);
});
