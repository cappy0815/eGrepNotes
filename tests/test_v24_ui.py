"""2.4 UI: three time modes (Uhr ab / Uhr auf = hall clock counting up per period / Spielzeit),
migration of the 2.2/2.3 mode, centred referee signals. Chromium, no real Android."""
from pathlib import Path
import json,os,sys
from playwright.sync_api import sync_playwright,expect
from test_ui import boot,state,skip_operator,confirm,assert_fit
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v24');OUT.mkdir(parents=True,exist_ok=True)
CHROMIUM=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None))
KEY='nev-spielnotiz-v0.1'
def roster(meta=None):
    m={'date':'2026-10-24','number':'T_024','operatorName':'','operatorPrompted':True};m.update(meta or {})
    return {'version':9,'currentPeriod':1,'meta':m,
      'home':{'name':'Neusser EV','players':[{'id':'h30','number':'30','name':'Alex Torwart','isGoalie':True,'starter':True},{'id':'h12','number':'12','name':'Neumann, Mia'},{'id':'h48','number':'48','name':'Neumann, Leo'}],'startGoalie':'30'},
      'away':{'name':'EV Duisburg','players':[],'startGoalie':''},'events':[],'shootout':[]}
def game(p):p.get_by_role('button',name='Spiel',exact=True).click();skip_operator(p)
def keys(p,n):
    for x in n:p.locator('[data-digit="'+x+'"]').click()
def goal(p,raw,num='12',jump=None):
    p.locator('#new-event').click();keys(p,raw);p.locator('[data-action="next"]').click()
    if jump:
        expect(p.locator('#time-jump-dialog')).to_be_visible();p.locator('#time-jump-'+jump).click()
    else:assert not p.locator('#time-jump-dialog').is_visible(),'unexpected time jump question'
    p.locator('[data-type="goal"]').click();p.locator('[data-team="home"]').click();p.locator(f'[data-pick-number="{num}"]').click();p.locator('[data-action="pick-save"]').click()
    if p.locator('#choice-dialog').is_visible():confirm(p)
    expect(p.locator('#detail-dialog')).to_be_visible()

