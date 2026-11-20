'use strict';
const assert=require('node:assert/strict');
const O=require('../app/src/main/assets/ocr.js');
const H='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext';
function word(x,y,w,text,confidence=95){return [5,1,1,1,Math.round(y),1,x,y,w,12,confidence,text];}
function make(markSecond=false,confidence=95,withHeader=true){
 const rows=[[1,1,0,0,0,0,0,0,1000,1000,-1,''],word(120,300,18,'Nr.'),word(520,300,18,'Nr.')];
 if(withHeader)rows.push(word(415,300,30,'Start'));
 rows.push(word(86,350,15,'TW'),word(120,350,18,'30'),word(170,350,80,'BEISPIEL,'),word(260,350,40,'Alex'),word(425,350,10,'X',confidence));
 rows.push(word(86,390,15,'TW'),word(120,390,18,'35'),word(170,390,80,'MUSTER,'),word(260,390,40,'Kim'));
 if(markSecond)rows.push(word(425,390,10,'X'));
 rows.push(word(100,700,25,'HC'));
 return [H,...rows.map(r=>r.join('\t'))].join('\n');
}
let r=O.parseRosterFromTsv(make());assert.equal(r.home.length,2);assert.equal(r.home[0].isGoalie,true);assert.equal(r.home[0].starter,true);assert.equal(r.home[1].starter,false);
r=O.parseRosterFromTsv(make(true));assert(r.home.every(p=>!p.starter),'two marks must not pick a starter');
r=O.parseRosterFromTsv(make(false,45));assert(r.home.every(p=>!p.starter),'uncertain mark must not pick a starter');
r=O.parseRosterFromTsv(make(false,95,false));assert(r.home.every(p=>!p.starter),'unlabelled X must not pick a starter');
console.log('Goalie parser PASS: explicit starter, multiple marks, low confidence, missing column label. Synthetic OCR tokens only.');
