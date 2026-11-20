"""1.9 UI: number grid for scorer/assists/penalised player (like eGrep). Chromium, no real Android."""
from pathlib import Path
import json,os,sys
from playwright.sync_api import sync_playwright,expect
from test_ui import boot,state,skip_operator,confirm,assert_fit
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v19');OUT.mkdir(parents=True,exist_ok=True)
CHROMIUM=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None))
KEY='nev-spielnotiz-v0.1'
HOME=[('2','Sommer, Tim',True),('1','Becker, Lena',True),('9','Engel, Ola',False),('12','Neumann, Mia',False),('16','Maier, Max',False),('68','Dietz, Lars',False),('83','Marx, Felix',False),('97','Wendt, Ben',False),('7','Ohm, Mika',False),('8','Zander, Jan',False),('14','Voss, Malte',False),('17','Albers, Lukas',False),('23','Wenz, Luca',False),('39','Wendt, Fabian',False),('48','Neumann, Leo',False),('57','Falk, Tom',False),('91','Graf, Paul',False),('5','Beispiel, Max',False),('77','Muster, Kim',False)]
def roster():
    return {'version':8,'currentPeriod':1,'meta':{'date':'2026-10-19','number':'T_019','operatorName':'','operatorPrompted':True},
      'home':{'name':'SpG Neusser EV / GSC Moers','players':[{'id':'h'+n,'number':n,'name':nm,'isGoalie':g,'starter':n=='2'} for n,nm,g in HOME],'startGoalie':'2'},
      'away':{'name':'EV Duisburg 1b','players':[],'startGoalie':''},'events':[]}
def game(p):p.get_by_role('button',name='Spiel',exact=True).click();skip_operator(p)
def start(p,clock,kind,team):
    p.locator('#new-event').click()
    for x in clock:p.locator('[data-digit="'+x+'"]').click()
    p.locator('[data-action="next"]').click()
    if p.locator('#time-jump-dialog').is_visible():p.locator('#time-jump-retro').click()
    p.locator('[data-type="'+kind+'"]').click();p.locator('[data-team="'+team+'"]').click()
def tap(p,*numbers):
    for n in numbers:p.locator('[data-pick-number="'+n+'"]').click()
def roles(p):return {b.get_attribute('data-pick-number'):b.locator('.pick-role').inner_text() for b in p.locator('.pick-btn.selected').all()}

