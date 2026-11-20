/* 1.7: TSV without header keeps the page-size row; commas allowed in names. Node only. */
const assert=require('assert');
const O=require('../app/src/main/assets/ocr.js');
const L=require('../app/src/main/assets/logic.js');
assert.ok(/^[123]\.\d+$/.test(L.VERSION));
const w=(x,y,wd,t,line)=>[5,1,1,1,line,1,x,y,wd,14,95,t].join('\t');
// Tesseract.js style: first line is the PAGE row (level 1), no header line.
const rows=['1\t1\t0\t0\t0\t0\t0\t0\t1000\t1000\t-1\t',w(120,250,20,'Nr.',1),w(520,250,20,'Nr.',1)];
['56 Alex Beispiel','18 Kim Muster','12 Sam Beispiel','7 Robin Muster','9 Luca Beispiel','4 Max Muster'].forEach((txt,i)=>{
  const [n,a,b]=txt.split(' '),y=300+i*60;rows.push(w(122,y,16,n,i+2),w(170,y,50,a,i+2),w(230,y,60,b,i+2));
});
const r=O.parseRosterFromTsv(rows.join('\n'));
assert.deepStrictEqual(r.home.map(p=>p.number),['56','18','12','7','9','4'],'all rows kept with real page height');
// With header line the old format still works.
const H='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext';
assert.strictEqual(O.parseRosterFromTsv([H,...rows].join('\n')).home.length,6);
// Commas are allowed (e.g. "Nachname, Vorname").
assert.deepStrictEqual(O.nameIssues('Beispiel, Alex'),[]);assert.deepStrictEqual(O.nameIssues('Muster,Kim'),[]);
assert.ok(O.nameIssues('Tom @Meier').includes('Sonderzeichen'));
console.log('V17 LOGIC PASS: page row kept for header-less TSV (all 6 rows), header TSV still parsed, commas allowed.');
