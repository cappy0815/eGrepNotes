'use strict';
const assert=require('node:assert/strict');
const L=require('../app/src/main/assets/logic.js');
let count=0;
function test(name,fn){fn();count++;console.log('PASS '+name);}
function e(id,time,period=1,extra={}){return Object.assign({id,order:Number(id)||1,time,period,team:'home',type:'goal',player:'56',assist1:'',assist2:''},extra);}
test('clock conversion and period boundaries',()=>{
 for(const [clock,period,out] of [['1012',1,'9:48 (1)'],['1000',2,'30:00 (2)'],['905',3,'50:55 (3)'],['0',1,'20:00 (1)'],['2000',2,'20:00 (2)'],['0005',1,'19:55 (1)']])assert.equal(L.formatGameTime({time:L.normalizeTime(clock),period}),out);
 for(const bad of ['', '2060','2059','2001','9999','-1','12345','1:9','a','19:60'])assert.equal(L.normalizeTime(bad),'');
 for(const [n,out] of [['00','0'],['05','5'],['99','99'],['4 (60)',''],['100',''],['#12','12']])assert.equal(L.normalizeNumber(n),out);
});
test('stable order, reverse time and equal boundary seconds',()=>{
 const es=[e('4','20:00',2),e('2','10:00'),e('1','12:00'),e('3','0:00'),e('5','10:00')];
 assert.deepEqual(L.sortedEventsByGameTime(es).map(e=>e.id),['1','2','5','3','4']);
 assert.equal(L.chronologyIssue(e('6','12:00'),[e('1','10:00')]).relation,'before');
 assert.equal(L.chronologyIssue(e('6','10:00'),[e('1','10:00')]),null);
 const original=[e('1','12:00'),e('2','10:00'),e('3','9:00')];
 assert.equal(L.chronologyIssue(e('2','13:00'),original,'2').relation,'before');
 assert.equal(L.chronologyIssue(e('2','8:00'),original,'2').relation,'after');
 assert.equal(L.chronologyIssue(e('2','11:00'),original,'2'),null);
});
test('unknown numbers only checked against that teams existing roster',()=>{
 const s=L.emptyState(),event=e('1','10:00',1,{assist1:'12'});
 assert.equal(L.unknownPlayers(s,event).length,0);
 L.appendPlayer(s.away,'1','Away goalie');assert.equal(L.unknownPlayers(s,event).length,0);
 L.appendPlayer(s.home,'56','Home scorer');assert.deepEqual(L.unknownPlayers(s,event),[['Assist 1','12']]);
 assert.equal(L.unknownPlayers(s,e('2','10:00',1,{type:'penalty',bench:true,player:'',penalty:'Bankstrafe'})).length,0);
 assert.equal(L.hasDuplicateNumber(s.home,'056'),false);assert.equal(L.hasDuplicateNumber(s.home,'56'),true);
});
test('participants, score, proper goal and goalie validation',()=>{
 const s=L.emptyState();assert.equal(L.validateEvent(e('1','10:00')), '');
 assert(L.validateEvent(e('1','10:00',1,{assist1:'56'})));
 assert(L.validateEvent(e('1','10:00',1,{assist2:'12'})));
 assert(L.validateEvent(e('1','20:01')));
 assert(L.validateEvent(e('1','10:00',null)));
 assert(L.validateEvent(e('1','10:00',1,{type:'goalie',goalieOut:'30',goalieIn:'30'})));
 const gc=e('2','10:00',1,{type:'goalie',goalieOut:'30',goalieIn:'35'});assert.equal(L.validateEvent(gc),'');
 s.events=[e('1','10:00'),gc,e('3','9:00',1,{team:'away'}),e('4','8:00',1,{type:'penalty',penalty:'Haken'})];
 assert.deepEqual(L.score(s),{home:1,away:1});assert.equal(L.eventNames(s,gc).length,2);
});
test('goalie suggestion is time-aware, reversible and never guesses starter',()=>{
 const s=L.emptyState();L.appendPlayer(s.home,'30','A').isGoalie=true;L.appendPlayer(s.home,'35','B').isGoalie=true;
 assert.equal(L.goalieSuggestions(s,'home',e('1','10:00')).out,'');
 s.home.startGoalie='30';assert.equal(L.goalieSuggestions(s,'home',e('1','10:00')).incoming,'35');
 const change=e('1','10:00',1,{type:'goalie',goalieOut:'30',goalieIn:'35'});s.events.push(change);
 assert.equal(L.goalieAt(s,'home',e('2','12:00')),'30');assert.equal(L.goalieAt(s,'home',e('2','9:00')),'35');
 assert.equal(L.goalieAt(s,'home',change),'30');assert.equal(L.goalieSuggestions(s,'home',e('2','9:00')).incoming,'30');
 s.events=[];assert.equal(L.goalieAt(s,'home',e('2','9:00')),'30');
 L.appendPlayer(s.home,'40','C').isGoalie=true;assert.equal(L.goalieSuggestions(s,'home',e('2','9:00')).incoming,'');
 s.home.startGoalie='';s.home.players[0].starter=true;s.home.players[1].starter=true;assert.equal(L.getStartGoalie(s.home),'');
});
test('version 1.0 migration and safe name lookup',()=>{
 const s=L.emptyState();const p=L.appendPlayer(s.home,'56','Example');s.events=[e('1','10:00',1,{player:p.id})];
 const x=L.migrateState(s);assert.equal(x.events[0].player,'56');assert.equal(L.playerLabel(x,'home','56'),'#56 Example');
 assert.equal(L.playerLabel(x,'away','56'),'#56');assert.equal(L.migrateState(null).events.length,0);
 assert.deepEqual(L.migrateState(x),x);
});
test('persistent current period: fresh, migrated, invalid, and preserved',()=>{
 const s=L.emptyState();assert.equal(s.currentPeriod,null);
 for(const value of [1,2,3]){s.currentPeriod=value;assert.equal(L.migrateState(s).currentPeriod,value);}
 for(const value of [undefined,null,0,4,'',true,'x']){s.currentPeriod=value;assert.equal(L.migrateState(s).currentPeriod,null);}
 delete s.currentPeriod;s.events=[e('1','9:00',3)];assert.equal(L.migrateState(s).currentPeriod,null);
 s.currentPeriod=2;assert.equal(L.migrateState(JSON.parse(JSON.stringify(s))).currentPeriod,2);
});
test('clock jump uses last chronological event within the same period',()=>{
 const es=[e('a','0:50',1),e('b','10:00',1),e('c','1:00',2)];
 assert.equal(L.clockJumpIssue(e('n','18:30',1),es).event.id,'a');
 assert.equal(L.clockJumpIssue(e('n','0:50',1),es),null);
 assert.equal(L.clockJumpIssue(e('n','0:49',1),es),null);
 assert.equal(L.clockJumpIssue(e('n','18:30',3),es),null);
 assert.equal(L.clockJumpIssue(e('n','18:30',null),es),null);
 assert.equal(L.clockJumpIssue(e('n','20:61',1),es),null);
 assert.equal(L.clockJumpIssue(e('n','20:00',2),[e('a','0:00',1)]),null);
});
console.log(count+' logic groups passed');
