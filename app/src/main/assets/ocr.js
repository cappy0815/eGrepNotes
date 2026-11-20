/* OCR parsing and local Tesseract runtime, derived from the working v1.0. 1.5: German LSTM model (tessdata_fast deu). */
(function(root,factory){
  const L = typeof module === 'object' && module.exports ? require('./logic.js') : root.EgrepLogic;
  const api = factory(L);
  if(typeof module === 'object' && module.exports) module.exports=api; else root.EgrepOCR=api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function(L){
'use strict';
const normalizeNumber=L.normalizeNumber, cryptoId=L.uid;
function cleanName(words) {
  // 2.9: "MUSTER. Kai" - a period right after the all-caps surname is a misread comma.
  words = words.map((w, i) => i === 0 && /^[A-ZÄÖÜß\-']{2,}\.$/.test(w) && words.length > 1 ? w.slice(0, -1) + ',' : w);
  // 1.8: eGrep writes "NACHNAME, Vorname"; uppercase words AFTER the first name are notes
  // on the sheet (e.g. "TK", "GSCMOE"), not part of the name.
  const comma = words.findIndex(w => /,/.test(w));
  if (comma >= 0) words = words.filter((w, i) => i <= comma + 1 || !/^[A-ZÄÖÜ]{2,}$/.test(w.replace(/[^A-Za-zÄÖÜäöüß]/g, '')));
  return words.join(' ')
    .replace(/[[(][^\])]{0,6}[\])]/g, ' ')
    .replace(/[|_[\]{}]/g, ' ')
    .replace(/\((?:A|C)\)/gi, '')
    .replace(/\b\d{5,}\b/g, '')
    .replace(/\s+/g, ' ')
    .replace(/^[-.,: ]+|[-.,: ]+$/g, '')
    .trim()
    .toLocaleLowerCase('de-DE')
    .replace(/(^|[\s-])([a-zäöü])/g, (_, before, letter) => before + letter.toLocaleUpperCase('de-DE'));
}

// 1.5: plausibility check after OCR. Only flags entries for a human decision, never changes them.
// Umlauts are deliberately not judged (Micha: not critical).
const NAME_VOWELS=/[aeiouyäöüàáâãåèéêëìíîïòóôõùúûýæøœ]/i;
function nameIssues(name) {
  const value=String(name==null?'':name).trim(), issues=[];
  if(!value)return ['Kein Name erkannt'];
  if(/\d/.test(value))issues.push('Ziffern im Namen');
  if(/[^A-Za-zÀ-ÖØ-öø-ÿĀ-žß0-9\s'.,-]/.test(value))issues.push('Sonderzeichen');  // 1.7: comma allowed
  const words=value.split(/[\s,-]+/).filter(Boolean);
  if(words.length===1)issues.push('Nur ein Wort');
  if(words.length>4||value.length>40)issues.push('Ungewöhnlich lang');
  if(words.some(w=>w.replace(/[.',]/g,'').length===1&&!/^[A-Za-zÄÖÜ]\.$/.test(w)))issues.push('Einzelner Buchstabe');
  if(words.some(w=>w.length>=2&&/[A-Za-zÄÖÜäöüß]/.test(w)&&!NAME_VOWELS.test(w)))issues.push('Wort ohne Vokal');
  // Common German/foreign digraphs count as one sound, so Schmidt/Hirschfeld stay unflagged.
  if(words.some(w=>/[bcdfghjklmnpqrstvwxzß]{5,}/i.test(w.toLowerCase().replace(/sch|ch|ck|ph|th|sz|tz/g,'X'))))issues.push('Viele Konsonanten');
  if(/(.)\1\1/i.test(value))issues.push('Gleiche Zeichen in Folge');
  return issues;
}

function cleanTeamName(words) {
  return words.map(word => {
    const cleaned = word.replace(/^[^A-Za-zÄÖÜäöüß]+|[^A-Za-zÄÖÜäöüß-]+$/g, '');
    if (/^[A-ZÄÖÜ]{2,4}$/.test(cleaned)) return cleaned;
    return cleaned.toLocaleLowerCase('de-DE').replace(/(^|-)([a-zäöü])/g, (_, before, letter) => before + letter.toLocaleUpperCase('de-DE'));
  }).filter(Boolean).join(' ').trim();
}

function cleanGameNumber(value) {
  return String(value).toUpperCase().replace(/[^A-Z0-9_-]+/g, '_').replace(/^_+|_+$/g, '');
}

// 2.9: if "Nr." was read on one side only, place the missing header from that side's Pos.->Nr. distance.
function withNrHeaders(rows, pageWidth, pageHeight) {
  const nr = rows.filter(w => /^(Nr|No)[.,]?$/i.test(w.text));
  const pos = rows.filter(w => /^Pos[.,:]?$/i.test(w.text));
  if (!nr.length) {
    // No "Nr." at all: on the official sheet it sits between "Pos." and "Name" (about 57 % of that distance).
    const names = rows.filter(w => /^Name[.,:]?$/i.test(w.text));
    return pos.map(p => { const n = names.filter(w => w.left > p.left && w.left - p.left < pageWidth * .15 && Math.abs(w.top - p.top) < pageHeight * .02).sort((a,b)=>a.left-b.left)[0];
      return n ? { level:5, text:'Nr.', left: p.left + (n.left - p.left) * .57, top: p.top, width: Math.max(10, p.width * .6), height: p.height, conf: 40, synthetic:true } : null; }).filter(Boolean);
  }
  if (nr.length !== 1 || pos.length < 2) return nr;
  const own = pos.filter(p => p.left < nr[0].left && nr[0].left - p.left < pageWidth * .12).sort((a,b)=>b.left-a.left)[0];
  const other = pos.filter(p => p !== own && Math.abs(p.top - nr[0].top) < pageHeight * .03 && Math.abs(p.left - nr[0].left) > pageWidth * .2)[0];
  if (!own || !other) return nr;
  return nr.concat([{ level:5, text:'Nr.', left: other.left + (nr[0].left - own.left), top: nr[0].top, width: nr[0].width, height: nr[0].height, conf: 50, synthetic:true }]);
}
function parseRosterFromTsv(tsv, extraWords) {
  // 1.7 fix: Tesseract.js TSV has NO header line. Only skip a real header ("level\t..."),
  // otherwise the page row with the image size was dropped and the size had to be guessed.
  const lines = String(tsv).trim().split(/\r?\n/);
  const allRows = (/^level\t/i.test(lines[0] || '') ? lines.slice(1) : lines).map(line => {
    const c = line.split('\t');
    return { level:+c[0], block:+c[2], par:+c[3], line:+c[4], left:+c[6], top:+c[7], width:+c[8], height:+c[9], conf:+c[10], text:(c.slice(11).join('\t') || '').trim() };
  });
  const rows = allRows.filter(w => w.level === 5 && w.text && w.conf > -1).concat(extraWords || []);
  if (!rows.length) return { home: [], away: [], teamNames: [], gameNumber: '' };
  const pageRow = allRows.find(w => w.level === 1 && w.width && w.height);
  const pageWidth = pageRow?.width || Math.max(...rows.map(w => w.left + w.width));
  const pageHeight = pageRow?.height || Math.max(...rows.map(w => w.top + w.height));
  const headerWords = withNrHeaders(rows, pageWidth, pageHeight);
  const playerCountWords = rows.filter(w => /^Spieler$/i.test(w.text));
  const rosterHeader = headerWords.length ? Math.min(...headerWords.map(w => w.top))
    : playerCountWords.length ? Math.max(...playerCountWords.map(w => w.top + w.height))
    : pageHeight * .31;
  const staffWords = rows.filter(w => /^(HC|AC|ML|Punktrichter|Zeitnehmer)$/i.test(w.text.replace(/[^A-Za-z]/g, '')) && w.top > rosterHeader);
  // 2.9: long rosters (20+ players): no fixed cut-off; end at the staff/footer line or the image end.
  const rosterEnd = staffWords.length ? Math.min(...staffWords.map(w => w.top)) : pageHeight;
  // 2.9: staff lines (HC/ML) of one team must not cut off the other, longer list.
  // 2.9: border between home and away table = left edge of the away "Pos." header (fallback 46 %).
  const awayNr = headerWords.filter(w => w.left + w.width / 2 > pageWidth * .45).sort((a,b)=>a.left-b.left)[0];
  const awayPos = awayNr && rows.filter(w => /^Pos[.,:]?$/i.test(w.text) && w.left < awayNr.left && awayNr.left - w.left < pageWidth * .12 && Math.abs(w.top - awayNr.top) < pageHeight * .03).sort((a,b)=>b.left-a.left)[0];
  // Without a "Pos." header: goalie marks (TW/G) just left of the away numbers still belong to the away table.
  const awayMarks = awayNr ? rows.filter(w => w.top > awayNr.top && /^(G|GK|TW)$/i.test(w.text.replace(/[.,|]/g,''))
    && w.left < awayNr.left && w.left > awayNr.left - pageWidth * .10) : [];
  const split = awayPos ? awayPos.left - pageWidth * .004
    : awayNr ? Math.min(awayNr.left - pageWidth * .05, ...awayMarks.map(w => w.left - pageWidth * .004)) : pageWidth * .46;
  const sideEnd = nrX => { const left = nrX < split; const own = staffWords.filter(w => (w.left + w.width / 2 < split) === left || /Punktrichter|Zeitnehmer/i.test(w.text)); return own.length ? Math.min(...own.map(w => w.top)) : pageHeight; };
  const nrXs = headerWords.map(w => w.left + w.width / 2);
  const homeX = nrXs.filter(x => x < pageWidth * .45).sort((a,b)=>a-b)[0] || pageWidth * .14;
  const awayX = nrXs.filter(x => x > pageWidth * .45).sort((a,b)=>a-b)[0] || pageWidth * .54;

  function parseSide(nrX, nameEnd, sideStart) {
    // 1.8: the narrow Pos. column sits directly left of Nr.; "G" is easily read as "6".
    const nrHeader = headerWords.find(w => Math.abs(w.left + w.width / 2 - nrX) < 2);
    const posHeader = rows.filter(w => /^Pos[.,:]?$/i.test(w.text) && w.left < nrX && nrX - w.left < pageWidth * .12
      && Math.abs(w.top - rosterHeader) < pageHeight * .03).sort((a,b)=>b.left-a.left)[0];
    const posX = posHeader ? posHeader.left + posHeader.width / 2 : null;
    const nrLeft = posX == null ? -Infinity : (posX + nrX) / 2;   // border between Pos. and Nr.
    // "(31) BECKER" / "2|(71)": a bracketed number is never the jersey number.
    const noBrackets = text => text.replace(/[[(][^\])]*[\])]?/g, '');
    const rawCandidates = rows.filter(w => {
      const center = w.left + w.width / 2, text = noBrackets(w.text);
      const nearNumberColumn = center > nrX - pageWidth * .035 && center < nrX + pageWidth * .055 && center > nrLeft;
      // "(31) BECKER": a bracketed number belongs to the name column, not the Nr. column.
      const numberLike = /^\D*\d{1,2}(?:\D.*)?$/.test(text) && !/^\D*\d{3,}/.test(text);
      return nearNumberColumn && numberLike && w.top > rosterHeader + 4 && w.top < sideEnd(nrX);
    }).sort((a,b) => (a.top + a.height / 2) - (b.top + b.height / 2));

    const candidateRows = [];
    rawCandidates.forEach(candidate => {
      const centerY = candidate.top + candidate.height / 2;
      const group = candidateRows.find(row => Math.abs(row.y - centerY) < 16);
      if (group) {
        group.items.push(candidate);
        group.y = group.items.reduce((sum, item) => sum + item.top + item.height / 2, 0) / group.items.length;
      } else candidateRows.push({ y:centerY, items:[candidate] });
    });
    // 2.9: a confident number from the first pass wins over the digits-only pass (which misreads e.g. 23 -> 33).
    const candidates = candidateRows.map(row => { const items = row.items.sort((a,b)=>a.left-b.left);
      const pick = items.find(w => !w.strip && w.conf >= 70 && /^\D*\d{1,2}\D*$/.test(noBrackets(w.text))) || items[0];
      // Both passes read a number but disagree: keep the pick, remember the other one for the yellow check mark.
      const digitsOf = w => (noBrackets(w.text).match(/\d{1,2}/) || [''])[0].replace(/^0+(?=\d)/, '');
      const other = items.find(w => w !== pick && w.strip !== pick.strip && /^\D*\d{1,2}\D*$/.test(noBrackets(w.text)) && digitsOf(w) !== digitsOf(pick));
      return other ? Object.assign({}, pick, { alt: digitsOf(other) }) : pick; });

    const players = [];
    candidates.forEach(candidate => {
      const centerY = candidate.top + candidate.height / 2;
      const duplicate = players.find(p => Math.abs(p.y - centerY) < Math.max(11, candidate.height * .8));
      if (duplicate) return;
      const matchedNumber = noBrackets(candidate.text).match(/\d{1,2}/);
      const number = matchedNumber ? normalizeNumber(matchedNumber[0]) : '';
      if (!number) return;
      if (players.some(player => player.number === number)) return;
      // 1.8: match the name by position on the sheet. Tesseract may put surname and first
      // name into different text lines once the table lines are removed.
      const nameWords = rows.filter(w => {
        const wordY = w.top + w.height / 2;
        const sameRow = Math.abs(wordY - centerY) < Math.max(12, candidate.height * .7);
        // 2.9: a number from the digits pass has an estimated width; on a slanted photo the surname may start
        // left of its estimated right edge, so only its left edge is used as the boundary.
        const after = candidate.strip ? candidate.left + 2 : candidate.left + candidate.width * .6;
        return sameRow && !w.strip && w.left > Math.max(after, candidate.strip ? 0 : sideStart) && w.left < nameEnd;
      }).sort((a,b) => a.left - b.left).map(w => w.text).filter(text => /[A-Za-zÄÖÜäöüß]/.test(text) && !/\d{3,}/.test(text) && !/^(Pos|Nr|No|Name|Lizenz|Geburtsdatum|Start)[.,]?$/i.test(text));
      const name = cleanName(nameWords);
      const letterCount = (name.match(/[A-Za-zÄÖÜäöüß]/g) || []).length;
      const sideLeft = nrX < split ? 0 : split;
      const sideRight = nrX < split ? split : pageWidth;
      const rowWords = rows.filter(w => w.left >= sideLeft && w.left < sideRight
        && Math.abs(w.top+w.height/2-centerY) < Math.max(10,candidate.height*.85));
      // 1.8: inside the Pos. column only G/LD/RD/C/LF/RF can appear, so a lower confidence is enough there.
      const inPosColumn = w => posX != null && Math.abs(w.left + w.width / 2 - posX) < pageWidth * .03;
      const isGoalie = rowWords.some(w => w.left < candidate.left && w.left > candidate.left-pageWidth*.10
        && w.conf >= (inPosColumn(w) ? 35 : 65) && /^(G|GK|TW|GOALIE|TORWART|GOALKEEPER)$/i.test(w.text.replace(/[.,|]/g,'')));
      const startHeader = headerWords.length && rows.find(w => w.left>=sideLeft && w.left<sideRight
        && w.top<=rosterHeader+pageHeight*.025 && w.top>=rosterHeader-pageHeight*.025
        && /^(Start|Starter|Starting)[.:]?$/i.test(w.text));
      const starter = Boolean(isGoalie && startHeader && rowWords.some(w => w.conf >= 65
        && Math.abs((w.left+w.width/2)-(startHeader.left+startHeader.width/2)) < pageWidth*.025
        && /^(x|\*|S|\u2713|\u2714)$/i.test(w.text)));
      // Row with a clearly read field position (D/F/LD/RD/C/...): needed for the goalie order rule below.
      const field = !isGoalie && rowWords.some(w => w.left < candidate.left && w.left > candidate.left-pageWidth*.10
        && /^(LD|RD|LF|RF|LW|RW|C|D|F|ST|V)$/i.test(w.text.replace(/[.,|]/g,'')));
      if (name.length >= 2 && letterCount >= 3) players.push(Object.assign({ number, name, y:centerY, isGoalie, starter, field }, candidate.alt ? { alt: candidate.alt } : {}));
    });
    // 2.9: on the official sheet the goalies are listed first; a "G" below a row with a clearly read
    // field position is a misread "C"/"D". Rows without a readable position do not count.
    let fieldSeen = false;
    players.forEach(p => { if (p.field) fieldSeen = true; else if (p.isGoalie && fieldSeen) { p.isGoalie = false; p.starter = false; } });
    const marked = players.filter(p=>p.starter).length;
    return players.map(({number,name,isGoalie,starter,alt}) => Object.assign({id:cryptoId(),number,name,isGoalie,starter:marked===1 && starter}, alt ? { check:['Nummer pr\u00fcfen: '+number+' oder '+alt+'?'] } : {}));
  }

  // 1.8: the name column ends where the "Lizenz" column starts (if that header was read).
  const licence = rows.filter(w => /izen[sz]/i.test(w.text) && Math.abs(w.top - rosterHeader) < pageHeight * .03);
  const nameEndFor = (nrX, fallback) => { const l = licence.filter(w => w.left > nrX).sort((a,b)=>a.left-b.left)[0]; return l ? l.left - 4 : fallback; };
  // Name starts right of the Nr. header (scale-independent instead of a fixed page share).
  const nameStartFor = nrX => { const h = headerWords.find(w => Math.abs(w.left + w.width / 2 - nrX) < 2); return h ? h.left + h.width : nrX + pageWidth * .018; };
  const home = parseSide(homeX, nameEndFor(homeX, pageWidth * .40), nameStartFor(homeX));
  const away = parseSide(awayX, nameEndFor(awayX, pageWidth * .87), nameStartFor(awayX));
  const normalizedLabel = word => word.text.toLocaleLowerCase('de-DE').replace(/[^a-zäöü0-9]/g, '');
  const topWords = rows.filter(word => word.top < rosterHeader);
  const spielLabel = topWords.find(word => normalizedLabel(word) === 'spiel');
  const bewerbLabel = topWords.find(word => /^bewer[bt]$/.test(normalizedLabel(word)));
  const homeLabel = topWords.find(word => /^(heim|helm)$/.test(normalizedLabel(word)));
  const awayLabel = topWords.find(word => normalizedLabel(word) === 'gast');

  function valueBelow(label, rightBoundary) {
    if (!label) return [];
    const maxDrop = Math.max(90, label.height * 5);
    const candidates = topWords.filter(word => {
      const centerX = word.left + word.width / 2;
      return word.top > label.top + label.height * .45 && word.top < label.top + maxDrop
        && centerX >= label.left - 12 && centerX < rightBoundary && /[A-Za-zÄÖÜäöüß0-9]/.test(word.text);
    }).sort((a,b) => a.top - b.top || a.left - b.left);
    if (!candidates.length) return [];
    const first = candidates[0];
    return candidates.filter(word => word.block === first.block && word.par === first.par && word.line === first.line).sort((a,b) => a.left - b.left);
  }

  function rosterTeamName(side) {
    const isAway = side === 'away';
    const playerLabel = rows.find(word => normalizedLabel(word) === 'spieler'
      && (isAway ? word.left > pageWidth * .5 : word.left < pageWidth * .5));
    if (!playerLabel) return '';
    const lines = new Map();
    rows.filter(word => word.top < playerLabel.top && playerLabel.top - word.top < 110
      && (isAway ? word.left > pageWidth * .48 : word.left < pageWidth * .48)
      && /[A-Za-zÄÖÜäöüß]/.test(word.text)).forEach(word => {
      const key = `${word.block}-${word.par}-${word.line}`;
      if (!lines.has(key)) lines.set(key, []);
      lines.get(key).push(word);
    });
    const candidates = [...lines.values()].map(line => ({
      words: line.sort((a,b) => a.left - b.left),
      top: Math.min(...line.map(word => word.top))
    })).filter(line => line.words.some(word => /[A-Za-zÄÖÜäöüß]{2,}/.test(word.text)))
      .sort((a,b) => b.top - a.top);
    return candidates.length ? cleanTeamName(candidates[0].words.map(word => word.text)) : '';
  }

  function gameNumberFromAllText() {
    const text = [...rows].sort((a,b) => a.top - b.top || a.left - b.left).map(word => word.text).join(' ');
    const match = text.match(/(?:^|[^A-Z0-9])([A-Z]\d{1,2})[_\s-]+([A-Z]{1,4})[_\s-]+(\d{2,4})(?:$|[^A-Z0-9])/i);
    return match ? `${match[1]}_${match[2]}_${match[3]}`.toUpperCase() : '';
  }

  const homeRight = awayLabel ? awayLabel.left - 8 : pageWidth * .62;
  const awayRight = pageWidth * .88;
  const gameRight = bewerbLabel ? bewerbLabel.left - 8 : pageWidth * .25;
  const homeName = rosterTeamName('home') || cleanTeamName(valueBelow(homeLabel, homeRight).map(word => word.text));
  const awayName = rosterTeamName('away') || cleanTeamName(valueBelow(awayLabel, awayRight).map(word => word.text));
  const labelledNumber = cleanGameNumber(valueBelow(spielLabel, gameRight).map(word => word.text).join('_'));
  const gameNumber = gameNumberFromAllText() || (/^(?:[A-Z0-9]+[_-]){1,4}[0-9]{2,6}$/.test(labelledNumber) ? labelledNumber : '');
  return { home, away, teamNames: [homeName, awayName], gameNumber };
}

// 1.8: the eGrep sheet is a table. Its grid lines touch the narrow Pos./Nr. columns and are
// read together with the characters ("|2" -> "6"). Long straight dark runs are lines, not text:
// paint them white before recognition. Characters are far shorter than these runs.
// 2.9: geometry of the Pos./Nr. columns, used for a second, digits-only pass over these narrow strips.
// Tesseract's page layout analysis often merges the narrow columns into garbage ("000D0D000O0").
function numberStrips(tsv) {
  const lines = String(tsv).trim().split(/\r?\n/);
  const all = (/^level\t/i.test(lines[0] || '') ? lines.slice(1) : lines).map(line => { const c = line.split('\t');
    return { level:+c[0], left:+c[6], top:+c[7], width:+c[8], height:+c[9], conf:+c[10], text:(c.slice(11).join('\t') || '').trim() }; });
  const rows = all.filter(w => w.level === 5 && w.text && w.conf > -1);
  const page = all.find(w => w.level === 1 && w.width && w.height);
  if (!page || !rows.length) return [];
  const nr = withNrHeaders(rows, page.width, page.height);
  if (!nr.length) return [];
  const top = Math.min(...nr.map(w => w.top));
  const staff = rows.filter(w => /^(HC|AC|ML|Punktrichter|Zeitnehmer)$/i.test(w.text.replace(/[^A-Za-z]/g, '')) && w.top > top);
  return nr.map(h => {
    const left0 = h.left < page.width * .45;
    const own = staff.filter(w => (w.left + w.width / 2 < page.width * .46) === left0 || /Punktrichter|Zeitnehmer/i.test(w.text));
    const end = own.length ? Math.min(...own.map(w => w.top)) : page.height;
    const pos = rows.filter(w => /^Pos[.,:]?$/i.test(w.text) && w.left < h.left && h.left - w.left < page.width * .12 && Math.abs(w.top - h.top) < page.height * .03).sort((a,b)=>b.left-a.left)[0];
    const left = Math.max(0, Math.round((pos ? pos.left : h.left - page.width * .05) - page.width * .006));
    // Right edge: just before the "Name" header (the surnames must not get into the digits pass).
    const name = rows.filter(w => /^Name[.,:]?$/i.test(w.text) && w.left > h.left && w.left - h.left < page.width * .12 && Math.abs(w.top - h.top) < page.height * .03).sort((a,b)=>a.left-b.left)[0];
    const right = Math.min(page.width, Math.round(name ? name.left - page.width * .004 : h.left + h.width + page.width * .012));
    return { left, right, nrLeft: Math.max(left, Math.round(h.left - page.width * .012)), top: Math.round(top + h.height + 2), bottom: Math.round(end), width: page.width, height: page.height };
  }).filter(s => s.right - s.left > 10 && s.bottom - s.top > 20);
}
function missingNumberCells(tsv, strips, extra) {
  const words = String(tsv).trim().split(/\r?\n/).map(l => l.split('\t')).filter(c => c[0] === '5' && +c[10] > -1)
    .map(c => ({ left:+c[6], top:+c[7], width:+c[8], height:+c[9], text:(c[11] || '').trim() }));
  const cells = [];
  strips.forEach(strip => {
    const surnames = words.filter(w => /^[A-ZÄÖÜ][A-ZÄÖÜß\-']{1,},$/.test(w.text) && w.left >= strip.right - 4 && w.left < strip.right + strip.width * .12
      && w.top > strip.top && w.top < strip.bottom);
    surnames.forEach(w => {
      const y = w.top + w.height / 2, h = Math.max(14, w.height);
      const has = extra.some(e => /^\d{1,2}$/.test(e.text) && e.left >= strip.left - 2 && e.left < strip.right + 2 && Math.abs(e.top + e.height / 2 - y) < h * .7);
      if (!has && !cells.some(c => Math.abs(c.y - y) < h * .7 && c.right === strip.right))
        cells.push({ left: strip.nrLeft != null ? strip.nrLeft : strip.left, right: strip.right, top: Math.max(0, Math.round(y - h * 1.1)), bottom: Math.round(y + h * 1.1), width: strip.width, height: strip.height, y });
    });
  });
  return cells.slice(0, 30);
}
function stripCanvas(source, strip, scale) {
  const c = document.createElement('canvas');
  c.width = Math.round((strip.right - strip.left) * scale) + 40; c.height = Math.round((strip.bottom - strip.top) * scale) + 40;
  const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, c.width, c.height);
  x.drawImage(source, strip.left, strip.top, strip.right - strip.left, strip.bottom - strip.top, 20, 20, c.width - 40, c.height - 40);
  return c;
}
function stripWords(tsv, strip, scale) {
  const out = [];
  String(tsv).trim().split(/\r?\n/).map(l => l.split('\t')).filter(c => c[0] === '5' && (c[11] || '').trim() && +c[10] > -1).forEach(c => {
    const w = { level:5, block:900, par:1, line:1, left: strip.left + (+c[6] - 20) / scale, top: strip.top + (+c[7] - 20) / scale,
      width: +c[8] / scale, height: +c[9] / scale, conf: +c[10], text: c[11].trim(), strip:true };
    // Position and number are often read as one word ("G31", "LD68"); jersey numbers have at most two digits,
    // a third leading "1" is a table line.
    const m = w.text.match(/^([GDFLRC]{1,2})?(\d{1,3})$/);
    if (!m) { if (/^[GDFLRC]{1,2}$/.test(w.text)) out.push(Object.assign(w, { conf: Math.max(w.conf, 60) })); return; }
    let digits = m[2]; if (digits.length === 3 && digits[0] === '1') digits = digits.slice(1); if (digits.length === 3) return;
    const share = m[1] ? Math.min(.55, m[1].length / w.text.length + .1) : 0;
    if (m[1]) out.push(Object.assign({}, w, { text: m[1], width: w.width * share * .8, conf: 60 }));
    out.push(Object.assign({}, w, { text: digits, left: w.left + w.width * share, width: w.width * (1 - share), conf: Math.max(w.conf, 60) }));
  });
  return out;
}
function removeTableLines(pixels, width, height) {
  const d = pixels.data, n = width * height, gray = new Uint8Array(n), erase = new Uint8Array(n);
  for (let i = 0, j = 0; j < n; i += 4, j++) gray[j] = d[i];
  // Lines may be tilted (photo: wander sideways), dashed and grey (copy/scan).
  // Horizontal: only long unbroken runs, otherwise a row of letters would look like a line.
  // Vertical: small gaps allowed; character strokes are much shorter than minV.
  function scan(len, count, at, minLen, maxGap, side, isLine) {
    for (let a = side; a < count - side; a++) {
      let start = -1, last = -1;
      const hit = i => { for (let c = -side; c <= side; c++) if (isLine(gray[at(i, a + c)])) return true; return false; };
      for (let i = 0; i <= len; i++) {
        if (i < len && hit(i)) { if (start < 0) start = i; last = i; continue; }
        if (start >= 0 && (i === len || i - last > maxGap)) {
          if (last - start + 1 >= minLen) for (let k = start; k <= last; k++) for (let c = -side - 1; c <= side + 1; c++) {
            const j = at(k, Math.min(count - 1, Math.max(0, a + c))); if (gray[j] < 235) erase[j] = 1;
          }
          start = -1;
        }
      }
    }
  }
  scan(width, height, (x, y) => y * width + x, Math.round(width * .12), 2, 1, v => v < 190);
  scan(height, width, (y, x) => y * width + x, Math.round(height * .03), 6, 2, v => v < 215);
  for (let j = 0; j < n; j++) if (erase[j]) { const i = j * 4; d[i] = d[i + 1] = d[i + 2] = 255; }
}

function prepareImage(file, fullPage) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const url = URL.createObjectURL(file);
    image.onload = () => {
      // Photos: trim the edges and the title area. 2.9: a page rendered from a PDF is already the sheet - keep it whole.
      const cropX = fullPage ? 0 : Math.round(image.naturalWidth * .025);
      const cropY = fullPage ? 0 : Math.round(image.naturalHeight * .145);
      const cropWidth = fullPage ? image.naturalWidth : Math.round(image.naturalWidth * .95);
      const cropHeight = fullPage ? image.naturalHeight : Math.round(image.naturalHeight * .845);   // 2.9: down to the image end (long rosters)
      const targetWidth = fullPage ? 2400 : 1800;   // 2.9: PDF pages have small print
      const targetHeight = Math.round(cropHeight * targetWidth / cropWidth);
      const canvas = document.createElement('canvas');
      canvas.width = targetWidth; canvas.height = targetHeight;
      const context = canvas.getContext('2d', { willReadFrequently:true });
      context.drawImage(image, cropX, cropY, cropWidth, cropHeight, 0, 0, targetWidth, targetHeight);
      const pixels = context.getImageData(0, 0, targetWidth, targetHeight);
      for (let i = 0; i < pixels.data.length; i += 4) {
        const gray = .299 * pixels.data[i] + .587 * pixels.data[i+1] + .114 * pixels.data[i+2];
        const value = gray < 175 ? Math.max(0, gray * .78) : Math.min(255, gray * 1.12);
        pixels.data[i] = pixels.data[i+1] = pixels.data[i+2] = value;
      }
      removeTableLines(pixels, targetWidth, targetHeight);
      context.putImageData(pixels, 0, 0);
      URL.revokeObjectURL(url);
      resolve(canvas);
    };
    image.onerror = () => { URL.revokeObjectURL(url); reject(new Error('Foto konnte nicht geladen werden')); };
    image.src = url;
  });
}


function metadataImage(file) {
  return new Promise((resolve,reject)=>{
    const img=new Image(), url=URL.createObjectURL(file);
    img.onload=()=>{
      const canvas=document.createElement('canvas');
      canvas.width=2200;
      const cropHeight=Math.round(img.naturalHeight*.55);
      canvas.height=Math.round(cropHeight*canvas.width/img.naturalWidth);
      const ctx=canvas.getContext('2d');
      ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);
      ctx.drawImage(img,0,0,img.naturalWidth,cropHeight,0,0,canvas.width,canvas.height);
      URL.revokeObjectURL(url);resolve(canvas);
    };
    img.onerror=()=>{URL.revokeObjectURL(url);reject(new Error('Foto nicht lesbar'));};
    img.src=url;
  });
}
function decodeBase64(text) {
  const raw=atob(text), bytes=new Uint8Array(raw.length);
  for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);
  return bytes;
}
// 2.9: PDF line-ups. pdf.js (3.11.174, Apache 2.0) is loaded only when a PDF is chosen; it runs without a
// Worker (pdf.worker.min.js as a plain script) and with isEvalSupported:false (CVE-2024-4367 mitigation).
function isPdf(file) { return /pdf$/i.test(file && file.type || '') || /\.pdf$/i.test(file && file.name || ''); }
function loadScript(src) {
  return new Promise((resolve, reject) => { const s = document.createElement('script'); s.src = src; s.onload = resolve; s.onerror = () => reject(new Error(src + ' fehlt')); document.head.appendChild(s); });
}
async function loadPdfJs() {
  if (!window.pdfjsWorker) await loadScript('pdf.worker.min.js');
  if (!window.pdfjsLib) await loadScript('pdf.min.js');
  return window.pdfjsLib;
}
// Text items of page 1 -> Tesseract-like TSV (one row per word, coordinates scaled to 1800 px width),
// so the same parser reads roster, team names and game number.
function pdfTextToTsv(items, viewport) {
  const out = ['level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext',
    ['1','1','0','0','0','0','0','0',Math.round(viewport.width),Math.round(viewport.height),'-1',''].join('\t')];
  let n = 0; const lineIds = [];
  // Words on the same baseline share one line number (the team-name lookup groups by line, like Tesseract).
  const lineOf = y => { let hit = lineIds.find(l => Math.abs(l.y - y) < 3); if (!hit) { hit = { y, id: lineIds.length + 1 }; lineIds.push(hit); } return hit.id; };
  items.forEach(item => {
    const text = String(item.str || '').replace(/\s+/g, ' ').trim();
    if (!text) return;
    const t = item.transform, fontH = Math.hypot(t[2], t[3]) * viewport.scale || 10;
    const [x, baseline] = viewport.convertToViewportPoint(t[4], t[5]);
    const totalW = Math.max(1, (item.width || text.length * fontH * .5) * viewport.scale), perChar = totalW / text.length;
    let offset = 0;
    text.split(' ').forEach(word => {
      if (word) out.push(['5','1','1','1',String(lineOf(baseline)),String(++n),Math.round(x + offset * perChar),Math.round(baseline - fontH * .8),Math.max(1, Math.round(word.length * perChar)),Math.round(fontH),'99',word].join('\t'));
      offset += word.length + 1;
    });
  });
  return out.join('\n');
}
async function readPdf(file, progress) {
  progress(3, 'PDF wird geöffnet ...');
  const lib = await loadPdfJs();
  const data = new Uint8Array(await file.arrayBuffer());
  const doc = await lib.getDocument({ data, isEvalSupported:false, disableFontFace:true, useSystemFonts:false }).promise;
  const page = await doc.getPage(1);
  const base = page.getViewport({ scale:1 }), viewport = page.getViewport({ scale: 1800 / base.width });
  const content = await page.getTextContent();
  const words = content.items.filter(i => String(i.str || '').trim()).length;
  if (words >= 25) { const tsv = pdfTextToTsv(content.items, viewport); doc.destroy(); return { tsv }; }
  // No text layer (scanned PDF): render page 1 and use the photo OCR.
  progress(8, 'PDF ohne Text – Seite wird als Bild gelesen ...');
  const canvas = document.createElement('canvas'); const scale = 2400 / base.width; const vp = page.getViewport({ scale });
  canvas.width = Math.round(vp.width); canvas.height = Math.round(vp.height);
  const ctx = canvas.getContext('2d'); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
  await page.render({ canvasContext: ctx, viewport: vp }).promise; doc.destroy();
  const blob = await new Promise(r => canvas.toBlob(r, 'image/png'));
  return { image: blob };
}
function start(file,onProgress) {
  if (isPdf(file)) {
    let canceled = false, inner = null;
    const progress = (pct, text) => { if (!canceled) onProgress(pct, text); };
    const promise = (async () => {
      const pdf = await readPdf(file, progress);
      if (canceled) return null;
      if (pdf.image) { inner = startImage(pdf.image, onProgress, { fullPage:true }); return inner.promise; }
      const parsed = parseRosterFromTsv(pdf.tsv);
      if (typeof window !== 'undefined') window._pdfTsv = pdf.tsv;
      parsed.teamNames = (parsed.teamNames || []).map(n => typeof n === 'string' && n.length >= 3 && n.length <= 65 && !/^(Gast|Heim|Spieler|Name|Lizenz|Bewerb)$/i.test(n) ? n : '');
      progress(100, 'PDF gelesen. Bitte Aufstellung kontrollieren.');
      return parsed;
    })();
    return { promise, cancel: () => { canceled = true; if (inner) inner.cancel(); } };
  }
  return startImage(file, onProgress);
}
function startImage(file,onProgress,options) {
  const fullPage=!!(options&&options.fullPage);
  let canceled=false,worker=null,workerUrl='',coreUrl='';
  const progress=(pct,text)=>{if(!canceled)onProgress(pct,text);};
  const promise=(async()=>{
    try {
      if(!window.NEV_OCR_DATA)throw new Error('Eingebettete OCR-Daten fehlen');
      progress(1,'Texterkennung wird geladen ...');
      const data=window.NEV_OCR_DATA;
      workerUrl=URL.createObjectURL(new Blob([decodeBase64(data.worker)],{type:'application/javascript'}));
      coreUrl=URL.createObjectURL(new Blob([decodeBase64(data.core)],{type:'application/javascript'}));
      let pass=0;
      worker=await Tesseract.createWorker([{code:'deu',data:decodeBase64(data.language)}],1,{
        workerPath:workerUrl,corePath:coreUrl+'#tesseract-core-lstm.wasm.js',gzip:true,
        workerBlobURL:false,cacheMethod:'none',
        logger:d=>{if(typeof d.progress==='number')progress(5+Math.round(d.progress*(pass?23:64))+(pass?65:0),pass?'Spielangaben werden gelesen ...':'Aufstellung wird gelesen ...');}
      });
      if(canceled)return null;
      await worker.setParameters({tessedit_pageseg_mode:Tesseract.PSM.AUTO});
      const prepared=await prepareImage(file,fullPage);
      if(canceled)return null;
      const result=await worker.recognize(prepared,{}, {text:true,tsv:true});
      if(canceled)return null;
      let parsed=parseRosterFromTsv(result.data.tsv||'');
      // 2.9: digits-only pass over the Pos./Nr. strips, then parse again with these words.
      try {
        const strips=numberStrips(result.data.tsv||'');
        if(strips.length){
          await worker.setParameters({tessedit_pageseg_mode:Tesseract.PSM.SINGLE_BLOCK,tessedit_char_whitelist:'0123456789GDFLRC'});
          const extra=[];const scale=2;
          for(const strip of strips){
            if(canceled)return null;
            const r=await worker.recognize(stripCanvas(prepared,strip,scale),{}, {text:true,tsv:true});
            extra.push(...stripWords(r.data.tsv||'',strip,scale));
          }
          // Name rows (SURNAME,) without any number from the strip: read just that Nr. cell again.
          // A single digit next to the position letter is often dropped; the number alone (digits only) is reliable.
          await worker.setParameters({tessedit_pageseg_mode:Tesseract.PSM.SINGLE_LINE,tessedit_char_whitelist:'0123456789'});
          for(const cell of missingNumberCells(result.data.tsv||'',strips,extra)){
            if(canceled)return null;
            const r=await worker.recognize(stripCanvas(prepared,cell,3),{}, {text:true,tsv:true});
            extra.push(...stripWords(r.data.tsv||'',cell,3));
          }
          await worker.setParameters({tessedit_pageseg_mode:Tesseract.PSM.AUTO,tessedit_char_whitelist:''});
          if(typeof window!=='undefined')window._strip=extra;
          const again=parseRosterFromTsv(result.data.tsv||'',extra);
          if(again.home.length+again.away.length>=parsed.home.length+parsed.away.length)parsed=again;
        }
      } catch(error) { if(canceled)return null; console.warn('Nummernspalte',error); }
      pass=1;
      // Full upper half of the original photo; the roster crop must not cut off the header.
      let meta={teamNames:[],gameNumber:''};
      try {
        const preparedMeta=await metadataImage(file);
        if(canceled)return null;
        const metadata=await worker.recognize(preparedMeta,{}, {text:true,tsv:true});
        meta=parseRosterFromTsv(metadata.data.tsv||'');
      } catch(error) { if(canceled)return null; console.warn('Kopferkennung',error); }
      if(canceled)return null;
      const usableName=n=>typeof n==='string' && n.length>=3 && n.length<=65 && !/^(Gast|Heim|Spieler|Name|Lizenz|Bewerb)$/i.test(n);
      parsed.teamNames=[0,1].map(i=>usableName(meta.teamNames[i])?meta.teamNames[i]:(usableName(parsed.teamNames[i])?parsed.teamNames[i]:''));
      parsed.gameNumber=meta.gameNumber||parsed.gameNumber;
      progress(100,'Erkennung abgeschlossen. Bitte Aufstellung kontrollieren.');
      return parsed;
    } finally {
      if(worker){try{await worker.terminate();}catch(_){}}
      if(workerUrl)URL.revokeObjectURL(workerUrl);
      if(coreUrl)URL.revokeObjectURL(coreUrl);
    }
  })();
  return {promise,cancel:()=>{canceled=true;if(worker)worker.terminate().catch(()=>{});}};
}
return {isPdf,pdfTextToTsv,readPdf,startImage,parseRosterFromTsv,numberStrips,stripWords,missingNumberCells,cleanName,cleanTeamName,cleanGameNumber,nameIssues,removeTableLines,start};
});
