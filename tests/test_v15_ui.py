"""1.5 UI regressions on the shipped DOM/JS/CSS (Chromium). No real Android device.
Covers: wizard order and constant height, keypad position/size, skip button below keypad,
quick penalties, timeout incl. one-per-team question, newest-first history, danger dialog,
OCR review dialogs (names, goalies, starting goalie) with mocked OCR output.
"""
from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright,expect
from test_ui import boot,state,digits,next_,skip_operator,add_player,select_setup,confirm,cancel_choice,assert_fit
import os
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v15')
OUT.mkdir(parents=True,exist_ok=True)
CHROMIUM=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None))
KEY='nev-spielnotiz-v0.1'

def game(p):p.get_by_role('button',name='Spiel',exact=True).click();skip_operator(p)
def wiz_h(p):return round(p.locator('#wizard').bounding_box()['height'],1)
def key_box(p):return p.locator('[data-digit="5"]').bounding_box()

def roster():
    return {'version':7,'currentPeriod':1,'meta':{'date':'2026-10-18','number':'T_015','operatorName':'','operatorPrompted':True},
      'home':{'name':'Neusser EV','players':[{'id':'h30','number':'30','name':'Alex Torwart','isGoalie':True,'starter':True},{'id':'h35','number':'35','name':'Kim Ersatz','isGoalie':True,'starter':False},{'id':'h56','number':'56','name':'Max Beispiel'},{'id':'h18','number':'18','name':'Luca Muster'},{'id':'h12','number':'12','name':'Sam Beispiel'}],'startGoalie':'30'},
      'away':{'name':'Ratinger Ice Aliens','players':[{'id':'a20','number':'20','name':'Robin Gast'}],'startGoalie':''},'events':[]}

