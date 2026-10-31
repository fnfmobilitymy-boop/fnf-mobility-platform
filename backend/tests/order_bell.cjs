const {readFileSync}=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const session=new Map(),settings=new Map();let notes=0,allowResume=true;
const elements=Object.fromEntries(['#order-bell','#order-bell-status','#order-alert-controls'].map(id=>[id,{textContent:'',disabled:false,dataset:{},setAttribute(k,v){this[k]=v}}]));
class Audio{constructor(){this.state='suspended';this.currentTime=0;this.destination={}}async resume(){if(allowResume)this.state='running'}createOscillator(){return{frequency:{value:0},connect(){},start(){notes++},stop(){}}}createGain(){return{gain:{setValueAtTime(){},exponentialRampToValueAtTime(){}},connect(){}}}}
function context(){return vm.createContext({$:s=>elements[s],T:(en)=>en,window:{AudioContext:Audio},localStorage:{getItem:k=>settings.get(k)??null,setItem:(k,v)=>settings.set(k,v)},sessionStorage:{getItem:k=>session.get(k)??null,setItem:(k,v)=>session.set(k,v)},Date,setTimeout,clearTimeout,toast(){},console})}
const src=readFileSync('backend/static/admin-tools.js','utf8');let ctx=context();vm.runInContext(src,ctx);const run=s=>vm.runInContext(s,ctx),settle=()=>new Promise(r=>setImmediate(r));
(async()=>{
 run("observeOrderNotifications([{id:'old'}])");assert.equal(notes,0);assert.equal(run('pendingOrderIds.size'),0,'first visit establishes existing-order baseline');
 run("observeOrderNotifications([{id:'new'},{id:'old'}])");await settle();assert.equal(notes,0);assert.equal(run('pendingOrderIds.size'),1,'locked audio retains pending alert');
 await run('enableOrderBell()');assert.equal(notes,6);assert.equal(run('pendingOrderIds.size'),0);assert.equal(elements['#order-alert-controls'].dataset.audio,'ready');
 run("observeOrderNotifications([{id:'new'},{id:'old'}])");await settle();assert.equal(notes,6,'same order must not ring twice');
 // Reopening a dashboard must not replace the independent notification ledger.
 run("observeOrderNotifications([{id:'another'},{id:'new'},{id:'old'}])");await settle();assert.equal(notes,12);
 run("orderAudio.state='suspended'");allowResume=false;run("observeOrderNotifications([{id:'blocked'},{id:'another'}])");await settle();assert.equal(notes,12);assert.equal(run('pendingOrderIds.size'),1);assert.equal(run('orderAudioUnlocked'),false);assert.equal(elements['#order-alert-controls'].dataset.audio,'locked');
 // Reload restores preference/seen/pending IDs, but never claims browser audio is unlocked.
 ctx=context();vm.runInContext(src,ctx);assert.equal(run('orderSound'),true);assert.equal(run('orderAudioUnlocked'),false);assert.equal(run('pendingOrderIds.size'),1);run("observeOrderNotifications([{id:'blocked'},{id:'another'}])");assert.equal(notes,12);
 allowResume=true;await run('enableOrderBell()');assert.equal(notes,18);assert.equal(run('pendingOrderIds.size'),0);
 run("orderSound=false;saveBellState();observeOrderNotifications([{id:'muted'},{id:'blocked'}])");await settle();assert.equal(notes,18);assert.equal(run('pendingOrderIds.size'),1);
 await run('enableOrderBell()');assert.equal(notes,24);assert.equal(run('pendingOrderIds.size'),0);
 // A stale list cannot forget IDs and re-ring for already observed orders.
 run("observeOrderNotifications([{id:'old'}]);observeOrderNotifications([{id:'muted'},{id:'old'}])");await settle();assert.equal(notes,24);
 console.log('PASS order sound: baseline, pending locked audio, audible-test scheduling, deduplication, paused audio, refresh recovery, mute, stale snapshots');
})().catch(e=>{console.error(e);process.exitCode=1});
