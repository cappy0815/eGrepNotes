/* 2.0 logic: durations, empty net, shootout, period scores, power-play hint. Node only. */
const A=require('node:assert/strict');
const L=require('../app/src/main/assets/logic.js');
A.ok(/^[23]\.\d+$/.test(L.VERSION));A.equal(L.emptyState().version,9);A.deepEqual(L.emptyState().shootout,[]);
A.ok(L.PENALTIES.includes('Disziplinarstrafe'));
const ev=(id,type,team,period,time,extra={})=>Object.assign({id,order:Number(id.replace(/\D/g,''))||1,type,team,period,time,clock:time.replace(':','')},extra);

// Empty net: valid in either direction, never both; label, short text, migration.
const g=(o,i)=>ev('g1','goalie','home',3,'2:00',{goalieOut:o,goalieIn:i});
A.equal(L.validateEvent(g('30','EN')),'');A.equal(L.validateEvent(g('EN','30')),'');A.ok(L.validateEvent(g('EN','EN')));A.ok(L.validateEvent(g('30','')));
A.equal(L.eventShort(g('30','EN')),'#30 → leer');A.equal(L.playerLabel(L.emptyState(),'home','EN'),'Leeres Tor');
A.equal(L.migrateState({home:{name:'A',players:[]},away:{name:'B',players:[]},events:[g('30','EN')]}).events[0].goalieIn,'EN');
// Suggestions: after pulling #30 the return suggests #30.
const s=L.emptyState();s.home.players=[{id:'a',number:'30',name:'Torwart A',isGoalie:true,starter:true},{id:'b',number:'35',name:'Torwart B',isGoalie:true}];s.home.startGoalie='30';
s.events=[g('30','EN')];
A.equal(L.goalieAt(s,'home',{period:3,time:'0:00',order:99}),'EN');
const sug=L.goalieSuggestions(s,'home',{id:null,period:3,time:'1:00',order:99});A.equal(sug.out,'EN');A.equal(sug.incoming,'30');
A.deepEqual(L.unknownPlayers(s,g('30','EN')),[]);

// Durations and texts.
for(const [v,l] of [['2+2','2+2 Min.'],['10','10 Min.']]){const p=ev('p1','penalty','home',1,'10:00',{player:'4',penalty:'Haken',penaltyDuration:v});A.equal(L.validateEvent(p),'');A.equal(L.penaltyDurationLabel(p),l);}

// Shootout: only the winner gets ONE goal; tie or empty -> no change.
const so=L.emptyState();so.events=[ev('e1','goal','home',1,'15:00',{player:'9'}),ev('e2','goal','away',2,'10:00',{player:'7'})];
A.deepEqual(L.score(so),{home:1,away:1});A.equal(L.scoreLabel(so),'1 : 1');
so.shootout=[{team:'home',player:'9',scored:true},{team:'away',player:'7',scored:false},{team:'home',player:'',scored:true},{team:'away',player:'8',scored:true}];
A.deepEqual(L.shootoutResult(so),{home:2,away:1,attempts:4,winner:'home'});A.deepEqual(L.score(so),{home:2,away:1});A.equal(L.scoreLabel(so),'2 : 1 n.P.');
so.shootout.push({team:'away',scored:true});A.equal(L.shootoutResult(so).winner,'');A.equal(L.scoreLabel(so),'1 : 1');
const m=L.migrateState(JSON.parse(JSON.stringify(so)));A.equal(m.shootout.length,5);A.equal(m.shootout[2].player,'');
// Period scores.
A.deepEqual(L.periodScores(so),[{home:1,away:0},{home:0,away:1},{home:0,away:0}]);

// Power-play hint (hint only).
const pp=L.emptyState();
pp.events=[ev('p1','penalty','away',1,'15:00',{player:'4',penalty:'Haken',penaltyDuration:'2'}),ev('g2','goal','home',1,'14:00',{player:'9'}),ev('g3','goal','home',1,'13:30',{player:'9'})];
A.equal(L.powerPlayHint(pp,pp.events[1]).kind,'PP');A.equal(L.powerPlayHint(pp,pp.events[2]),null,'minor ends with the first PP goal');
const sh=ev('g4','goal','away',1,'14:30',{player:'7'});pp.events.push(sh);A.equal(L.powerPlayHint(pp,sh).kind,'SH');
const five=L.emptyState();five.events=[ev('p5','penalty','away',1,'15:00',{player:'4',penalty:'Check',penaltyDuration:'5'}),ev('g6','goal','home',1,'14:00'),ev('g7','goal','home',1,'12:00')];
A.equal(L.powerPlayHint(five,five.events[2]).kind,'PP','5 minutes run their full time');
const late=ev('g8','goal','home',1,'9:59');five.events.push(late);A.equal(L.powerPlayHint(five,late),null,'after 5:00 no hint');
const mis=L.emptyState();mis.events=[ev('p9','penalty','away',1,'15:00',{player:'4',penalty:'Disziplinarstrafe',penaltyDuration:'10'}),ev('p10','penalty','away',1,'15:00',{player:'5',penalty:'Spieldauer',penaltyDuration:'game'}),ev('g11','goal','home',1,'14:00')];
A.equal(L.powerPlayHint(mis,mis.events[2]),null,'10 min / game misconduct do not change numbers');
const even=L.emptyState();even.events=[ev('p12','penalty','away',1,'15:00',{penaltyDuration:'2'}),ev('p13','penalty','home',1,'15:00',{penaltyDuration:'2'}),ev('g14','goal','home',1,'14:00')];
A.equal(L.powerPlayHint(even,even.events[2]),null,'equal numbers -> no hint');
console.log('V20 LOGIC PASS: empty net, 2+2/10, shootout +1 and n.P., period scores, PP/SH hint incl. minor ending, 5-min, misconducts, even strength.');
