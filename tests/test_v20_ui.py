"""2.0 UI: 2+2/10 min incl. "+10" second entry, empty net, PP/SH hint, period line,
penalty shootout, archive. Chromium on the shipped DOM/JS/CSS; no real Android."""
from pathlib import Path
import json,os,sys
from playwright.sync_api import sync_playwright,expect
from test_ui import boot,state,skip_operator,confirm,cancel_choice,assert_fit
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v20');OUT.mkdir(parents=True,exist_ok=True)
CHROMIUM=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None))
KEY='nev-spielnotiz-v0.1'
HOME=[('30','Alex Torwart',True),('35','Kim Ersatz',True),('48','Neumann, Leo',False),('9','Engel, Ola',False),('12','Neumann, Mia',False)]
def roster():
    return {'version':9,'currentPeriod':1,'meta':{'date':'2026-10-19','number':'T_020','operatorName':'','operatorPrompted':True},
      'home':{'name':'Neusser EV','players':[{'id':'h'+n,'number':n,'name':nm,'isGoalie':g,'starter':n=='30'} for n,nm,g in HOME],'startGoalie':'30'},
      'away':{'name':'EV Duisburg','players':[],'startGoalie':''},'events':[],'shootout':[]}
def game(p):p.get_by_role('button',name='Spiel',exact=True).click();skip_operator(p)
def start(p,clock,kind,team):
    p.locator('#new-event').click()
    for x in clock:p.locator('[data-digit="'+x+'"]').click()
    p.locator('[data-action="next"]').click()
    if p.locator('#time-jump-dialog').is_visible():p.locator('#time-jump-retro').click()
    p.locator('[data-type="'+kind+'"]').click();p.locator('[data-team="'+team+'"]').click()
def keypad(p,n):
    for x in n:p.locator('[data-digit="'+x+'"]').click()
    p.locator('[data-action="next"]').click()
def rows(p):return {r.locator('dt').inner_text().strip().upper():r.locator('dd').inner_text().strip() for r in p.locator('#detail-sheet .detail-row').all()}

