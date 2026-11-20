"""3.2 UI: 'Bisher' while editing, player memory + EHV comparison (mocked network), backup save/restore,
update check (mocked version file), settings switches. Chromium with the real assets, fantasy names only."""
from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright,expect
from uihelper import boot,state,skip_operator,CHROMIUM
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v32');OUT.mkdir(parents=True,exist_ok=True)
KEY='nev-spielnotiz-v0.1';SET='egrep-settings';MEM='egrep-spieler-v1';ARCH='egrep-notes-archiv-v1'
HOME=[('30','Torwart, Tom',True),('7','Schlöber, Tim',False),('23','Wenz, Luca',False),('9','Engel, Ola',False)]
def game(events=None,number='U13_LL_005'):
    return {'version':9,'currentPeriod':1,'meta':{'date':'2026-11-21','number':number,'operatorName':'','operatorPrompted':True,'timeMode':'down'},
      'home':{'name':'Neusser EV','players':[{'id':'h'+n,'number':n,'name':nm,'isGoalie':g,'starter':n=='30'} for n,nm,g in HOME],'startGoalie':'30'},
      'away':{'name':'EC Musterstadt','players':[{'id':'a4','number':'4','name':'Gast, Gina','isGoalie':False}],'startGoalie':''},
      'events':events or [],'shootout':[]}
GOAL={'id':'e1','order':1,'type':'goal','team':'home','period':1,'time':'08:00','clock':'1200','player':'9','assist1':'7','assist2':''}
PEN={'id':'e2','order':2,'type':'penalty','team':'away','period':1,'time':'09:00','clock':'1100','player':'4','bench':False,'penalty':'Haken','penaltyDuration':'2'}
MEMORY={'version':1,'teams':{'neusser ev|u13':{'name':'Neusser EV','t':1,'players':{
  '7':{'n':'Schlößer, Tim','g':False,'c':3,'t':1,'s':'app'},'29':{'n':'Wenz, Luca','g':False,'c':2,'t':1,'s':'app'},'30':{'n':'Torwart, Tom','g':True,'c':2,'t':1,'s':'app'}}}}}
MOCK_EHV='''()=>{window.egrepFetchText=async url=>{
  if(url.startsWith('https://ehv-nrw.de'))throw new Error('x');
  if(url.includes('/Schedule?'))return JSON.stringify(url.includes('divisionId=21419')?{data:{rows:[{id:'g1',divisionId:21419,gameName:'U13_LL_005',homeTeamLongName:'Neusser EV',awayTeamLongName:'EC Musterstadt',gameStatus:0,gameUtcTimestamp:1}]}}:{data:{rows:[]}});
  if(url.includes('GetGameReport'))return JSON.stringify({data:{homeFieldPlayers:[{playerJerseyNr:'7',playerLastname:'SCHLÖSSER',playerFirstname:'TIM'}],homeGoalKeepers:[{playerJerseyNr:'30',playerLastname:'TORWART',playerFirstname:'TOM'}],
     awayFieldPlayers:[{playerJerseyNr:'4',playerLastname:'GAST',playerFirstname:'GINA'},{playerJerseyNr:'11',playerLastname:'ELF',playerFirstname:'EDDA'}],awayGoalKeepers:[]}});
  throw new Error('unerwartet '+url);};}'''
def saved(p):return p.evaluate('window._saved')
def open_settings(p):p.locator('#open-menu').click();p.locator('#open-settings').click();expect(p.locator('#settings-dialog')).to_be_visible()

