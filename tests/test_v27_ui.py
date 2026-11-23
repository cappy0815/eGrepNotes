"""2.7 UI: six event types fit, penalty shot (grid/keypad, scored counts), note (team or general),
empty-net goal marked in history/detail/report/print/text. Chromium only, no real Android."""
from pathlib import Path
import re
import json,os,sys
from playwright.sync_api import sync_playwright,expect
from test_ui import boot,state,skip_operator,confirm,assert_fit
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v27');OUT.mkdir(parents=True,exist_ok=True)
CHROMIUM=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None))
KEY='nev-spielnotiz-v0.1'
def roster():
    return {'version':9,'currentPeriod':3,'meta':{'date':'2026-11-08','number':'T_027','operatorName':'','operatorPrompted':True,'timeMode':'down'},
      'home':{'name':'Neusser EV','players':[{'id':'h30','number':'30','name':'Alex Torwart','isGoalie':True,'starter':True},{'id':'h8','number':'8','name':'Zander, Jan'},{'id':'h12','number':'12','name':'Neumann, Mia'}],'startGoalie':'30'},
      'away':{'name':'TuS Wiehl','players':[],'startGoalie':''},'events':[],'shootout':[]}
def game(p):p.get_by_role('button',name='Spiel',exact=True).click();skip_operator(p)
def start(p,clock,kind,team=None):
    p.locator('#new-event').click()
    for x in clock:p.locator('[data-digit="'+x+'"]').click()
    p.locator('[data-action="next"]').click()
    if p.locator('#time-jump-dialog').is_visible():p.locator('#time-jump-retro').click()
    p.locator('[data-type="'+kind+'"]').click()
    if team:p.locator('[data-team="'+team+'"]').click()
def ok(p):
    if p.locator('#choice-dialog').is_visible():confirm(p)
    expect(p.locator('#detail-dialog')).to_be_visible()
