/* 3.2: player memory and EHV comparison (roster.js), node only, fantasy names, mocked EHV responses. */
'use strict';
const A=require('node:assert/strict');const R=require('../app/src/main/assets/roster.js');
A.equal(R.ageClass('U13_LL_005'),'u13');A.equal(R.ageClass('SEN_BZL_019'),'sen');A.equal(R.ageClass(''),'');A.equal(R.ageClass('Testspiel'),'');
A.equal(R.teamKey('Neusser EV','U13_LL_005'),'neusser ev|u13');A.notEqual(R.teamKey('Neusser EV','U13_LL_005'),R.teamKey('Neusser EV','U15_LL_001'));
A.ok(R.samePerson('Schlößer, Tim','Schlöber, Tim'));A.ok(R.samePerson('Muster, Kai','MUSTER, K.'));A.ok(!R.samePerson('Muster, Kai','Beispiel, Kai'));
// learn + memory: confirmed players only (no open check marks), count up, other person replaces, age classes separate.
let db=R.emptyDb();
db=R.learn(db,'Neusser EV','U13_LL_001',[{number:'7',name:'Muster, Kai',isGoalie:false},{number:'30',name:'Torwart, Tom',isGoalie:true},{number:'9',name:'Unsicher, X',check:['Name prüfen']}],'app',1000);
db=R.learn(db,'Neusser EV','U13_LL_002',[{number:'7',name:'Muster, Kai'},{number:'12',name:'Neu, Nina'}],'app',2000);
let mem=R.memoryFor(db,'Neusser EV','U13_LL_099');
A.deepEqual(mem.map(p=>[p.number,p.name,p.count]).sort(),[['12','Neu, Nina',1],['30','Torwart, Tom',1],['7','Muster, Kai',2]]);
A.equal(R.memoryFor(db,'Neusser EV','U15_LL_001').length,0,'other age class not mixed');
db=R.learn(db,'Neusser EV','U13_LL_003',[{number:'12',name:'Anders, Ole'}],'app',3000);
A.equal(R.memoryFor(db,'Neusser EV','U13_LL_003').find(p=>p.number==='12').name,'Anders, Ole');
A.deepEqual(R.stats(db),{teams:1,players:3});
A.deepEqual(R.normalizeDb({teams:{x:{players:{'1':{n:'A, B'},abc:{n:'x'},'123':{n:'too long'}}}}}).teams.x.players,{'1':{n:'A, B',g:false,c:1,t:0,s:'app'}});
A.deepEqual(R.normalizeDb('kaputt'),R.emptyDb());A.deepEqual(R.normalizeDb({teams:[]}),R.emptyDb());
// suggestions from memory (not exact): spelling, number, goalie only with count >= 2; nothing for unknown players.
const ref=[{number:'7',name:'Schlößer, Tim',isGoalie:false,count:3},{number:'29',name:'Wenz, Luca',count:2},{number:'30',name:'Torwart, Tom',isGoalie:true,count:2},{number:'44',name:'Fern, Ali',count:1}];
const scanned=[{number:'7',name:'Schlöber, Tim'},{number:'23',name:'Wenz, Luca',check:['Nummer prüfen: 23 oder 29?']},{number:'30',name:'Torwart, Tom',isGoalie:false},{number:'5',name:'Neu, Nina'}];
let s=R.suggest(scanned,ref,false,'Gedächtnis');
A.deepEqual(s.map(x=>[x.kind,x.number,x.to]),[['name','7','Schlößer, Tim'],['number','23','29'],['goalie','30',true]]);
A.equal(R.describe(s[0]),'#7: „Schlöber, Tim“ → „Schlößer, Tim“');A.equal(R.describe(s[1]),'Wenz, Luca: #23 → #29');
let applied=R.applySuggestions(scanned,s);
A.deepEqual(applied.map(p=>[p.number,p.name,!!p.isGoalie,p.check||null]),[['7','Schlößer, Tim',false,null],['29','Wenz, Luca',false,null],['30','Torwart, Tom',true,null],['5','Neu, Nina',false,null]]);
A.equal(scanned[0].name,'Schlöber, Tim','input not changed');
// exact EHV lineup of this game: missing players and different persons are suggested too.
s=R.suggest([{number:'7',name:'Muster, Kai'},{number:'8',name:'Falsch, Fritz'}],[{number:'7',name:'Muster, Kai'},{number:'8',name:'Richtig, Rita'},{number:'1',name:'Goalie, Gil',isGoalie:true}],true,'EHV');
A.deepEqual(s.map(x=>[x.kind,x.number,x.to]),[['name','8','Richtig, Rita'],['missing','1','Goalie, Gil']]);
applied=R.applySuggestions([{number:'7',name:'Muster, Kai'}],[{kind:'missing',number:'1',to:'Goalie, Gil',isGoalie:true}]);
A.equal(applied.length,2);A.ok(applied[1].isGoalie&&applied[1].id);
A.deepEqual(R.suggest([],[],true,'x'),[]);
// empty roster + exact lineup -> whole lineup as suggestions ("load from EHV")
A.equal(R.suggest([],[{number:'4',name:'A, B'},{number:'5',name:'C, D'}],true,'EHV').filter(x=>x.kind==='missing').length,2);
// merge (backup import)
const db2=R.learn(R.emptyDb(),'EC Musterstadt','U13_LL_001',[{number:'3',name:'Gast, Gina'}],'app',5000);
A.deepEqual(R.stats(R.mergeDb(db,db2)),{teams:2,players:4});
// hockeydata parsing: upper-case names to the OCR style, goalies, no birthdates kept.
const rep={data:{homeFieldPlayers:[{playerJerseyNr:'7',playerLastname:'MUSTER-MANN',playerFirstname:'KAI',playerBirthdate:{value:'2013-01-01'}}],homeGoalKeepers:[{playerJerseyNr:30,playerLastname:'Torwart',playerFirstname:'Tom'}],awayFieldPlayers:[],awayGoalKeepers:null}};
A.deepEqual(R.reportPlayers(rep,'home'),[{number:'7',name:'Muster-Mann, Kai',isGoalie:false},{number:'30',name:'Torwart, Tom',isGoalie:true}]);
A.ok(!JSON.stringify(R.reportPlayers(rep,'home')).includes('2013'));
A.ok(R.sameTeam('Neusser EV','Neusser EV U13','u13','U13_LL_1'));A.ok(!R.sameTeam('Neusser EV','Neusser EV U13','u15','U13_LL_1'));A.ok(!R.sameTeam('Neusser EV','Krefelder EV','u13','U13_LL_1'));
A.deepEqual(R.parseJson('cb({"a":1});'),{a:1});
// EHV lookup with a mocked network.
const row=(id,n,h,a,s,t)=>({id,divisionId:1,gameName:n,homeTeamLongName:h,awayTeamLongName:a,gameStatus:s,gameUtcTimestamp:t});
const schedule={data:{rows:[row('g1','U13_LL_005','EC Musterstadt','Neusser EV',0,9e12),row('g2','U13_LL_001','Neusser EV','Grefrather EG',4,1e12),row('g3','U13_LL_002','Neusser EV','EC Musterstadt',4,2e12)]}};
const reports={g1:{data:{homeFieldPlayers:[{playerJerseyNr:'3',playerLastname:'GAST',playerFirstname:'GINA'}],awayFieldPlayers:[{playerJerseyNr:'7',playerLastname:'MUSTER',playerFirstname:'KAI'}]}},
  g2:{data:{homeFieldPlayers:[{playerJerseyNr:'7',playerLastname:'MUSTER',playerFirstname:'KAI'}]}},g3:{data:{homeFieldPlayers:[{playerJerseyNr:'7',playerLastname:'MUSTER',playerFirstname:'KAI'},{playerJerseyNr:'8',playerLastname:'ACHT',playerFirstname:'ANNA'}]}}};