def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox'])
    errors=[]
    # ---- Wizard: order, constant height, keypad identical in all goal number stages.
    for size in [(320,480),(360,640),(390,844),(412,915)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(roster())});game(p);p.locator('#new-event').click()
      heights=[wiz_h(p)];assert_fit(p);digits(p,'1012');next_(p)
      assert p.locator('#wizard-title').inner_text()=='Was ist passiert?',p.locator('#wizard-title').inner_text()
      assert p.locator('[data-type]').count()==6 and p.locator('[data-type="timeout"]').count()==1   # 2.7: + Penalty, Notiz
      heights.append(wiz_h(p));assert_fit(p);p.locator('[data-type="goal"]').click()
      assert p.locator('#wizard-title').inner_text()=='Welche Mannschaft?'
      heights.append(wiz_h(p));assert_fit(p);p.locator('[data-team="home"]').click()
      p.locator('[data-action="other-number"]').click()   # 1.9: keypad path via "Andere Nummer"
      k0=key_box(p);heights.append(wiz_h(p));assert_fit(p)
      if size==(360,640):p.screenshot(path=str(OUT/'tor-schuetze-360x640.png'))
      digits(p,'56');next_(p);k1=key_box(p);heights.append(wiz_h(p));assert_fit(p)
      skip=p.locator('[data-action="skip-assists"]').bounding_box();assert skip['y']>k1['y']+k1['height'],'skip button below keypad'
      if size==(360,640):p.screenshot(path=str(OUT/'assist1-360x640.png'))
      digits(p,'18');next_(p);k2=key_box(p);heights.append(wiz_h(p));assert_fit(p)
      assert p.locator('[data-action="skip-assists"]').bounding_box()['y']>k2['y']+k2['height']
      assert k0==k1==k2,(size,k0,k1,k2)
      assert len(set(heights))==1,(size,heights)
      if size[1]>=640:assert k0['height']>=60,(size,k0)   # 1.4: 49 px
      else:assert k0['height']>=40,(size,k0)
      p.locator('[data-action="skip-assists"]').click();ev=state(p)['events'][-1]
      assert ev['type']=='goal' and ev['player']=='56' and ev['assist1']=='18' and ev['assist2']==''
      # Penalty and goalie stages keep the same height; 8 quick penalties incl. the two new ones.
      p.locator('#new-event').click();digits(p,'1000');next_(p);p.locator('[data-type="penalty"]').click();p.locator('[data-team="away"]').click()
      assert wiz_h(p)==heights[0];digits(p,'20');next_(p);assert wiz_h(p)==heights[0];assert_fit(p)
      quick=p.locator('.penalty-list [data-penalty]').all_text_contents()   # 2.1: full list by frequency
      assert 'Übertriebene Härte' in quick[:8] and 'Bandencheck' in quick[:8],quick
      if size==(360,640):p.screenshot(path=str(OUT/'strafe-360x640.png'))
      p.locator('[data-penalty="Bandencheck"]').click();assert state(p)['events'][-1]['penalty']=='Bandencheck'
      p.locator('#new-event').click();digits(p,'900');next_(p);p.locator('[data-type="goalie"]').click();p.locator('[data-team="home"]').click()
      assert wiz_h(p)==heights[0];assert_fit(p)
      assert p.locator('[data-goalie-field="goalieOut"] strong').inner_text()=='#30'
      p.locator('#wizard-close').click();confirm(p)
      p.close()
    # ---- Timeout, one per team; newest entry first; latest row fully visible.
    for size in [(360,640),(390,844)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(roster())});game(p)
      def goal(clock,player='56'):
        p.locator('#new-event').click();digits(p,clock);next_(p)
        if p.locator('#time-jump-dialog').is_visible():p.locator('#time-jump-retro').click()
        p.locator('[data-type="goal"]').click();p.locator('[data-team="home"]').click();digits(p,player);next_(p);p.locator('[data-action="skip-assists"]').click()
        if p.locator('#choice-dialog').is_visible():confirm(p)
      def timeout(clock,team):
        p.locator('#new-event').click();digits(p,clock);next_(p)
        if p.locator('#time-jump-dialog').is_visible():p.locator('#time-jump-retro').click()
        p.locator('[data-type="timeout"]').click();p.locator('[data-team="'+team+'"]').click()
      goal('1500');timeout('1200','home');expect(p.locator('#wizard')).not_to_be_visible()
      ev=state(p)['events'][-1];assert ev['type']=='timeout' and ev['team']=='home' and ev['player']==''
      # second home timeout: question, cancel keeps 1, confirm stores
      timeout('800','home');expect(p.locator('#choice-dialog')).to_be_visible()
      assert 'Timeout bereits genommen' in p.locator('#choice-title').inner_text() and 'nur ein Timeout' in p.locator('#choice-text').inner_text()
      cancel_choice(p);assert sum(e['type']=='timeout' for e in state(p)['events'])==1
      p.locator('#wizard-close').click();confirm(p)
      timeout('700','away');expect(p.locator('#wizard')).not_to_be_visible()   # other team: no question
      goal('1900')   # retro entry with earlier game time -> must still be on top
      clocks=p.locator('.event-clock').all_text_contents();assert clocks==['1900','700','1200','1500'],clocks
      first=p.locator('.event-row').first;assert 'latest' in first.get_attribute('class')
      box=first.bounding_box();assert box['y']+box['height']<=size[1],(size,box)
      assert p.locator('.event-row').nth(1).evaluate('e=>!e.classList.contains("latest")')
      p.screenshot(path=str(OUT/f'spielverlauf-{size[0]}x{size[1]}.png'))
      # report stays chronological, timeout visible in report, text and print
      p.get_by_role('button',name='Bericht',exact=True).click()
      rows=p.locator('#report-sheet tbody tr .time-clock').all_text_contents();assert rows==['1900','1500','1200','700'],rows
      assert p.locator('#report-sheet tr.timeout').count()==2
      txt=p.evaluate('EgrepUI.reportText()');assert 'Timeout' in txt
      line=[l for l in txt.split('\n') if 'Timeout' in l][0];assert not line.endswith('| '),line
      p.evaluate('EgrepUI.preparePrintReport()');assert p.locator('#print-output tr.timeout').count()==2
      # danger confirmation is visually distinct
      # 2.0: reset archives the game (normal OK); destructive confirms (delete) stay marked as danger.
      p.locator('#reset-game').click();assert p.locator('#choice-confirm').get_attribute('class')=='primary';cancel_choice(p)
      p.get_by_role('button',name='Spiel',exact=True).click();p.locator('[data-action="show-event"]').first.click();p.locator('#detail-edit').click()
      p.locator('[data-action="delete-event"]').click()
      assert 'danger-confirm' in p.locator('#choice-confirm').get_attribute('class');cancel_choice(p);p.locator('#wizard-close').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      p.close()
    # ---- OCR review with mocked recognition output (no real image recognition claimed).
    p=b.new_page(viewport={'width':360,'height':640});p.on('pageerror',lambda e:errors.append(str(e)));boot(p)
    p.evaluate('''()=>{window.EgrepOCR.start=()=>({promise:Promise.resolve({
      home:[{id:'1',number:'30',name:'Alex Torwart',isGoalie:false,starter:false},{id:'2',number:'31',name:'Ben Keeper',isGoalie:false,starter:false},{id:'3',number:'56',name:'M4x Beispiel',isGoalie:false,starter:false},{id:'4',number:'77',name:'Xqzt Brm',isGoalie:false,starter:false},{id:'5',number:'18',name:'Luca Muster',isGoalie:false,starter:false}],
      away:[{id:'6',number:'1',name:'Robin Gast',isGoalie:true,starter:false},{id:'7',number:'9',name:'Kim Feld',isGoalie:false,starter:false}],
      teamNames:['Neusser EV','Ratinger Ice Aliens'],gameNumber:'U13_LL_005'}),cancel:()=>{}})}''')
    select_setup(p);p.locator('#photo-input').set_input_files(str(Path(__file__).resolve().parents[1]/'app/src/main/assets/nev-logo.png'))
    # 1.6: no name list any more; implausible names are only marked yellow in Aufstellung.
    expect(p.locator('#review-dialog')).to_be_visible();assert p.locator('#review-title').inner_text()=='Kein Torwart erkannt'
    assert p.evaluate('document.activeElement.id')=='review-title','no keyboard pops up on open'
    p.screenshot(path=str(OUT/'ocr-kein-torwart.png'))
    p.locator('[data-pick="30"]').click();p.locator('[data-pick="31"]').click();p.locator('[data-review="apply"]').click()
    assert p.locator('#review-title').inner_text()=='Starting-Goalie?'
    p.locator('[data-pick="30"]').click();p.locator('[data-pick="31"]').click()   # single select: last tap wins
    assert p.locator('[data-pick="30"]').get_attribute('aria-pressed')=='false'
    p.locator('[data-review="apply"]').click()
    home=state(p)['home'];assert home['startGoalie']=='31' and sorted(x['number'] for x in home['players'] if x['isGoalie'])==['30','31']
    assert p.locator('#review-title').inner_text()=='Nur ein Torwart erkannt' and 'Ratinger' in p.locator('#review-copy').inner_text()
    p.locator('[data-review="skip"]').click();expect(p.locator('#review-dialog')).not_to_be_visible()
    assert [x['number'] for x in state(p)['away']['players'] if x['isGoalie']]==['1']
    expect(p.locator('#metadata-dialog')).not_to_be_visible()   # names and game number were recognised
    names={x['number']:x['name'] for x in state(p)['home']['players']};assert names['56']=='M4x Beispiel' and names['77']=='Xqzt Brm',names
    assert p.locator('#teams .player-row.needs-check').count()==2 and '2 Namen bitte' in p.locator('.check-hint').inner_text()
    bg=p.locator('#teams .player-row.needs-check').first.evaluate('e=>getComputedStyle(e).backgroundColor');assert bg=='rgb(255, 246, 201)',bg
    p.screenshot(path=str(OUT/'aufstellung-gelb.png'),full_page=True)
    # Opening and saving (unchanged) clears the mark; it persists across restart until then.
    q=b.new_page(viewport={'width':360,'height':640});boot(q,p.evaluate('window._saved'));select_setup(q)
    assert q.locator('#teams .player-row.needs-check').count()==2;q.close()
    row=p.locator('#teams .player-row.needs-check').first;row.locator('[data-action="edit-player"]').click()
    p.locator('#player-form button[type="submit"]').click()
    assert p.locator('#teams .player-row.needs-check').count()==1 and '1 Name bitte' in p.locator('.check-hint').inner_text()
    p.locator('#undo').click();assert p.locator('#teams .player-row.needs-check').count()==2   # undo restores the mark
    p.locator('#undo').click();assert state(p)['home']['startGoalie']==''   # each answer is its own undo step
    # Back button closes a review question without changing data.
    p.evaluate('''()=>{window.EgrepOCR.start=()=>({promise:Promise.resolve({home:[{id:'9',number:'5',name:'Leon',isGoalie:false,starter:false}],away:[],teamNames:['Neusser EV','Gast X'],gameNumber:'X_1'}),cancel:()=>{}})}''')
    p.locator('#photo-input').set_input_files(str(Path(__file__).resolve().parents[1]/'app/src/main/assets/nev-logo.png'))
    expect(p.locator('#review-dialog')).to_be_visible();p.evaluate('window.egrepBack()')
    assert state(p)['home']['players'][0]['name']=='Leon'
    assert not errors,errors;b.close()
  print('V15 UI PASS: type->team order, constant wizard height, identical keypad position, larger keys, skip below keypad, 8 quick penalties, timeout + one-per-team question, newest-first history fully visible, chronological report, danger confirm, OCR yellow name marks + goalie/starter review. Real Android not tested.')
if __name__=='__main__':main()
