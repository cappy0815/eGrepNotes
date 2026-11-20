/* eGrep Notes: pure, testable match logic. No network or DOM dependencies. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.EgrepLogic = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const VERSION = '3.0';
  const DATA_VERSION = 9;
  const PERIOD_SECONDS = 1200;
  // 2.1: sorted by frequency in a sample of 27 EHV NRW games (241 penalties, hockeydata game reports,
  // Oct. 2026); penalties without occurrences follow in the previous order, "Sonstige" stays last.
  const PENALTIES = [
    'Beinstellen', 'Haken', 'Unkorrekter K\u00f6rperangriff', 'Halten', 'Stockschlag',
    '\u00dcbertriebene H\u00e4rte', 'Bandencheck', 'Behinderung', 'Stockcheck / Cross-Check',
    'Unsportliches Verhalten', 'Faustkampf', 'Hoher Stock', 'Kniecheck', 'Zu viele Spieler auf dem Eis',
    'Spielverz\u00f6gerung', 'Stockstich', 'Disziplinarstrafe', 'Ellbogencheck', 'Check gegen Kopf / Nacken',
    'Check mit den Beinen / Clipping', 'Unzul\u00e4ssige Ausr\u00fcstung',
    'Check von hinten', 'Halten des Stocks', 'Torh\u00fcterbehinderung', 'Beschimpfung von Spieloffiziellen',
    'Stockendensto\u00df', 'Stockwurf / Werfen von Ausr\u00fcstung', 'Slew-Footing', 'Treten', 'Kopfsto\u00df',
    'Schwalbe / Vort\u00e4uschen',
    'Sonstige'
  ];
  // Kept for compatibility; 2.1 shows the whole list (scrollable) instead of 8 quick buttons.
  const QUICK_PENALTIES = 8;
  const PENALTY_DURATIONS = Object.freeze([
    {value:'2',label:'2 Min.',short:'2 Min.'},
    {value:'2+2',label:'2+2 Min.',short:'2+2 Min.'},
    {value:'5',label:'5 Min.',short:'5 Min.'},
    {value:'10',label:'10 Min.',short:'10 Min.'},
    {value:'game',label:'Spieldauer',short:'Spieldauer'}
  ]);
  function normalizePenaltyDuration(value) {
    const raw = String(value == null ? '' : value);
    return PENALTY_DURATIONS.some(p=>p.value===raw) ? raw : '';
  }
  function penaltyDurationLabel(event) {
    const p = PENALTY_DURATIONS.find(p=>p.value===String(event.penaltyDuration));
    return p ? p.short : 'Dauer nicht erfasst';
  }
  function penaltyDescription(event) {
    return String(event.penalty||'') + ' \u00b7 ' + penaltyDurationLabel(event);
  }
  // 2.7: 'penaltyshot' = penalty shot during the game (scored counts as a goal), 'note' = free text
  // with time; a note may be general (team '').
  const TYPE_LABELS = {goal:'Tor', penalty:'Strafe', goalie:'Torwartwechsel', timeout:'Timeout', penaltyshot:'Penalty', note:'Notiz'};
  const NOTE_MAX = 300;
  function cleanNote(value) { return String(value||'').replace(/[\r\n\t]+/g,' ').replace(/\s+/g,' ').trim().slice(0,NOTE_MAX); }
  function isGoal(event) { return event.type==='goal' || (event.type==='penaltyshot' && !!event.scored); }
  function uid() { return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2,10); }
  function localDate() {
    const d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
  }
  function emptyState() {
    return {version:DATA_VERSION, currentPeriod:null, meta:{date:localDate(),number:'',operatorName:'',operatorPrompted:false,timeMode:'down'}, home:{name:'Neusser EV',players:[],startGoalie:''},
      away:{name:'Gast',players:[],startGoalie:''}, events:[], shootout:[]};
  }
  function normalizePeriod(value) {
    return [1,2,3,'1','2','3'].includes(value) ? Number(value) : null;
  }
  function clockJumpIssue(candidate,events) {
    if (!normalizePeriod(candidate.period) || !normalizeTime(candidate.time)) return null;
    const inPeriod = sortedEventsByGameTime(events.filter(e=>Number(e.period)===Number(candidate.period) && e.id!==candidate.id));
    const last = inPeriod[inPeriod.length-1];
    return last && compareMoments(candidate,last)<0 ? {relation:'before',event:last} : null;
  }
  // 2.0: goalie pulled -> "EN" (empty net) instead of a jersey number.
  const EMPTY_NET = 'EN';
  function normalizeGoalie(value) { return String(value||'').toUpperCase()===EMPTY_NET ? EMPTY_NET : normalizeNumber(value); }
  function normalizeNumber(value) {
    const raw = String(value == null ? '' : value).trim().replace(/^#/, '');
    return /^\d{1,2}$/.test(raw) ? String(Number(raw)) : '';
  }
  function normalizeTime(value) {
    const raw = String(value == null ? '' : value).trim();
    let mins, secs;
    if (/^\d{1,2}:\d{2}$/.test(raw)) [mins,secs] = raw.split(':').map(Number);
    else if (/^\d{1,4}$/.test(raw)) {
      const digits = raw.padStart(3,'0');
      mins = Number(digits.slice(0,-2)); secs = Number(digits.slice(-2));
    } else return '';
    if (secs > 59 || mins*60+secs > PERIOD_SECONDS) return '';
    return mins + ':' + String(secs).padStart(2,'0');
  }
  // 2.2: "Uhr auf" - elapsed game time over all periods (as in DEB/EHV reports), e.g. 2713 = 27:13.
  // Converted to period + remaining clock, so events are stored exactly as before.
  // 2.4: three time modes per game. 'down' = clock counts down (remaining time, default),
  // 'up' = hall clock counts up and restarts at 0:00 every period, 'game' = continuous game
  // time 0:00-60:00 as in DEB/EHV reports (this was "Uhr auf" in 2.2/2.3).
  const TIME_MODES = ['down','up','game'];
  function normalizeTimeMode(value) { return TIME_MODES.includes(value) ? value : 'down'; }
  // Hall clock counting up within a period: 5:12 played -> 14:48 remaining.
  function upToClock(value) {
    const t = normalizeTime(value);
    if (!t) return null;
    const [m,ss] = t.split(':').map(Number), left = PERIOD_SECONDS - m*60 - ss, lm = Math.floor(left/60), ls = String(left%60).padStart(2,'0');
    return {up: t, time: lm + ':' + ls, clock: lm ? String(lm) + ls : String(left%60)};
  }
  function upSeconds(event) {
    const t = normalizeTime(event.time || '');
    if (!t) return NaN;
    const [m,ss] = t.split(':').map(Number);
    return PERIOD_SECONDS - m*60 - ss;
  }
  function upLabel(event) { const s = upSeconds(event); return Number.isFinite(s) ? Math.floor(s/60) + ':' + String(s%60).padStart(2,'0') : '\u2014'; }
  function upDigits(event) { const s = upSeconds(event); return Number.isFinite(s) ? (Math.floor(s/60) ? String(Math.floor(s/60)) + String(s%60).padStart(2,'0') : String(s%60)) : ''; }
  function elapsedToClock(value) {
    const raw = String(value == null ? '' : value).trim();
    let mins, secs;
    if (/^\d{1,2}:\d{2}$/.test(raw)) [mins,secs] = raw.split(':').map(Number);
    else if (/^\d{1,4}$/.test(raw)) { const d = raw.padStart(3,'0'); mins = Number(d.slice(0,-2)); secs = Number(d.slice(-2)); }
    else return null;
    const total = mins*60 + secs;
    if (secs > 59 || total > 3*PERIOD_SECONDS) return null;
    // Period end belongs to that period: 20:00 = 1st period, clock 0:00; 0:00 = 1st period, clock 20:00.
    const period = Math.min(3, Math.max(1, Math.ceil(total/PERIOD_SECONDS)));
    const left = period*PERIOD_SECONDS - total, m = Math.floor(left/60), ss = String(left%60).padStart(2,'0');
    return {period, time: m + ':' + ss, clock: m ? String(m) + ss : String(left%60), elapsed: mins + ':' + String(secs).padStart(2,'0')};
  }
  function elapsedDigits(event) {
    const secs = eventElapsedSeconds(event);
    return Number.isFinite(secs) ? String(Math.floor(secs/60)) + String(secs%60).padStart(2,'0') : '';
  }
  // 2.5: club logo by team name (data = window.EGREP_TEAM_LOGOS). Exact name first, then the club
  // without age group / team suffix ("Krefelder EV U15 A" -> "krefelder ev").
  function normTeamName(value) {
    return String(value||'').toLowerCase().replace(/[„“"']/g,'').replace(/[_\-\/.,()]+/g,' ').replace(/\s+/g,' ').trim();
  }
  const TEAM_SUFFIX = /(?:\s+(?:1b|1c|1d|2b|u\d{1,2}|[ab]|senioren|frauen|damen|ladies|juniors?))+$/;
  function baseTeamName(value) { return normTeamName(value).replace(TEAM_SUFFIX,'').trim(); }
  function teamLogoIndex(data, name) {
    if (!data || !data.logos) return null;
    const n = normTeamName(name), b = baseTeamName(name);
    if (!n) return null;
    const own = Object.prototype.hasOwnProperty;
    const i = own.call(data.names||{},n) ? data.names[n] : own.call(data.names||{},b) ? data.names[b] : own.call(data.bases||{},b) ? data.bases[b] : null;
    return i == null || !data.logos[i] ? null : {index:i, src:data.logos[i], color:(data.colors||[])[i]||''};
  }
  function eventElapsedSeconds(event) {
    const time = normalizeTime(event.time || '');
    const period = Number(event.period);
    if (!time || ![1,2,3].includes(period)) return Infinity;
    const [m,s] = time.split(':').map(Number);
    return (period-1)*PERIOD_SECONDS + PERIOD_SECONDS-m*60-s;
  }
  function compareMoments(a,b) {
    return eventElapsedSeconds(a)-eventElapsedSeconds(b) || Number(a.period)-Number(b.period);
  }
  function compareEventsByGameTime(a,b) {
    return compareMoments(a,b) || Number(a.order||0)-Number(b.order||0);
  }
  function sortedEventsByGameTime(events) { return events.slice().sort(compareEventsByGameTime); }
  // 1.5: game screen shows the most recently ENTERED event first (Nachtraege included).
  function sortedEventsByEntryDesc(events) {
    return events.slice().sort((a,b)=>Number(b.order||0)-Number(a.order||0) || compareEventsByGameTime(b,a));
  }
  function formatGameTime(event) {
    const secs = eventElapsedSeconds(event);
    if (!Number.isFinite(secs)) return '\u2014';
    return Math.floor(secs/60) + ':' + String(secs%60).padStart(2,'0') + ' (' + event.period + ')';
  }
  function clockDigits(event) { return String(event.clock || event.time || '').replace(':',''); }
  function hasDuplicateNumber(team,number,excludedId) {
    return team.players.some(p=>p.id!==excludedId && normalizeNumber(p.number)===normalizeNumber(number));
  }
  function appendPlayer(team,number,name) {
    const p = {id:uid(),number:normalizeNumber(number),name:String(name||'').trim(),isGoalie:false,starter:false};
    team.players.push(p); return p;
  }
  function playerByNumber(state,side,number) {
    return state[side] && state[side].players.find(p=>normalizeNumber(p.number)===normalizeNumber(number));
  }
  function playerLabel(state,side,number) {
    if (number === '' || number == null) return '\u2014';
    if (number === EMPTY_NET) return 'Leeres Tor';
    const player = playerByNumber(state,side,number);
    return '#' + number + (player && player.name ? ' ' + player.name : '');
  }
  function chronologyIssue(candidate,events,editingId) {
    const chronological = sortedEventsByGameTime(events);
    if (!editingId) {
      const last = chronological[chronological.length-1];
      return last && compareMoments(candidate,last)<0 ? {relation:'before',event:last} : null;
    }
    const at = chronological.findIndex(e=>e.id===editingId);
    if (at<0) return null;
    const before = chronological[at-1], after = chronological[at+1];
    if (before && compareMoments(candidate,before)<0) return {relation:'before',event:before};
    if (after && compareMoments(candidate,after)>0) return {relation:'after',event:after};
    return null;
  }
  function getStartGoalie(team) {
    const explicit = normalizeNumber(team.startGoalie);
    if (explicit && team.players.some(p=>normalizeNumber(p.number)===explicit)) return explicit;
    const starters = team.players.filter(p=>p.isGoalie && p.starter===true);
    return starters.length===1 ? normalizeNumber(starters[0].number) : '';
  }
  function goalieAt(state,side,candidate) {
    let current = getStartGoalie(state[side]);
    sortedEventsByGameTime(state.events).forEach(e=>{
      if (e.team===side && e.type==='goalie' && e.id!==candidate.id && compareEventsByGameTime(e,candidate)<=0) {
        current = normalizeGoalie(e.goalieIn);
      }
    });
    return current;
  }
  function goalieSuggestions(state,side,candidate) {
    const out = goalieAt(state,side,candidate);
    if (out === EMPTY_NET) {
      // Coming back from an empty net: suggest the goalie who left it.
      let last = getStartGoalie(state[side]);
      sortedEventsByGameTime(state.events).forEach(e=>{
        if (e.team===side && e.type==='goalie' && e.id!==candidate.id && compareEventsByGameTime(e,candidate)<=0 && normalizeGoalie(e.goalieIn)===EMPTY_NET) last = normalizeGoalie(e.goalieOut);
      });
      return {out, incoming:last && last!==EMPTY_NET ? last : '', choices:state[side].players.filter(p=>p.isGoalie)};
    }
    const others = state[side].players.filter(p=>p.isGoalie && normalizeNumber(p.number)!==out);
    return {out, incoming:out && others.length===1 ? normalizeNumber(others[0].number) : '', choices:others};
  }
  function participants(event) {
    if (event.type==='goalie') return [['Torwart raus',event.goalieOut],['Torwart rein',event.goalieIn]];
    if (event.type==='goal') return [['Torsch\u00fctze',event.player],['Assist 1',event.assist1],['Assist 2',event.assist2]];
    if (event.type==='timeout' || event.type==='note') return [];
    if (event.type==='penaltyshot') return [['Sch\u00fctze',event.player]];
    // 2.9: who serves a goalie or bench penalty.
    const served = event.servedBy ? [['Sitzt ab',event.servedBy]] : [];
    return (event.bench ? [] : [['Spieler',event.player]]).concat(served);
  }
  // 2.9: a goalie (roster TW or currently in goal) or a bench penalty is served by a field player.
  function needsServer(state,event) {
    if (!event || event.type!=='penalty' || !['home','away'].includes(event.team)) return false;
    if (event.bench) return true;
    const n = normalizeNumber(event.player); if (n==='') return false;
    const p = playerByNumber(state,event.team,n);
    if (p && p.isGoalie) return true;
    return goalieAt(state,event.team,event)===n;
  }
  function servedLabel(event) {
    if (!event || event.type!=='penalty') return '';
    if (event.servedBy) return 'abgesessen von #' + event.servedBy;
    return event.servedLater ? 'Absitzender offen' : '';
  }
  function unknownPlayers(state,event) {
    if (!state[event.team] || !state[event.team].players.length) return [];
    return participants(event).filter(([,n])=>n!=='' && n!=null && n!==EMPTY_NET && !playerByNumber(state,event.team,n));
  }
  function validateEvent(event) {
    if (!TYPE_LABELS[event.type]) return 'Bitte eine Ereignisart w\u00e4hlen.';
    if (!['home','away'].includes(event.team) && !(event.type==='note' && event.team==='')) return 'Bitte eine Mannschaft w\u00e4hlen.';
    if (![1,2,3].includes(Number(event.period))) return 'Bitte das Drittel bewusst ausw\u00e4hlen.';
    if (!normalizeTime(event.time)) return 'Die Uhrzeit muss zwischen 0:00 und 20:00 liegen (Sekunden 00\u201359).';
    if (event.type==='timeout') return '';
    if (event.type==='note') return cleanNote(event.text) ? '' : 'Bitte einen Notiztext eingeben.';
    if (event.type==='penaltyshot') {
      if (normalizeNumber(event.player)==='') return 'Bitte die Trikotnummer des Sch\u00fctzen eingeben.';
      if (typeof event.scored!=='boolean') return 'Bitte Tor oder kein Tor w\u00e4hlen.';
      return '';
    }
    if (event.type==='goalie') {
      const out = normalizeGoalie(event.goalieOut), incoming = normalizeGoalie(event.goalieIn);
      if (out==='' || incoming==='') return 'Beide Felder ausf\u00fcllen (Nummer oder leeres Tor).';
      if (out===incoming) return out===EMPTY_NET ? 'Raus und rein k\u00f6nnen nicht beide \u201eleeres Tor\u201c sein.' : 'Raus und rein m\u00fcssen unterschiedliche Torwarte sein.';
    } else {
      if (!event.bench && normalizeNumber(event.player)==='') return 'Bitte die Trikotnummer eingeben.';
      if (event.type==='goal') {
        const numbers = [event.player,event.assist1,event.assist2].filter(n=>n!=='' && n!=null).map(normalizeNumber);
        if (numbers.includes('')) return 'Bitte g\u00fcltige Spielernummern von 0 bis 99 verwenden.';
        if (new Set(numbers).size!==numbers.length) return 'Torsch\u00fctze und Assists m\u00fcssen unterschiedliche Spieler sein.';
        if (!event.assist1 && event.assist2) return 'Bitte zuerst Assist 1 eintragen.';
      }
      if (event.type==='penalty' && !String(event.penalty||'').trim()) return 'Bitte die Strafart angeben.';
      if (event.type==='penalty' && event.penaltyDuration!=null && event.penaltyDuration!=='' && !normalizePenaltyDuration(event.penaltyDuration))
        return 'Bitte ein Strafma\u00df ausw\u00e4hlen (2, 2+2, 5, 10 Min. oder Spieldauer).';
    }
    return '';
  }
  function regularScore(state) {
    return state.events.reduce((r,e)=>{if(isGoal(e) && ['home','away'].includes(e.team))r[e.team]++;return r;},{home:0,away:0});
  }
  // 2.0: penalty shootout. Only the winner gets ONE goal added to the regular result.
  function shootoutResult(state) {
    const list = Array.isArray(state.shootout) ? state.shootout : [];
    const r = {home:0, away:0, attempts:list.length, winner:''};
    list.forEach(a=>{ if (a.scored && r[a.team]!=null) r[a.team]++; });
    if (list.length && r.home!==r.away) r.winner = r.home>r.away ? 'home' : 'away';
    return r;
  }
  function score(state) {
    const r = regularScore(state), so = shootoutResult(state);
    if (so.winner) r[so.winner]++;
    return r;
  }
  function scoreLabel(state) { const s = score(state); return s.home + ' : ' + s.away + (shootoutResult(state).winner ? ' n.P.' : ''); }
  // 2.0: goals per period, e.g. [{home:1,away:0},{home:2,away:1},{home:0,away:0}].
  function periodScores(state) {
    const r = [1,2,3].map(()=>({home:0,away:0}));
    state.events.forEach(e=>{ const i = Number(e.period)-1; if (isGoal(e) && r[i] && r[i][e.team]!=null) r[i][e.team]++; });
    return r;
  }
  // 2.0: HINT only. Which penalties may still run at the moment of this goal?
  // Minor (2) ends at the first goal of the other team; 2+2/5 run their full time;
  // 10 min and game misconducts do not change the numbers on ice. Not a rule decision.
  const PENALTY_SECONDS = {'2':120, '2+2':240, '5':300};
  function runningPenalties(state, at) {
    const t = eventElapsedSeconds(at);
    if (!Number.isFinite(t)) return [];
    const goals = sortedEventsByGameTime(state.events.filter(e=>e.type==='goal' && e.id!==at.id));
    return state.events.filter(e=>e.type==='penalty' && e.id!==at.id && PENALTY_SECONDS[e.penaltyDuration]).filter(e=>{
      const start = eventElapsedSeconds(e); let end = start + PENALTY_SECONDS[e.penaltyDuration];
      if (e.penaltyDuration==='2') { const g = goals.find(g=>g.team!==e.team && eventElapsedSeconds(g)>start && eventElapsedSeconds(g)<end); if (g) end = eventElapsedSeconds(g); }
      return start < t && t < end;
    });
  }
  function powerPlayHint(state, goal) {
    if (!goal || goal.type!=='goal') return null;
    const running = runningPenalties(state, goal);
    const own = running.filter(e=>e.team===goal.team).length, other = running.filter(e=>e.team!==goal.team).length;
    if (own===other) return null;
    return {kind: other>own ? 'PP' : 'SH', label: other>own ? 'M\u00f6gliches \u00dcberzahltor' : 'M\u00f6gliches Unterzahltor', penalties: running};
  }
  // 2.7: goal while the other team's net is empty (from the recorded goalie changes).
  function emptyNetGoal(state, event) {
    if (!event || event.type!=='goal' || !['home','away'].includes(event.team)) return false;
    return goalieAt(state, event.team==='home' ? 'away' : 'home', event) === EMPTY_NET;
  }
  // Only one timeout per team and game: returns the already recorded one, if any.
  function timeoutIssue(state,candidate) {
    return state.events.find(e=>e.type==='timeout' && e.team===candidate.team && e.id!==candidate.id) || null;
  }
  function eventShort(event) {
    if (event.type==='timeout') return '';
    if (event.type==='note') return cleanNote(event.text);
    if (event.type==='penaltyshot') return event.player + ', ' + (event.scored ? 'Tor' : 'kein Tor');
    if (event.type==='goalie') { const g = n => n===EMPTY_NET ? 'leer' : '#' + n; return g(event.goalieOut) + ' \u2192 ' + g(event.goalieIn); }
    if (event.type==='goal') return [event.player,event.assist1,event.assist2].filter(n=>n!=='' && n!=null).join(', ');
    return (event.bench ? 'Bank' : event.player) + ', ' + event.penalty + ', ' + penaltyDurationLabel(event) + (servedLabel(event) ? ', ' + servedLabel(event) : '');
  }
  // 1.6: clock as read from the rink clock, e.g. 1012 -> 10:12 (input for eGrep).
  function clockLabel(event) { return normalizeTime(clockDigits(event)) || normalizeTime(event.time) || '\u2014'; }
  function eventNames(state,event) {
    return participants(event).filter(([,n])=>n!=='' && n!=null).map(([role,n])=>({role,number:n,label:playerLabel(state,event.team,n)}));
  }
  function migrateState(saved) {
    if (!saved || !saved.home || !saved.away || !Array.isArray(saved.events)) return emptyState();
    const result = emptyState();
    result.currentPeriod = normalizePeriod(saved.currentPeriod);
    result.meta.date = String(saved.meta && saved.meta.date || localDate());
    result.meta.number = String(saved.meta && saved.meta.number || '');
    result.meta.operatorName = String(saved.meta && saved.meta.operatorName || '').replace(/[\r\n\t]+/g,' ').trim().slice(0,100);
    result.meta.operatorPrompted = !!(result.meta.operatorName || (saved.meta && saved.meta.operatorPrompted));
    // 2.2/2.3 stored clockMode 'up' for continuous game time -> now 'game'.
    const sm = saved.meta || {};
    result.meta.timeMode = TIME_MODES.includes(sm.timeMode) ? sm.timeMode : (sm.clockMode === 'up' ? 'game' : 'down');
    ['home','away'].forEach(side=>{
      result[side].name = String(saved[side].name || result[side].name);
      const seen = new Set();
      (Array.isArray(saved[side].players)?saved[side].players:[]).forEach(p=>{
        const number = normalizeNumber(p.number);
        if (number==='' || seen.has(number)) return;
        seen.add(number);
        const player = {id:String(p.id||uid()),number,name:String(p.name||''),isGoalie:!!p.isGoalie,starter:!!p.starter};
        // 1.6: OCR plausibility marks stay until the player is opened and saved once.
        if (Array.isArray(p.check) && p.check.length) player.check = p.check.map(String).slice(0,8);
        result[side].players.push(player);
      });
      result[side].startGoalie = normalizeNumber(saved[side].startGoalie);
    });
    // 2.0: shootout attempts (team, number, scored), no clock time.
    (Array.isArray(saved.shootout) ? saved.shootout : []).forEach((a,i)=>{
      if (!['home','away'].includes(a.team)) return;
      result.shootout.push({id:String(a.id||uid()), order:Number.isFinite(Number(a.order))?Number(a.order):i+1, team:a.team, player:normalizeNumber(a.player), scored:!!a.scored});
    });
    saved.events.forEach((source,i)=>{
      const e = Object.assign({},source);
      if (!TYPE_LABELS[e.type]) return;
      if (!['home','away'].includes(e.team)) { if (e.type!=='note') return; e.team=''; }
      e.id = String(e.id||uid());
      e.order = Number.isFinite(Number(e.order)) ? Number(e.order) : i+1;
      ['player','assist1','assist2','goalieOut','goalieIn'].forEach(key=>{
        const p = e.team ? result[e.team].players.find(p=>p.id===e[key]) : null;
        e[key] = p ? p.number : (key.startsWith('goalie') ? normalizeGoalie(e[key]) : normalizeNumber(e[key]));
      });
      e.period = Number(e.period)||1;
      e.time = normalizeTime(e.time);
      e.clock = String(e.clock||source.time||'').replace(':','');
      e.penalty = String(e.penalty||''); e.bench = !!e.bench;
      if (e.type==='note') { e.text = cleanNote(e.text); e.player=''; e.assist1=''; e.assist2=''; e.goalieOut=''; e.goalieIn=''; e.penalty=''; e.bench=false; }
      if (e.type==='penaltyshot') { e.scored = !!e.scored; e.assist1=''; e.assist2=''; e.goalieOut=''; e.goalieIn=''; e.penalty=''; e.bench=false; }
      if (e.type==='timeout') { e.player=''; e.assist1=''; e.assist2=''; e.goalieOut=''; e.goalieIn=''; e.penalty=''; e.bench=false; }
      // Missing in older versions means UNKNOWN, never invent a historical 2-minute penalty.
      e.penaltyDuration = e.type==='penalty' ? normalizePenaltyDuration(e.penaltyDuration) : '';
      // 2.9: servedBy = number serving a goalie/bench penalty; servedLater = asked, still open.
      e.servedBy = e.type==='penalty' ? normalizeNumber(e.servedBy) : '';
      e.servedLater = e.type==='penalty' && !e.servedBy && !!e.servedLater;
      if (e.time) result.events.push(e);
    });
    return result;
  }
  return {NOTE_MAX,cleanNote,isGoal,emptyNetGoal,normTeamName,baseTeamName,teamLogoIndex,TIME_MODES,normalizeTimeMode,upToClock,upLabel,upDigits,elapsedToClock,elapsedDigits,EMPTY_NET,normalizeGoalie,regularScore,shootoutResult,scoreLabel,periodScores,runningPenalties,powerPlayHint,VERSION,DATA_VERSION,QUICK_PENALTIES,PERIOD_SECONDS,PENALTIES,PENALTY_DURATIONS,normalizePenaltyDuration,penaltyDurationLabel,penaltyDescription,TYPE_LABELS,uid,localDate,emptyState,normalizePeriod,clockJumpIssue,normalizeNumber,normalizeTime,
    eventElapsedSeconds,compareMoments,compareEventsByGameTime,sortedEventsByGameTime,sortedEventsByEntryDesc,formatGameTime,clockDigits,
    hasDuplicateNumber,appendPlayer,playerByNumber,playerLabel,chronologyIssue,getStartGoalie,goalieAt,goalieSuggestions,
    participants,needsServer,servedLabel,unknownPlayers,validateEvent,timeoutIssue,score,eventShort,eventNames,clockLabel,migrateState};
});
