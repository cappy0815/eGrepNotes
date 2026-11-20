/* 2.7 logic: penalty shot (scored = goal), note (general allowed), empty-net goal detection, migration. Node only. */
const A=require('node:assert/strict');
const L=require('../app/src/main/assets/logic.js');
A.ok(/^[23]\.\d+$/.test(L.VERSION));A.equal(L.TYPE_LABELS.penaltyshot,'Penalty');A.equal(L.TYPE_LABELS.note,'Notiz');A.equal(L.emptyState().version,9);
const ev=(id,type,team,period,time,extra={})=>Object.assign({id,order:Number(id.replace(/\D/g,''))||1,type,team,period,time,clock:time.replace(':','')},extra);
// Validation.
A.equal(L.validateEvent(ev('p1','penaltyshot','home',2,'10:00',{player:'8',scored:true})),'');
A.ok(L.validateEvent(ev('p2','penaltyshot','home',2,'10:00',{player:'',scored:true})));
A.ok(L.validateEvent(ev('p3','penaltyshot','home',2,'10:00',{player:'8'})),'result required');
A.equal(L.validateEvent(ev('n1','note','','1','5:00',{text:'Schiri verletzt'})),'');A.equal(L.validateEvent(ev('n2','note','away',1,'5:00',{text:'x'})),'');
A.ok(L.validateEvent(ev('n3','note','',1,'5:00',{text:'   '})));A.ok(L.validateEvent(ev('g0','goal','',1,'5:00',{player:'8'})),'only notes may be general');
A.equal(L.cleanNote(' a\n b\t c '),'a b c');A.equal(L.cleanNote('x'.repeat(400)).length,L.NOTE_MAX);
// Score: scored penalty shot = goal (also per period); missed does not count.
const s=L.emptyState();s.events=[ev('g1','goal','home',1,'15:00',{player:'9'}),ev('p4','penaltyshot','away',2,'12:00',{player:'7',scored:true}),ev('p5','penaltyshot','home',3,'8:00',{player:'4',scored:false}),ev('n4','note','',2,'11:00',{text:'Unterbrechung'})];
A.deepEqual(L.score(s),{home:1,away:1});A.deepEqual(L.periodScores(s),[{home:1,away:0},{home:0,away:1},{home:0,away:0}]);
A.equal(L.eventShort(s.events[1]),'7, Tor');A.equal(L.eventShort(s.events[2]),'4, kein Tor');A.equal(L.eventShort(s.events[3]),'Unterbrechung');
A.deepEqual(L.unknownPlayers(s,s.events[3]),[]);A.deepEqual(L.participants(s.events[1]),[['Schütze','7']]);
A.equal(L.powerPlayHint(s,s.events[1]),null,'no PP hint for penalty shots');
// Empty net: away pulls #30 at 58:00 (clock 2:00, 3rd), home goal at 58:30 -> EN; after #30 is back -> no EN.
const en=L.emptyState();en.away.players=[{id:'a',number:'30',name:'TW',isGoalie:true,starter:true}];en.away.startGoalie='30';
en.events=[ev('w1','goalie','away',3,'2:00',{goalieOut:'30',goalieIn:'EN'}),ev('g2','goal','home',3,'1:30',{player:'9'}),ev('w2','goalie','away',3,'1:20',{goalieOut:'EN',goalieIn:'30'}),ev('g3','goal','home',3,'0:40',{player:'9'}),ev('g4','goal','away',3,'1:50',{player:'5'})];
A.equal(L.emptyNetGoal(en,en.events[1]),true);A.equal(L.emptyNetGoal(en,en.events[3]),false);
A.equal(L.emptyNetGoal(en,en.events[4]),false,'own net empty is not an EN goal');A.equal(L.emptyNetGoal(en,en.events[0]),false);
// Migration keeps new types; general note survives; garbage dropped.
const m=L.migrateState({home:{name:'A',players:[]},away:{name:'B',players:[]},events:[ev('p6','penaltyshot','home',1,'9:00',{player:'08',scored:1}),ev('n5','note','x',1,'9:00',{text:' Hallo\nWelt '}),ev('g5','goal','x',1,'9:00',{player:'1'})]});
A.equal(m.events.length,2);A.equal(m.events[0].player,'8');A.equal(m.events[0].scored,true);A.equal(m.events[1].team,'');A.equal(m.events[1].text,'Hallo Welt');
console.log('V27 LOGIC PASS: penalty shot validation/score/period/text, notes incl. general + cleaning, empty-net goal detection (only other team, until goalie back), migration.');