def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox']);errors=[]
    for size in [(320,480),(360,640)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(roster())},auto_ok=False);game(p)
      # ---- Durations: five buttons, two rows; fits without scrolling.
      start(p,'1500','penalty','away');keypad(p,'4')
      assert [x.get_attribute('data-duration') for x in p.locator('[data-duration]').all()]==['2','2+2','5','10','game']
      assert_fit(p)
      if size==(360,640):p.screenshot(path=str(OUT/'strafmass-360x640.png'))
      # 2 min Haken, then "+10 Min." from the summary -> second entry, same time and player.
      p.locator('[data-penalty="Haken"]').click();expect(p.locator('#detail-plus10')).to_be_visible()
      p.locator('#detail-plus10').click();ev=state(p)['events'][-1]
      assert (ev['penalty'],ev['penaltyDuration'],ev['player'],ev['clock'],ev['team'])==('Disziplinarstrafe','10','4','1500','away'),ev
      assert len(state(p)['events'])==2 and p.locator('#detail-plus10').count()==0,'no +10 on a 10-min entry'
      p.locator('#detail-ok').click()
      # 10 min selected directly -> "Disziplinarstrafe" button saves; 2+2 saves.
      start(p,'1450','penalty','home');p.locator('[data-pick-number="12"]').click()
      assert p.locator('[data-action="misconduct"]').is_hidden();p.locator('[data-duration="10"]').click();assert p.locator('[data-action="misconduct"]').is_visible()
      p.locator('[data-action="misconduct"]').click();ev=state(p)['events'][-1];assert (ev['penalty'],ev['penaltyDuration'])==('Disziplinarstrafe','10');p.locator('#detail-ok').click()
      start(p,'1440','penalty','home');p.locator('[data-pick-number="9"]').click();p.locator('[data-duration="2+2"]').click();p.locator('[data-penalty="Hoher Stock"]').click()
      assert state(p)['events'][-1]['penaltyDuration']=='2+2' and '2+2 Min.' in rows(p)['STRAFE'];p.locator('#detail-ok').click()
      # ---- PP hint: away 2 min at 15:00 is running at 14:00 (home has 2+2 from 14:40 too -> 14:20 equal numbers?)
      # home 2+2 started 14:40 (elapsed 5:20), so at 14:30 home 1 vs away 1 -> no hint; check a goal at 14:50.
      start(p,'1450','goal','away');keypad(p,'7');p.locator('[data-action="skip-assists"]').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      hint=p.locator('.detail-hint').inner_text();assert 'Unterzahltor' in hint and '#4' in hint,hint
      if size==(360,640):p.screenshot(path=str(OUT/'hinweis-unterzahl-360x640.png'))
      p.locator('#detail-ok').click()
      start(p,'1430','goal','home');p.locator('[data-pick-number="48"]').click();p.locator('[data-action="pick-save"]').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      assert p.locator('.detail-hint').count()==0,'1 vs 1 running -> no hint';p.locator('#detail-ok').click()
      # ---- Empty net: out #30 -> leeres Tor, back: leer -> #30 suggested.
      start(p,'200','goalie','home')
      assert p.locator('[data-goalie-field="goalieOut"] strong').inner_text()=='#30'
      p.locator('[data-goalie-number="EN"]').click();assert p.locator('[data-goalie-field="goalieIn"] strong').inner_text()=='leer'
      p.locator('[data-action="next"]').click();ev=state(p)['events'][-1];assert (ev['goalieOut'],ev['goalieIn'])==('30','EN'),ev
      assert rows(p)['REIN']=='Leeres Tor';p.locator('#detail-ok').click()
      assert p.locator('#home-goalie').inner_text()=='Im Tor: Leeres Tor'
      start(p,'130','goalie','home')
      assert p.locator('[data-goalie-field="goalieOut"] strong').inner_text()=='leer' and p.locator('[data-goalie-field="goalieIn"] strong').inner_text()=='#30'
      p.locator('[data-action="next"]').click();ev=state(p)['events'][-1];assert (ev['goalieOut'],ev['goalieIn'])==('EN','30'),ev;p.locator('#detail-ok').click()
      assert 'Alex Torwart' in p.locator('#home-goalie').inner_text()
      # ---- Period line in report and text.
      p.get_by_role('button',name='Bericht',exact=True).click()
      assert 'Drittel: 1:1 · 0:0 · 0:0' in p.locator('#report-sheet').inner_text(),p.locator('.report-periods').inner_text()
      assert 'Drittel 1:1' in p.evaluate('EgrepUI.reportText()')
      # ---- Shootout: button visible in 3rd period; teams alternate; winner +1, n.P.
      game(p);assert p.locator('#open-shootout').is_hidden();p.locator('[data-current-period="3"]').click();assert p.locator('#open-shootout').is_visible()
      p.locator('#open-shootout').click();expect(p.locator('#shootout-dialog')).to_be_visible()
      p.locator('[data-shootout-team="home"]').click();p.locator('[data-shootout-player="48"]').click();p.locator('[data-shootout-result="1"]').click()
      assert 'EV Duisburg' in p.locator('#shootout-entry').inner_text(),'teams alternate'
      p.locator('#shootout-number').fill('9');p.locator('[data-shootout-player="?"]').click();p.locator('[data-shootout-result="0"]').click()
      p.locator('[data-shootout-player=""]').first.click();p.locator('[data-shootout-result="1"]').click()   # home, ohne Nummer
      if size==(360,640):p.screenshot(path=str(OUT/'penaltyschiessen-360x640.png'))
      box=p.locator('#shootout-dialog').bounding_box();assert box['y']>=-1 and box['y']+box['height']<=size[1]+1,box
      so=state(p)['shootout'];assert [(a['team'],a['player'],a['scored']) for a in so]==[('home','48',True),('away','9',False),('home','',True)],so
      assert 'Neusser EV 2 : 0 EV Duisburg' in p.locator('#shootout-score').inner_text()
      p.locator('#shootout-done').click()
      assert p.locator('#score-home').inner_text()=='2' and p.locator('#score-away').inner_text()=='1' and 'n.P.' in p.locator('.score-colon').inner_text()
      assert 'Penaltyschießen' in p.locator('.shootout-card').text_content()
      # remove one attempt via tap -> confirm (danger)
      p.locator('.shootout-card').click();p.locator('[data-shootout-remove]').nth(2).click();assert 'danger-confirm' in p.locator('#choice-confirm').get_attribute('class');confirm(p)
      assert len(state(p)['shootout'])==2;p.locator('#shootout-done').click()
      p.get_by_role('button',name='Bericht',exact=True).click()
      assert '2 : 1 n.P.' in p.locator('.report-match').inner_text() and p.locator('#report-sheet .shootout-row').count()==2
      txt=p.evaluate('EgrepUI.reportText()');assert 'Penaltyschießen 1:0' in txt and 'Spielstand 2:1 n.P.' in txt,txt
      p.evaluate('EgrepUI.preparePrintReport()');assert p.locator('#print-output .shootout-row').count()==2 and 'n.P.' in p.locator('#print-output .print-score').text_content()
      # ---- Archive: reset archives; open restores; delete removes.
      before=len(state(p)['events']);p.locator('#reset-game').click();confirm(p)
      assert state(p)['events']==[] and p.locator('#open-archive').inner_text()=='Archiv (1)'
      p.get_by_role('button',name='Bericht',exact=True).click();p.locator('#open-archive').click();expect(p.locator('#archive-dialog')).to_be_visible()
      item=p.locator('.archive-item').first.inner_text();assert 'Neusser EV' in item and '2 : 1 n.P.' in item,item
      if size==(360,640):p.screenshot(path=str(OUT/'archiv-360x640.png'))
      p.locator('[data-archive-open]').first.click();confirm(p)
      assert len(state(p)['events'])==before and len(state(p)['shootout'])==2 and p.locator('#open-archive').inner_text()=='Archiv'
      # current (restored) game is archived again when another is opened/reset; deleting works.
      p.locator('#reset-game').click();confirm(p);p.get_by_role('button',name='Bericht',exact=True).click();p.locator('#open-archive').click()
      p.locator('[data-archive-delete]').first.click();confirm(p);assert p.locator('.archive-item').count()==0;p.locator('#close-archive').click()
      assert p.locator('#open-archive').inner_text()=='Archiv'
      # Empty game is not archived.
      p.locator('#reset-game').click();confirm(p);assert p.locator('#open-archive').inner_text()=='Archiv'
      p.close()
    assert not errors,errors;b.close()
  print('V20 UI PASS: durations 2/2+2/5/10/Spieldauer fit, +10 second entry, Disziplinarstrafe button, 2+2, SH hint + even strength, empty net out/back with suggestion, period line, shootout alternate/winner +1/n.P./delete/report/text/print, archive reset/open/delete/empty, 2 viewports. Real Android not tested.')
if __name__=='__main__':main()
