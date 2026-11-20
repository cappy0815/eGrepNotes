/* 2.1 logic: penalty list sorted by the EHV sample, complete, unique, Sonstige last; signs mapping. Node only. */
const A=require('node:assert/strict');
const L=require('../app/src/main/assets/logic.js');
A.ok(/^[23]\.\d+$/.test(L.VERSION));A.equal(L.emptyState().version,9);
const P=L.PENALTIES;
A.deepEqual(P.slice(0,9),['Beinstellen','Haken','Unkorrekter Körperangriff','Halten','Stockschlag','Übertriebene Härte','Bandencheck','Behinderung','Stockcheck / Cross-Check']);
A.equal(P[P.length-1],'Sonstige');A.equal(new Set(P).size,P.length,'no duplicates');
const v20=['Beinstellen','Haken','Halten','Behinderung','Stockschlag','Hoher Stock','Übertriebene Härte','Bandencheck','Stockcheck / Cross-Check','Ellbogencheck','Kniecheck','Check von hinten','Check gegen Kopf / Nacken','Unkorrekter Körperangriff','Halten des Stocks','Torhüterbehinderung','Spielverzögerung','Zu viele Spieler auf dem Eis','Unsportliches Verhalten','Disziplinarstrafe','Beschimpfung von Spieloffiziellen','Faustkampf','Stockstich','Stockendenstoß','Stockwurf / Werfen von Ausrüstung','Slew-Footing','Check mit den Beinen / Clipping','Treten','Kopfstoß','Schwalbe / Vortäuschen','Unzulässige Ausrüstung','Sonstige'];
A.deepEqual([...P].sort(),[...v20].sort(),'same penalties as 2.0, only reordered');
// Signs: every key is a known penalty, values are embedded JPEG data URIs.
global.window={};require('../app/src/main/assets/signs.js');const S=global.window.EGREP_SIGNS;
A.equal(Object.keys(S).length,21);for(const [k,v] of Object.entries(S)){A.ok(P.includes(k),k);A.ok(v.startsWith('data:image/jpeg;base64,'),k);}
A.equal(S['Faustkampf'],S['Übertriebene Härte'],'same signal');A.equal(S['Spieldauer-Disziplinarstrafe'],undefined);
console.log('V21 LOGIC PASS: frequency order, complete/unique, Sonstige last, 21 signal entries all mapped to known penalties.');