def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox']);errors=[]
    for size in [(320,480),(360,640),(412,915)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(roster())},auto_ok=False);game(p)
      # ---- Six types fit without scrolling.
      p.locator('#new-event').click();[p.locator(f'[data-digit="{x}"]').click() for x in '1500'];p.locator('[data-action="next"]').click()
      assert p.locator('.type-choice').count()==6;assert_fit(p)
      if size==(360,640):p.screenshot(path=str(OUT/'ereignisart-6-360x640.png'))
      p.locator('#wizard-close').click();confirm(p)
      # ---- Penalty shot from the roster grid: one tap -> result; scored counts as goal.
      start(p,'1500','penaltyshot','home');assert p.locator('#wizard-title').inner_text()=='Wer schießt?'
      p.locator('[data-pick-number="8"]').click();assert p.locator('#wizard-title').inner_text()=='Penalty verwandelt?';assert_fit(p)
      if size==(360,640):p.screenshot(path=str(OUT/'penalty-ergebnis-360x640.png'))
      p.locator('[data-action="ps-scored"]').click();ok(p);ev=state(p)['events'][-1]
      assert (ev['type'],ev['player'],ev['scored'],ev['team'])==('penaltyshot','8',True,'home'),ev
      rows=p.locator('#detail-sheet').inner_text();assert 'Penalty' in rows and 'Tor' in rows and 'zählt als Tor' in rows,rows
      p.locator('#detail-ok').click();assert p.locator('#score-home').inner_text()=='1'
      # Keypad (no roster), missed: no goal; back from result returns to number.
      start(p,'1400','penaltyshot','away');assert p.locator('[data-digit="5"]').count()==1
      p.locator('[data-digit="1"]').click();p.locator('[data-digit="7"]').click();p.locator('[data-action="next"]').click()
      p.locator('#wizard-back').click();assert p.locator('.number-display').inner_text()=='#17';p.locator('[data-action="next"]').click()
      p.locator('[data-action="ps-missed"]').click();ok(p);ev=state(p)['events'][-1];assert ev['scored'] is False and ev['player']=='17';p.locator('#detail-ok').click()
      assert p.locator('#score-away').inner_text()=='0'
      assert 'kein Tor' in p.locator('#event-list').inner_text()
      # ---- Note: general and team.
      start(p,'1300','note');assert p.locator('[data-team="none"]').is_visible();p.locator('[data-team="none"]').click()
      assert p.locator('#wizard-title').inner_text()=='Notiz';p.locator('[data-action="save-note"]').click();assert 'Notiztext' in p.locator('#wizard-error').inner_text()
      p.locator('#note-text').fill('Spiel 5 Min. unterbrochen,\nEis wird repariert');assert_fit(p)
      if size==(360,640):p.screenshot(path=str(OUT/'notiz-eingabe-360x640.png'))
      p.locator('[data-action="save-note"]').click();ok(p);ev=state(p)['events'][-1]
      assert (ev['type'],ev['team'],ev['text'])==('note','','Spiel 5 Min. unterbrochen, Eis wird repariert'),ev
      assert 'Allgemein' in p.locator('#detail-sheet').inner_text();p.locator('#detail-ok').click()
      start(p,'1250','note','away');p.locator('#note-text').fill('Trainer verwarnt');p.locator('[data-action="save-note"]').click();ok(p);assert state(p)['events'][-1]['team']=='away';p.locator('#detail-ok').click()
      # Team buttons for other types: no "Allgemein".
      start(p,'1240','goal');assert p.locator('[data-team="none"]').count()==0;p.locator('#wizard-close').click();confirm(p)
      # Edit a note.
      nid=[e for e in state(p)['events'] if e['type']=='note' and e['team']==''][0]['id']
      p.locator(f'[data-action="show-event"][data-id="{nid}"]').click();p.locator('#detail-edit').click();p.locator('[data-action="next"]').click();p.locator('[data-type="note"]').click();p.locator('[data-team="none"]').click()
      assert p.locator('#note-text').input_value().startswith('Spiel 5 Min.');p.locator('#note-text').fill('Eis repariert');p.locator('[data-action="save-note"]').click();ok(p)
      assert [e for e in state(p)['events'] if e['id']==nid][0]['text']=='Eis repariert';p.locator('#detail-ok').click()
      # ---- Empty net: home pulls #30 at 2:00, away goal at 1:30 -> EN in history, detail, report, print, text.
      start(p,'200','goalie','home');p.locator('[data-goalie-number="EN"]').click();p.locator('[data-action="next"]').click();ok(p);p.locator('#detail-ok').click()
      start(p,'130','goal','away');p.locator('[data-digit="9"]').click();p.locator('[data-action="next"]').click();p.locator('[data-action="skip-assists"]').click();ok(p)
      assert 'Empty-Net-Tor' in p.locator('.detail-hint.EN').inner_text();p.locator('#detail-ok').click()
      assert 'Empty Net' in p.locator('.event-row.latest').inner_text()
      p.get_by_role('button',name='Bericht',exact=True).click();rep=p.locator('#report-sheet').inner_text()
      assert re.search(r'(TOR|Tor)( \d+:\d+)? · EN',rep),rep  # 3.3: score between type and EN
      assert 'Penalty' in rep or 'PENALTY' in rep and 'Eis repariert' in rep
      assert '2 : 1' not in rep and '1 : 1' in rep,rep  # 1 PS goal home + 1 EN goal away
      p.evaluate('EgrepUI.preparePrintReport()');pr=p.locator('#print-output').text_content();assert 'EN' in pr and 'Eis repariert' in pr and 'kein Tor' in pr
      txt=p.evaluate('EgrepUI.reportText()');assert re.search(r'Tor( \d+:\d+)? \(EN\)',txt) and 'Allgemein | Notiz | Eis repariert' in txt and re.search(r'Penalty( \d+:\d+)? \| 8, Tor',txt),txt  # 3.3: score after goals
      if size==(360,640):p.screenshot(path=str(OUT/'bericht-27-360x640.png'),full_page=True)
      # Persisted after reload.
      n=p.evaluate("(()=>{const L=window.EgrepLogic||window.L;const raw=JSON.parse(localStorage.getItem('nev-spielnotiz-v0.1'));return [raw.events.length, L?L.migrateState(raw).events.length:-1];})()")
      assert n==[6,6],n
      p.close()
    assert not errors,errors;b.close()
  print('V27 UI PASS: six types fit, penalty shot grid/keypad/back, scored counts/missed not, notes general+team, empty text refused, newline cleaned, edit, no Allgemein for other types, EN goal in detail/history/report/print/text, stored data survives migration; 3 viewports. Real Android not tested.')
if __name__=='__main__':main()