const calls=[];
const fetchText=async url=>{calls.push(url);if(url.includes('ehv-nrw.de/leagues'))throw new Error('CORS');if(url.includes('/Schedule?'))return JSON.stringify(url.includes('divisionId=21419')?schedule:{data:{rows:[]}});
  const id=decodeURIComponent(/gameId=([^&]+)/.exec(url)[1]);return JSON.stringify(reports[id]||{data:{}});};
(async()=>{
  // Sheet: Neusser EV at home, but EHV lists the game the other way round -> swapped back.
  let r=await R.ehvLookup({fetchText,homeName:'Neusser EV',awayName:'EC Musterstadt',gameNumber:'U13_LL_005'});
  A.ok(r.exact);A.equal(r.game.id,'g1');A.deepEqual(r.home.map(p=>p.name),['Muster, Kai']);A.deepEqual(r.away.map(p=>p.name),['Gast, Gina']);
  A.equal(calls.filter(u=>u.includes('/Schedule?')).length,R.EHV.divisions.length,'all divisions asked once');A.ok(calls.every(u=>/^https:\/\/(api\.hockeydata\.net|ehv-nrw\.de)\//.test(u)));
  A.ok(r.rows.length===3);
  // Unknown game number -> last finished games of each team (cache used, no new schedule requests).
  calls.length=0;r=await R.ehvLookup({fetchText,cache:{at:Date.now(),rows:r.rows},homeName:'Neusser EV',awayName:'Niemand EV',gameNumber:'U13_LL_777'});
  A.ok(!r.exact);A.equal(calls.filter(u=>u.includes('/Schedule?')).length,0);A.equal(r.games,2);
  A.deepEqual(r.home.map(p=>[p.number,p.name,p.count]).sort(),[['7','Muster, Kai',2],['8','Acht, Anna',1]]);A.deepEqual(r.away,[]);
  // Network down -> clear error, nothing invented.
  await A.rejects(R.ehvLookup({fetchText:async()=>{throw new Error('offline');},homeName:'Neusser EV',gameNumber:'U13_LL_005'}),/EHV nicht erreichbar/);
  console.log('V32 LOGIC PASS: age classes, player memory (confirmed only, counts, replace, classes separate, limits, broken data), suggestions name/number/goalie/missing (memory vs. exact EHV lineup), apply without changing input, merge, hockeydata parsing without birthdates, team matching, EHV lookup exact/swapped/recent/cached/offline.');
})().catch(e=>{console.error(e);process.exit(1);});
