'use strict';
const A=require('node:assert/strict');const L=require('../app/src/main/assets/logic.js');
const base={id:'p',type:'penalty',team:'home',player:'56',penalty:'Beinstellen',time:'10:12',period:1};
A.deepEqual(L.PENALTY_DURATIONS.map(x=>x.value),['2','2+2','5','10','game']);
for(const [v,label] of [['2','2 Min.'],['2+2','2+2 Min.'],['5','5 Min.'],['10','10 Min.'],['game','Spieldauer']]){
 const e={...base,penaltyDuration:v};A.equal(L.validateEvent(e),'');A.ok(L.eventShort(e).includes(label));
 A.equal(L.penaltyDurationLabel(e),label);const s=L.emptyState();s.events=[e];s.currentPeriod=2;
 const migrated=L.migrateState(JSON.parse(JSON.stringify(s)));A.equal(migrated.events[0].penaltyDuration,v);
 A.equal(migrated.currentPeriod,2);A.deepEqual(L.score(migrated),{home:0,away:0});A.equal(L.formatGameTime(e),'9:48 (1)');
}
// since 2.x: 2+2 and 10 are valid durations
for(const value of ['two','2+5','Spieldauer'])A.ok(L.validateEvent({...base,penaltyDuration:value}));
for(const value of [null,undefined,'']){
 const s=L.emptyState();s.events=[{...base,penaltyDuration:value}];const m=L.migrateState(s);
 A.equal(m.events[0].penaltyDuration,'');A.ok(L.eventShort(m.events[0]).includes('Dauer nicht erfasst'));
}
A.equal(L.normalizePenaltyDuration(2),'2');A.equal(L.normalizePenaltyDuration(5),'5');
console.log('PASS duration validation, separate game misconduct, output, migration without invented historical durations, score and clock unaffected.');
