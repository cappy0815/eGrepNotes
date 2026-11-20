'use strict';
const assert = require('assert');
const { parseRosterFromTsv, normalizeTime, formatGameTime, appendPlayer, hasDuplicateNumber, eventElapsedSeconds, sortedEventsByGameTime, chronologyIssue } = require('../app/src/main/assets/app.js');

const header = 'level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext';
const words = [
  [5,1,1,1,1,1,70,90,35,12,95,'Spiel'], [5,1,1,1,1,2,240,90,45,12,95,'Bewerb'],
  [5,1,1,1,1,3,380,90,38,12,84,'|Helm'], [5,1,1,1,1,4,500,90,30,12,95,'Gast'],
  [5,1,1,1,2,1,70,112,90,14,95,'U15_LL_042'], [5,1,1,1,2,2,380,112,55,14,95,'Neusser'],
  [5,1,1,1,2,3,440,112,18,14,95,'EV'], [5,1,1,1,2,4,500,112,60,14,95,'Kölner'],
  [5,1,1,1,2,5,565,112,32,14,95,'Haie'],
  [5,1,1,1,1,1,120,300,18,10,95,'Nr.'], [5,1,1,1,1,2,520,300,18,10,95,'Nr.'],
  [5,1,2,1,1,1,112,340,12,10,95,'4'], [5,1,2,1,1,2,130,338,28,14,95,'(60)'],
  [5,1,2,1,1,3,170,340,75,11,95,'MUSTER,'], [5,1,2,1,1,4,250,340,35,11,95,'Alex'],
  [5,1,2,1,1,5,492,340,45,11,95,'2|(71)'], [5,1,2,1,1,6,550,340,45,11,95,'BEISPIEL,'],
  [5,1,2,1,1,7,602,340,65,11,95,'Kim'], [5,1,3,1,1,1,100,650,25,11,95,'[HC']
];
const tsv = [header, ...words.map(row => row.join('\t'))].join('\n');
const result = parseRosterFromTsv(tsv);
assert.strictEqual(result.home[0].number, '4', 'the jersey number must win over the number in brackets');
assert.strictEqual(result.home[0].name, 'Muster, Alex');
assert.strictEqual(result.away[0].number, '2');
assert.deepStrictEqual(result.teamNames, ['Neusser EV', 'Kölner Haie']);
assert.strictEqual(result.gameNumber, 'U15_LL_042');

const fallbackWords = [
  [5,1,1,1,1,1,70,80,90,14,95,'U17_OL_099'],
  [5,1,2,1,1,1,500,210,75,16,95,'Duisburger'], [5,1,2,1,1,2,582,210,45,16,95,'Füchse'],
  [5,1,3,1,1,1,500,245,20,14,95,'18'], [5,1,3,1,1,2,530,245,55,14,95,'Spieler'],
  [5,1,4,1,1,1,120,300,18,10,95,'Nr.'], [5,1,4,1,1,2,520,300,18,10,95,'Nr.']
];
const fallback = parseRosterFromTsv([header, ...fallbackWords.map(row => row.join('\t'))].join('\n'));
assert.strictEqual(fallback.teamNames[1], 'Duisburger Füchse');
assert.strictEqual(fallback.gameNumber, 'U17_OL_099');
assert.strictEqual(normalizeTime('1012'), '10:12');
assert.strictEqual(formatGameTime({time:'10:12',period:1}), '9:48 (1)');
assert.strictEqual(formatGameTime({time:'10:00',period:2}), '30:00 (2)');
const team = {players:[]};
appendPlayer(team, '45', 'Test Spieler');
assert.strictEqual(team.players.length, 1);
assert.strictEqual(team.players[0].number, '45');
assert.strictEqual(hasDuplicateNumber(team, '45'), true);
assert.strictEqual(hasDuplicateNumber(team, '12'), false);

const first = {id:'first', period:1, time:'10:00', order:1};
const missed = {id:'missed', period:1, time:'12:00', order:2};
const secondPeriod = {id:'second', period:2, time:'20:00', order:3};
assert.strictEqual(eventElapsedSeconds(first), 600);
assert.strictEqual(eventElapsedSeconds(secondPeriod), 1200);
assert.strictEqual(chronologyIssue(missed, [first]).event.id, 'first');
assert.deepStrictEqual(sortedEventsByGameTime([first, missed, secondPeriod]).map(event => event.id), ['missed', 'first', 'second']);

const sameTimeLater = {id:'same-later', period:1, time:'10:00', order:4};
assert.deepStrictEqual(sortedEventsByGameTime([sameTimeLater, first]).map(event => event.id), ['first', 'same-later']);
console.log('Parser tests passed');