def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox']);errors=[]
    for size in [(320,480),(360,640),(412,915)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(roster())},auto_ok=False);game(p)
      start(p,'1012','goal','home')
      # Grid shows every reported number ascending, goalies marked, no keypad.
      nums=[x.get_attribute('data-pick-number') for x in p.locator('.pick-btn').all()]
      assert nums==sorted([n for n,_,_ in HOME],key=int),nums
      assert p.locator('[data-digit="5"]').count()==0 and p.locator('#wizard-title').inner_text()=='Torschütze und Assists'
      assert p.locator('[data-pick-number="2"] .pick-tw').count()==1 and p.locator('[data-pick-number="48"] .pick-tw').count()==0
      assert 'Neumann' in p.locator('[data-pick-number="48"]').inner_text()
      assert p.locator('[data-action="pick-save"]').is_disabled()
      assert_fit(p)
      grid=p.locator('.pick-grid').evaluate('n=>[n.clientHeight,n.scrollHeight]')
      if size[1]>=640:assert grid[1]<=grid[0]+1,('all 19 numbers visible without scrolling',size,grid)
      # Tap order = scorer, A1, A2; tapping again removes and the rest moves up; max three.
      tap(p,'48','5','77');assert roles(p)=={'48':'T','5':'A1','77':'A2'},roles(p)
      assert p.locator('.pick-summary').inner_text()=='T #48 · A1 #5 · A2 #77'
      if size==(360,640):p.screenshot(path=str(OUT/'nummernraster-360x640.png'))
      tap(p,'9');assert roles(p)=={'48':'T','5':'A1','77':'A2'},'fourth tap ignored'
      tap(p,'5');assert roles(p)=={'48':'T','77':'A1'},roles(p)
      tap(p,'5');assert roles(p)=={'48':'T','77':'A1','5':'A2'},roles(p)
      sel=p.locator('[data-pick-number="48"]').evaluate('e=>getComputedStyle(e).backgroundColor');assert sel=='rgb(216, 23, 42)',sel
      p.locator('[data-action="pick-save"]').click()
      expect(p.locator('#detail-dialog')).to_be_visible();ev=state(p)['events'][-1]
      assert (ev['player'],ev['assist1'],ev['assist2'])==('48','77','5'),ev
      p.locator('#detail-ok').click()
      # Scorer only.
      start(p,'1000','goal','home');tap(p,'17');p.locator('[data-action="pick-save"]').click()
      ev=state(p)['events'][-1];assert (ev['player'],ev['assist1'],ev['assist2'])==('17','',''),ev;p.locator('#detail-ok').click()
      # Penalty: one tap goes straight to the penalty type.
      start(p,'950','penalty','home');assert p.locator('#wizard-title').inner_text()=='Welcher Spieler?'
      tap(p,'12');assert p.locator('#wizard-title').inner_text()=='Welche Strafe?'
      p.locator('[data-penalty="Haken"]').click();ev=state(p)['events'][-1];assert ev['player']=='12' and ev['penalty']=='Haken';p.locator('#detail-ok').click()
      # Bench penalty from the grid.
      start(p,'940','penalty','home');p.locator('[data-action="bench-penalty"]').click();p.locator('[data-penalty="Bandencheck"]').click();p.locator('[data-action="served-later"]').click()
      assert state(p)['events'][-1]['bench'];p.locator('#detail-ok').click()
      # Back from the penalty type returns to the grid.
      start(p,'930','penalty','home');tap(p,'14');p.locator('#wizard-back').click();assert p.locator('.pick-grid').count()==1
      assert roles(p)=={'14':'T'} or p.locator('[data-pick-number="14"]').get_attribute('aria-pressed')=='true'
      p.locator('#wizard-close').click();confirm(p)
      # "Andere Nummer": keypad, number outside the roster -> existing warning.
      start(p,'920','goal','home');p.locator('[data-action="other-number"]').click();assert p.locator('[data-digit="9"]').count()==1
      p.locator('[data-digit="9"]').click();p.locator('[data-digit="9"]').click();p.locator('[data-action="next"]').click();p.locator('[data-action="skip-assists"]').click()
      assert 'Nummer' in p.locator('#choice-title').inner_text();confirm(p);assert state(p)['events'][-1]['player']=='99';p.locator('#detail-ok').click()
      # Team without roster: keypad directly.
      start(p,'910','goal','away');assert p.locator('.pick-grid').count()==0 and p.locator('[data-digit="5"]').count()==1
      p.locator('#wizard-close').click();confirm(p)
      # Edit: grid opens with the stored order preselected.
      first=[x for x in state(p)['events'] if x['player']=='48'][0]['id']
      p.locator(f'[data-action="show-event"][data-id="{first}"]').click();p.locator('#detail-edit').click()
      p.locator('[data-action="next"]').click();p.locator('[data-type="goal"]').click();p.locator('[data-team="home"]').click()
      assert roles(p)=={'48':'T','77':'A1','5':'A2'},roles(p)
      tap(p,'77');p.locator('[data-action="pick-save"]').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      ev=[x for x in state(p)['events'] if x['id']==first][0];assert (ev['player'],ev['assist1'],ev['assist2'])==('48','5',''),ev
      p.locator('#detail-ok').click()
      # Edited goal with a number outside the roster falls back to the keypad.
      other=[x for x in state(p)['events'] if x['player']=='99'][0]['id']
      p.locator(f'[data-action="show-event"][data-id="{other}"]').click();p.locator('#detail-edit').click()
      p.locator('[data-action="next"]').click();p.locator('[data-type="goal"]').click();p.locator('[data-team="home"]').click()
      assert p.locator('.pick-grid').count()==0 and p.locator('.number-display').inner_text()=='#99'
      p.locator('#wizard-close').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      p.close()
    assert not errors,errors;b.close()
  print('V19 UI PASS: number grid ascending incl. TW marks, tap order T/A1/A2, untap moves up, max 3, OK disabled empty, scorer only, penalty one tap -> type, bench, back to grid, Andere Nummer keypad + unknown warning, no roster -> keypad, edit preselects order, edit with unknown number -> keypad, 3 viewports. Real Android not tested.')
if __name__=='__main__':main()
