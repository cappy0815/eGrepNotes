/* 1.6 logic: name marks survive migration/restart, clock label for eGrep. Node only. */
const assert=require('assert');
const L=require('../app/src/main/assets/logic.js');
assert.ok(/^[123]\.\d+$/.test(L.VERSION));assert.ok(L.emptyState().version>=8);
const m=L.migrateState({home:{name:'A',players:[{id:'x',number:'56',name:'M4x',check:['Ziffern im Namen']},{id:'y',number:'18',name:'Luca Muster'}]},away:{name:'B',players:[]},events:[]});
assert.deepStrictEqual(m.home.players[0].check,['Ziffern im Namen']);assert.strictEqual('check' in m.home.players[1],false);
assert.strictEqual(L.clockLabel({clock:'1012',time:'10:12'}),'10:12');
assert.strictEqual(L.clockLabel({clock:'905',time:'9:05'}),'9:05');
assert.strictEqual(L.clockLabel({time:'0:30'}),'0:30');
// Data from 1.5 (format 7) loads unchanged.
const old=L.migrateState({version:7,home:{name:'A',players:[]},away:{name:'B',players:[]},events:[{id:'t',order:1,team:'home',type:'timeout',period:1,time:'5:00',clock:'500'}]});
assert.strictEqual(old.events.length,1);assert.strictEqual(old.version,L.DATA_VERSION);
console.log('V16 LOGIC PASS: name marks persist, clock label, format 7 -> 8 migration.');
