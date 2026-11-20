"""2.2 UI (2.4: mode is now called "Spielzeit"): game-wide time entry (elapsed game time from DEB/EHV reports), operator name with pencil
in the report, version in the info dialog from logic.js. Chromium, no real Android."""
from pathlib import Path
import json,os,sys,re
from playwright.sync_api import sync_playwright,expect
from test_ui import boot,state,skip_operator,confirm,assert_fit
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v22');OUT.mkdir(parents=True,exist_ok=True)
CHROMIUM=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None))
KEY='nev-spielnotiz-v0.1'
def roster(op=''):
    return {'version':9,'currentPeriod':None,'meta':{'date':'2026-10-18','number':'T_022','operatorName':op,'operatorPrompted':True},
      'home':{'name':'Neusser EV','players':[{'id':'h30','number':'30','name':'Alex Torwart','isGoalie':True,'starter':True},{'id':'h12','number':'12','name':'Neumann, Mia'},{'id':'h48','number':'48','name':'Neumann, Leo'}],'startGoalie':'30'},
      'away':{'name':'EV Duisburg','players':[],'startGoalie':''},'events':[],'shootout':[]}
def game(p):p.get_by_role('button',name='Spiel',exact=True).click();skip_operator(p)
def keys(p,n):
    for x in n:p.locator('[data-digit="'+x+'"]').click()
def goal_home(p,raw,num='12'):
    p.locator('#new-event').click();keys(p,raw);p.locator('[data-action="next"]').click()
    if p.locator('#time-jump-dialog').is_visible():
        assert p.locator('#time-jump-next').is_hidden(),'Uhr auf: no "next period" choice';p.locator('#time-jump-retro').click()
    p.locator('[data-type="goal"]').click();p.locator('[data-team="home"]').click();p.locator(f'[data-pick-number="{num}"]').click();p.locator('[data-action="pick-save"]').click()
    if p.locator('#choice-dialog').is_visible():confirm(p)
    expect(p.locator('#detail-dialog')).to_be_visible()

