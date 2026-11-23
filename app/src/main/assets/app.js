/* eGrep Notes 2.0 -- local UI. Numeric entry uses its own large keypad. */
(function(){
'use strict';
if(typeof document==='undefined'){
  if(typeof module!=='undefined')module.exports=Object.assign({},require('./logic.js'),require('./ocr.js'));
  return;
}
const L=window.EgrepLogic, OCR=window.EgrepOCR, $=id=>document.getElementById(id);
const STORAGE_KEY='nev-spielnotiz-v0.1',ARCHIVE_KEY='egrep-notes-archiv-v1',ARCHIVE_MAX=20;
const esc=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// 3.0: home club (settings). Default Neusser EV with its colours; colours never change per club
// (red = home, blue = away are functional). The club gives logo, name for new games, report and print.
const SETTINGS_KEY='egrep-settings',DEFAULT_CLUB='neusser-ev',CLUBS=(window.EGREP_CLUBS||[]).slice();
const GENERIC_LOGO='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 110"><path d="M48 4 88 18v34c0 28-18 46-40 54C26 98 8 80 8 52V18Z" fill="#fff" stroke="#8a95a3" stroke-width="5"/><ellipse cx="48" cy="62" rx="22" ry="9" fill="#202329"/><path d="M26 62v-8c0 5 10 9 22 9s22-4 22-9v8" fill="#202329"/></svg>');
function loadSettings(){try{const s=JSON.parse(localStorage.getItem(SETTINGS_KEY)||'{}');return s&&typeof s==='object'&&!Array.isArray(s)?s:{};}catch(_){return {};}}
function saveSettings(){try{localStorage.setItem(SETTINGS_KEY,JSON.stringify(settings));return true;}catch(_){return false;}}
let settings=loadSettings();
function homeClub(){
  const custom=String(settings.homeCustom||'').trim().slice(0,60);
  if(custom)return {id:'',name:custom,logo:''};
  return CLUBS.find(c=>c.id===settings.homeClub)||CLUBS.find(c=>c.id===DEFAULT_CLUB)||{id:DEFAULT_CLUB,name:'Neusser EV',logo:'nev-logo.png'};
}
function freshState(){const s=L.emptyState();s.home.name=homeClub().name;return s;}
let state=freshState(), history=[], saveFailed=false;
try{const saved=localStorage.getItem(STORAGE_KEY);if(saved)state=L.migrateState(JSON.parse(saved));}catch(e){saveFailed=true;}
let draft=null,stage='time',trail=[],numericField='player',replaceOnDigit=false,saving=false;
let editingPlayer=null,choiceResolver=null,photoUrl='',photoGeneration=0,recognition=null;
let soTeam=null,soPlayer=null,soStep='team',detailId=null,detailMode='view',reviewResolver=null,jumpResolver=null,advancing=false,periodPickerOpen=false,chronologyApproval=null;
let screenMode='auto',plugged=false,powerKnown=false,keepEnabled=false;
const isNative=location.protocol==='file:';
const sideName=side=>side==='home'||side==='away'?(state[side].name||(side==='home'?'Heim':'Gast')):'Allgemein';
// 2.5: club logo of a team (EHV NRW logos, offline); Neuss without match keeps the NEV logo.
function teamLogo(side){
  const hit=L.teamLogoIndex(window.EGREP_TEAM_LOGOS,sideName(side));
  if(hit)return hit;
  const club=homeClub();if(club.logo&&L.normTeamName(sideName(side))===L.normTeamName(club.name))return {src:club.logo,color:''};
  return /neuss/i.test(sideName(side))?{src:'nev-logo.png',color:''}:null;
}
// 2.6: no colour ring (Micha's choice); white disc stays so dark logos show on the dark scoreboard.
function logoImg(side,cls){const l=teamLogo(side);return l?`<img class="team-logo ${cls}" src="${esc(l.src)}" alt="">`:'';}
function logoSource(){const img=document.querySelector('.app-header img');return img?img.src:'nev-logo.png';}
const nextOrder=()=>Math.max(Date.now(),...state.events.map(e=>Number(e.order||0)+1));
function toast(text){$('toast').textContent=text;$('toast').classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').classList.remove('show'),2700);}
function snapshot(){history.push(JSON.stringify(state));if(history.length>30)history.shift();}
function persist(){try{localStorage.setItem(STORAGE_KEY,JSON.stringify(state));saveFailed=false;}catch(e){saveFailed=true;console.warn(e);}return !saveFailed;}
function commit(text){persist();renderAll();if(saveFailed)toast('Achtung: Speichern auf dem Ger\u00e4t fehlgeschlagen. App nicht schlie\u00dfen!');else if(text)toast(text);}
function undo(){
  if(!history.length)return;
  // Navigation preference is not part of undo: a historical correction must not switch the live period.
  const activePeriod=state.currentPeriod,operatorName=state.meta.operatorName,operatorPrompted=state.meta.operatorPrompted,timeMode_=state.meta.timeMode;
  state=L.migrateState(JSON.parse(history.pop()));state.currentPeriod=activePeriod;state.meta.operatorName=operatorName;state.meta.operatorPrompted=operatorPrompted;state.meta.timeMode=L.normalizeTimeMode(timeMode_);
  commit('Letzte \u00c4nderung r\u00fcckg\u00e4ngig');
}
function renderPeriod(){
  document.querySelectorAll('[data-current-period]').forEach(b=>{
    const active=Number(b.dataset.currentPeriod)===state.currentPeriod;
    b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));
  });
  $('clock-mode').textContent=MODE_LABELS[timeMode()];$('clock-mode').dataset.mode=timeMode();$('clock-mode').setAttribute('aria-pressed',String(timeMode()!=='down'));$('clock-mode').classList.toggle('active',timeMode()!=='down');
  $('current-period-note').textContent=gameMode()?'Spielzeit: Drittel ergibt sich aus der Zeit.':state.currentPeriod
    ?state.currentPeriod+'. Drittel bleibt f\u00fcr neue Ereignisse eingestellt.'
    :'Vor dem ersten Ereignis bitte einmal das Drittel w\u00e4hlen.';
  $('capture-context').textContent=gameMode()?'Spielzeit zuerst \u00b7 dann Aktion und Team':state.currentPeriod
    ?state.currentPeriod+'. Drittel \u00b7 Zeit, Aktion und Team'
    :(hallUp()?'Uhr (aufw\u00e4rts) zuerst':'Uhrzeit zuerst')+' \u00b7 dann Aktion und Team';
}
// 2.4: time entry for the whole game: 'down' = clock counts down (remaining time), 'up' = hall clock
// counts up and restarts every period, 'game' = continuous game time 0:00-60:00 (DEB/EHV report).
const MODE_LABELS={down:'Uhr ab \u25bc',up:'Uhr auf \u25b2',game:'Spielzeit'};
const MODE_TOASTS={down:'Zeiteingabe: Uhr ab (Restzeit)',up:'Zeiteingabe: Uhr auf (Hallenuhr, pro Drittel ab 0:00)',game:'Zeiteingabe: Spielzeit (wie im Spielbericht, 0:00 bis 60:00)'};
function timeMode(){return L.normalizeTimeMode(state.meta&&state.meta.timeMode);}
function gameMode(){return timeMode()==='game';}
function hallUp(){return timeMode()==='up';}
function gameTime(){return gameMode()&&draft?L.elapsedToClock(draft.rawTime):null;}
function hallTime(){return hallUp()&&draft?L.upToClock(draft.rawTime):null;}
// Display of the clock the operator actually reads (hall clock up -> elapsed in the period).
function dispClock(e){return hallUp()?L.upDigits(e):L.clockDigits(e);}
function dispClockLabel(e){return hallUp()?L.upLabel(e):L.clockLabel(e);}
function setTimeMode(mode){state.meta.timeMode=L.normalizeTimeMode(mode);commit(MODE_TOASTS[timeMode()]);}
function nextTimeMode(){const m=L.TIME_MODES;return m[(m.indexOf(timeMode())+1)%m.length];}
function setCurrentPeriod(period){
  const valid=L.normalizePeriod(period);if(!valid||state.currentPeriod===valid)return;
  state.currentPeriod=valid;commit();
}
function setDraftPeriod(period){
  if(!draft||saving||advancing)return;
  draft.period=L.normalizePeriod(period);chronologyApproval=null;periodPickerOpen=false;
  // Initial choice also establishes the live period. Subsequent per-event changes are local only.
  if(!draft.id&&!state.currentPeriod)setCurrentPeriod(draft.period);
  renderWizard();
}
function showScreen(id){document.querySelectorAll('.screen').forEach(n=>n.classList.toggle('active',n.id===id));document.querySelectorAll('.tab').forEach(n=>n.classList.toggle('active',n.dataset.screen===id));if(id==='report')renderReport();window.scrollTo(0,0);if(id==='game'&&!state.meta.operatorPrompted)openOperator();}
function openOperator(){
  $('operator-name').value=state.meta.operatorName||'';
  $('operator-later').textContent=state.meta.operatorName?'Abbrechen':'Sp\u00e4ter';
  if(!$('operator-dialog').open)$('operator-dialog').showModal();
}
function closeOperator(save){
  if(save)state.meta.operatorName=$('operator-name').value.replace(/[\r\n\t]+/g,' ').trim().slice(0,100);
  state.meta.operatorPrompted=true;
  $('operator-dialog').close();commit(save?'Bediener gespeichert':null);
}
function renderTeams(){
  const marked=['home','away'].reduce((n,side)=>n+state[side].players.filter(p=>p.check&&p.check.length).length,0);
  $('teams').innerHTML=(marked?`<p class="check-hint" role="status"><b>${marked} ${marked===1?'Name':'Namen'} bitte pr\u00fcfen</b> (gelb markiert). Mit \u270e \u00f6ffnen und speichern.</p>`:'')+['home','away'].map(side=>{
    const team=state[side],players=team.players.slice().sort((a,b)=>Number(a.number)-Number(b.number)),start=L.getStartGoalie(team);
    const goalies=players.filter(p=>p.isGoalie);
    return `<div class="team-panel ${side}"><div class="team-title"><input data-team-name="${side}" value="${esc(team.name)}" maxlength="100" aria-label="${side==='home'?'Heim':'Gast'} Mannschaftsname"><span>${players.length} Spieler</span></div>
      ${players.length?players.map(p=>`<div class="player-row${p.check&&p.check.length?' needs-check':''}"><strong>${esc(p.number)}</strong><span>${esc(p.name||'Spieler #'+p.number)}${p.check&&p.check.length?`<small class="check-reason">${esc(p.check.join(' \u00b7 '))}</small>`:''}</span><small class="${p.isGoalie?'role-chip'+(p.number===start?' starter':''):'hidden'}">${p.number===start?'TW \u00b7 Start':'TW'}</small><button type="button" data-action="edit-player" data-side="${side}" data-id="${esc(p.id)}" aria-label="Spieler ${esc(p.number)} bearbeiten">\u270e</button></div>`).join(''):'<div class="empty">Noch keine Spieler erfasst</div>'}
      ${goalies.length?`<label class="goalie-setting">Starting-Goalie<select data-start-goalie="${side}" aria-label="Starting-Goalie ${esc(team.name)}"><option value="">Nicht festgelegt</option>${goalies.map(p=>`<option value="${esc(p.number)}" ${p.number===start?'selected':''}>#${esc(p.number)} ${esc(p.name)}</option>`).join('')}</select></label>`:''}
      <div class="player-add"><input id="new-number-${side}" type="text" inputmode="numeric" maxlength="2" placeholder="Nr." aria-label="Neue Trikotnummer" autocomplete="off"><input id="new-name-${side}" type="text" placeholder="Name (optional)" maxlength="100" aria-label="Neuer Spielername" autocomplete="off"><button type="button" data-action="add-player" data-side="${side}" aria-label="Spieler hinzuf\u00fcgen">+</button></div></div>`;
  }).join('');
}
/* 2.0: period results and shootout, shared by report, print and text. */
function periodLine(){return L.periodScores(state).map(p=>p.home+':'+p.away).join(' \u00b7 ');}
function shootoutList(){return (state.shootout||[]).slice().sort((a,b)=>a.order-b.order);}
function shootoutLabel(a){return a.player?L.playerLabel(state,a.team,a.player):'ohne Nummer';}
function shootoutTable(cls){
  const list=shootoutList();if(!list.length)return '';const so=L.shootoutResult(state);
  return `<div class="${cls}-shootout"><h3>Penaltyschie\u00dfen ${so.home}:${so.away}${so.winner?' \u00b7 Sieger '+esc(sideName(so.winner))+' (+1 Tor)':''}</h3><table><thead><tr><th>#</th><th>Team</th><th>Sch\u00fctze</th><th>Ergebnis</th></tr></thead><tbody>${list.map((a,i)=>`<tr class="shootout-row ${a.team} ${a.scored?'scored':'missed'}"><td>${i+1}</td><td>${esc(sideName(a.team))}</td><td>${esc(shootoutLabel(a))}</td><td>${a.scored?'Treffer':'kein Treffer'}</td></tr>`).join('')}</tbody></table></div>`;
}
function renderScore(){
  const score=L.score(state);
  document.querySelector('.score-colon').innerHTML=L.shootoutResult(state).winner?':<small class="np">n.P.</small>':':';
  $('open-shootout').classList.toggle('hidden',!(state.currentPeriod===3||(state.shootout||[]).length));
  ['home','away'].forEach(side=>{
    $('score-'+side).textContent=score[side];$('score-'+side+'-name').textContent=sideName(side);
    {const l=teamLogo(side),img=$('score-'+side+'-logo');img.classList.toggle('hidden',!l);if(l){if(img.getAttribute('src')!==l.src)img.src=l.src;}else img.removeAttribute('src');}
    const current=L.goalieAt(state,side,{period:3,time:'0:00',order:Number.MAX_SAFE_INTEGER});
    $(side+'-goalie').textContent=current?'Im Tor: '+L.playerLabel(state,side,current):'';
  });
}
function renderEvents(){
  // 1.5: last entered event on top (also Nachtraege). Report and print stay chronological.
  const events=L.sortedEventsByEntryDesc(state.events);
  $('event-count').textContent=events.length?events.length+' Eintr\u00e4ge \u00b7 neueste oben':'';
  $('event-list').innerHTML=events.length?events.map((e,index)=>{
    let details;
    if(e.type==='timeout')details='<small>Timeout genommen</small>';
    else if(e.type==='note')details=`<span class="note-text">${esc(e.text)}</span>`;
    else if(e.type==='penaltyshot')details=`${esc(L.playerLabel(state,e.team,e.player))}<br><small>${e.scored?'Tor (Penalty)':'kein Tor'}</small>`;
    else if(e.type==='goalie')details=`${esc(L.playerLabel(state,e.team,e.goalieOut))}<br><small>\u2192 ${esc(L.playerLabel(state,e.team,e.goalieIn))}</small>`;
    else if(e.type==='penalty')details=`${esc(e.bench?'Bank / Trainer':L.playerLabel(state,e.team,e.player))}<br><small>${esc(L.penaltyDescription(e))}</small>${servedHtml(e)}`;
    else{
      const assists=[e.assist1,e.assist2].filter(n=>n!==''&&n!=null).map(n=>L.playerLabel(state,e.team,n));
      details=esc(L.playerLabel(state,e.team,e.player))+(assists.length?`<br><small>A: ${esc(assists.join(' \u00b7 '))}</small>`:'')+(L.emptyNetGoal(state,e)?'<br><small class="en-mark">Empty Net</small>':'');
    }
    // 1.6: the whole row opens the large detail view; editing happens from there.
    return `<button type="button" class="event-row ${e.type} ${e.team||'general'}${e.type==='penaltyshot'&&e.scored?' scored':''}${index===0?' latest':''}" data-action="show-event" data-id="${esc(e.id)}" aria-label="Ereignis ${esc(dispClock(e))} anzeigen"><span class="event-time">${esc(L.formatGameTime(e))}<span class="event-clock">${esc(dispClock(e))}</span></span><span class="event-body"><span class="event-type">${esc(L.TYPE_LABELS[e.type])} \u00b7 ${esc(sideName(e.team))}</span><span class="event-details">${details}</span></span><span class="event-open" aria-hidden="true">\u203a</span></button>`;
  }).join(''):'<div class="empty">Noch keine Ereignisse.<br>Mit dem Uhrsymbol geht es los.</div>';
  if((state.shootout||[]).length){const so=L.shootoutResult(state);
    $('event-list').insertAdjacentHTML('afterbegin',`<button type="button" class="event-row shootout-card" data-action="open-shootout"><span class="event-time">P<span class="event-clock">${so.home}:${so.away}</span></span><span class="event-body"><span class="event-type">Penaltyschie\u00dfen</span><span class="event-details">${so.attempts} Versuche${so.winner?' \u00b7 Sieger '+esc(sideName(so.winner)):''}</span></span><span class="event-open" aria-hidden="true">\u203a</span></button>`);}
}
function renderReport(){
  const score=L.score(state),events=L.sortedEventsByGameTime(state.events),running=L.runningScores(state);
  $('report-sheet').innerHTML=`<div class="report-brand"><img src="${esc(logoSource())}" alt="${esc(homeClub().name)}"><div><strong>eGrep Notes</strong><small>SPIELNOTIZEN \u00b7 EISHOCKEY</small></div></div><div class="report-meta"><span>${esc(state.meta.date||'Datum offen')}</span><span>Spiel ${esc(state.meta.number||'\u2014')}</span></div><div class="report-match"><span class="rm-logo rm-home">${logoImg('home','report-logo')}</span><strong>${esc(L.scoreLabel(state))}</strong><span class="rm-logo rm-away">${logoImg('away','report-logo')}</span><span class="rm-name rm-home">${esc(sideName('home'))}</span><span class="rm-name rm-away">${esc(sideName('away'))}</span></div><p class="report-periods">Drittel: ${esc(periodLine())}</p>
  ${state.meta.operatorName?`<p class="report-operator">Spielbericht erstellt von: <strong>${esc(state.meta.operatorName)}</strong></p>`:''}
  <table><thead><tr><th>Zeit</th><th>Team</th><th>Ereignis</th></tr></thead><tbody>${events.length?events.map(e=>`<tr class="${e.type} ${e.team||'general'}"><td><span class="time-main">${esc(L.formatGameTime(e))}</span><span class="time-clock">${esc(dispClock(e))}</span></td><td>${esc(sideName(e.team))}</td><td><span class="report-type">${esc(L.TYPE_LABELS[e.type])}${running[e.id]?` <span class="report-score">${esc(running[e.id])}</span>`:''}${L.emptyNetGoal(state,e)?' \u00b7 EN':''}</span>${e.type==='penalty'?penaltyLines(e):esc(L.eventShort(e))+`<div class="print-names event-names">${L.eventNames(state,e).filter(p=>p.label!=='#'+p.number).map(p=>`<span><b>${esc(p.role)}:</b> ${esc(p.label)}</span>`).join('')}</div>`}</td></tr>`).join(''):'<tr><td colspan="3">Noch keine Ereignisse erfasst.</td></tr>'}</tbody></table>${shootoutTable('report')}<p class="report-footer">Spielzeit fortlaufend, Drittel in Klammern. ${gameMode()?'Erfasst als Spielzeit (wie Spielbericht); grau: daraus berechnete Restzeit.':hallUp()?'Uhr lief aufw\u00e4rts; darunter grau: Hallenuhr.':'Darunter grau: urspr\u00fcngliche Uhranzeige.'}<br>Private Spielnotizen \u00b7 kein offizieller Spielbericht \u00b7 eGrep Notes ${L.VERSION} \u00b7 Michael Nowak &amp; KI</p>`;
}
function renderAll(){
  $('game-date').value=state.meta.date||'';$('game-number').value=state.meta.number||'';
  $('save-status').textContent=saveFailed?'Nicht dauerhaft gespeichert':'Lokal gespeichert';$('save-status').classList.toggle('error',saveFailed);
  $('operator-summary').textContent=state.meta.operatorName?'Bediener: '+state.meta.operatorName:'Bediener eintragen';
  $('operator-report-summary').textContent=state.meta.operatorName?'Bediener: '+state.meta.operatorName:'Bedienername eintragen';
  $('undo').disabled=!history.length;renderPeriod();renderTeams();renderScore();renderEvents();renderReport();
}
function showChoice(title,text,label='Best\u00e4tigen',cancel=true,danger=false){
  if(choiceResolver)closeChoice(false);
  $('choice-title').textContent=title;$('choice-text').textContent=text;$('choice-confirm').textContent=label;
  // 1.5 fix: destructive confirmations are visibly different from a normal OK.
  $('choice-confirm').className=danger?'danger danger-confirm':'primary';$('choice-cancel').classList.toggle('hidden',!cancel);
  $('choice-confirm').classList.toggle('full-row',!cancel);$('choice-dialog').showModal();
  return new Promise(resolve=>{choiceResolver=resolve;});
}
function closeChoice(value){if($('choice-dialog').open)$('choice-dialog').close();const resolve=choiceResolver;choiceResolver=null;if(resolve)resolve(value);}
async function addPlayer(side){
  const number=L.normalizeNumber($('new-number-'+side).value),name=$('new-name-'+side).value.trim();
  if(number==='')return toast('Bitte eine Trikotnummer von 0 bis 99 eingeben');
  if(L.hasDuplicateNumber(state[side],number))return showChoice('Nummer bereits vorhanden','#'+number+' steht bereits in der Aufstellung von '+sideName(side)+'.','OK',false);
  snapshot();L.appendPlayer(state[side],number,name);commit('Spieler #'+number+' hinzugef\u00fcgt');$('new-number-'+side).focus();
}
function openPlayer(side,id){
  const p=state[side].players.find(p=>p.id===id);if(!p)return;
  editingPlayer={side,id};$('player-dialog-title').textContent='Spieler bearbeiten';$('player-number').value=p.number;
  $('player-name').value=p.name||'';$('player-goalie').checked=!!p.isGoalie;$('player-starter').checked=L.getStartGoalie(state[side])===p.number;
  $('player-starter').disabled=!p.isGoalie;$('player-dialog').showModal();
}
async function savePlayer(ev){
  ev.preventDefault();if(!editingPlayer)return;
  const {side,id}=editingPlayer,number=L.normalizeNumber($('player-number').value),name=$('player-name').value.trim();
  if(number==='')return toast('Trikotnummer von 0 bis 99 eingeben');
  if(L.hasDuplicateNumber(state[side],number,id))return showChoice('Nummer bereits vorhanden','Diese Trikotnummer ist in der Mannschaft schon vergeben.','OK',false);
  snapshot();const p=state[side].players.find(p=>p.id===id),wasStart=L.getStartGoalie(state[side])===p.number;
  p.number=number;p.name=name;p.isGoalie=$('player-goalie').checked;delete p.check;p.starter=p.isGoalie&&$('player-starter').checked;
  if(wasStart)state[side].startGoalie='';
  if(p.starter){state[side].players.forEach(other=>{if(other.id!==id)other.starter=false;});state[side].startGoalie=number;}
  $('player-dialog').close();commit('Spieler gespeichert');
}
async function deletePlayer(){
  if(!editingPlayer)return;const {side,id}=editingPlayer,p=state[side].players.find(p=>p.id===id);if(!p)return;
  if(!await showChoice('Spieler l\u00f6schen?',L.playerLabel(state,side,p.number)+' wird aus der Aufstellung entfernt.','L\u00f6schen',true,true))return;
  snapshot();if(state[side].startGoalie===p.number)state[side].startGoalie='';state[side].players=state[side].players.filter(p=>p.id!==id);
  $('player-dialog').close();commit('Spieler gel\u00f6scht');
}
// 3.2: while editing, the original entry stays visible ("Bisher: ...") and its choices are marked.
let editOriginal=null;
function previousText(e){
  if(!e)return '';const who=e.type==='note'&&!e.team?'Allgemein':sideName(e.team);
  const nums=e.type==='goal'?[e.player,e.assist1,e.assist2].filter(Boolean).map((n,i)=>(i?'A ':'')+'#'+n).join(', '):e.type==='penalty'?(e.bench?'Bank':'#'+e.player)+', '+e.penalty+', '+L.penaltyDurationLabel(e):L.eventShort(e);
  return [L.formatGameTime(e),L.TYPE_LABELS[e.type],who,nums].filter(Boolean).join(' \u00b7 ');
}
function markPrevious(){
  // Marks the choices of the saved entry with "bisher" (type, team, numbers, penalty, duration).
  const o=editOriginal,root=$('wizard-content');if(!o||!root)return;
  const tag=(b)=>{if(!b||b.classList.contains('previous'))return;b.classList.add('previous');if(b.hasAttribute('data-pick-number')||b.hasAttribute('data-served-number')||b.hasAttribute('data-duration'))return;const t=document.createElement('em');t.className='prev-badge';t.textContent='bisher';b.appendChild(t);};
  const q=(attr,val)=>{if(val==null||val==='')return;root.querySelectorAll('['+attr+']').forEach(b=>{if(b.getAttribute(attr)===String(val))tag(b);});};
  q('data-type',o.type);q('data-team',o.type==='note'&&!o.team?'none':o.team);
  if(o.type==='penalty'){q('data-penalty',o.penalty);q('data-duration',o.penaltyDuration);if(o.bench)q('data-action','bench-penalty');}
  [o.player,o.assist1,o.assist2].forEach(n=>q('data-pick-number',n));
  if(o.servedBy)q('data-served-number',o.servedBy);
}
function newEvent(id){
  const existing=id&&state.events.find(e=>e.id===id);editOriginal=existing?JSON.parse(JSON.stringify(existing)):null;
  draft=existing?Object.assign({},existing,{rawTime:gameMode()?L.elapsedDigits(existing):hallUp()?L.upDigits(existing):L.clockDigits(existing)}):{id:null,order:nextOrder(),period:state.currentPeriod,rawTime:'',time:'',team:null,type:null,player:'',assist1:'',assist2:'',penalty:'',penaltyDuration:'2',bench:false,goalieOut:'',goalieIn:''};
  trail=[];stage='time';numericField='player';replaceOnDigit=!!draft.rawTime;saving=false;
  advancing=false;periodPickerOpen=!gameMode()&&!draft.period;chronologyApproval=null;
  $('wizard').showModal();renderWizard();
}
function stageField(){return stage==='time'?'rawTime':stage==='goalie'?numericField:stage;}
function goTo(next,push=true){if(push)trail.push(stage);stage=next;replaceOnDigit=!!draft[stageField()];renderWizard();}
function wizardError(text){$('wizard-error').textContent=text;}
function rawClock(raw){if(!raw)return '\u2014 : \u2014';const n=raw.padStart(3,'0');return n.slice(0,-2).padStart(2,'0')+':'+n.slice(-2);}
function keypad(label,disabled=false){return `<div class="keypad" aria-label="Zifferntastatur">${['1','2','3','4','5','6','7','8','9'].map(n=>`<button type="button" data-digit="${n}">${n}</button>`).join('')}<button type="button" class="erase" data-action="erase" aria-label="Letzte Ziffer l\u00f6schen">\u232b</button><button type="button" data-digit="0">0</button><button type="button" class="next" data-action="next" ${disabled?'disabled':''}>${label}</button></div>`;}
function durationSelector(){
  const current=L.normalizePenaltyDuration(draft.penaltyDuration);
  return `<div class="penalty-duration penalty-duration-5" role="group" aria-label="Strafma\u00df">${L.PENALTY_DURATIONS.map(p=>`<button type="button" data-duration="${p.value}" aria-pressed="${current===p.value}" class="${current===p.value?'active':''}">${esc(p.label)}</button>`).join('')}</div>${!current?'<p class="duration-unknown">Bisher kein Strafma\u00df erfasst. Auswahl erg\u00e4nzen oder unver\u00e4ndert lassen.</p>':''}`;
}
function setPenaltyDuration(value){
  if(!draft||saving||draft.type!=='penalty')return;
  const valid=L.normalizePenaltyDuration(value);if(!valid)return;
  draft.penaltyDuration=valid;
  // Do not rebuild the text input: changing duration must not dismiss its keyboard.
  document.querySelectorAll('[data-duration]').forEach(b=>{
    const active=b.dataset.duration===valid;
    b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));
  });
  const note=document.querySelector('.duration-unknown');if(note)note.remove();
  const mis=document.querySelector('.misconduct-btn');if(mis)mis.classList.toggle('hidden',valid!=='10');
}
// 2.9: who serves a goalie or bench penalty (shown in history).
function servedHtml(e){if(e.type!=='penalty')return '';if(e.servedBy)return `<br><small class="served">Abgesessen von ${esc(L.playerLabel(state,e.team,e.servedBy))}</small>`;return e.servedLater?'<br><small class="served open">Absitzender offen</small>':'';}
// Penalty chosen: goalie or bench penalties ask who serves it, everything else saves directly.
function finishPenalty(){if(!draft||saving)return;if(L.needsServer(state,candidateFromDraft()))return goTo(state[draft.team].players.some(p=>!p.isGoalie)?'served':'servedBy');return saveDraft();}
function participantHint(number){if(number===L.EMPTY_NET)return 'Leeres Tor';const p=draft.team&&L.playerByNumber(state,draft.team,L.normalizeNumber(number));return p&&p.name?p.name:number?'Spieler #'+number:'';}
function renderWizard(){
  if(!draft)return;wizardError('');
  $('wizard').classList.toggle('period-expanded',stage==='time'&&periodPickerOpen);
  $('wizard').classList.toggle('editing',!!draft.id);
  $('wizard').classList.toggle('penalty-stage',stage==='penalty'||stage==='customPenalty');
  $('wizard').classList.toggle('penalty-home',draft.type==='penalty'&&draft.team==='home');
  $('wizard').classList.toggle('penalty-away',draft.type==='penalty'&&draft.team==='away');
  const context=[draft.time&&L.formatGameTime(draft),draft.type&&L.TYPE_LABELS[draft.type],draft.team&&sideName(draft.team)].filter(Boolean).join(' \u00b7 ');
  $('wizard-context').textContent=editOriginal?'Bisher: '+previousText(editOriginal):(context||'Neues Ereignis');$('wizard-context').classList.toggle('previous-context',!!editOriginal);$('wizard-back').disabled=!trail.length;
  let html='',title='';
  if(stage==='time'&&gameMode()){
    const up=gameTime();if(up)draft.period=up.period;
    title=up?'Spielzeit \u00b7 '+up.period+'. Drittel':'Spielzeit eingeben';
    html=`<div class="time-period-line"><p class="wizard-hint">Spielzeit wie im Spielbericht, z. B. <b>2713</b> = 27:13.</p><span class="clock-mode-badge">Spielzeit</span></div>
      <div class="number-display" aria-live="polite">${esc(rawClock(draft.rawTime))}</div><div class="number-hint ${draft.rawTime&&!up?'unknown':''}">${draft.rawTime&&!up?'Spielzeit ung\u00fcltig (max. 60:00)':up?esc(up.period+'. Drittel \u00b7 Uhr '+up.time):'Gespielte Zeit eingeben (0:00 bis 60:00)'}</div>${keypad('Weiter',!up)}${draft.id?'<div class="edit-extra"><button type="button" class="danger" data-action="delete-event">L\u00f6schen</button><button type="button" class="secondary" data-action="save-existing">Direkt speichern</button></div>':''}`;
  }else if(stage==='time'){
    const hu=hallUp(),hall=hallTime(),word=hu?'Uhr aufw\u00e4rts':'Restzeit';
    title=draft.period?word+' \u00b7 '+draft.period+'. Drittel':word+' eingeben';
    const valid=hu?(hall&&hall.time):L.normalizeTime(draft.rawTime);
    const scope=(draft.id||state.currentPeriod)?'\u00c4nderung gilt nur f\u00fcr diesen Eintrag.':'Einmal w\u00e4hlen; bleibt f\u00fcr neue Ereignisse eingestellt.';
    html=`<div class="time-period-line"><p class="wizard-hint">${hu?'Hallenuhr l\u00e4uft aufw\u00e4rts, z. B. <b>512</b> = 5:12.':'Uhranzeige, z. B. <b>1012</b>.'}</p>${hu?'<span class="clock-mode-badge">Uhr auf</span>':''}${draft.period?`<button type="button" class="period-change" data-action="toggle-period" aria-expanded="${periodPickerOpen}">Drittel ${periodPickerOpen?'schlie\u00dfen':'\u00e4ndern'}</button>`:''}</div>
      ${periodPickerOpen?`<div class="period-selector event-period-selector" role="group" aria-label="Drittel dieses Ereignisses">${[1,2,3].map(p=>`<button type="button" data-period="${p}" class="${draft.period===p?'active':''}" aria-pressed="${draft.period===p}">${p}. Drittel</button>`).join('')}</div><p class="period-scope">${scope}</p>`:''}
      <div class="number-display" aria-live="polite">${esc(rawClock(draft.rawTime))}</div><div class="number-hint ${draft.rawTime&&!valid?'unknown':''}">${draft.rawTime&&!valid?'Uhrzeit ung\u00fcltig (max. 20:00)':valid&&draft.period?'Spielzeit '+esc(L.formatGameTime({time:valid,period:draft.period})):!draft.period?'Bitte einmal das Drittel w\u00e4hlen':(hu?'Angezeigte Zeit der Hallenuhr eingeben':'Restzeit auf der Spieluhr eingeben')}</div>${keypad('Weiter',!valid||!draft.period)}${draft.id?'<div class="edit-extra"><button type="button" class="danger" data-action="delete-event">L\u00f6schen</button><button type="button" class="secondary" data-action="save-existing">Direkt speichern</button></div>':''}`;
  }else if(stage==='team'){
    title='Welche Mannschaft?';
    html=`<p class="wizard-hint">${draft.type==='penaltyshot'?'Welche Mannschaft schie\u00dft den Penalty?':esc(L.TYPE_LABELS[draft.type]||'')+' f\u00fcr welche Mannschaft?'}</p><div class="choice-grid team-grid">${['home','away'].map(side=>`<button type="button" class="team-choice ${side}" data-team="${side}">${logoImg(side,'choice-logo')||`<span class="team-initial">${side==='home'?'H':'G'}</span>`}<span>${esc(sideName(side))}<small>${side==='home'?'Heimmannschaft':'Gastmannschaft'}</small></span></button>`).join('')}${draft.type==='note'?'<button type="button" class="team-choice general" data-team="none"><span class="team-initial">\u2013</span><span>Allgemein<small>Keiner Mannschaft zugeordnet</small></span></button>':''}</div>`;
  }else if(stage==='type'){
    title='Was ist passiert?';
    // 1.6: one row per event type; colour by type (team is chosen afterwards).
    html=`<div class="choice-grid type-grid"><button type="button" class="type-choice goal" data-type="goal"><span class="type-symbol">\u25ce</span><span>Tor<small>Sch\u00fctze und Assists</small></span></button><button type="button" class="type-choice penalty" data-type="penalty"><span class="type-symbol">!</span><span>Strafe<small>Spieler und Strafart</small></span></button><button type="button" class="type-choice goalie" data-type="goalie"><span class="type-symbol">\u21c4</span><span>Torwart\u00adwechsel<small>Raus und rein</small></span></button><button type="button" class="type-choice timeout" data-type="timeout"><span class="type-symbol timeout-symbol">TO</span><span>Timeout<small>Einer pro Mannschaft</small></span></button><button type="button" class="type-choice penaltyshot" data-type="penaltyshot"><span class="type-symbol">P</span><span>Penalty<small>Strafschuss im Spiel</small></span></button><button type="button" class="type-choice note" data-type="note"><span class="type-symbol">\u270e</span><span>Notiz<small>Freier Text</small></span></button></div>`;
  }else if(stage==='note'){
    title='Notiz';
    html=`<div class="custom-penalty note-entry"><label>Text<textarea id="note-text" maxlength="${L.NOTE_MAX}" rows="4" enterkeyhint="done" placeholder="z. B. Schiri-Ansage, Verletzung, Spielunterbrechung" autocomplete="off">${esc(draft.text||'')}</textarea></label><button class="primary full" data-action="save-note" type="button">Notiz speichern</button></div>`;
  }else if(stage==='psresult'){
    title='Penalty verwandelt?';
    html=`<p class="wizard-summary">Sch\u00fctze ${esc(L.playerLabel(state,draft.team,draft.player))} \u00b7 ${esc(sideName(draft.team))}</p><div class="shootout-result ps-result"><button type="button" class="primary scored-btn" data-action="ps-scored">Tor</button><button type="button" class="secondary" data-action="ps-missed">Kein Tor</button></div><p class="wizard-hint">Ein verwandelter Penalty z\u00e4hlt als Tor.</p>`;
  }else if(['player','assist1','assist2'].includes(stage)){
    title=stage==='player'?(draft.type==='goal'?'Wer hat getroffen?':draft.type==='penaltyshot'?'Wer schie\u00dft?':'Welcher Spieler?'):stage==='assist1'?'Erster Assist':'Zweiter Assist';
    const number=draft[stage]||'',p=L.playerByNumber(state,draft.team,L.normalizeNumber(number));
    const noList=!state[draft.team].players.length;
    const hint=participantHint(number);
    // 1.5: identical slots in every number stage (summary, display, keypad, bottom button), so nothing jumps.
    const summaryText=stage!=='player'?'Tor: '+L.playerLabel(state,draft.team,draft.player)+(draft.assist1&&stage==='assist2'?' \u00b7 A1: '+L.playerLabel(state,draft.team,draft.assist1):'')
      :(draft.type==='goal'?'Torsch\u00fctze':draft.type==='penaltyshot'?'Penalty-Sch\u00fctze':'Spieler mit Strafe')+' \u00b7 '+sideName(draft.team);
    const bottom=stage==='assist1'?'<button class="skip-button" data-action="skip-assists" type="button">Ohne Assists speichern</button>':stage==='assist2'?'<button class="skip-button" data-action="skip-assists" type="button">Ohne 2. Assist speichern</button>':draft.type==='penalty'?'<button class="skip-button" data-action="bench-penalty" type="button">Bank / Trainer statt Spielernummer</button>':'<span class="skip-placeholder" aria-hidden="true"></span>';
    html=`<p class="wizard-summary">${esc(summaryText)}</p><div class="number-display" aria-live="polite">${number?'#'+esc(number):'Nr.'}</div><div class="number-hint ${number&&!p&&!noList?'unknown':''}">${esc(hint)}${number&&!p&&!noList?' \u00b7 nicht in Aufstellung':''}</div>${keypad(stage==='assist2'?'Speichern':'Weiter',!number)}<div class="wizard-bottom">${bottom}</div>`;
  }else if(stage==='penalty'){
    title='Welche Strafe?';
    // 2.1: one scrollable list sorted by frequency; referee signals optional (per device).
    const signs=showSigns(),pics=window.EGREP_SIGNS||{};
    html=durationSelector()+`<div class="penalty-intro"><p class="wizard-hint">${esc(draft.bench?'Bank / Trainer':L.playerLabel(state,draft.team,draft.player))} \u00b7 Strafart antippen.</p><button type="button" class="signs-toggle${signs?' active':''}" data-action="toggle-signs" aria-pressed="${signs}">Schiri-Zeichen</button>${draft.id&&draft.penalty?'<button type="button" class="secondary" data-action="save-existing">Speichern</button>':''}</div><button type="button" class="misconduct-btn primary full ${L.normalizePenaltyDuration(draft.penaltyDuration)==='10'?'':'hidden'}" data-action="misconduct">Disziplinarstrafe (10 Min.) speichern</button><div class="penalty-list${signs?' with-signs':''}" role="group" aria-label="Strafarten">${L.PENALTIES.slice(0,-1).map(p=>`<button type="button" class="penalty-item${draft.penalty===p?' selected':''}" data-penalty="${esc(p)}">${signs?(pics[p]?`<img src="${pics[p]}" alt="" loading="lazy">`:'<span class="no-sign">kein Zeichen</span>'):''}<span>${esc(p)}</span></button>`).join('')}<button class="penalty-item custom" data-action="custom-penalty" type="button"><span>Sonstige / eigener Text</span></button></div>`;
  }else if(stage==='served'){
    title='Wer sitzt die Strafe ab?';
    const who=draft.bench?'Bankstrafe':L.playerLabel(state,draft.team,draft.player)+' (Torwart)';
    const players=state[draft.team].players.filter(p=>!p.isGoalie&&L.normalizeNumber(p.number)!==L.normalizeNumber(draft.player)).sort((a,b)=>Number(a.number)-Number(b.number));
    html=`<p class="wizard-summary pick-summary">${esc(who+' \u00b7 '+draft.penalty+' \u00b7 '+L.penaltyDurationLabel(draft))}</p><div class="pick-grid ${draft.team}" role="group" aria-label="Feldspieler">${players.map(p=>{const sel=L.normalizeNumber(p.number)===L.normalizeNumber(draft.servedBy);
      return `<button type="button" class="pick-btn${sel?' selected':''}" data-served-number="${esc(p.number)}" aria-pressed="${sel}"><strong>${esc(p.number)}</strong><small>${esc(String(p.name||'').split(',')[0].trim())}</small></button>`;}).join('')}</div>
      <div class="pick-actions"><button type="button" class="secondary" data-action="served-other">Andere Nummer</button><button type="button" class="secondary" data-action="served-later">Sp\u00e4ter eintragen</button></div>`;
  }else if(stage==='servedBy'){
    title='Wer sitzt die Strafe ab?';
    const number=draft.servedBy||'',p=L.playerByNumber(state,draft.team,L.normalizeNumber(number));
    const noList=!state[draft.team].players.length,who=draft.bench?'Bankstrafe':L.playerLabel(state,draft.team,draft.player)+' (Torwart)';
    html=`<p class="wizard-summary">${esc(who+' \u00b7 Absitzender')}</p><div class="number-display" aria-live="polite">${number?'#'+esc(number):'Nr.'}</div><div class="number-hint ${number&&!p&&!noList?'unknown':''}">${esc(participantHint(number))}${number&&!p&&!noList?' \u00b7 nicht in Aufstellung':''}</div>${keypad('Speichern',!number)}<div class="wizard-bottom"><button class="skip-button" data-action="served-later" type="button">Sp\u00e4ter eintragen</button></div>`;
  }else if(stage==='customPenalty'){
    title='Strafe selbst eingeben';
    html=durationSelector()+`<div class="custom-penalty"><label>Bezeichnung<input id="custom-penalty" type="text" maxlength="160" enterkeyhint="done" placeholder="z. B. genaue Ansage des Schiris" value="${esc(draft.penalty||'')}" autocomplete="off"></label><button class="primary full" data-action="save-custom" type="button">Strafe speichern</button></div>`;
  }else if(stage==='pick'){
    const goal=draft.type==='goal',list=picks(),roles=['T','A1','A2'];
    const ps=draft.type==='penaltyshot';
    title=goal?'Torsch\u00fctze und Assists':ps?'Wer schie\u00dft?':'Welcher Spieler?';
    const summary=ps?'Penalty-Sch\u00fctze \u00b7 '+sideName(draft.team):goal?(list.length?list.map((n,i)=>roles[i]+' #'+n).join(' \u00b7 '):'Erst Torsch\u00fctze, dann bis zu zwei Assists antippen'):'Spieler mit Strafe \u00b7 '+sideName(draft.team);
    const players=state[draft.team].players.slice().sort((a,b)=>Number(a.number)-Number(b.number));
    html=`<p class="wizard-summary pick-summary">${esc(summary)}</p><div class="pick-grid ${draft.team}" role="group" aria-label="Gemeldete Spieler">${players.map(p=>{
      const at=list.indexOf(String(p.number)),surname=String(p.name||'').split(',')[0].trim();
      return `<button type="button" class="pick-btn${at>=0?' selected':''}" data-pick-number="${esc(p.number)}" aria-pressed="${at>=0}">${p.isGoalie?'<span class="pick-tw">TW</span>':''}${at>=0?`<span class="pick-role">${roles[at]}</span>`:''}<strong>${esc(p.number)}</strong><small>${esc(surname)}</small></button>`;}).join('')}</div>
      <div class="pick-actions"><button type="button" class="secondary" data-action="other-number">Andere Nummer</button>${goal?`<button type="button" class="primary" data-action="pick-save" ${list.length?'':'disabled'}>OK</button>`:ps?'':'<button type="button" class="secondary" data-action="bench-penalty">Bank / Trainer</button>'}</div>`;
  }else if(stage==='goalie'){
    title='Torwartwechsel';
    const goalies=state[draft.team].players.filter(p=>p.isGoalie&&(numericField==='goalieOut'||p.number!==draft.goalieOut));
    html=`<p class="wizard-hint">${numericField==='goalieOut'?'Welcher Torwart geht raus?':'Wer kommt ins Tor? Vorschl\u00e4ge sind \u00e4nderbar.'}</p><div class="goalie-fields">${[['goalieOut','Raus'],['goalieIn','Rein']].map(([field,label])=>`<button type="button" class="goalie-field ${numericField===field?'active':''}" data-goalie-field="${field}"><small>${label}</small><strong>${draft[field]===L.EMPTY_NET?'leer':draft[field]?'#'+esc(draft[field]):'\u2014'}</strong><span>${esc(participantHint(draft[field]||''))||'Nummer eingeben'}</span></button>`).join('')}</div><div class="goalie-options"><button type="button" class="empty-net" data-goalie-number="${L.EMPTY_NET}">Leeres Tor</button>${goalies.map(p=>`<button type="button" data-goalie-number="${esc(p.number)}">#${esc(p.number)} ${esc(p.name)}</button>`).join('')}</div>${keypad(numericField==='goalieOut'?'Weiter':'Speichern',!draft[numericField])}`;
  }
  $('wizard-title').textContent=title;$('wizard-content').innerHTML=html;$('wizard-content').scrollTop=0;markPrevious();
  if(stage==='customPenalty')setTimeout(()=>{const n=$('custom-penalty');if(n)n.focus();},50);
  if(stage==='note')setTimeout(()=>{const n=$('note-text');if(n)n.focus();},50);
}
function enterDigit(n){
  if(!draft||saving||advancing||!['time','player','assist1','assist2','goalie','servedBy'].includes(stage))return;
  const field=stageField(),limit=stage==='time'?4:2;
  if(replaceOnDigit){draft[field]='';replaceOnDigit=false;}
  if(String(draft[field]||'').length<limit)draft[field]=String(draft[field]||'')+n;
  if(stage==='goalie')draft.goalieTouched=true;
  renderWizard();
}
function eraseDigit(){if(!draft||saving||advancing)return;const field=stageField();draft[field]=draft[field]===L.EMPTY_NET?'':String(draft[field]||'').slice(0,-1);replaceOnDigit=false;renderWizard();}
function candidateFromDraft(){
  const up=gameTime(),hall=hallTime();
  const e=Object.assign({},draft,up?{time:up.time,clock:up.clock,period:up.period}:hall?{time:hall.time,clock:hall.clock,period:Number(draft.period)}:{time:L.normalizeTime(draft.rawTime),clock:draft.rawTime,period:Number(draft.period)});
  ['player','assist1','assist2'].forEach(f=>e[f]=L.normalizeNumber(e[f]));['goalieOut','goalieIn'].forEach(f=>e[f]=L.normalizeGoalie(e[f]));
  if(e.type!=='goal'){e.assist1='';e.assist2='';}
  if(e.type!=='penalty'){e.penalty='';e.bench=false;e.penaltyDuration='';}else e.penaltyDuration=L.normalizePenaltyDuration(e.penaltyDuration);
  if(e.type!=='goalie'){e.goalieOut='';e.goalieIn='';}else e.player='';
  if(e.type==='timeout')e.player='';
  if(e.bench)e.player='';
  e.servedBy=L.normalizeNumber(e.servedBy||'');e.servedLater=!!e.servedLater&&!e.servedBy;
  if(!L.needsServer(state,e)){e.servedBy='';e.servedLater=false;}
  delete e.rawTime;delete e.goalieTouched;return e;
}
function reviewKey(candidate,issue){
  return issue?[candidate.period,L.normalizeTime(candidate.time),issue.relation,issue.event.id,
    issue.event.period,L.normalizeTime(issue.event.time)].join('|'):null;
}
function closeTimeJump(value){
  if($('time-jump-dialog').open)$('time-jump-dialog').close();
  const resolve=jumpResolver;jumpResolver=null;if(resolve)resolve(value);
}
function askTimeJump(candidate,issue){
  const next=Number(candidate.period)+1;
  const canAdvance=!gameMode()&&candidate.period===state.currentPeriod&&next<=3&&!state.events.some(e=>Number(e.period)>Number(candidate.period));
  $('time-jump-title').textContent=canAdvance?'Neues Drittel oder Nachtrag?':'Fr\u00fcheres Ereignis nachtragen?';
  $('time-jump-text').textContent=gameMode()?'Zuletzt im '+candidate.period+'. Drittel: Spielzeit '+L.formatGameTime(issue.event)+
    '. Jetzt eingegeben: '+L.formatGameTime(candidate)+'.\nDie Spielzeit liegt vor dem bisherigen letzten Eintrag.':hallUp()?'Zuletzt im '+candidate.period+'. Drittel: Uhr '+L.upLabel(issue.event)+
    '. Jetzt eingegeben: '+L.upLabel(candidate)+'.\nDie Uhrzeit ist kleiner als beim bisherigen letzten Eintrag (Uhr l\u00e4uft aufw\u00e4rts).':'Zuletzt im '+candidate.period+'. Drittel: Uhr '+issue.event.time+
    '. Jetzt eingegeben: '+candidate.time+'.\nDie Restzeit ist h\u00f6her als beim bisherigen letzten Eintrag.';
  $('time-jump-next').textContent=next+'. Drittel beginnen';$('time-jump-next').classList.toggle('hidden',!canAdvance);
  $('time-jump-retro').textContent='Nachtrag im '+candidate.period+'. Drittel';
  $('time-jump-dialog').showModal();
  return new Promise(resolve=>{jumpResolver=resolve;});
}
async function reviewNewEventTime(){
  if(!draft||draft.id)return true;
  const original=draft,candidate=candidateFromDraft(),issue=L.clockJumpIssue(candidate,state.events);
  const chronological=L.chronologyIssue(candidate,state.events);
  if(!issue||chronologyApproval===reviewKey(candidate,chronological))return true;
  const action=await askTimeJump(candidate,issue);
  if(draft!==original||!action)return false;
  if(action==='next'){
    draft.period=Number(draft.period)+1;chronologyApproval=null;setCurrentPeriod(draft.period);
  }else if(action==='retro'){
    // This exact time has already been acknowledged; avoid a second identical warning at save.
    chronologyApproval=reviewKey(candidate,chronological);
  }
  return true;
}
async function nextStep(){
  if(!draft||saving||advancing)return;
  if(stage==='time'){
    const up=gameTime();
    if(gameMode()&&!up)return wizardError('Bitte eine g\u00fcltige Spielzeit eingeben (max. 60:00).');
    const hall=hallTime(),time=up?up.time:hallUp()?(hall&&hall.time):L.normalizeTime(draft.rawTime);if(up)draft.period=up.period;
    if(!draft.period||!time)return wizardError(hallUp()?'Bitte Drittel und eine g\u00fcltige Uhrzeit eingeben (max. 20:00).':'Bitte Drittel und eine g\u00fcltige Restzeit eingeben.');
    draft.time=time;advancing=true;
    try{if(await reviewNewEventTime()){
      // Uhr auf: the period follows the entered time; keep the game screen in step for new events.
      if(up&&!draft.id&&(!state.currentPeriod||up.period>state.currentPeriod))setCurrentPeriod(up.period);
      goTo('type');}}finally{advancing=false;}
  }else if(stage==='player'){
    const number=L.normalizeNumber(draft.player);if(number==='')return wizardError('Bitte eine Spielernummer eingeben.');draft.player=number;
    goTo(draft.type==='goal'?'assist1':draft.type==='penaltyshot'?'psresult':'penalty');
  }else if(stage==='assist1'){
    if(L.normalizeNumber(draft.assist1)==='')return wizardError('Nummer eingeben oder Assists \u00fcberspringen.');
    draft.assist1=L.normalizeNumber(draft.assist1);goTo('assist2');
  }else if(stage==='assist2')await saveDraft();
  else if(stage==='servedBy'){
    const n=L.normalizeNumber(draft.servedBy);if(n==='')return wizardError('Nummer eingeben oder \u201eSp\u00e4ter eintragen\u201c w\u00e4hlen.');
    draft.servedBy=n;draft.servedLater=false;await saveDraft();
  }
  else if(stage==='goalie'){
    if(L.normalizeGoalie(draft[numericField])==='')return wizardError('Bitte eine Torwartnummer eingeben oder \u201eLeeres Tor\u201c w\u00e4hlen.');
    if(numericField==='goalieOut'){numericField='goalieIn';replaceOnDigit=!!draft.goalieIn;renderWizard();}else await saveDraft();
  }
}
async function saveDraft(){
  if(!draft||saving)return;
  // 2.9: never save a goalie/bench penalty without asking who serves it.
  {const c=candidateFromDraft();if(L.needsServer(state,c)&&!c.servedBy&&!c.servedLater&&stage!=='served'&&stage!=='servedBy'&&!L.validateEvent(c))return finishPenalty();}
  saving=true;const originalDraft=draft,e=candidateFromDraft();
  try{
    const error=L.validateEvent(e);if(error){wizardError(error);return;}
    const unknown=L.unknownPlayers(state,e);
    if(unknown.length&&!await showChoice('Nummer nicht in der Aufstellung',unknown.map(([role,n])=>role+' #'+n).join(', ')+' ist nicht in der Aufstellung von '+sideName(e.team)+'.','Trotzdem speichern'))return;
    if(draft!==originalDraft)return;
    const issue=L.chronologyIssue(e,state.events,e.id);
    if(issue&&chronologyApproval!==reviewKey(e,issue)&&!await showChoice('Zeitliche Reihenfolge pr\u00fcfen','Dieses Ereignis liegt '+(issue.relation==='before'?'vor':'nach')+' dem Vergleichseintrag '+L.formatGameTime(issue.event)+' (Uhr '+dispClock(issue.event)+'). Es wird chronologisch einsortiert.','Trotzdem speichern'))return;
    if(draft!==originalDraft)return;
    if(e.type==='timeout'){
      const taken=L.timeoutIssue(state,e);
      if(taken&&!await showChoice('Timeout bereits genommen',sideName(e.team)+' hat schon einen Timeout bei '+L.formatGameTime(taken)+' (Uhr '+dispClock(taken)+').\nPro Mannschaft ist nur ein Timeout erlaubt.','Trotzdem speichern'))return;
    }
    if(draft!==originalDraft)return;
    if(e.type==='goalie'){
      const expected=L.goalieAt(state,e.team,e);
      if(expected&&expected!==e.goalieOut&&!await showChoice('Torwartnummer pr\u00fcfen','Laut bisherigem Verlauf steht zu diesem Zeitpunkt #'+expected+' im Tor. Eingetragen wurde als raus: #'+e.goalieOut+'.','Trotzdem speichern'))return;
    }
    if(draft!==originalDraft)return;
    snapshot();e.id=e.id||L.uid();const i=state.events.findIndex(old=>old.id===e.id);
    if(i>=0)state.events[i]=e;else state.events.push(e);
    // 1.6: saved immediately (no data loss if Android ends the app), then shown as summary.
    const wasNew=!originalDraft.id;
    draft=null;$('wizard').close();commit();showScreen('game');openDetail(e.id,wasNew?'new':'saved');
  }finally{saving=false;}
}
/* 1.6: large detail / summary in eGrep order: team, event, number, penalty. */
function detailRow(label,value,sub,cls=''){return `<div class="detail-row ${cls}"><dt>${esc(label)}</dt><dd><b>${esc(value)}</b>${sub?`<span>${esc(sub)}</span>`:''}</dd></div>`;}
function personRow(label,side,number){if(number===L.EMPTY_NET)return detailRow(label,'Leeres Tor','');const p=L.playerByNumber(state,side,number);return detailRow(label,number!==''&&number!=null?'#'+number:'\u2014',p&&p.name?p.name:'');}
function renderDetail(e){
  let rows=detailRow('Team',sideName(e.team),'','team')+detailRow('Ereignis',L.TYPE_LABELS[e.type],'','kind');
  if(e.type==='goal'){rows+=personRow('Nummer',e.team,e.player);if(e.assist1)rows+=personRow('Assist 1',e.team,e.assist1);if(e.assist2)rows+=personRow('Assist 2',e.team,e.assist2);}
  else if(e.type==='penalty'){rows+=e.bench?detailRow('Nummer','Bank / Trainer',''):personRow('Nummer',e.team,e.player);rows+=detailRow('Strafe',e.penalty,L.penaltyDurationLabel(e),'penalty');if(e.servedBy)rows+=personRow('Sitzt ab',e.team,e.servedBy);else if(e.servedLater)rows+=detailRow('Sitzt ab','offen','sp\u00e4ter eintragen','served-open');}
  else if(e.type==='goalie'){rows+=personRow('Raus',e.team,e.goalieOut)+personRow('Rein',e.team,e.goalieIn);}
  else if(e.type==='penaltyshot'){rows+=personRow('Sch\u00fctze',e.team,e.player)+detailRow('Ergebnis',e.scored?'Tor':'Kein Tor',e.scored?'z\u00e4hlt als Tor':'','ps-result');}
  else if(e.type==='note'){rows+=detailRow('Notiz',e.text,'','note');}
  // 2.0: hint only - a goal while a penalty may still run.
  const hint=L.powerPlayHint(state,e);
  const en=L.emptyNetGoal(state,e)?`<p class="detail-hint EN"><b>Empty-Net-Tor</b> Laut Torwartwechsel stand bei ${esc(sideName(e.team==='home'?'away':'home'))} kein Torwart im Tor.</p>`:'';
  const hintHtml=en+(hint?`<p class="detail-hint ${hint.kind}"><b>${esc(hint.label)}?</b> Laut Eintr\u00e4gen l\u00e4uft noch: ${hint.penalties.map(p=>esc((p.bench?'Bank':('#'+p.player))+' '+sideName(p.team)+' ('+L.penaltyDurationLabel(p)+', Uhr '+dispClockLabel(p)+')')).join(', ')}</p>`:'');
  const band=gameMode()?`<small>${esc(e.period)}. Drittel \u00b7 Uhr ${esc(L.clockLabel(e))}</small><div class="detail-clock">${esc(L.formatGameTime(e).replace(/ \(\d\)$/,''))}</div><small>Spielzeit</small>`:`<small>${esc(e.period)}. Drittel \u00b7 Spielzeit ${esc(L.formatGameTime(e))}</small><div class="detail-clock">${esc(dispClockLabel(e))}</div><small>${hallUp()?'Uhr (aufw\u00e4rts)':'Uhr'}</small>`;
  return `<div class="detail-band ${e.type} ${e.team||'general'}">${band}</div><dl class="detail-list">${rows}</dl>${hintHtml}`;
}
function openDetail(id,mode){
  const e=state.events.find(x=>x.id===id);if(!e)return;
  detailId=id;detailMode=mode;$('detail-dialog').dataset.mode=mode;
  $('detail-title').textContent=mode==='new'?'Ereignis gespeichert':mode==='saved'?'\u00c4nderung gespeichert':'Ereignis';
  $('detail-sheet').innerHTML=renderDetail(e);
  const plus10=mode==='new'&&e.type==='penalty'&&!e.bench&&['2','2+2','5'].includes(e.penaltyDuration);
  $('detail-actions').innerHTML=(plus10?'<button type="button" class="secondary full-row plus10" id="detail-plus10">+ 10 Min. Disziplinarstrafe (zweiter Eintrag)</button>':'')+(mode==='new'
    ?'<button type="button" class="danger" id="detail-discard">Verwerfen</button><button type="button" class="secondary" id="detail-edit">\u00c4ndern</button><button type="button" class="primary full-row" id="detail-ok">OK</button>'
    :mode==='saved'?'<button type="button" class="secondary" id="detail-edit">\u00c4ndern</button><button type="button" class="primary" id="detail-ok">OK</button>'
    :'<button type="button" class="secondary" id="detail-edit">Bearbeiten</button><button type="button" class="primary" id="detail-ok">Schlie\u00dfen</button>');
  if(!$('detail-dialog').open)$('detail-dialog').showModal();
}
function closeDetail(){if($('detail-dialog').open)$('detail-dialog').close();detailId=null;}
function discardDetail(){
  const id=detailId;closeDetail();if(!state.events.some(e=>e.id===id))return;
  snapshot();state.events=state.events.filter(e=>e.id!==id);commit('Ereignis verworfen \u00b7 R\u00fcckg\u00e4ngig m\u00f6glich');
}
// 2.0: 10-minute misconduct is a SECOND entry with the same time and player (as in eGrep).
function addMisconduct(){
  const base=state.events.find(e=>e.id===detailId);if(!base)return;
  const e=Object.assign({},base,{id:L.uid(),order:nextOrder(),penalty:'Disziplinarstrafe',penaltyDuration:'10'});
  // 2.9: the 10 minutes may be served by someone else: leave it open.
  if(e.servedBy||e.servedLater){e.servedBy='';e.servedLater=true;}
  snapshot();state.events.push(e);commit();openDetail(e.id,'new');
}
function editDetail(){const id=detailId;closeDetail();newEvent(id);}
async function deleteEvent(){
  if(!draft||!draft.id)return;
  if(!await showChoice('Ereignis l\u00f6schen?','Dieser Eintrag wird aus Spielverlauf und Bericht entfernt.','L\u00f6schen',true,true))return;
  snapshot();state.events=state.events.filter(e=>e.id!==draft.id);draft=null;$('wizard').close();commit('Ereignis gel\u00f6scht');
}
async function cancelWizard(){
  if(!draft)return;
  if(draft.rawTime&&!await showChoice('Eingabe verwerfen?','Die noch nicht gespeicherten Angaben werden verworfen.','Verwerfen'))return;
  draft=null;$('wizard').close();saving=false;
}
function backStep(){if(!draft)return;if(trail.length){stage=trail.pop();replaceOnDigit=!!draft[stageField()];renderWizard();}else cancelWizard();}
function chooseType(type){
  if(draft.type&&draft.type!==type){draft.assist1='';draft.assist2='';draft.penalty='';draft.penaltyDuration='2';draft.bench=false;draft.goalieOut='';draft.goalieIn='';draft.scored=undefined;draft.text='';}
  draft.type=type;goTo('team');
}
// 1.5: order is time -> type -> team -> details. A timeout is complete after the team.
async function chooseTeam(team){
  if(draft.team!=null&&draft.team!==''&&draft.team!==(team==='none'?'':team)){['player','assist1','assist2','goalieOut','goalieIn'].forEach(f=>draft[f]='');draft.goalieTouched=false;draft.bench=false;}
  if(team==='none'){if(draft.type!=='note')return;team='';}
  draft.team=team;
  if(draft.type==='timeout')return saveDraft();
  if(draft.type==='note')return goTo('note');
  if(draft.type==='goalie'){
    if(!draft.id&&!draft.goalieTouched){const s=L.goalieSuggestions(state,draft.team,candidateFromDraft());draft.goalieOut=s.out;draft.goalieIn=s.incoming;}
    numericField=draft.goalieOut?'goalieIn':'goalieOut';return goTo('goalie');
  }
  // 1.9: roster known -> tap the reported numbers (like eGrep). Otherwise the keypad as before.
  const players=state[draft.team].players;
  const chosen=[draft.player,draft.assist1,draft.assist2].filter(n=>n!==''&&n!=null);
  goTo(players.length&&!draft.bench&&chosen.every(n=>L.playerByNumber(state,draft.team,n))?'pick':'player');
}
function picks(){return [draft.player,draft.assist1,draft.assist2].filter(n=>n!==''&&n!=null).map(String);}
function togglePick(number){
  if(!draft||saving||stage!=='pick')return;
  if(draft.type==='penalty'){draft.player=number;draft.bench=false;return goTo('penalty');}
  if(draft.type==='penaltyshot'){draft.player=number;return goTo('psresult');}
  let list=picks();
  // Tap again removes the number; the following ones move up (48,5,77 minus 5 -> 48,77).
  if(list.includes(number))list=list.filter(n=>n!==number);else if(list.length<3)list.push(number);
  draft.player=list[0]||'';draft.assist1=list[1]||'';draft.assist2=list[2]||'';
  renderWizard();
}
async function photoSelected(file){
  clearPhoto(false);const token=++photoGeneration;photoUrl=URL.createObjectURL(file);
  // 2.9: a PDF has no image preview; show its name instead.
  const pdf=OCR.isPdf(file);$('photo-preview').classList.toggle('hidden',pdf);$('pdf-name').classList.toggle('hidden',!pdf);
  if(pdf)$('pdf-name').textContent='PDF: '+(file.name||'Aufstellung');else $('photo-preview').src=photoUrl;
  $('ocr-panel').classList.remove('hidden');
  const job=OCR.start(file,(percent,text)=>{if(token!==photoGeneration)return;$('ocr-progress').style.width=percent+'%';$('ocr-message').textContent=text;});recognition=job;
  try{
    const parsed=await job.promise;if(token!==photoGeneration||!parsed)return;
    snapshot();['home','away'].forEach((side,index)=>{
      // 1.6: implausible names are only marked (yellow in Aufstellung), never changed.
      parsed[side].forEach(p=>{const issues=OCR.nameIssues(p.name).concat(p.check||[]);if(issues.length)p.check=issues;else delete p.check;});
      if(parsed[side].length){state[side].players=parsed[side];state[side].startGoalie='';state[side].startGoalie=L.getStartGoalie(state[side]);}
      if(parsed.teamNames[index])state[side].name=parsed.teamNames[index];
    });
    if(parsed.gameNumber)state.meta.number=parsed.gameNumber;
    commit('Erkennung abgeschlossen. Bitte Aufstellung kontrollieren.');
    const count=parsed.home.length+parsed.away.length;
    $('ocr-message').textContent=count+' Spieler erkannt. Torwarte und Start-Markierung bitte kontrollieren.';
    await reviewRecognition(token);if(token!==photoGeneration)return;
    // 3.2: compare with the player memory / EHV after the missing match data was asked.
    const askAway=!parsed.teamNames[1]&&(!state.away.name||state.away.name==='Gast'),askNumber=!parsed.gameNumber&&!state.meta.number;
    if(askAway||askNumber){pendingRosterCheck=true;openMetadata(askAway,askNumber);}else rosterCheck(true);
  }catch(e){
    if(token!==photoGeneration)return;
    $('ocr-message').textContent='OCR-Fehler: '+String(e.message||e).slice(0,210);toast('Manuelle Erfassung ist weiterhin m\u00f6glich.');
    openMetadata(!state.away.name||state.away.name==='Gast',!state.meta.number);
  }finally{if(recognition===job)recognition=null;}
}
/* 1.5: questions after OCR. Nothing is guessed: entries are only changed by an explicit answer. */
function openReview(title,copy,body,actions){
  if(reviewResolver)closeReview(null);
  $('review-title').textContent=title;$('review-copy').textContent=copy;$('review-body').innerHTML=body;
  $('review-actions').innerHTML=actions.map(a=>`<button type="button" class="${a.cls||'secondary'}" data-review="${esc(a.value)}">${esc(a.label)}</button>`).join('');
  $('review-dialog').showModal();$('review-body').scrollTop=0;
  return new Promise(resolve=>{reviewResolver=resolve;});
}
function closeReview(value){
  // Read inputs BEFORE closing, the caller applies them.
  const picks=Array.from($('review-body').querySelectorAll('[data-pick][aria-pressed="true"]')).map(b=>b.dataset.pick);
  if($('review-dialog').open)$('review-dialog').close();
  const resolve=reviewResolver;reviewResolver=null;if(resolve)resolve(value?{value,picks}:null);
}
function pickButtons(players,single){
  return `<div class="review-picks${single?' single':''}">${players.map(p=>`<button type="button" data-pick="${esc(p.number)}" aria-pressed="false"><strong>#${esc(p.number)}</strong> ${esc(p.name||'Spieler #'+p.number)}</button>`).join('')}</div>`;
}
const byNumber=(a,b)=>Number(a.number)-Number(b.number);
async function reviewGoalies(token,side){
  const team=state[side];if(!team.players.length)return;
  let goalies=team.players.filter(p=>p.isGoalie).sort(byNumber);
  if(goalies.length<2){
    const others=team.players.filter(p=>!p.isGoalie).sort(byNumber);if(!others.length)return;
    const none=!goalies.length;
    const answer=await openReview(none?'Kein Torwart erkannt':'Nur ein Torwart erkannt',
      none?sideName(side)+': Bitte die Torwarte antippen (Mehrfachauswahl m\u00f6glich).':sideName(side)+': '+L.playerLabel(state,side,goalies[0].number)+' ist als Torwart erkannt. Gibt es einen zweiten Torwart?',
      pickButtons(others,false),[{label:none?'Kein Torwart in der Liste':'Nein, nur einer',value:'skip'},{label:'\u00dcbernehmen',value:'apply',cls:'primary'}]);
    if(token!==photoGeneration)return;
    if(answer&&answer.value==='apply'&&answer.picks.length){
      snapshot();team.players.forEach(p=>{if(answer.picks.includes(p.number))p.isGoalie=true;});commit('Torwart gespeichert');
    }
    goalies=team.players.filter(p=>p.isGoalie).sort(byNumber);
  }
  if(goalies.length>=2&&!L.getStartGoalie(team)){
    const answer=await openReview('Starting-Goalie?',sideName(side)+': Wer startet im Tor?',pickButtons(goalies,true),[{label:'Noch offen',value:'skip'},{label:'\u00dcbernehmen',value:'apply',cls:'primary'}]);
    if(token!==photoGeneration||!answer||answer.value!=='apply'||answer.picks.length!==1)return;
    snapshot();team.startGoalie=answer.picks[0];team.players.forEach(p=>p.starter=p.isGoalie&&p.number===answer.picks[0]);commit('Starting-Goalie gespeichert');
  }
}
async function reviewRecognition(token){
  for(const side of ['home','away']){if(token!==photoGeneration)return;await reviewGoalies(token,side);}
}
function clearPhoto(eraseNative=true){
  photoGeneration++;if(recognition){recognition.cancel();recognition=null;}if(photoUrl)URL.revokeObjectURL(photoUrl);photoUrl='';
  $('photo-preview').removeAttribute('src');$('photo-preview').classList.remove('hidden');$('pdf-name').classList.add('hidden');$('photo-input').value='';$('camera-input').value='';if(eraseNative)nativeCommand('photo/clear');$('ocr-panel').classList.add('hidden');$('ocr-progress').style.width='0%';$('ocr-message').textContent='';
}
function openMetadata(away,number){
  if(!away&&!number)return;
  $('metadata-away-field').classList.toggle('hidden',!away);$('metadata-number-field').classList.toggle('hidden',!number);
  $('metadata-away').required=away;$('metadata-number').required=number;$('metadata-away').value=state.away.name==='Gast'?'':state.away.name;$('metadata-number').value=state.meta.number||'';
  if(!$('metadata-dialog').open)$('metadata-dialog').showModal();
}
function saveMetadata(ev){ev.preventDefault();snapshot();if(!$('metadata-away-field').classList.contains('hidden'))state.away.name=$('metadata-away').value.trim();if(!$('metadata-number-field').classList.contains('hidden'))state.meta.number=$('metadata-number').value.trim();$('metadata-dialog').close();commit('Spielangaben gespeichert');}
/* 2.0: archive of finished games (local, newest first, at most ARCHIVE_MAX). */
const SIGNS_KEY='egrep-notes-schirizeichen';
function showSigns(){try{return localStorage.getItem(SIGNS_KEY)==='1';}catch(_){return false;}}
function setShowSigns(on){try{localStorage.setItem(SIGNS_KEY,on?'1':'0');}catch(_){}}
// 2.5: reference of all referee signals (same pictures and order as the penalty list).
function openSigns(){
  const pics=window.EGREP_SIGNS||{};
  $('signs-list').innerHTML=L.PENALTIES.filter(p=>pics[p]).map(p=>`<button type="button" class="sign-card" data-sign="${esc(p)}" aria-expanded="false"><img src="${pics[p]}" alt=""><span>${esc(p)}</span></button>`).join('');
  $('signs-dialog').showModal();$('signs-list').scrollTop=0;
}
function loadArchive(){try{const a=JSON.parse(localStorage.getItem(ARCHIVE_KEY)||'[]');return Array.isArray(a)?a:[];}catch(_){return [];}}
function saveArchive(list){try{localStorage.setItem(ARCHIVE_KEY,JSON.stringify(list.slice(0,ARCHIVE_MAX)));return true;}catch(_){return false;}}
const hasContent=s=>s.events.length||(s.shootout||[]).length||s.home.players.length||s.away.players.length;
function archiveCurrent(){
  if(!hasContent(state))return true;
  if(memoryOn())try{learnFrom(state,'app');}catch(_){}
  const entry={id:L.uid(),archivedAt:new Date().toISOString(),date:state.meta.date||'',number:state.meta.number||'',home:sideName('home'),away:sideName('away'),score:L.scoreLabel(state),state:JSON.parse(JSON.stringify(state))};
  return saveArchive([entry,...loadArchive()]);
}
function renderArchiveButton(){const n=loadArchive().length;$('open-archive').textContent='Archiv'+(n?' ('+n+')':'');}
async function resetGame(){
  if(!await showChoice('Neues Spiel beginnen?','Das aktuelle Spiel wird ins Archiv gelegt (die letzten '+ARCHIVE_MAX+' Spiele bleiben erhalten). Das Foto wird entfernt.','Neues Spiel'))return;
  if(!archiveCurrent()&&!await showChoice('Archiv nicht gespeichert','Das Spiel konnte nicht ins Archiv gelegt werden. Trotzdem ohne Archiv neu beginnen?','Ohne Archiv neu',true,true))return;
  history=[];clearPhoto();state=freshState();commit('Neues Spiel \u00b7 altes Spiel im Archiv');renderArchiveButton();showScreen('setup');
}
function openArchive(){
  const list=loadArchive();
  $('archive-list').innerHTML=list.length?list.map(a=>`<div class="archive-item"><div><strong>${esc(a.home)} \u2013 ${esc(a.away)}</strong><span>${esc(String(a.date||'').replace(/^(\d{4})-(\d{2})-(\d{2})$/,'$3.$2.$1'))} \u00b7 Spiel ${esc(a.number||'\u2014')} \u00b7 ${esc(a.score)}</span></div><button type="button" class="secondary" data-archive-open="${esc(a.id)}">\u00d6ffnen</button><button type="button" class="danger" data-archive-delete="${esc(a.id)}" aria-label="Aus dem Archiv l\u00f6schen">\u00d7</button></div>`).join(''):'<p class="empty">Noch keine Spiele im Archiv.</p>';
  if(!$('archive-dialog').open)$('archive-dialog').showModal();
}
async function openArchived(id){
  const list=loadArchive(),entry=list.find(a=>a.id===id);if(!entry)return;
  $('archive-dialog').close();
  if(!await showChoice('Archiviertes Spiel \u00f6ffnen?',entry.home+' \u2013 '+entry.away+' ('+entry.score+'). Das aktuelle Spiel wird vorher ins Archiv gelegt.','\u00d6ffnen'))return openArchive();
  const rest=list.filter(a=>a.id!==id);if(!saveArchive(rest))return toast('Archiv konnte nicht ge\u00e4ndert werden.');
  if(!archiveCurrent())return toast('Aktuelles Spiel konnte nicht archiviert werden. Abgebrochen.');
  history=[];clearPhoto();state=L.migrateState(entry.state);commit('Archiviertes Spiel ge\u00f6ffnet');renderArchiveButton();showScreen('report');
}
async function deleteArchived(id){
  const entry=loadArchive().find(a=>a.id===id);if(!entry)return;
  $('archive-dialog').close();
  if(await showChoice('Aus dem Archiv l\u00f6schen?',entry.home+' \u2013 '+entry.away+' ('+entry.date+') wird endg\u00fcltig gel\u00f6scht.','L\u00f6schen',true,true)){saveArchive(loadArchive().filter(a=>a.id!==id));renderArchiveButton();toast('Aus dem Archiv gel\u00f6scht');}
  openArchive();
}
/* 2.0: penalty shootout. Attempts: team, shooter, scored or not. No clock time. */
function renderShootout(){
  const so=L.shootoutResult(state),list=shootoutList();
  $('shootout-score').textContent=sideName('home')+' '+so.home+' : '+so.away+' '+sideName('away');
  $('shootout-list').innerHTML=list.length?list.map((a,i)=>`<button type="button" class="shootout-item ${a.team} ${a.scored?'scored':'missed'}" data-shootout-remove="${esc(a.id)}"><span>${i+1}.</span><span>${esc(sideName(a.team))} \u00b7 ${esc(shootoutLabel(a))}</span><b>${a.scored?'\u2713 Treffer':'\u2717 kein Treffer'}</b></button>`).join(''):'<p class="dialog-copy">Noch keine Versuche.</p>';
  let html='';
  if(soStep==='team')html=`<p class="dialog-copy">Welche Mannschaft schie\u00dft?</p><div class="shootout-teams">${['home','away'].map(side=>`<button type="button" class="team-choice ${side}" data-shootout-team="${side}">${esc(sideName(side))}</button>`).join('')}</div>`;
  else if(soStep==='player'){
    const players=state[soTeam].players.slice().sort((a,b)=>Number(a.number)-Number(b.number));
    html=`<p class="dialog-copy">Sch\u00fctze ${esc(sideName(soTeam))}</p>${players.length?`<div class="pick-grid ${soTeam} shootout-grid">${players.map(p=>`<button type="button" class="pick-btn" data-shootout-player="${esc(p.number)}"><strong>${esc(p.number)}</strong><small>${esc(String(p.name||'').split(',')[0])}</small></button>`).join('')}</div>`:`<input id="shootout-number" type="text" inputmode="numeric" maxlength="2" placeholder="Nr." autocomplete="off"><button type="button" class="primary full" data-shootout-player="?">Weiter</button>`}<div class="shootout-row-actions"><button type="button" class="secondary" data-shootout-team="${soTeam==='home'?'away':'home'}">Andere Mannschaft</button><button type="button" class="secondary" data-shootout-player="">Ohne Nummer</button></div>`;
  }else html=`<p class="dialog-copy">${esc(sideName(soTeam))} \u00b7 ${esc(soPlayer?L.playerLabel(state,soTeam,soPlayer):'ohne Nummer')}</p><div class="shootout-result"><button type="button" class="primary scored-btn" data-shootout-result="1">Treffer</button><button type="button" class="secondary" data-shootout-result="0">Kein Treffer</button></div><button type="button" class="plain-button back-link" data-shootout-team="${soTeam}">\u2190 anderer Sch\u00fctze</button>`;
  $('shootout-entry').innerHTML=html;
}
function openShootout(){soStep='team';soTeam=null;soPlayer=null;renderShootout();if(!$('shootout-dialog').open)$('shootout-dialog').showModal();}
function shootoutClick(b){
  if(b.dataset.shootoutTeam!==undefined){soTeam=b.dataset.shootoutTeam;soStep='player';return renderShootout();}
  if(b.dataset.shootoutPlayer!==undefined){let n=b.dataset.shootoutPlayer;if(n==='?'){n=L.normalizeNumber($('shootout-number').value);if(n==='')return toast('Nummer 0\u201399 eingeben oder \u201eOhne Nummer\u201c');}soPlayer=n;soStep='result';return renderShootout();}
  if(b.dataset.shootoutResult!==undefined){
    snapshot();state.shootout=state.shootout||[];
    state.shootout.push({id:L.uid(),order:Math.max(0,...state.shootout.map(a=>a.order))+1,team:soTeam,player:soPlayer||'',scored:b.dataset.shootoutResult==='1'});
    commit();soTeam=soTeam==='home'?'away':'home';soPlayer=null;soStep='player';return renderShootout();   // teams alternate
  }
  if(b.dataset.shootoutRemove)return removeShootout(b.dataset.shootoutRemove);
}
async function removeShootout(id){
  const a=(state.shootout||[]).find(x=>x.id===id);if(!a)return;
  $('shootout-dialog').close();
  if(await showChoice('Versuch l\u00f6schen?',sideName(a.team)+' \u00b7 '+shootoutLabel(a)+' \u00b7 '+(a.scored?'Treffer':'kein Treffer'),'L\u00f6schen',true,true)){snapshot();state.shootout=state.shootout.filter(x=>x.id!==id);commit('Versuch gel\u00f6scht');}
  renderShootout();$('shootout-dialog').showModal();
}
function reportText(){
  const lines=[sideName('home')+' - '+sideName('away'),(state.meta.date||'')+' | '+(state.meta.number||''),'Spielstand '+L.scoreLabel(state).replace(/ : /,':'),'Drittel '+periodLine(),''];
  if(state.meta.operatorName)lines.splice(3,0,'Spielbericht erstellt von: '+state.meta.operatorName);
  const running=L.runningScores(state);
  L.sortedEventsByGameTime(state.events).forEach(e=>{
    const names=L.eventNames(state,e).map(p=>p.role+': '+p.label).join(' | ');
    lines.push([L.formatGameTime(e)+' / '+dispClock(e),sideName(e.team),L.TYPE_LABELS[e.type]+(running[e.id]?' '+running[e.id]:'')+(L.emptyNetGoal(state,e)?' (EN)':''),L.eventShort(e),names].filter(Boolean).join(' | '));
  });
  const so=shootoutList();if(so.length){const r=L.shootoutResult(state);lines.push('','Penaltyschie\u00dfen '+r.home+':'+r.away+(r.winner?' | Sieger '+sideName(r.winner):''));so.forEach((a,i)=>lines.push((i+1)+'. '+sideName(a.team)+' | '+shootoutLabel(a)+' | '+(a.scored?'Treffer':'kein Treffer')));}
  return lines.join('\n');
}
async function copyReport(){
  const text=reportText();try{if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(text);toast('Bericht kopiert');return;}}catch(_){}
  const area=document.createElement('textarea');area.value=text;area.style.cssText='position:fixed;left:0;top:0;width:1px;height:1px;opacity:0';document.body.appendChild(area);area.focus();area.select();
  try{if(!document.execCommand('copy'))throw new Error();toast('Bericht kopiert');}catch(_){toast('Kopieren nicht verf\u00fcgbar. Bitte PDF / Drucken verwenden.');}finally{area.remove();}
}
// 3.3: penalties in two lines: who (number + name) and what (duration · penalty), then who serves it.
function penaltyParts(e){return {who:e.bench?'Bank / Trainer':L.playerLabel(state,e.team,e.player),what:L.penaltyDurationLabel(e)+' \u00b7 '+e.penalty,
  served:e.servedBy?'abgesessen von '+L.playerLabel(state,e.team,e.servedBy):e.servedLater?'Absitzender offen':''};}
