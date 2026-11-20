/* 2.5 logic: club logo lookup by team name (exact, suffix, SpG, unknown), logo data sane, corrected signals present. Node only. */
const A=require('node:assert/strict');
const L=require('../app/src/main/assets/logic.js');
global.window={};require('../app/src/main/assets/teamlogos.js');require('../app/src/main/assets/signs.js');
const D=global.window.EGREP_TEAM_LOGOS,S=global.window.EGREP_SIGNS;
A.ok(/^[23]\.\d+$/.test(L.VERSION));
A.equal(D.logos.length,D.colors.length);A.ok(D.logos.length>=90);
for(const l of D.logos)A.ok(l.startsWith('data:image/webp;base64,'));
for(const c of D.colors)A.ok(c===''||/^#[0-9a-f]{6}$/.test(c),c);
for(const i of [...Object.values(D.names),...Object.values(D.bases)])A.ok(Number.isInteger(i)&&i>=0&&i<D.logos.length);
A.equal(L.normTeamName('KEC "Die Haie"'),'kec die haie');A.equal(L.baseTeamName('Krefelder EV U15_A'),'krefelder ev');A.equal(L.baseTeamName('Neusser EV 1b'),'neusser ev');
const hit=n=>L.teamLogoIndex(D,n);
A.ok(hit('EV Duisburg'));A.ok(hit('ev duisburg'),'case-insensitive');A.ok(hit('  Ratinger   Ice Aliens '),'spaces');
A.ok(hit('Neusser EV U17'),'age group suffix');A.ok(hit('Krefelder EV U15 A'));
A.notEqual(hit('SpG Neusser EV / GSC Moers').index,hit('Neusser EV').index,'own SpG logo');
A.equal(hit('Phantasie Pinguine'),null);A.equal(hit(''),null);A.equal(hit(null),null);A.equal(L.teamLogoIndex(null,'EV Duisburg'),null);
A.equal(hit('constructor'),null,'no prototype keys');
// Signals: 21 entries, Cross-Check and Haken replaced (2.5) but still present.
A.equal(Object.keys(S).length,21);A.ok(S['Stockcheck / Cross-Check'].startsWith('data:image/jpeg'));A.ok(S['Haken'].startsWith('data:image/jpeg'));
console.log('V25 LOGIC PASS: logo data sane, lookup exact/case/spaces/suffix/SpG/unknown/prototype, 21 signals incl. corrected Cross-Check/Haken.');
