/* 2.2 logic: elapsed game time ("Uhr auf") -> period + remaining clock, back conversion, clock mode migration. Node only. */
const A=require('node:assert/strict');
const L=require('../app/src/main/assets/logic.js');
A.ok(/^[23]\.\d+$/.test(L.VERSION));A.equal(L.emptyState().meta.timeMode,'down');A.equal(L.emptyState().version,9);
const c=r=>{const x=L.elapsedToClock(r);return x&&[x.period,x.time,x.clock];};
A.deepEqual(c('0'),[1,'20:00','2000']);A.deepEqual(c('730'),[1,'12:30','1230']);
A.deepEqual(c('2000'),[1,'0:00','0'],'20:00 = end of 1st period');A.deepEqual(c('2001'),[2,'19:59','1959']);
A.deepEqual(c('2713'),[2,'12:47','1247']);A.deepEqual(c('4000'),[2,'0:00','0']);A.deepEqual(c('4001'),[3,'19:59','1959']);
A.deepEqual(c('5805'),[3,'1:55','155']);A.deepEqual(c('5905'),[3,'0:55','55']);A.deepEqual(c('6000'),[3,'0:00','0']);
A.deepEqual(c('27:13'),[2,'12:47','1247']);
for(const bad of ['6001','2760','','abc','99999'])A.equal(L.elapsedToClock(bad),null,bad);
// Converted clock digits are valid normal clock entries; game time round-trips exactly.
for(let s=0;s<=3600;s+=7){const raw=String(Math.floor(s/60))+String(s%60).padStart(2,'0'),x=L.elapsedToClock(raw);
  A.equal(L.normalizeTime(x.clock),x.time,raw);const ev={period:x.period,time:x.time,clock:x.clock};
  A.equal(L.formatGameTime(ev),x.elapsed+' ('+x.period+')',raw);A.equal(L.elapsedDigits(ev),raw,raw);}
// Mode: only 'up' is kept; anything else falls back to the clock.
// 2.4: modes down/up/game; the 2.2 continuous mode is now 'game'.
A.equal(L.normalizeTimeMode('game'),'game');A.equal(L.normalizeTimeMode('up'),'up');A.equal(L.normalizeTimeMode('x'),'down');A.equal(L.normalizeTimeMode(undefined),'down');
const m=s=>L.migrateState({meta:s,home:{name:'A',players:[]},away:{name:'B',players:[]},events:[]}).meta.timeMode;
A.equal(m({clockMode:'up'}),'game','2.2/2.3 Uhr auf -> Spielzeit');A.equal(m({timeMode:'game'}),'game');A.equal(m({}),'down');A.equal(m(undefined),'down');
console.log('V22 LOGIC PASS: elapsed -> period/clock incl. period ends, invalid input, full round trip 0:00-60:00, clock mode default/migration.');
