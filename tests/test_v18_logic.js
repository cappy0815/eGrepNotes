/* 1.8: table-line removal, name cleanup, Pos./Nr. separation. Node only, synthetic data. */
const assert=require('assert');
const O=require('../app/src/main/assets/ocr.js');
const L=require('../app/src/main/assets/logic.js');
assert.ok(/^[123]\.\d+$/.test(L.VERSION));
// Pixel test: grey dashed vertical line (gaps 4 px, wobbles 1 px), long horizontal line, short "digit" strokes.
// Same scale as the real recognition image (prepareImage scales to 1800 px width).
const W=1800,H=1800,d=new Uint8ClampedArray(W*H*4).fill(255),set=(x,y,v)=>{const i=(y*W+x)*4;d[i]=d[i+1]=d[i+2]=v;};
for(let y=0;y<H;y++)if(y%14<10)for(let t=0;t<2;t++)set(100+t+(y>900?1:0),y,140);   // dashed + tilted, grey
for(let x=0;x<W;x++)for(let t=0;t<2;t++)set(x,1300+t,60);                              // long horizontal
for(let y=150;y<178;y++)for(let t=0;t<3;t++)set(140+t,y,30);                          // "1" stroke, 28 px tall
for(let x=160;x<180;x++)for(let t=0;t<3;t++)set(x,160+t,30);                          // short bar 20 px wide
O.removeTableLines({data:d},W,H);
const dark=(x,y)=>d[(y*W+x)*4]<190;
let lineLeft=0;for(let y=0;y<H;y++)for(let x=98;x<105;x++)if(dark(x,y))lineLeft++;
assert.strictEqual(lineLeft,0,'dashed grey vertical line removed');
let hLeft=0;for(let x=0;x<W;x++)if(dark(x,1300)||dark(x,1301))hLeft++;assert.ok(hLeft<6,'horizontal line removed: '+hLeft);
assert.ok(dark(141,160)&&dark(141,175),'digit stroke kept');assert.ok(dark(170,161),'short bar kept');
// Names: bracket numbers and notes after the first name are not part of the name.
assert.strictEqual(O.cleanName(['(31)','BECKER,','Lena']),'Becker, Lena');
assert.strictEqual(O.cleanName(['OHM,','Mika','TK']),'Ohm, Mika');
assert.strictEqual(O.cleanName(['ALBERS,','Lukas','GSCMOE']),'Albers, Lukas');
assert.strictEqual(O.cleanName(['FELD,','Paul','(C)']),'Feld, Paul');
assert.strictEqual(O.cleanName(['SCHUSTER,','Konrad']),'Schuster, Konrad');
// Pos. column: a "G" misread as "6" must not become the jersey number; G with low confidence in Pos. counts as goalie.
const H0='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext';
const w=(x,y,wd,t,c=95)=>[5,1,1,1,Math.round(y),1,x,y,wd,14,c,t].join('\t');
const tsv=[H0,'1\t1\t0\t0\t0\t0\t0\t0\t1000\t1000\t-1\t',w(60,300,30,'Pos.'),w(110,300,25,'Nr.'),w(160,300,40,'Name'),w(330,300,50,'Lizenz'),w(560,300,30,'Pos.'),w(610,300,25,'Nr.'),w(660,300,40,'Name'),w(830,300,50,'Lizenz'),
  w(68,340,10,'6',90),w(118,340,10,'2'),w(150,340,90,'SOMMER,'),w(245,340,60,'Tim'),w(335,340,50,'127896'),
  w(68,380,10,'G',42),w(112,380,20,'30'),w(150,380,60,'SANDER,'),w(215,380,50,'Sven'),
  w(62,420,20,'LD'),w(118,420,10,'9'),w(150,420,70,'ENGEL,'),w(225,420,50,'Ola'),
  w(100,700,20,'HC')].join('\n');
const r=O.parseRosterFromTsv(tsv);
assert.deepStrictEqual(r.home.map(p=>p.number),['2','30','9'],JSON.stringify(r.home));
assert.strictEqual(r.home[0].name,'Sommer, Tim');assert.strictEqual(r.home[1].isGoalie,true);assert.strictEqual(r.home[2].isGoalie,false);
console.log('V18 LOGIC PASS: dashed/tilted/grey lines removed, characters kept, name notes stripped, Pos./Nr. separated, low-confidence G in Pos. column.');