function penaltyLines(e){const p=penaltyParts(e);return `<span class="pen-who">${esc(p.who)}</span><span class="pen-what">${esc(p.what)}</span>${p.served?`<span class="pen-served${e.servedLater&&!e.servedBy?' open':''}">${esc(p.served)}</span>`:''}`;}
function printDetails(event){
  if(event.type==='timeout')return '';
  if(event.type==='note')return '<span class="print-note">'+esc(event.text)+'</span>';
  if(event.type==='penaltyshot')return esc(L.playerLabel(state,event.team,event.player))+' \u00b7 '+(event.scored?'<b>Tor</b>':'kein Tor');
  if(event.type==='penalty'){const p=penaltyParts(event);return esc(p.who)+'<br><span class="print-pen"><span class="print-duration">'+esc(L.penaltyDurationLabel(event))+'</span> \u00b7 '+esc(event.penalty)+(p.served?' \u00b7 '+(event.servedBy?esc(p.served):'<b>'+esc(p.served)+'</b>'):'')+'</span>';}
  if(event.type==='goalie')return esc(L.playerLabel(state,event.team,event.goalieOut))+' \u2192 '+esc(L.playerLabel(state,event.team,event.goalieIn));
  return L.eventNames(state,event).map(p=>`<span class="print-person">${p.role==='Torsch\u00fctze'?'':p.role==='Assist 1'?'A1: ':'A2: '}${esc(p.label)}</span>`).join(' \u00b7 ')+(L.emptyNetGoal(state,event)?' \u00b7 <b>EN</b>':'');
}
function preparePrintReport(){
  const printRunning=L.runningScores(state);
  const score=L.score(state),events=L.sortedEventsByGameTime(state.events);
  let output=$('print-output');if(!output){output=document.createElement('div');output.id='print-output';output.setAttribute('aria-hidden','true');document.body.appendChild(output);}
  // Reuse a loaded local logo, including in offline test fixtures. Never request a remote asset.
  const logo=document.querySelector('.app-header img');
  const logoUrl=logo?logo.src:'nev-logo.png';
  output.innerHTML=`<div class="print-sheet"><header class="print-heading"><img src="${esc(logoUrl)}" alt="${esc(homeClub().name)}"><div><h1>eGrep Notes</h1><p>SPIELNOTIZEN \u00b7 ${esc(state.meta.date||'Datum offen')} \u00b7 Spiel ${esc(state.meta.number||'\u2014')}</p></div><strong class="print-score">${esc(L.scoreLabel(state))}</strong></header><div class="print-match"><span>${logoImg('home','print-logo')}${esc(sideName('home'))}</span><span>gegen</span><span>${logoImg('away','print-logo')}${esc(sideName('away'))}</span><span class="print-periods">Drittel ${esc(periodLine())}</span></div>${state.meta.operatorName?`<p class="print-operator">Spielbericht erstellt von: <strong>${esc(state.meta.operatorName)}</strong></p>`:''}<table><colgroup><col style="width:21%"><col style="width:20%"><col style="width:59%"></colgroup><thead><tr><th>Zeit / Uhr</th><th>Team</th><th>Ereignis</th></tr></thead><tbody>${events.length?events.map(e=>`<tr class="${e.type} ${e.team||'general'}" data-print-event="${esc(e.id)}"><td class="print-time"><span>${esc(L.formatGameTime(e))}</span> <span class="print-clock">${esc(dispClock(e))}</span></td><td>${esc(sideName(e.team))}</td><td><b class="print-kind">${esc(L.TYPE_LABELS[e.type])}${printRunning[e.id]?' '+esc(printRunning[e.id]):''}</b> ${printDetails(e)}</td></tr>`).join(''):'<tr><td colspan="3">Noch keine Ereignisse erfasst.</td></tr>'}</tbody></table>${shootoutTable('print')}<footer class="print-footer">Spielzeit fortlaufend, Drittel in Klammern. ${gameMode()?'Erfasst als Spielzeit; grau: berechnete Restzeit.':hallUp()?'Uhr lief aufw\u00e4rts; grau: Hallenuhr.':'Grau: abgelesene Uhrzeit.'} \u00b7 ${events.length} Ereignisse<br>Private Spielnotizen \u00b7 kein offizieller Spielbericht \u00b7 eGrep Notes ${L.VERSION} \u00b7 Michael Nowak &amp; KI</footer></div>`;
  const sheet=output.firstElementChild,base=13.333333,mm=96/25.4;
  const onePage=$('print-single-page').checked;
  output.dataset.singlePage=String(onePage);
  // Conservative A4 content box; no fixed row heights, ellipsis, clipping or deleted rows.
  const maxHeight=263*mm,maxWidth=184*mm;
  function measure(size){sheet.style.fontSize=size+'px';return Math.max(sheet.offsetHeight,sheet.scrollHeight);}
  let font=base,height=measure(font);
  if(onePage&&height>maxHeight){
    let lo=.1,hi=base;
    for(let i=0;i<18;i++){const mid=(lo+hi)/2;if(measure(mid)<=maxHeight-3)lo=mid;else hi=mid;}
    font=lo; height=measure(font);
  }
  const fits=height<=maxHeight+1&&sheet.scrollWidth<=maxWidth+1;
  const result={onePage,fontPt:font*.75,heightPx:height,eventCount:events.length,fits:!onePage||fits};
  output.dataset.fontPt=result.fontPt.toFixed(2);output.dataset.fits=String(result.fits);
  return result;
}
async function printReport(){
  renderReport();
  const prepared=preparePrintReport();
  if(!prepared.fits){toast('Einseitenlayout konnte nicht berechnet werden. Bitte Mehrseitenansicht w\u00e4hlen.');return;}
  if(prepared.onePage&&prepared.fontPt<6.5){
    if(!await showChoice('Viele Ereignisse auf einer Seite','Die Schrift wird f\u00fcr '+prepared.eventCount+' Ereignisse sehr klein. F\u00fcr gr\u00f6\u00dfere Schrift kann im Bericht \u201eAuf eine A4-Seite\u201c ausgeschaltet werden.','Trotzdem drucken'))return;
  }
  // Allow loaded images and a layout frame to finish before handing the document to Android.
  const images=Array.from($('print-output').querySelectorAll('img'));
  await Promise.all(images.map(img=>img.complete?Promise.resolve():new Promise(resolve=>{img.onload=img.onerror=resolve;setTimeout(resolve,1500);}))); 
  await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  if(isNative)nativeCommand('print');else window.print();
}
window.addEventListener('beforeprint',preparePrintReport);
function nativeCommand(path){if(isNative)window.location.href='egrep://'+path;}
function updateScreenSetting(){
  keepEnabled=screenMode==='auto'?plugged:screenMode==='on';$('keep-screen').checked=keepEnabled;
  $('screen-auto').classList.toggle('active',screenMode==='auto');
  $('power-status').textContent=(screenMode==='auto'?'Automatik':'Manuell')+' \u00b7 '+(powerKnown?(plugged?'Ladeger\u00e4t':'Akkubetrieb'):'Ladestatus wird gelesen');
  nativeCommand('screen/'+(keepEnabled?'on':'off'));
}
function nativePower(connected){plugged=!!connected;powerKnown=true;updateScreenSetting();}
function requestPower(){if(isNative&&!document.hidden)nativeCommand('power');else if(!isNative){powerKnown=true;updateScreenSetting();}}
function resizeDialog(){document.documentElement.style.setProperty('--vh',(window.visualViewport?window.visualViewport.height:innerHeight)+'px');}
async function handleBack(){
  if($('operator-dialog').open){closeOperator(false);return;}
  if($('review-dialog').open)return closeReview(null);
  if($('detail-dialog').open)return closeDetail();
  if($('shootout-dialog').open){$('shootout-dialog').close();return;}
  if($('quick-menu').open){$('quick-menu').close();return;}
  if($('signs-dialog').open){$('signs-dialog').close();return;}
  if($('settings-dialog').open){$('settings-dialog').close();return;}
  if($('archive-dialog').open){$('archive-dialog').close();return;}
  if($('time-jump-dialog').open)return closeTimeJump(false);
  if($('choice-dialog').open)return closeChoice(false);
  if($('wizard').open)return backStep();
  const open=document.querySelector('dialog[open]');if(open){open.close();return;}
  if(await showChoice('eGrep Notes schlie\u00dfen?','Alle gespeicherten Eintr\u00e4ge bleiben auf dem Ger\u00e4t erhalten.','Schlie\u00dfen'))nativeCommand('exit');
}
document.addEventListener('click',async ev=>{
  const b=ev.target.closest('button');if(!b)return;
  if(b.dataset.screen)return showScreen(b.dataset.screen);
  if(b.dataset.digit!==undefined)return enterDigit(b.dataset.digit);
  if(b.dataset.currentPeriod)return setCurrentPeriod(b.dataset.currentPeriod);
  if(b.dataset.period)return setDraftPeriod(b.dataset.period);
  if(b.dataset.team)return chooseTeam(b.dataset.team);
  if(b.dataset.type)return chooseType(b.dataset.type);
  if(b.dataset.duration)return setPenaltyDuration(b.dataset.duration);
  if(b.dataset.penalty){draft.penalty=b.dataset.penalty;return finishPenalty();}
  if(b.dataset.goalieField){numericField=b.dataset.goalieField;replaceOnDigit=!!draft[numericField];return renderWizard();}
  if(b.dataset.servedNumber){draft.servedBy=b.dataset.servedNumber;draft.servedLater=false;return saveDraft();}
  if(b.dataset.pickNumber)return togglePick(b.dataset.pickNumber);
  if(b.dataset.goalieNumber){draft[numericField]=b.dataset.goalieNumber;draft.goalieTouched=true;replaceOnDigit=true;return renderWizard();}
  switch(b.dataset.action){
    case 'toggle-period':if(draft&&!advancing&&!saving){periodPickerOpen=!periodPickerOpen;renderWizard();}return;
    case 'add-player':return addPlayer(b.dataset.side);
    case 'edit-player':return openPlayer(b.dataset.side,b.dataset.id);
    case 'show-event':return openDetail(b.dataset.id,'view');
    case 'open-shootout':return openShootout();
    case 'erase':return eraseDigit();case 'next':return nextStep();
    case 'skip-assists':if(stage==='assist1')draft.assist1='';draft.assist2='';return saveDraft();
    case 'misconduct':if(draft){draft.penalty='Disziplinarstrafe';draft.penaltyDuration='10';return finishPenalty();}return;
    case 'other-number':return goTo('player');
    case 'pick-save':if(draft&&draft.player)return saveDraft();return;
    case 'bench-penalty':draft.bench=true;draft.player='';return goTo('penalty');
    case 'save-note':{const v=L.cleanNote(($('note-text')||{}).value);if(!v)return wizardError('Bitte einen Notiztext eingeben.');draft.text=v;return saveDraft();}
    case 'ps-scored':draft.scored=true;return saveDraft();
    case 'ps-missed':draft.scored=false;return saveDraft();
    case 'toggle-signs':setShowSigns(!showSigns());return renderWizard();
    case 'custom-penalty':draft.penalty=L.PENALTIES.includes(draft.penalty)?'':draft.penalty;return goTo('customPenalty');
    case 'save-custom':draft.penalty=$('custom-penalty').value.trim();if(!draft.penalty)return wizardError('Bitte die Strafart angeben.');return finishPenalty();
    case 'served-later':draft.servedBy='';draft.servedLater=true;return saveDraft();
    case 'served-other':return goTo('servedBy');
    case 'save-existing':return saveDraft();case 'delete-event':return deleteEvent();
  }
});
document.addEventListener('input',ev=>{if(ev.target.id==='custom-penalty'&&draft)draft.penalty=ev.target.value;if(ev.target.id==='note-text'&&draft){draft.text=ev.target.value;wizardError('');}});
document.addEventListener('change',ev=>{
  const t=ev.target;
  if(t.dataset.teamName){snapshot();state[t.dataset.teamName].name=t.value.trim();return commit();}
  if(t.dataset.startGoalie){const side=t.dataset.startGoalie;snapshot();state[side].startGoalie=t.value;state[side].players.forEach(p=>p.starter=p.isGoalie&&p.number===t.value);return commit('Starting-Goalie gespeichert');}
});
document.addEventListener('keydown',ev=>{
  if(!$('wizard').open||$('choice-dialog').open||$('time-jump-dialog').open)return;
  if(stage==='customPenalty'){if(ev.key==='Enter'){ev.preventDefault();draft.penalty=$('custom-penalty').value.trim();saveDraft();}return;}
  if(['time','player','assist1','assist2','goalie'].includes(stage)){
    if(/^\d$/.test(ev.key)){ev.preventDefault();enterDigit(ev.key);}
    else if(ev.key==='Backspace'){ev.preventDefault();eraseDigit();}
    else if(ev.key==='Enter'){ev.preventDefault();nextStep();}
  }
});
$('new-event').onclick=()=>newEvent();$('wizard-back').onclick=backStep;$('wizard-close').onclick=cancelWizard;
$('wizard').addEventListener('cancel',ev=>{ev.preventDefault();cancelWizard();});
$('undo').onclick=undo;
// 2.8: quick menu in the header (Schiri-Zeichen, Archiv, Info); tap outside or Back closes it.
$('open-menu').onclick=()=>{$('menu-archive-label').textContent=$('open-archive').textContent;$('quick-menu').showModal();};
$('quick-menu').addEventListener('click',ev=>{if(ev.target===$('quick-menu'))$('quick-menu').close();});
$('menu-archive').onclick=()=>{$('quick-menu').close();openArchive();};
// 3.0: settings dialog: choose the home club.
function applyClub(){
  const c=homeClub(),src=c.logo||GENERIC_LOGO;
  for(const img of [document.querySelector('.app-header img'),document.querySelector('#info-dialog > img')])if(img){if(img.getAttribute('src')!==src)img.src=src;img.alt=c.name;}
  $('info-club').textContent=c.name;$('menu-settings-note').textContent='Heimmannschaft: '+c.name;if(typeof renderUpdate==='function'&&document.getElementById('update-status'))try{renderUpdate();}catch(_){}
}
const foldText=t=>String(t||'').toLocaleLowerCase('de').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ß/g,'ss').replace(/[^a-z0-9]+/g,' ').trim();
function renderClubList(){
  const q=foldText($('club-search').value),cur=homeClub();
  const list=CLUBS.filter(c=>!q||foldText(c.name+' '+c.full).includes(q)).sort((a,b)=>a.name.localeCompare(b.name,'de'));
  $('club-list').innerHTML=list.length?list.map(c=>{const sel=!settings.homeCustom&&c.id===cur.id;
    return `<button type="button" class="club-item${sel?' selected':''}" role="option" aria-selected="${sel}" data-club="${esc(c.id)}"><img src="${esc(c.logo)}" alt=""><span>${esc(c.name)}<small>${esc(c.full)}</small></span>${sel?'<b aria-hidden="true">\u2713</b>':''}</button>`;}).join(''):'<p class="dialog-copy">Kein Verein gefunden. Unten einen eigenen Namen eintragen.</p>';
  $('club-custom').value=settings.homeCustom||'';
}
function openSettings(){$('club-search').value='';renderClubList();renderMemoryStats();renderUpdate();$('settings-dialog').showModal();const sel=$('club-list').querySelector('.selected');if(sel)sel.scrollIntoView({block:'center'});}
function setHomeClub(next){
  const before=homeClub().name;const keep=Object.assign({},settings);delete keep.homeClub;delete keep.homeCustom;settings=Object.assign(keep,next);if(!saveSettings())toast('Einstellung konnte nicht gespeichert werden.');
  const now=homeClub();applyClub();
  // An untouched game takes the new name; a running game keeps its teams.
  if(!state.events.length&&!state.home.players.length&&(!state.home.name||state.home.name===before)){state.home.name=now.name;persist();}
  renderAll();$('settings-dialog').close();toast('Heimmannschaft: '+now.name);
}
$('open-settings').onclick=()=>{$('quick-menu').close();openSettings();};$('close-settings').onclick=()=>$('settings-dialog').close();
$('club-search').addEventListener('input',renderClubList);
$('club-list').addEventListener('click',ev=>{const b=ev.target.closest('[data-club]');if(b)setHomeClub({homeClub:b.dataset.club});});
$('club-custom-save').onclick=()=>{const n=$('club-custom').value.trim().slice(0,60);if(!n){$('club-custom').focus();return;}setHomeClub({homeCustom:n});};
$('settings-reset').onclick=()=>setHomeClub({homeClub:DEFAULT_CLUB});
applyClub();
// 3.0: swipe between Aufstellung / Spiel / Bericht (left = next). Not on inputs, horizontal scroll areas
// or while a dialog is open; switchable in the settings ("swipe": false).
const SCREENS=['setup','game','report'];
const swipeOn=()=>settings.swipe!==false;
function scrollsSideways(n){for(;n&&n!==document.body;n=n.parentElement){const o=getComputedStyle(n).overflowX;if((o==='auto'||o==='scroll')&&n.scrollWidth>n.clientWidth+2)return true;}return false;}
let swipeStart=null;
document.querySelector('main').addEventListener('touchstart',ev=>{
  swipeStart=null;if(!swipeOn()||ev.touches.length!==1||document.querySelector('dialog[open]'))return;
  const t=ev.target;if(t.closest&&t.closest('input,textarea,select,[contenteditable],.no-swipe'))return;if(scrollsSideways(t))return;
  const p=ev.touches[0];swipeStart={x:p.clientX,y:p.clientY,at:Date.now()};
},{passive:true});
document.querySelector('main').addEventListener('touchend',ev=>{
  const s=swipeStart;swipeStart=null;if(!s||!ev.changedTouches.length||document.querySelector('dialog[open]'))return;
  const p=ev.changedTouches[0],dx=p.clientX-s.x,dy=p.clientY-s.y;
  if(Date.now()-s.at>700||Math.abs(dx)<Math.max(60,innerWidth*.18)||Math.abs(dx)<2*Math.abs(dy))return;
  const cur=SCREENS.indexOf((document.querySelector('.screen.active')||{}).id),next=cur+(dx<0?1:-1);
  if(cur<0||next<0||next>=SCREENS.length)return;
  showScreen(SCREENS[next]);const n=$(SCREENS[next]);n.classList.remove('swipe-from-left','swipe-from-right');void n.offsetWidth;n.classList.add(dx<0?'swipe-from-right':'swipe-from-left');
},{passive:true});
document.querySelector('main').addEventListener('touchcancel',()=>{swipeStart=null;},{passive:true});
$('swipe-toggle').checked=swipeOn();
$('swipe-toggle').onchange=()=>{settings=Object.assign({},settings,{swipe:$('swipe-toggle').checked});saveSettings();};
// ---------- 3.2: player memory (on the device) and optional EHV check ----------
const PLAYERS_KEY='egrep-spieler-v1',EHV_CACHE_KEY='egrep-ehv-cache-v1',R=window.EgrepRoster;
const memoryOn=()=>settings.memory!==false,ehvOn=()=>settings.ehv!==false;
function loadPlayers(){try{return R.normalizeDb(JSON.parse(localStorage.getItem(PLAYERS_KEY)||'null'));}catch(_){return R.emptyDb();}}
function savePlayers(db){try{localStorage.setItem(PLAYERS_KEY,JSON.stringify(db));return true;}catch(_){return false;}}
function learnFrom(s,src){let db=loadPlayers();['home','away'].forEach(side=>{const t=s[side];if(t&&Array.isArray(t.players)&&t.players.length)db=R.learn(db,t.name,s.meta&&s.meta.number,t.players,src);});savePlayers(db);}
function renderMemoryStats(){const st=R.stats(loadPlayers());$('memory-stats').textContent=st.players?'Spieler-Gedächtnis: '+st.players+' Spieler aus '+st.teams+' Mannschaften (nur auf diesem Gerät).':'Spieler-Gedächtnis: noch leer. Es lernt aus abgeschlossenen Spielen („Neues Spiel“) und aus EHV-Spielberichten.';}
async function fetchText(url){const c=new AbortController(),t=setTimeout(()=>c.abort(),12000);try{const r=await fetch(url,{signal:c.signal,cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);return await r.text();}finally{clearTimeout(t);}}
window.egrepFetchText=fetchText;
let checking=false,pendingRosterCheck=false;
function rosterStatus(t){$('roster-check-status').textContent=t;}
async function rosterCheck(auto){
  if(checking)return;const sides=['home','away'];
  if(!memoryOn()&&!ehvOn()){if(!auto)toast('Abgleich ist in den Einstellungen ausgeschaltet.');return;}
  checking=true;$('roster-check').disabled=true;
  try{
    const refs={home:[],away:[]};let exact=false,source='Spieler-Gedächtnis',note='';
    if(memoryOn()){const db=loadPlayers();sides.forEach(s=>refs[s]=R.memoryFor(db,state[s].name,state.meta.number));}
    if(ehvOn()){
      if(navigator.onLine===false)note='EHV nicht abgefragt (offline).';
      else{rosterStatus('EHV-Spielberichte werden abgefragt …');
        let cache={};try{cache=JSON.parse(localStorage.getItem(EHV_CACHE_KEY)||'{}')||{};}catch(_){}
        try{
          const r=await R.ehvLookup({fetchText:window.egrepFetchText,cache,homeName:sideName('home'),awayName:sideName('away'),gameNumber:state.meta.number,progress:(d,n)=>rosterStatus('EHV-Spielpläne '+d+'/'+n+' …')});
          if(r.rows)try{localStorage.setItem(EHV_CACHE_KEY,JSON.stringify({at:Date.now(),rows:r.rows}));}catch(_){}
          if(r.exact){sides.forEach(s=>refs[s]=r[s]);exact=true;source='EHV-Spielbericht '+((r.game&&r.game.n)||'');}
          else if(r.home.length||r.away.length){sides.forEach(s=>{const byNum=new Map(refs[s].map(p=>[String(p.number),p]));r[s].forEach(p=>byNum.set(String(p.number),p));refs[s]=[...byNum.values()];});source=memoryOn()?'Spieler-Gedächtnis und letzte EHV-Spiele':'letzte EHV-Spiele';}
          else note='Beim EHV nichts Passendes gefunden.';
          if(memoryOn()&&(r.home.length||r.away.length)){let d=loadPlayers();sides.forEach(s=>{if(r[s].length)d=R.learn(d,state[s].name,state.meta.number,r[s],'ehv');});savePlayers(d);}
        }catch(_){note='EHV nicht erreichbar.';}
      }
    }
    const list=[];sides.forEach(s=>R.suggest(state[s].players,refs[s],exact,source).forEach(x=>list.push(Object.assign({side:s},x))));
    if(!list.length){rosterStatus(((refs.home.length||refs.away.length)?'Abgleich ('+source+'): keine Abweichungen.':'Noch keine Vergleichsdaten für diese Mannschaften.')+(note?' '+note:''));if(!auto)toast('Keine Vorschläge');return;}
    rosterStatus(list.length+' Vorschläge ('+source+').'+(note?' '+note:''));
    const body=sides.map(s=>{const items=list.map((x,i)=>[x,i]).filter(([x])=>x.side===s);if(!items.length)return '';
      return `<h3 class="review-team">${esc(sideName(s))}</h3><div class="review-picks suggestion-picks">${items.map(([x,i])=>`<button type="button" data-pick="${i}" aria-pressed="true">${esc(R.describe(x))}</button>`).join('')}</div>`;}).join('');
    const answer=await openReview('Vorschläge zur Aufstellung','Quelle: '+source+'. Markierte Vorschläge werden übernommen (antippen zum Abwählen). Ohne deine Bestätigung ändert sich nichts.',body,[{label:'Nichts ändern',value:'none'},{label:'Übernehmen',value:'apply',cls:'primary'}]);
    if(!answer||answer.value!=='apply'||!answer.picks.length){rosterStatus(list.length+' Vorschläge, nichts geändert ('+source+').'+(note?' '+note:''));return;}
    snapshot();const chosen=answer.picks.map(Number).map(i=>list[i]).filter(Boolean);
    sides.forEach(s=>{const mine=chosen.filter(x=>x.side===s);if(mine.length){state[s].players=R.applySuggestions(state[s].players,mine);if(!state[s].startGoalie)state[s].startGoalie=L.getStartGoalie(state[s]);}});
    commit(chosen.length+' Vorschläge übernommen');rosterStatus(chosen.length+' von '+list.length+' Vorschlägen übernommen ('+source+').'+(note?' '+note:''));
  }finally{checking=false;$('roster-check').disabled=false;}
}
$('roster-check').onclick=()=>rosterCheck(false);
$('metadata-dialog').addEventListener('close',()=>{if(pendingRosterCheck){pendingRosterCheck=false;rosterCheck(true);}});
$('memory-toggle').checked=memoryOn();$('memory-toggle').onchange=()=>{settings=Object.assign({},settings,{memory:$('memory-toggle').checked});saveSettings();};
$('ehv-toggle').checked=ehvOn();$('ehv-toggle').onchange=()=>{settings=Object.assign({},settings,{ehv:$('ehv-toggle').checked});saveSettings();};
$('memory-clear').onclick=async()=>{$('settings-dialog').close();if(await showChoice('Spieler-Gedächtnis löschen?','Alle gemerkten Spielernamen werden von diesem Gerät entfernt. Spiele und Archiv bleiben.','Löschen',true,true)){try{localStorage.removeItem(PLAYERS_KEY);}catch(_){}toast('Spieler-Gedächtnis gelöscht');}openSettings();};

// ---------- 3.2: backup (file) ----------
const BACKUP_FORMAT='egrep-notes-backup';
function backupData(){return {format:BACKUP_FORMAT,version:1,app:L.VERSION,created:new Date().toISOString(),game:state,archive:loadArchive(),players:loadPlayers(),settings,signs:showSigns()};}
function saveBackup(){
  const json=JSON.stringify(backupData()),name='eGrep-Notes-Sicherung-'+(L.localDate()||'')+'.json';
  if(isNative){const url='egrep://backup?'+encodeURIComponent(name)+'&'+encodeURIComponent(json);
    if(url.length>1800000)return toast('Sicherung zu groß ('+Math.round(url.length/1024)+' kB). Bitte ältere Spiele aus dem Archiv löschen.');
    return nativeCommand(url.slice(8));}
  try{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([json],{type:'application/json'}));a.download=name;document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},2000);toast('Sicherung gespeichert');}catch(_){toast('Sicherung konnte nicht gespeichert werden.');}
}
window.egrepBackupSaved=ok=>toast(ok?'Sicherung gespeichert':'Sicherung nicht gespeichert');
function readBackup(text){
  let b;try{b=JSON.parse(text);}catch(_){throw new Error('Keine gültige Sicherungsdatei.');}
  if(!b||b.format!==BACKUP_FORMAT||!b.game)throw new Error('Das ist keine eGrep-Notes-Sicherung.');
  return b;
}
async function restoreBackup(text){
  let b;try{b=readBackup(text);}catch(e){return toast(e.message);}
  const archive=(Array.isArray(b.archive)?b.archive:[]).filter(a=>a&&a.id&&a.state);
  const created=String(b.created||'').slice(0,16).replace('T',' ');
  if(!await showChoice('Sicherung einlesen?','Sicherung vom '+(created||'?')+' mit '+archive.length+' archivierten Spielen. Nichts wird gelöscht: Archiv und Spieler-Gedächtnis werden zusammengeführt, ein laufendes Spiel kommt vorher ins Archiv.','Einlesen'))return;
  const game=L.migrateState(b.game);
  const merged=[...loadArchive()];const ids=new Set(merged.map(a=>a.id));archive.forEach(a=>{if(!ids.has(a.id)){merged.push(a);ids.add(a.id);}});
  merged.sort((x,y)=>String(y.archivedAt||'').localeCompare(String(x.archivedAt||'')));
  const dropped=Math.max(0,merged.length-ARCHIVE_MAX);
  const replace=hasContent(game)&&JSON.stringify(game)!==JSON.stringify(state);
  if(replace&&hasContent(state)){if(!archiveCurrent())return toast('Aktuelles Spiel konnte nicht archiviert werden. Abgebrochen.');const cur=loadArchive()[0];if(cur&&!ids.has(cur.id))merged.unshift(cur);}
  if(!saveArchive(merged))return toast('Archiv konnte nicht gespeichert werden.');
  savePlayers(R.mergeDb(loadPlayers(),b.players));
  if(b.settings&&typeof b.settings==='object'&&!localStorageHasSettings())settings=Object.assign({},b.settings),saveSettings(),applyClub();
  if(replace){history=[];clearPhoto();state=game;commit('Sicherung eingelesen');}else renderAll();
  renderArchiveButton();toast('Sicherung eingelesen'+(dropped?' · '+dropped+' älteste Spiele passten nicht ins Archiv':''));
}
function localStorageHasSettings(){try{return !!localStorage.getItem(SETTINGS_KEY);}catch(_){return false;}}
$('backup-save').onclick=saveBackup;
$('backup-input').onchange=async ev=>{const f=ev.target.files&&ev.target.files[0];ev.target.value='';if(!f)return;$('settings-dialog').close();
  if(f.size>5e6)return toast('Datei zu groß für eine Sicherung.');try{await restoreBackup(await f.text());}catch(_){toast('Sicherung konnte nicht gelesen werden.');}};