def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox']);errors=[]
    # ---------- 1) editing shows the saved entry ----------
    for size in [(320,480),(412,915)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(game([GOAL,PEN]))},auto_ok=False) if False else boot(p,{KEY:json.dumps(game([GOAL,PEN]))})
      p.get_by_role('button',name='Spiel',exact=True).click();skip_operator(p)
      p.locator('.event-row').filter(has_text='Tor').first.click();p.locator('#detail-edit').click();expect(p.locator('#wizard')).to_be_visible()
      ctx=p.locator('#wizard-context').inner_text();assert ctx.startswith('Bisher:') and 'Tor' in ctx and 'Neusser EV' in ctx and '#9' in ctx and 'A #7' in ctx,ctx
      p.locator('[data-action="next"]').click()
      if p.locator('#time-jump-dialog').is_visible():p.locator('#time-jump-retro').click()
      expect(p.locator('#wizard-title')).to_have_text('Was ist passiert?')
      prev=p.locator('#wizard-content .previous');assert prev.count()==1 and prev.get_attribute('data-type')=='goal' and 'bisher' in prev.inner_text(),prev.count()
      if size==(320,480):p.screenshot(path=str(OUT/'bearbeiten-bisher-320x480.png'))
      fit=p.locator('#wizard').evaluate('n=>[n.clientWidth,n.scrollWidth]');assert fit[1]<=fit[0]+1,fit
      p.locator('[data-type="goal"]').click();prev=p.locator('#wizard-content .previous');assert prev.get_attribute('data-team')=='home' and 'bisher' in prev.inner_text()
      p.locator('[data-team="home"]').click()
      marked=sorted(x.get_attribute('data-pick-number') for x in p.locator('#wizard-content [data-pick-number].previous').all());assert marked==['7','9'],marked
      assert 'Bisher:' in p.locator('#wizard-context').inner_text()
      p.locator('#wizard-close').click()
      if p.locator('#choice-dialog').is_visible():p.locator('#choice-confirm').click()
      # penalty: penalty type and duration marked
      p.locator('.event-row').filter(has_text='Haken').first.click();p.locator('#detail-edit').click()
      assert 'Strafe' in p.locator('#wizard-context').inner_text() and 'Haken' in p.locator('#wizard-context').inner_text()
      p.locator('[data-action="next"]').click()
      if p.locator('#time-jump-dialog').is_visible():p.locator('#time-jump-retro').click()
      p.locator('[data-type="penalty"]').click();p.locator('[data-team="away"]').click()
      if p.locator('[data-pick-number="4"]').count():p.locator('[data-pick-number="4"]').click()
      assert p.locator('[data-penalty="Haken"].previous').count()==1 and p.locator('[data-duration="2"].previous').count()==1
      # a new entry never shows "Bisher"
      p.locator('#wizard-close').click()
      if p.locator('#choice-dialog').is_visible():p.locator('#choice-confirm').click()
      p.locator('#new-event').click();assert not p.locator('#wizard-context').inner_text().startswith('Bisher') and p.locator('#wizard-content .previous').count()==0
      p.close()
    # ---------- 2) player memory + EHV ----------
    p=b.new_page(viewport={'width':360,'height':640});p.on('pageerror',lambda e:errors.append(str(e)))
    boot(p,{KEY:json.dumps(game()),MEM:json.dumps(MEMORY),SET:json.dumps({'ehv':False})})
    p.locator('#roster-check').click();expect(p.locator('#review-dialog')).to_be_visible()
    texts=[x.inner_text() for x in p.locator('#review-body [data-pick]').all()]
    assert texts==['#7: „Schlöber, Tim“ → „Schlößer, Tim“','Wenz, Luca: #23 → #29','#30 Torwart, Tom: ist Torwart'] or set(texts)=={'#7: „Schlöber, Tim“ → „Schlößer, Tim“','Wenz, Luca: #23 → #29'},texts
    assert 'Spieler-Gedächtnis' in p.locator('#review-copy').inner_text()
    p.screenshot(path=str(OUT/'abgleich-gedaechtnis-360x640.png'))
    p.locator('#review-body [data-pick]').nth(1).click()  # deselect the number suggestion
    p.locator('[data-review="apply"]').click()
    hp={x['number']:x['name'] for x in state(p)['home']['players']};assert hp['7']=='Schlößer, Tim' and '23' in hp and '29' not in hp,hp
    assert 'übernommen' in p.locator('#roster-check-status').inner_text()
    p.locator('#undo').click();assert {x['number']:x['name'] for x in state(p)['home']['players']}['7']=='Schlöber, Tim','undo restores'
    # "Nichts ändern" changes nothing
    p.locator('#roster-check').click();p.locator('[data-review="none"]').click();assert {x['number']:x['name'] for x in state(p)['home']['players']}['7']=='Schlöber, Tim'
    # EHV on: exact lineup of this game (mocked), memory learns names (no birthdates in storage)
    open_settings(p);p.locator('#ehv-toggle').check();p.locator('#close-settings').click()
    assert json.loads(saved(p)[SET])['ehv'] is True
    p.evaluate(MOCK_EHV);p.locator('#roster-check').click();expect(p.locator('#review-dialog')).to_be_visible()
    assert 'EHV-Spielbericht U13_LL_005' in p.locator('#review-copy').inner_text(),(p.locator('#review-copy').inner_text(),p.locator('#roster-check-status').inner_text())
    texts=[x.inner_text() for x in p.locator('#review-body [data-pick]').all()]
    assert '#11 Elf, Edda ergänzen' in texts and any('Schlößer' in t or 'Schlösser' in t for t in texts),texts
    p.locator('[data-review="apply"]').click()
    ap={x['number']:x['name'] for x in state(p)['away']['players']};assert ap.get('11')=='Elf, Edda',ap
    mem=json.loads(saved(p)[MEM]);assert 'ec musterstadt|u13' in mem['teams'] and 'birth' not in json.dumps(mem).lower()
    cache=json.loads(saved(p)['egrep-ehv-cache-v1']);assert cache['rows'] and all(set(r)<= {'d','id','n','s','t','h','a'} for r in cache['rows'])
    # EHV unreachable -> memory only, clear note
    p.evaluate("()=>{window.egrepFetchText=async()=>{throw new Error('offline')};}");p.evaluate("()=>{delete window._saved['egrep-ehv-cache-v1']}")
    p.locator('#roster-check').click();p.wait_for_timeout(300)
    if p.locator('#review-dialog').is_visible():p.locator('[data-review="none"]').click()
    assert 'EHV nicht erreichbar' in p.locator('#roster-check-status').inner_text(),p.locator('#roster-check-status').inner_text()
    # learning at "Neues Spiel": confirmed players of both teams
    p.evaluate("()=>{delete window._saved['egrep-spieler-v1']}")
    p.get_by_role('button',name='Bericht',exact=True).click();skip_operator(p);p.locator('#reset-game').click();p.locator('#choice-confirm').click();skip_operator(p)
    mem=json.loads(saved(p)[MEM]);assert set(mem['teams'])=={'neusser ev|u13','ec musterstadt|u13'},mem['teams'].keys()
    open_settings(p);assert 'Spieler aus 2 Mannschaften' in p.locator('#memory-stats').inner_text()
    p.locator('#memory-clear').click();p.locator('#choice-confirm').click();assert MEM not in saved(p)
    p.locator('#close-settings').click();p.close()
    # ---------- 3) backup ----------
    p=b.new_page(viewport={'width':360,'height':640},accept_downloads=True);p.on('pageerror',lambda e:errors.append(str(e)))
    arch=[{'id':'old1','archivedAt':'2026-11-01T10:00:00Z','date':'2026-11-01','number':'U13_LL_001','home':'Neusser EV','away':'Grefrather EG','score':'3:2','state':game([GOAL],'U13_LL_001')}]
    boot(p,{KEY:json.dumps(game([GOAL])),ARCH:json.dumps(arch),MEM:json.dumps(MEMORY),SET:json.dumps({'homeClub':'krefelder-ev','swipe':False})})
    open_settings(p)
    with p.expect_download() as dl:p.locator('#backup-save').click()
    d=dl.value;assert d.suggested_filename.startswith('eGrep-Notes-Sicherung-') and d.suggested_filename.endswith('.json')
    data=json.loads(Path(d.path()).read_text());assert data['format']=='egrep-notes-backup' and data['game']['events'][0]['id']=='e1' and len(data['archive'])==1 and data['players']['teams'] and data['settings']['homeClub']=='krefelder-ev'
    (OUT/'sicherung.json').write_text(json.dumps(data))
    # restore on an "empty phone": everything back
    q=b.new_page(viewport={'width':360,'height':640});q.on('pageerror',lambda e:errors.append(str(e)));boot(q)
    open_settings(q);q.locator('#backup-input').set_input_files(str(OUT/'sicherung.json'));expect(q.locator('#choice-dialog')).to_be_visible()
    assert '1 archivierten Spielen' in q.locator('#choice-text').inner_text();q.locator('#choice-confirm').click()
    s=state(q);assert s['events'][0]['id']=='e1' and len(json.loads(saved(q)[ARCH]))==1 and json.loads(saved(q)[MEM])['teams']
    assert json.loads(saved(q)[SET])['homeClub']=='krefelder-ev' and q.evaluate("document.querySelector('.app-header img').alt")=='Krefelder EV'
    # restore again: nothing duplicated
    open_settings(q);q.locator('#backup-input').set_input_files(str(OUT/'sicherung.json'));q.locator('#choice-confirm').click();assert len(json.loads(saved(q)[ARCH]))==1
    # running other game -> goes to the archive first; invalid files are refused
    q.evaluate("s=>window.EgrepUI&&0",None);other=game([PEN],'U13_LL_009');boot(q,{KEY:json.dumps(other)})
    open_settings(q);q.locator('#backup-input').set_input_files(str(OUT/'sicherung.json'));q.locator('#choice-confirm').click()
    a=json.loads(saved(q)[ARCH]);assert len(a)==2 and any(x['number']=='U13_LL_009' for x in a) and state(q)['events'][0]['id']=='e1',[x['number'] for x in a]
    (OUT/'kaputt.json').write_text('{"format":"irgendwas"}');open_settings(q);q.locator('#backup-input').set_input_files(str(OUT/'kaputt.json'))
    expect(q.locator('#toast')).to_contain_text('keine eGrep-Notes-Sicherung');q.close();p.close()
    # ---------- 4) update check ----------
    p=b.new_page(viewport={'width':360,'height':640});p.on('pageerror',lambda e:errors.append(str(e)))
    boot(p)
    p.evaluate("()=>{window.egrepFetchText=async u=>{window._asked=u;return JSON.stringify({version:'9.9',download:'https://cappy0815.github.io/downloads/eGrep-Notes-v9.9.apk',page:'https://cappy0815.github.io/#egrep-notes'});};}")
    open_settings(p);assert p.locator('#update-toggle').is_checked();p.locator('#update-check').click()
    expect(p.locator('#update-status')).to_contain_text('Neue Version 9.9');assert p.evaluate('window._asked').startswith('https://cappy0815.github.io/downloads/egrep-notes.json')
    assert p.locator('#update-download').is_visible() and p.locator('#update-download').get_attribute('href')=='https://cappy0815.github.io/downloads/eGrep-Notes-v9.9.apk'
    p.screenshot(path=str(OUT/'update-360x640.png'))
    p.locator('#close-settings').click();assert 'has-update' in p.locator('#open-menu').get_attribute('class')
    p.evaluate("()=>{window.egrepFetchText=async()=>JSON.stringify({version:'1.0',download:'https://evil.example/x.apk'});}")
    open_settings(p);p.locator('#update-check').click();expect(p.locator('#update-status')).to_contain_text('Aktuell');assert not p.locator('#update-download').is_visible()
    p.evaluate("()=>{window.egrepFetchText=async()=>JSON.stringify({version:'9.9',download:'https://evil.example/x.apk'});}");p.locator('#update-check').click()
    expect(p.locator('#update-status')).to_contain_text('Neue Version');assert p.locator('#update-download').get_attribute('href')=='https://cappy0815.github.io/#egrep-notes','foreign download never linked'
    p.evaluate("()=>{window.egrepFetchText=async()=>{throw new Error('x')};}");p.locator('#update-check').click();expect(p.locator('#update-status')).to_contain_text('nicht erreichbar')
    p.locator('#update-toggle').uncheck();assert json.loads(saved(p)['egrep-update'])['auto'] is False;p.close()
    # automatic check: due -> asked once after start; switched off -> never
    for auto,expected in [(True,True),(False,False)]:
      p=b.new_page(viewport={'width':360,'height':640});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{'egrep-update':json.dumps({'auto':auto,'last':0})})
      p.evaluate("()=>{window._asked=null;window.egrepFetchText=async u=>{window._asked=u;return JSON.stringify({version:'0.1'})};}")
      p.wait_for_timeout(4600);assert bool(p.evaluate('window._asked'))==expected,auto;p.close()
    assert not errors,errors;b.close()
  print('V32 UI PASS: editing shows "Bisher" and marks type/team/numbers/penalty/duration (not for new entries); memory suggestions with deselect/apply/undo/none; EHV exact lineup (mocked) adds missing player and learns without birthdates; EHV unreachable noted; learning at new game; memory stats/clear; backup download, restore on empty device, no duplicates, running game archived first, invalid file refused; update check newer/current/foreign link/unreachable/auto on+off.')
if __name__=='__main__':main()
