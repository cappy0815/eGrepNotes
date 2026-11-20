/* 2.4 logic: hall clock counting up per period -> remaining clock, back conversion, three time modes, migration. Node only. */
const A=require('node:assert/strict');
const L=require('../app/src/main/assets/logic.js');
A.ok(/^[23]\.\d+$/.test(L.VERSION));A.deepEqual(L.TIME_MODES,['down','up','game']);A.equal(L.emptyState().meta.timeMode,'down');
const u=r=>{const x=L.upToClock(r);return x&&[x.up,x.time,x.clock];};
A.deepEqual(u('0'),['0:00','20:00','2000']);A.deepEqual(u('512'),['5:12','14:48','1448']);A.deepEqual(u('1930'),['19:30','0:30','30']);
A.deepEqual(u('2000'),['20:00','0:00','0']);A.equal(L.upToClock('2001'),null);A.equal(L.upToClock('1260'),null);A.equal(L.upToClock(''),null);
// Round trip for every second of a period; stored clock is a valid normal clock entry; game time = elapsed in period.
for(let s=0;s<=1200;s++){const raw=(Math.floor(s/60)?String(Math.floor(s/60)):'')+String(s%60).padStart(Math.floor(s/60)?2:1,'0'),x=L.upToClock(raw);
  A.ok(x,raw);A.equal(L.normalizeTime(x.clock),x.time,raw);const ev={period:2,time:x.time,clock:x.clock};
  A.equal(L.upLabel(ev),x.up,raw);A.equal(L.normalizeTime(L.upDigits(ev)),x.up,raw);A.equal(L.formatGameTime(ev),(20+Math.floor(s/60))+':'+String(s%60).padStart(2,'0')+' (2)',raw);}
// Rising clock: a smaller value is earlier -> the existing order check reports it (question "Neues Drittel oder Nachtrag?").
const st=L.emptyState();const e1={id:'a',type:'goal',team:'home',period:1,time:L.upToClock('1030').time,order:1};
A.ok(L.clockJumpIssue({id:'b',period:1,time:L.upToClock('300').time},[e1]),'smaller rising time -> issue');
A.equal(L.clockJumpIssue({id:'c',period:1,time:L.upToClock('1100').time},[e1]),null,'larger rising time -> no issue');
const m=x=>L.migrateState({meta:x,home:{name:'A',players:[]},away:{name:'B',players:[]},events:[]}).meta.timeMode;
A.equal(m({clockMode:'up'}),'game');A.equal(m({clockMode:'down'}),'down');A.equal(m({timeMode:'up'}),'up');A.equal(m({timeMode:'game'}),'game');A.equal(m({timeMode:'?'}),'down');
console.log('V24 LOGIC PASS: hall clock up 0:00-20:00 round trip each second, invalid >20:00, rising-clock order check, modes, 2.2/2.3 migration.');
