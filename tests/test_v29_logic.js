/* 2.9: who serves goalie/bench penalties (logic), OCR helpers for long rosters (number strips,
   split "G31", missing number cells, synthetic "Nr." header, goalie order rule, number conflict mark),
   PDF text -> TSV. Node only, synthetic data with fantasy names. */
const assert=require('assert');
const L=require('../app/src/main/assets/logic.js');
const O=require('../app/src/main/assets/ocr.js');
assert.ok(/^[23]\.\d+$/.test(L.VERSION));

// ---- Wer sitzt die Strafe ab? ----
const st=L.emptyState();
st.home.players=[{id:'a',number:'2',name:'Sommer, Tim',isGoalie:true,starter:true},{id:'b',number:'9',name:'Engel, Ola',isGoalie:false}];
st.home.startGoalie='2';
st.events=[{id:'g1',order:1,type:'goalie',team:'away',period:1,time:'20:00',clock:'2000',goalieOut:'',goalieIn:'30'}];
const pen=(o)=>Object.assign({id:'x',type:'penalty',team:'home',period:1,time:'10:00',clock:'1000',player:'',bench:false,penalty:'Bandencheck',penaltyDuration:'2'},o);
assert.strictEqual(L.needsServer(st,pen({player:'2'})),true,'goalie in roster');
assert.strictEqual(L.needsServer(st,pen({player:'9'})),false,'field player');
assert.strictEqual(L.needsServer(st,pen({bench:true})),true,'bench');
assert.strictEqual(L.needsServer(st,pen({team:'away',player:'30'})),true,'in goal by goalie change, no roster');
assert.strictEqual(L.needsServer(st,pen({team:'away',player:'31'})),false);
assert.strictEqual(L.needsServer(st,{type:'goal',team:'home',player:'2'}),false,'only penalties');
assert.strictEqual(L.eventShort(pen({player:'2',servedBy:'9'})),'2, Bandencheck, 2 Min., abgesessen von #9');
assert.strictEqual(L.eventShort(pen({bench:true,servedLater:true})),'Bank, Bandencheck, 2 Min., Absitzender offen');
assert.strictEqual(L.eventShort(pen({player:'9'})),'9, Bandencheck, 2 Min.');
assert.deepStrictEqual(L.participants(pen({bench:true,servedBy:'9'})),[['Sitzt ab','9']]);
assert.deepStrictEqual(L.unknownPlayers(st,pen({bench:true,servedBy:'77'})),[['Sitzt ab','77']],'unknown serving player is reported');
// Migration: kept, normalised, removed from other types; older data stays without the fields.
const m=L.migrateState({home:st.home,away:st.away,events:[pen({id:'p1',player:'2',servedBy:' 09 '}),pen({id:'p2',bench:true,servedLater:true}),
  {id:'t1',type:'goal',team:'home',period:1,time:'09:00',player:'9',servedBy:'9'},pen({id:'p3',player:'2'})]});
const byId=Object.fromEntries(m.events.map(e=>[e.id,e]));
assert.strictEqual(byId.p1.servedBy,'9');assert.strictEqual(byId.p1.servedLater,false);
assert.strictEqual(byId.p2.servedBy,'');assert.strictEqual(byId.p2.servedLater,true);
assert.strictEqual(byId.t1.servedBy,'');assert.strictEqual(byId.p3.servedBy,'');assert.strictEqual(byId.p3.servedLater,false);