def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox']);errors=[]
    for size in [(320,480),(360,640),(412,915)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(roster())},auto_ok=False);game(p)
      btn=p.locator('#clock-mode')
      # ---- Cycle: Uhr ab -> Uhr auf -> Spielzeit -> Uhr ab; row still fits.
      labels=[btn.inner_text()]
      for _ in range(3):btn.click();labels.append(btn.inner_text())
      assert labels==['Uhr ab ▼','Uhr auf ▲','Spielzeit','Uhr ab ▼'],labels
      btn.click();assert state(p)['meta']['timeMode']=='up'
      row=p.locator('.screen-setting').evaluate('n=>[n.clientWidth,n.scrollWidth]');assert row[1]<=row[0]+1,row
      if size==(360,640):p.screenshot(path=str(OUT/'uhr-auf-hallenuhr-360x640.png'))
      # ---- Hall clock counting up: 5:12 in the 1st period -> remaining 14:48.
      p.locator('#new-event').click();assert p.locator('#wizard-title').inner_text()=='Uhr aufwärts · 1. Drittel'
      keys(p,'512');assert p.locator('.number-display').inner_text()=='05:12' and p.locator('.number-hint').inner_text()=='Spielzeit 5:12 (1)',p.locator('.number-hint').inner_text()
      assert_fit(p)
      if size==(360,640):p.screenshot(path=str(OUT/'uhr-auf-eingabe-360x640.png'))
      p.locator('#wizard-close').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      goal(p,'512');ev=state(p)['events'][-1];assert (ev['period'],ev['time'],ev['clock'])==(1,'14:48','1448'),ev
      assert p.locator('.detail-clock').inner_text()=='5:12' and 'Uhr (aufwärts)' in p.locator('.detail-band').inner_text() and 'Spielzeit 5:12 (1)' in p.locator('.detail-band').inner_text()
      p.locator('#detail-ok').click()
      goal(p,'1030','48');assert state(p)['events'][-1]['time']=='9:30';p.locator('#detail-ok').click()
      # Smaller time than before -> "Neues Drittel oder Nachtrag?" (question turned round for a rising clock).
      p.locator('#new-event').click();keys(p,'300');p.locator('[data-action="next"]').click()
      expect(p.locator('#time-jump-dialog')).to_be_visible();txt=p.locator('#time-jump-text').inner_text()
      assert 'Uhr 10:30' in txt and '3:00' in txt and 'kleiner' in txt,txt;assert p.locator('#time-jump-next').is_visible()
      if size==(360,640):p.screenshot(path=str(OUT/'uhr-auf-neues-drittel-360x640.png'))
      p.locator('#time-jump-next').click();p.locator('[data-type="goal"]').click();p.locator('[data-team="home"]').click();p.locator('[data-pick-number="12"]').click();p.locator('[data-action="pick-save"]').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      ev=state(p)['events'][-1];assert (ev['period'],ev['time'])==(2,'17:00'),ev;assert state(p)['currentPeriod']==2;p.locator('#detail-ok').click()
      # Later time in the same period -> no question; Nachtrag for an earlier time still possible.
      goal(p,'645');assert state(p)['events'][-1]['period']==2;p.locator('#detail-ok').click()
      goal(p,'100','48',jump='retro');assert (state(p)['events'][-1]['period'],state(p)['events'][-1]['time'])==(2,'19:00');p.locator('#detail-ok').click()
      # Invalid > 20:00.
      p.locator('#new-event').click();keys(p,'2001');assert 'ungültig' in p.locator('.number-hint').inner_text() and p.locator('[data-action="next"]').is_disabled()
      p.locator('#wizard-close').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      # History: game time + hall clock in grey; edit opens with the hall clock value.
      lst=p.locator('#event-list').inner_text();assert '23:00 (2)' in lst and '300' in lst and '1448' not in lst,lst
      eid=[e for e in state(p)['events'] if e['time']=='17:00'][0]['id']
      p.locator(f'[data-action="show-event"][data-id="{eid}"]').click();assert p.locator('.detail-clock').inner_text()=='3:00'
      p.locator('#detail-edit').click();assert p.locator('.number-display').inner_text()=='03:00'
      p.locator('[data-action="erase"]').click();keys(p,'5');p.locator('[data-action="save-existing"]').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      ev=[e for e in state(p)['events'] if e['id']==eid][0];assert (ev['period'],ev['time'])==(2,'16:55'),ev;p.locator('#detail-ok').click()
      # Report / print / text.
      p.get_by_role('button',name='Bericht',exact=True).click();rep=p.locator('#report-sheet').inner_text()
      assert 'Uhr lief aufwärts' in rep and '305' in rep,rep
      p.evaluate('EgrepUI.preparePrintReport()');assert 'Uhr lief aufwärts' in p.locator('#print-output').text_content()
      assert '23:05 (2) / 305' in p.evaluate('EgrepUI.reportText()')
      # Undo keeps the mode; switching to Spielzeit shows the same events as continuous time.
      p.locator('#undo').click();assert state(p)['meta']['timeMode']=='up'
      game(p);btn.click();assert state(p)['meta']['timeMode']=='game' and '23:00 (2)' in p.locator('#event-list').inner_text()
      p.close()
      # ---- Migration: a 2.2/2.3 game with "Uhr auf" (continuous) opens as "Spielzeit".
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(roster({'clockMode':'up'}))},auto_ok=False);game(p)
      assert p.locator('#clock-mode').inner_text()=='Spielzeit' and state(p)['meta']['timeMode']=='game'
      p.locator('#new-event').click();keys(p,'2713');assert p.locator('.number-hint').inner_text()=='2. Drittel · Uhr 12:47'
      p.locator('#wizard-close').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      # ---- Referee signals centred in their cards (picture and label).
      p.locator('#new-event').click();keys(p,'2713');p.locator('[data-action="next"]').click()
      p.locator('[data-type="penalty"]').click();p.locator('[data-team="home"]').click();p.locator('[data-pick-number="12"]').click()
      p.locator('[data-action="toggle-signs"]').click()
      off=p.locator('.penalty-list.with-signs .penalty-item:not(.custom)').evaluate_all('bs=>bs.map(b=>{const r=b.getBoundingClientRect();return [...b.children].map(c=>{const i=c.getBoundingClientRect();return Math.abs((i.left-r.left)-(r.right-i.right));});}).flat()')
      assert max(off)<=1.5,(size,max(off))
      if size==(360,640):p.screenshot(path=str(OUT/'schirizeichen-mittig-360x640.png'))
      p.close()
    assert not errors,errors;b.close()
  print('V24 UI PASS: mode cycle Uhr ab/Uhr auf/Spielzeit, row fits; hall clock up 5:12 -> 1st period remaining 14:48, summary shows 5:12; smaller time -> new period or Nachtrag; later time no question; invalid >20:00; history/edit/report/print/text with hall clock; undo keeps mode; same events as Spielzeit; 2.2/2.3 Uhr auf -> Spielzeit; signal pictures and labels centred; 3 viewports. Real Android not tested.')
if __name__=='__main__':main()
