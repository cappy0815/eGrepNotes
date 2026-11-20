/* 1.5 logic: timeout, entry order, quick penalties, OCR name plausibility. Node only. */
const assert=require('assert');
const L=require('../app/src/main/assets/logic.js');
const O=require('../app/src/main/assets/ocr.js');

assert.ok(/^[123]\.\d+$/.test(L.VERSION));
assert.ok(L.emptyState().version>=7);
// 2.1: list sorted by frequency; the 1.5 quick penalties are still within the first twelve.
for(const p of ['Beinstellen','Haken','Halten','Behinderung','Stockschlag','Hoher Stock','Übertriebene Härte','Bandencheck'])assert.ok(L.PENALTIES.indexOf(p)<12,p);

// Timeout: valid without player, one per team.
const s=L.emptyState();
const to={id:'t1',order:5,team:'home',type:'timeout',period:2,time:'4:00',clock:'400',player:''};
assert.strictEqual(L.validateEvent(to),'');
assert.strictEqual(L.TYPE_LABELS.timeout,'Timeout');
assert.deepStrictEqual(L.participants(to),[]);
assert.strictEqual(L.eventShort(to),'');
s.events.push(to);
assert.strictEqual(L.timeoutIssue(s,{id:null,team:'home'}).id,'t1');
assert.strictEqual(L.timeoutIssue(s,{id:null,team:'away'}),null);
assert.strictEqual(L.timeoutIssue(s,{id:'t1',team:'home'}),null,'editing the same timeout is no duplicate');
assert.deepStrictEqual(L.score(s),{home:0,away:0});

// Migration keeps timeouts and strips stray participant fields.
const migrated=L.migrateState({home:{name:'A',players:[]},away:{name:'B',players:[]},events:[Object.assign({},to,{player:'12',penalty:'x'})]});
assert.strictEqual(migrated.events.length,1);assert.strictEqual(migrated.events[0].player,'');assert.strictEqual(migrated.events[0].penalty,'');
assert.strictEqual(migrated.version,L.DATA_VERSION);

// Entry order: last entered first, even for a retro entry with an earlier game time.
const events=[{id:'a',order:1,period:1,time:'10:00'},{id:'b',order:2,period:2,time:'15:00'},{id:'c',order:3,period:1,time:'18:00'}];
assert.deepStrictEqual(L.sortedEventsByEntryDesc(events).map(e=>e.id),['c','b','a']);
assert.deepStrictEqual(L.sortedEventsByGameTime(events).map(e=>e.id),['c','a','b'],'report order unchanged');

// Name plausibility: real-looking names pass, OCR garbage is flagged. Umlauts are not judged.
['Max Mustermann','Lukas Hirschfeld','Jan Schmidt','Anna-Lena Schwarz','Müller Jonas','Muller Jonas','Tim Krzywinski','Jan O\'Neil','Joh. Meier','Sebastian Wróbel']
  .forEach(n=>assert.deepStrictEqual(O.nameIssues(n),[],n));
const flagged={'M4x Muster':'Ziffern im Namen','Xqzt Brm':'Wort ohne Vokal','Leon':'Nur ein Wort','A Bcde':'Einzelner Buchstabe','Kim Mrkvcka':'Viele Konsonanten','Nnnn Abc':'Gleiche Zeichen in Folge','Tom @Meier':'Sonderzeichen','':'Kein Name erkannt'};
Object.entries(flagged).forEach(([n,issue])=>assert.ok(O.nameIssues(n).includes(issue),n+' -> '+issue));
console.log('V15 LOGIC PASS: timeout rules/migration, entry order, 8 quick penalties, name plausibility.');