// ---- OCR helpers ----
const H0='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext';
const PAGE='1\t1\t0\t0\t0\t0\t0\t0\t1000\t1400\t-1\t';
const w=(x,y,wd,t,c=95)=>[5,1,1,1,Math.round(y),1,x,y,wd,14,c,t].join('\t');
// cleanName: "MUSTER. Kai" -> comma
assert.strictEqual(O.cleanName(['MUSTER.','Kai']),'Muster, Kai');
// stripWords: "G31" split into position + number, 3 digits with leading 1 = table line, others dropped.
const strip={left:100,right:160,top:300,bottom:900,width:1000,height:1400};
const sw=O.stripWords(['1\t1\t0\t0\t0\t0\t0\t0\t140\t1240\t-1\t','5\t1\t1\t1\t1\t1\t20\t40\t60\t28\t80\tG31','5\t1\t1\t1\t2\t1\t20\t100\t40\t28\t50\t168','5\t1\t1\t1\t3\t1\t20\t160\t40\t28\t90\t456','5\t1\t1\t1\t4\t1\t20\t220\t20\t28\t40\tD'].join('\n'),strip,2);
assert.deepStrictEqual(sw.map(x=>x.text),['G','31','68','D'],JSON.stringify(sw));
assert.ok(sw.every(x=>x.strip&&x.conf>=60));assert.ok(Math.abs(sw[1].top-310)<1,'mapped back to page coordinates');
// numberStrips: one strip per "Nr." header, from Pos. to just before Name, down to the staff line of its side.
const head=[w(60,300,30,'Pos.'),w(110,300,25,'Nr.'),w(160,300,40,'Name'),w(560,300,30,'Pos.'),w(610,300,25,'Nr.'),w(660,300,40,'Name')];
const strips=O.numberStrips([H0,PAGE,...head,w(60,800,20,'HC'),w(560,1100,20,'HC')].join('\n'));
assert.strictEqual(strips.length,2);
assert.ok(strips[0].left<60&&strips[0].right<160&&strips[0].right>135,JSON.stringify(strips[0]));
assert.ok(strips[0].bottom===800&&strips[1].bottom===1100,'each side ends at its own staff line');
// missingNumberCells: surname without a number next to it gets a number-only cell.
const tsvNames=[H0,PAGE,...head,w(170,340,80,'SOMMER,'),w(170,380,80,'ENGEL,')].join('\n');
const extra=[{text:'2',left:115,top:338,width:10,height:14}];
const cells=O.missingNumberCells(tsvNames,O.numberStrips(tsvNames),extra);
assert.strictEqual(cells.length,1);assert.ok(Math.abs(cells[0].y-387)<1&&cells[0].left<110,JSON.stringify(cells));
// parse: no "Nr." read at all -> synthesised from Pos./Name; number conflict between passes -> check mark;
// goalie order: a "G" below a row with a clearly read field position is not a goalie.
const rows=[w(60,300,30,'Pos.'),w(160,300,40,'Name'),w(560,300,30,'Pos.'),w(660,300,40,'Name'),
  w(62,340,12,'G'),w(112,340,20,'30'),w(170,340,80,'SOMMER,'),w(255,340,40,'Tim'),
  w(62,380,20,'LD'),w(115,380,12,'9'),w(170,380,80,'ENGEL,'),w(255,380,40,'Ola'),
  w(62,420,12,'G',90),w(112,420,20,'23',75),w(170,420,80,'WENZ,'),w(255,420,40,'Luca'),
  w(562,340,12,'G'),w(612,340,20,'1'),w(670,340,80,'BECKER,'),w(755,340,40,'Lena'),
  w(60,800,20,'HC')].join('\n');
const extraWords=[{level:5,left:112,top:420,width:20,height:14,conf:80,text:'29',strip:true}];
const r=O.parseRosterFromTsv([H0,PAGE,rows].join('\n'),extraWords);
assert.deepStrictEqual(r.home.map(p=>p.number),['30','9','23'],JSON.stringify(r.home));
assert.deepStrictEqual(r.home.map(p=>p.isGoalie),[true,false,false],'G below LD row is a misread C/D');
assert.deepStrictEqual(r.home[2].check,['Nummer prüfen: 23 oder 29?']);
assert.deepStrictEqual(r.away.map(p=>[p.number,p.isGoalie]),[['1',true]]);
// Long roster: 26 players per side are all read (no fixed cut-off).
const many=[H0,'1\t1\t0\t0\t0\t0\t0\t0\t1000\t2600\t-1\t',w(60,200,30,'Pos.'),w(110,200,25,'Nr.'),w(160,200,40,'Name'),w(560,200,30,'Pos.'),w(610,200,25,'Nr.'),w(660,200,40,'Name')];
const SUR=['ALBERS','BRANDT','CORNELS','DAHMEN','EBERT','FALKE','GERDES','HAHNE','IMHOF','JANSEN','KORTE','LANGE','MOHR','NOLTE','OTTEN','PETERS','QUANDT','ROLOFF','SANDER','THEIS','ULRICH','VOGEL','WAGNER','XANDER','YILMAZ','ZANDER'];
SUR.forEach((s,i)=>{const y=240+i*80;many.push(w(115,y,20,String(i+2)),w(170,y,80,s+','),w(255,y,40,'Kim'),w(615,y,20,String(i+40)),w(670,y,80,s+','),w(755,y,40,'Ben'));});
const rm=O.parseRosterFromTsv(many.join('\n'));
assert.strictEqual(rm.home.length,26);assert.strictEqual(rm.away.length,26);
// PDF text items -> TSV: words on one baseline share a line, words split proportionally.
const vp={width:600,height:800,scale:1,convertToViewportPoint:(x,y)=>[x,800-y]};
const tsv=O.pdfTextToTsv([{str:'Nr. Name',transform:[10,0,0,10,50,700],width:40},{str:'Pos.',transform:[10,0,0,10,10,700],width:20},{str:'12',transform:[10,0,0,10,50,680],width:10}],vp);
const lines=tsv.split('\n').slice(2).map(l=>l.split('\t'));
assert.deepStrictEqual(lines.map(c=>c[11]),['Nr.','Name','Pos.','12']);
assert.ok(lines[0][4]===lines[2][4]&&lines[0][4]!==lines[3][4],'same baseline -> same line id');
assert.ok(+lines[1][6]>+lines[0][6],'second word right of the first');
assert.strictEqual(O.isPdf({type:'application/pdf',name:'x'}),true);assert.strictEqual(O.isPdf({type:'',name:'Aufstellung.PDF'}),true);assert.strictEqual(O.isPdf({type:'image/jpeg',name:'a.jpg'}),false);
console.log('V29 LOGIC PASS: served-by for goalie (roster/in goal)/bench, text, unknown check, migration; OCR strips/split G31/missing cells/synthetic Nr./goalie order/number conflict/26 per side; PDF text to TSV; isPdf.');
