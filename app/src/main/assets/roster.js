/* 3.2: player memory (on the device) and optional check against EHV game reports (hockeydata).
   Pure functions + a small EHV client. Nothing here changes a roster: it only produces suggestions
   that the user accepts explicitly. Birthdates or other fields from the EHV reports are never stored. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.EgrepRoster=api;})(this,function(){
  'use strict';
  const DB_VERSION=1,MAX_TEAMS=80,MAX_PLAYERS=60;
  const fold=s=>String(s||'').toLocaleLowerCase('de').replace(/ß/g,'ss').normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9, ]+/g,' ').replace(/\s+/g,' ').trim();
  const teamNorm=s=>fold(s).replace(/,/g,' ').replace(/\s+/g,' ').trim();
  // Age class from the game number, e.g. "U13_LL_005" -> "u13", "SEN_BZL_019" -> "sen". Unknown -> "".
  function ageClass(gameNumber){const m=/^\s*([A-Za-z]{1,4}\d{0,2})_/.exec(String(gameNumber||''));return m?m[1].toLowerCase():'';}
  function teamKey(teamName,gameNumber){const t=teamNorm(teamName);return t?t+'|'+ageClass(gameNumber):'';}
  const surname=n=>fold(String(n||'').split(',')[0]);
  function lev(a,b){if(a===b)return 0;const m=a.length,n=b.length;if(!m||!n)return Math.max(m,n);let prev=Array.from({length:n+1},(_,i)=>i);
    for(let i=1;i<=m;i++){const cur=[i];for(let j=1;j<=n;j++)cur[j]=Math.min(prev[j]+1,cur[j-1]+1,prev[j-1]+(a[i-1]===b[j-1]?0:1));prev=cur;}return prev[n];}
  function similarity(a,b){a=fold(a);b=fold(b);if(!a&&!b)return 1;if(!a||!b)return 0;return 1-lev(a,b)/Math.max(a.length,b.length);}
  // Same person? Surname decides; a missing or abbreviated first name is fine.
  // OCR reads "ß" often as "B": compare with ß -> s (one letter) instead of ss.
  function samePerson(a,b){const k=n=>surname(String(n||'').replace(/ß/g,'s'));const sa=k(a),sb=k(b);if(!sa||!sb)return false;
    const sim=1-lev(sa,sb)/Math.max(sa.length,sb.length);return sim>=.8||(Math.min(sa.length,sb.length)>=6&&sim>=.75);}
  function emptyDb(){return {version:DB_VERSION,teams:{}};}
  function normalizeDb(db){
    if(!db||typeof db!=='object'||typeof db.teams!=='object'||Array.isArray(db.teams))return emptyDb();
    const out=emptyDb();
    for(const [k,t] of Object.entries(db.teams)){if(!t||typeof t!=='object'||!t.players||typeof t.players!=='object')continue;
      const players={};for(const [num,p] of Object.entries(t.players)){const n=String(num).replace(/\D/g,'').replace(/^0+(?=\d)/,'');if(!n||n.length>2||!p||!p.n)continue;
        players[n]={n:String(p.n).slice(0,80),g:!!p.g,c:Math.max(1,Math.min(999,Number(p.c)||1)),t:Number(p.t)||0,s:p.s==='ehv'?'ehv':'app'};}
      out.teams[k]={name:String(t.name||'').slice(0,80),players,t:Number(t.t)||0};}
    return out;
  }
  // Learn confirmed players. Same number + same person -> count up; same number, other person -> replaced.
  function learn(db,teamName,gameNumber,players,src,now){
    db=normalizeDb(db);const key=teamKey(teamName,gameNumber);if(!key||!Array.isArray(players))return db;
    now=now||Date.now();const team=db.teams[key]||{name:String(teamName).slice(0,80),players:{},t:0};team.t=now;team.name=String(teamName).slice(0,80);
    for(const p of players){const n=String(p&&p.number||'').replace(/\D/g,'').replace(/^0+(?=\d)/,'');const name=String(p&&p.name||'').trim();
      if(!n||n.length>2||!name||(p.check&&p.check.length))continue;
      const old=team.players[n];
      if(old&&samePerson(old.n,name)){old.c=Math.min(999,old.c+1);old.t=now;if(src==='ehv'||old.s!=='ehv')old.n=name;old.g=!!p.isGoalie;if(src==='ehv')old.s='ehv';}
      else team.players[n]={n:name,g:!!p.isGoalie,c:1,t:now,s:src==='ehv'?'ehv':'app'};}
    const nums=Object.keys(team.players);if(nums.length>MAX_PLAYERS)nums.sort((a,b)=>team.players[a].t-team.players[b].t).slice(0,nums.length-MAX_PLAYERS).forEach(n=>delete team.players[n]);
    db.teams[key]=team;
    const keys=Object.keys(db.teams);if(keys.length>MAX_TEAMS)keys.sort((a,b)=>db.teams[a].t-db.teams[b].t).slice(0,keys.length-MAX_TEAMS).forEach(k=>delete db.teams[k]);
    return db;
  }
  function memoryFor(db,teamName,gameNumber){db=normalizeDb(db);const t=db.teams[teamKey(teamName,gameNumber)];if(!t)return [];
    return Object.entries(t.players).map(([number,p])=>({number,name:p.n,isGoalie:p.g,count:p.c,src:p.s}));}
  function stats(db){db=normalizeDb(db);const teams=Object.values(db.teams);return {teams:teams.length,players:teams.reduce((s,t)=>s+Object.keys(t.players).length,0)};}
  function mergeDb(a,b){a=normalizeDb(a);b=normalizeDb(b);for(const [k,t] of Object.entries(b.teams)){const cur=a.teams[k];
      if(!cur){a.teams[k]=t;continue;}for(const [n,p] of Object.entries(t.players)){const q=cur.players[n];if(!q||p.t>q.t)cur.players[n]=p;}cur.t=Math.max(cur.t,t.t);}return a;}
  /* Suggestions for one team. scanned: players in the app. reference: [{number,name,isGoalie,count,src}].
     exact=true: reference is the lineup of THIS game (EHV game report) -> also missing players and goalies. */
  function suggest(scanned,reference,exact,sourceLabel){
    const out=[],have=new Map(scanned.map(p=>[String(p.number),p]));const used=new Set(scanned.map(p=>String(p.number)));
    const ref=(reference||[]).filter(r=>r&&r.number&&r.name);const matchedRef=new Set();
    for(const p of scanned){const num=String(p.number);const r=ref.find(x=>String(x.number)===num);
      if(r&&samePerson(r.name,p.name)){matchedRef.add(r);
        if(fold(r.name)!==fold(p.name)&&similarity(r.name,p.name)<1)out.push({kind:'name',number:num,from:p.name,to:r.name,src:sourceLabel});
        if((exact||r.count>=2)&&!!r.isGoalie!==!!p.isGoalie)out.push({kind:'goalie',number:num,name:p.name,to:!!r.isGoalie,src:sourceLabel});
        continue;}
      // Same person under another number (e.g. OCR read 23 instead of 29).
      const other=ref.find(x=>!matchedRef.has(x)&&samePerson(x.name,p.name)&&String(x.number)!==num);
      if(other&&!used.has(String(other.number))){matchedRef.add(other);out.push({kind:'number',number:num,to:String(other.number),name:p.name,src:sourceLabel});continue;}
      if(r&&exact)out.push({kind:'name',number:num,from:p.name,to:r.name,src:sourceLabel,different:true});}
    if(exact)for(const r of ref){if(matchedRef.has(r)||have.has(String(r.number)))continue;if(scanned.some(p=>samePerson(p.name,r.name)))continue;
      out.push({kind:'missing',number:String(r.number),to:r.name,isGoalie:!!r.isGoalie,src:sourceLabel});}
    return out;
  }
  function applySuggestions(players,list){
    const res=players.map(p=>Object.assign({},p));
    for(const s of list){const p=res.find(x=>String(x.number)===String(s.number));
      if(s.kind==='name'&&p){p.name=s.to;if(p.check)p.check=p.check.filter(c=>!/^Name|unsicher|prüfen/i.test(c)||/Nummer/.test(c));if(p.check&&!p.check.length)delete p.check;}
      else if(s.kind==='goalie'&&p)p.isGoalie=!!s.to;
      else if(s.kind==='number'&&p&&!res.some(x=>String(x.number)===String(s.to))){p.number=String(s.to);if(p.check)p.check=p.check.filter(c=>!/^Nummer/.test(c));if(p.check&&!p.check.length)delete p.check;}
      else if(s.kind==='missing'&&!res.some(x=>String(x.number)===String(s.number)))res.push({id:'m'+s.number+'-'+Math.random().toString(36).slice(2,7),number:String(s.number),name:s.to,isGoalie:!!s.isGoalie,starter:false});}
    return res;
  }
  function describe(s){
    if(s.kind==='name')return '#'+s.number+': „'+s.from+'“ → „'+s.to+'“';
    if(s.kind==='number')return s.name+': #'+s.number+' → #'+s.to;
    if(s.kind==='goalie')return '#'+s.number+' '+s.name+(s.to?': ist Torwart':': kein Torwart');
    return '#'+s.number+' '+s.to+(s.isGoalie?' (TW)':'')+' ergänzen';
  }
  /* ---------------- EHV (hockeydata) ---------------- */
  const EHV={api:'https://api.hockeydata.net/data/ebel/',page:'https://ehv-nrw.de/leagues/next-games/',
    // Fallback (ehv-nrw.de, 20.11.2026); read fresh from the EHV page when reachable.
    key:'f4b71c8702bd3a6eadc89becf6da5a4e',
    divisions:'21419,21420,21623,21627,21628,21632,21633,21637,21648,21652,21656,21660,21664,21668,21669,21673,21674,21675,21679,21680,21681,21691,21692,21693,22359,22386,22387,22388'.split(','),
    allGames:'%7B%22live%22%3Afalse%2C%22semantic%22%3Atrue%2C%22noScorers%22%3Atrue%7D'};
  const SCHEDULE_TTL=6*3600*1000;
  function parseJson(text){const t=String(text||'').trim();const s=t[0]==='{'?t:t.replace(/^[^(]*\(/,'').replace(/\);?\s*$/,'');return JSON.parse(s);}
  function scheduleRows(json,div){const rows=json&&json.data&&json.data.rows;return Array.isArray(rows)?rows.map(r=>({d:String(r.divisionId||div),id:r.id,n:r.gameName||'',s:r.gameStatus,t:r.gameUtcTimestamp||0,h:r.homeTeamLongName||'',a:r.awayTeamLongName||''})):[];}
  // "SONSTWER-MEIER" -> "Sonstwer-Meier" (same style as the OCR names); mixed case stays as it is.
  const nice=v=>{v=String(v||'').trim().replace(/\s+/g,' ');return v&&v===v.toUpperCase()?v.toLocaleLowerCase('de').replace(/(^|[\s\-'])(\p{L})/gu,(m,a,b)=>a+b.toLocaleUpperCase('de')):v;};
  function reportPlayers(json,side){const d=json&&json.data||{};const pick=(arr,g)=>(Array.isArray(arr)?arr:[]).map(p=>({number:String(p.playerJerseyNr==null?'':p.playerJerseyNr).replace(/\D/g,''),
      name:[nice(p.playerLastname),nice(p.playerFirstname)].filter(Boolean).join(', '),isGoalie:g})).filter(p=>p.number&&p.name);
    return pick(d[side+'FieldPlayers'],false).concat(pick(d[side+'GoalKeepers'],true));}
  function sameTeam(a,b,cls,gameName){const x=teamNorm(a),y=teamNorm(b);if(!x||!y)return false;if(x===y)return true;
    // "Neusser EV" on the sheet vs "Neusser EV U13" / "Neusser EV 1b" in hockeydata only within the same age class.
    const base=s=>s.replace(/\b(u\d{1,2}|1b|1c|2|ii|iii|junioren|jugend|kleinschueler|schueler|knaben|bambini|damen|frauen|senioren)\b/g,'').replace(/\s+/g,' ').trim();
    return !!cls&&ageClass(gameName)===cls&&base(x)===base(y);}
  async function ehvLookup(opts){
    const fetchText=opts.fetchText,cache=opts.cache||{},now=opts.now||Date.now(),cls=ageClass(opts.gameNumber),progress=opts.progress||(()=>{});
    let key=EHV.key,divisions=EHV.divisions;
    try{const html=await fetchText(EHV.page);const mk=/"apiKey"\s*:\s*"([0-9a-fA-F]+)"/.exec(html);const ids=[...html.matchAll(/"divisionId"\s*:\s*"(\d+)"/g)].map(m=>m[1]);
      if(mk&&ids.length){key=mk[1];divisions=[...new Set(ids)];}}catch(_){/* fallback values stay */}
    let rows=cache.rows&&now-(cache.at||0)<SCHEDULE_TTL?cache.rows:null,fresh=false;
    if(!rows){rows=[];let done=0,failed=0;const queue=divisions.slice();
      const worker=async()=>{while(queue.length){const d=queue.shift();try{rows.push(...scheduleRows(parseJson(await fetchText(EHV.api+'Schedule?apiKey='+key+'&divisionId='+d+'&referer=ehv-nrw.de&widgetOptions='+EHV.allGames)),d));}catch(_){failed++;}progress(++done,divisions.length);}};
      await Promise.all(Array.from({length:6},worker));
      if(!rows.length)throw new Error(failed?'EHV nicht erreichbar':'Keine Spiele gefunden');fresh=true;}
    const report=async r=>parseJson(await fetchText(EHV.api+'GetGameReport?apiKey='+key+'&divisionId='+r.d+'&gameId='+encodeURIComponent(r.id)+'&referer=ehv-nrw.de'));
    const result={home:[],away:[],exact:false,game:null,rows:fresh?rows:null,games:0};
    const num=String(opts.gameNumber||'').trim().toLowerCase();
    const game=num&&rows.find(r=>String(r.n).toLowerCase()===num);
    if(game){try{const rep=await report(game);const h=reportPlayers(rep,'home'),a=reportPlayers(rep,'away');
        if(h.length||a.length){
          // The sheet's home team must be the report's home team; otherwise sides are swapped.
          const swap=opts.homeName&&sameTeam(opts.homeName,game.a,cls,game.n)&&!sameTeam(opts.homeName,game.h,cls,game.n);
          result.home=swap?a:h;result.away=swap?h:a;result.exact=true;result.game=game;result.games=1;return result;}}catch(_){/* fall back to recent games */}}
    for(const side of ['home','away']){const name=opts[side+'Name'];if(!name)continue;
      const recent=rows.filter(r=>r.s===4&&(sameTeam(name,r.h,cls,r.n)||sameTeam(name,r.a,cls,r.n))&&(!cls||ageClass(r.n)===cls)).sort((x,y)=>y.t-x.t).slice(0,3);
      const seen=new Map();
      for(const r of recent){try{const rep=await report(r);const which=sameTeam(name,r.h,cls,r.n)?'home':'away';result.games++;
          for(const p of reportPlayers(rep,which)){const cur=seen.get(p.number);if(!cur)seen.set(p.number,Object.assign({count:1,src:'ehv'},p));else if(samePerson(cur.name,p.name))cur.count++;}}catch(_){}}
      result[side]=[...seen.values()];}
    return result;
  }
  return {DB_VERSION,fold,ageClass,teamKey,similarity,samePerson,emptyDb,normalizeDb,learn,memoryFor,stats,mergeDb,suggest,applySuggestions,describe,
    EHV,parseJson,scheduleRows,reportPlayers,sameTeam,ehvLookup};
});