def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox']);errors=[]
    for size in [(320,480),(360,640),(412,915)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(roster())},auto_ok=False)
      # ---- Info version comes from logic.js.
      p.locator('#open-menu').click();p.locator('#show-info').click()   # 2.8: via quick menu
      want='Version '+re.search(r"VERSION = '([^']+)'",(Path(__file__).resolve().parent.parent/'app/src/main/assets/logic.js').read_text()).group(1)
      assert p.locator('#info-version').inner_text()==want,p.locator('#info-version').inner_text();p.locator('#close-info').click()
      # ---- Report: operator line with pencil.
      p.get_by_role('button',name='Bericht',exact=True).click()
      assert p.locator('#operator-report-summary').inner_text()=='Bedienername eintragen' and p.locator('#edit-operator-report .operator-pencil').inner_text()=='✎'
      p.locator('#edit-operator-report').click();p.locator('#operator-name').fill('Micha Test');p.locator('#operator-form button[type="submit"]').click()
      assert p.locator('#operator-report-summary').inner_text()=='Bediener: Micha Test',p.locator('#operator-report-summary').inner_text()
      if size==(360,640):p.locator('#edit-operator-report').scroll_into_view_if_needed();p.screenshot(path=str(OUT/'bericht-bediener-360x640.png'))
      # ---- Switch in the screen row; fits on 320 px.
      game(p);btn=p.locator('#clock-mode');assert btn.inner_text().startswith('Uhr ab') and btn.get_attribute('aria-pressed')=='false'
      row=p.locator('.screen-setting').evaluate('n=>[n.clientWidth,n.scrollWidth]');assert row[1]<=row[0]+1,row
      bb=btn.bounding_box();assert bb['x']+bb['width']<=size[0],bb
      btn.click();btn.click();assert btn.inner_text()=='Spielzeit' and btn.get_attribute('aria-pressed')=='true' and state(p)['meta']['timeMode']=='game'
      assert 'Spielzeit zuerst' in p.locator('#capture-context').inner_text()
      if size==(360,640):p.screenshot(path=str(OUT/'uhr-auf-schalter-360x640.png'))
      # ---- New event without chosen period: game time decides the period.
      p.locator('#new-event').click();assert p.locator('#wizard-title').inner_text()=='Spielzeit eingeben' and p.locator('[data-period]').count()==0
      assert p.locator('[data-action="next"]').is_disabled();keys(p,'2713')
      assert p.locator('.number-display').inner_text()=='27:13' and p.locator('.number-hint').inner_text()=='2. Drittel · Uhr 12:47'
      assert p.locator('#wizard-title').inner_text()=='Spielzeit · 2. Drittel';assert_fit(p)
      if size==(360,640):p.screenshot(path=str(OUT/'spielzeit-eingabe-360x640.png'))
      p.locator('#wizard-close').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      goal_home(p,'2713');ev=state(p)['events'][-1];assert (ev['period'],ev['time'],ev['clock'])==(2,'12:47','1247'),ev
      assert p.locator('.detail-clock').inner_text()=='27:13' and 'Uhr 12:47' in p.locator('.detail-band').inner_text() and 'Spielzeit' in p.locator('.detail-band').inner_text()
      if size==(360,640):p.screenshot(path=str(OUT/'zusammenfassung-spielzeit-360x640.png'))
      p.locator('#detail-ok').click();assert state(p)['currentPeriod']==2
      # Earlier time -> only "Nachtrag" offered (period comes from the time).
      goal_home(p,'730','48');ev=state(p)['events'][-1];assert (ev['period'],ev['time'])==(1,'12:30'),ev;p.locator('#detail-ok').click()
      assert state(p)['currentPeriod']==2,'Nachtrag does not move the live period back'
      goal_home(p,'5805');assert state(p)['events'][-1]['period']==3 and state(p)['currentPeriod']==3;p.locator('#detail-ok').click()
      # Invalid time.
      p.locator('#new-event').click();keys(p,'6001');assert 'ungültig' in p.locator('.number-hint').inner_text() and p.locator('[data-action="next"]').is_disabled()
      p.locator('#wizard-close').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      # History shows game time; edit opens with game time digits.
      assert '27:13 (2)' in p.locator('#event-list').inner_text()
      eid=[e for e in state(p)['events'] if e['time']=='12:47'][0]['id']
      p.locator(f'[data-action="show-event"][data-id="{eid}"]').click();p.locator('#detail-edit').click();assert p.locator('.number-display').inner_text()=='27:13'
      p.locator('[data-action="erase"]').click();keys(p,'5');p.locator('[data-action="save-existing"]').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      ev=[e for e in state(p)['events'] if e['id']==eid][0];assert (ev['period'],ev['time'])==(2,'12:45'),ev;p.locator('#detail-ok').click()
      # Undo keeps the mode; report notes the conversion.
      p.locator('#undo').click();assert state(p)['meta']['timeMode']=='game'
      p.get_by_role('button',name='Bericht',exact=True).click();assert 'Erfasst als Spielzeit' in p.locator('#report-sheet').inner_text()
      p.evaluate('EgrepUI.preparePrintReport()');assert 'Erfasst als Spielzeit' in p.locator('#print-output').text_content()
      # ---- Reset: new game starts with "Uhr ab"; archived game keeps "Uhr auf".
      p.locator('#reset-game').click();confirm(p);assert state(p)['meta']['timeMode']=='down'
      game(p);assert p.locator('#clock-mode').inner_text().startswith('Uhr ab')
      p.locator('#new-event').click();assert 'Restzeit' in p.locator('#wizard-title').inner_text() or 'Drittel' in p.locator('#wizard-content').inner_text()
      p.locator('#wizard-close').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      p.get_by_role('button',name='Bericht',exact=True).click();p.locator('#open-archive').click();p.locator('[data-archive-open]').first.click();confirm(p)
      assert state(p)['meta']['timeMode']=='game' and len(state(p)['events'])==3
      # Switching back to "Uhr ab" works for the same game; stored events unchanged.
      before=state(p)['events'];game(p);p.locator('#clock-mode').click();assert state(p)['meta']['timeMode']=='down' and state(p)['events']==before
      p.close()
    assert not errors,errors;b.close()
  print('V22 UI PASS: info version from logic, report operator name + pencil, Uhr ab/auf switch fits 320 px, game time 27:13 -> 2nd period/clock 12:47 without period choice, summary shows game time, Nachtrag without next-period option, live period follows, invalid >60:00, history/edit with game time, undo keeps mode, report/print note, reset -> Uhr ab, archive keeps Uhr auf, switch back keeps events, 3 viewports. Real Android not tested.')
if __name__=='__main__':main()