// ---------- 3.2: update check (like the other apps: version file on the project page) ----------
const UPDATE_KEY='egrep-update',UPDATE_URL='https://cappy0815.github.io/downloads/egrep-notes.json',UPDATE_PAGE='https://cappy0815.github.io/#egrep-notes',DAY_MS=864e5;
function loadUpdate(){try{return JSON.parse(localStorage.getItem(UPDATE_KEY)||'{}')||{};}catch(_){return {};}}
function saveUpdate(u){try{localStorage.setItem(UPDATE_KEY,JSON.stringify(u));}catch(_){}}
function newerVersion(a,b){const p=v=>String(v||'').replace(/^v/i,'').split('.').map(x=>parseInt(x,10)||0);const x=p(a),y=p(b);for(let i=0;i<Math.max(x.length,y.length);i++){if((x[i]||0)!==(y[i]||0))return (x[i]||0)>(y[i]||0);}return false;}
const updateAuto=()=>loadUpdate().auto!==false;
function renderUpdate(){
  const u=loadUpdate(),avail=u.latest&&newerVersion(u.latest,L.VERSION);
  $('update-toggle').checked=updateAuto();
  $('update-status').textContent=avail?'Neue Version '+u.latest+' verfügbar (installiert: '+L.VERSION+').'+(u.failed?' Letzte Prüfung: Projektseite nicht erreichbar.':''):u.failed?'Projektseite nicht erreichbar'+(u.last?' · zuletzt geprüft '+new Date(u.last).toLocaleString('de-DE'):'')+'.':u.last?'Aktuell (Version '+L.VERSION+') · geprüft '+new Date(u.last).toLocaleString('de-DE')+'.':'Noch nicht geprüft.';
  $('update-download').classList.toggle('hidden',!avail);if(avail)$('update-download').href=/^https:\/\/cappy0815\.github\.io\//.test(u.download||'')?u.download:UPDATE_PAGE;
  $('menu-settings-note').textContent=(avail?'Update '+u.latest+' · ':'')+'Heimmannschaft: '+homeClub().name;
  $('open-menu').classList.toggle('has-update',!!avail);
}
let updateBusy=false;
async function checkUpdate(manual){
  if(updateBusy)return;updateBusy=true;if(manual)$('update-status').textContent='Prüfe …';
  const u=loadUpdate();
  try{const o=JSON.parse(await window.egrepFetchText(UPDATE_URL+'?t='+Date.now()));const v=String(o.version||'').trim().replace(/^v/i,'');if(!/^\d+(\.\d+)*$/.test(v))throw new Error('format');
    Object.assign(u,{latest:v,download:String(o.download||''),page:String(o.page||UPDATE_PAGE),last:Date.now(),failed:false});saveUpdate(u);
    if(newerVersion(v,L.VERSION)&&!manual&&u.notified!==v){u.notified=v;saveUpdate(u);toast('Neue Version '+v+' verfügbar · Menü › Einstellungen');}
    if(manual)toast(newerVersion(v,L.VERSION)?'Neue Version '+v+' verfügbar':'eGrep Notes ist aktuell ('+L.VERSION+')');
  }catch(_){Object.assign(u,{last:Date.now(),failed:true});saveUpdate(u);if(manual)toast('Projektseite nicht erreichbar.');}
  finally{updateBusy=false;renderUpdate();}
}
$('update-check').onclick=()=>checkUpdate(true);
$('update-toggle').onchange=()=>{const u=loadUpdate();u.auto=$('update-toggle').checked;saveUpdate(u);};
renderUpdate();
setTimeout(()=>{const u=loadUpdate();if(updateAuto()&&navigator.onLine!==false&&Date.now()-(u.last||0)>DAY_MS)checkUpdate(false);},4000);
$('show-info').onclick=()=>{$('quick-menu').close();$('info-dialog').showModal();};$('close-info').onclick=()=>$('info-dialog').close();
$('choice-confirm').onclick=()=>closeChoice(true);$('choice-cancel').onclick=()=>closeChoice(false);$('choice-dialog').addEventListener('cancel',ev=>{ev.preventDefault();closeChoice(false);});
$('time-jump-next').onclick=()=>closeTimeJump('next');$('time-jump-retro').onclick=()=>closeTimeJump('retro');$('time-jump-cancel').onclick=()=>closeTimeJump(false);
$('time-jump-dialog').addEventListener('cancel',ev=>{ev.preventDefault();closeTimeJump(false);});
$('player-form').onsubmit=savePlayer;$('cancel-player').onclick=()=>$('player-dialog').close();$('delete-player').onclick=deletePlayer;
$('player-goalie').onchange=()=>{$('player-starter').disabled=!$('player-goalie').checked;if(!$('player-goalie').checked)$('player-starter').checked=false;};
$('game-date').onchange=ev=>{snapshot();state.meta.date=ev.target.value;commit();};$('game-number').onchange=ev=>{snapshot();state.meta.number=ev.target.value.trim();commit();};
['photo-input','camera-input'].forEach(id=>{$(id).onchange=ev=>{const f=ev.target.files&&ev.target.files[0];if(f)photoSelected(f);};});$('remove-photo').onclick=()=>{clearPhoto();toast('Bild entfernt');};
$('operator-form').onsubmit=ev=>{ev.preventDefault();closeOperator(true);};$('operator-later').onclick=()=>closeOperator(false);
$('operator-dialog').addEventListener('cancel',ev=>{ev.preventDefault();closeOperator(false);});
$('clock-mode').onclick=()=>setTimeMode(nextTimeMode());$('info-version').textContent='Version '+L.VERSION;$('edit-operator-game').onclick=openOperator;$('edit-operator-report').onclick=openOperator;
$('shootout-dialog').addEventListener('click',ev=>{const b=ev.target.closest('button');if(b&&$('shootout-dialog').contains(b)&&b.id!=='shootout-done')shootoutClick(b);});
$('shootout-done').onclick=()=>$('shootout-dialog').close();
$('open-shootout').onclick=openShootout;$('show-signs').onclick=()=>{$('quick-menu').close();openSigns();};$('close-signs').onclick=()=>$('signs-dialog').close();
$('signs-list').onclick=ev=>{const c=ev.target.closest('.sign-card');if(!c)return;const big=!c.classList.contains('big');document.querySelectorAll('.sign-card.big').forEach(x=>{x.classList.remove('big');x.setAttribute('aria-expanded','false');});if(big){c.classList.add('big');c.setAttribute('aria-expanded','true');c.scrollIntoView({block:'nearest'});}};
$('open-archive').onclick=openArchive;$('close-archive').onclick=()=>$('archive-dialog').close();
$('archive-list').onclick=ev=>{const b=ev.target.closest('button');if(!b)return;if(b.dataset.archiveOpen)openArchived(b.dataset.archiveOpen);else if(b.dataset.archiveDelete)deleteArchived(b.dataset.archiveDelete);};
$('detail-actions').onclick=ev=>{const b=ev.target.closest('button');if(!b)return;if(b.id==='detail-ok')closeDetail();else if(b.id==='detail-plus10')addMisconduct();else if(b.id==='detail-edit')editDetail();else if(b.id==='detail-discard')discardDetail();};
$('detail-dialog').addEventListener('cancel',ev=>{ev.preventDefault();closeDetail();});
$('review-actions').onclick=ev=>{const b=ev.target.closest('[data-review]');if(b)closeReview(b.dataset.review);};
$('review-body').onclick=ev=>{
  const b=ev.target.closest('[data-pick]');if(!b)return;
  const on=b.getAttribute('aria-pressed')!=='true';
  if(b.closest('.single'))$('review-body').querySelectorAll('[data-pick]').forEach(x=>x.setAttribute('aria-pressed','false'));
  b.setAttribute('aria-pressed',String(on));
};
$('review-form').onsubmit=ev=>ev.preventDefault();
$('review-dialog').addEventListener('cancel',ev=>{ev.preventDefault();closeReview(null);});
$('metadata-form').onsubmit=saveMetadata;$('cancel-metadata').onclick=()=>$('metadata-dialog').close();
$('copy-report').onclick=copyReport;$('print-report').onclick=printReport;$('reset-game').onclick=resetGame;
$('keep-screen').onchange=ev=>{screenMode=ev.target.checked?'on':'off';updateScreenSetting();};$('screen-auto').onclick=()=>{screenMode='auto';requestPower();};
window.egrepCameraRecovered=function(url){
  const token=photoGeneration,image=new Image();
  image.onload=()=>{
    if(token!==photoGeneration)return;
    const scale=Math.min(1,3200/Math.max(image.naturalWidth,image.naturalHeight));
    const canvas=document.createElement('canvas');canvas.width=Math.round(image.naturalWidth*scale);canvas.height=Math.round(image.naturalHeight*scale);
    canvas.getContext('2d').drawImage(image,0,0,canvas.width,canvas.height);
    try{canvas.toBlob(blob=>{if(blob&&token===photoGeneration)photoSelected(blob);},'image/jpeg',.95);}
    catch(_){toast('Foto konnte nicht geladen werden. Bitte erneut aufnehmen.');}
  };
  image.onerror=()=>toast('Foto konnte nicht geladen werden. Bitte erneut aufnehmen.');image.src=url;
};
// 2.9: long-press on the app icon -> "Schiri-Zeichen" (Android shortcut opens index.html#signs or calls this).
function openSignsFromShortcut(){try{if($('quick-menu').open)$('quick-menu').close();if(!$('signs-dialog').open)openSigns();}catch(_){}}
window.egrepOpenSigns=openSignsFromShortcut;
window.egrepPower=nativePower;window.egrepHostReady=requestPower;window.egrepBack=handleBack;
window.addEventListener('resize',resizeDialog);if(window.visualViewport)window.visualViewport.addEventListener('resize',resizeDialog);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)requestPower();});
resizeDialog();renderAll();renderArchiveButton();if(state.events.length)showScreen('game');if(location.hash==='#signs'){openSignsFromShortcut();setTimeout(()=>{try{window.history.replaceState(null,'',location.href.split('#')[0]);}catch(_){}},0);}setTimeout(requestPower,150);setInterval(requestPower,20000);
// Narrow hooks for reproducible automated UI tests, no network/debug bridge.
window.EgrepUI={getState:()=>JSON.parse(JSON.stringify(state)),getPower:()=>({mode:screenMode,plugged,enabled:keepEnabled}),reportText,preparePrintReport};
})();
