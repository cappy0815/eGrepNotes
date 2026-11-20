"""1.6 UI regressions on the shipped DOM/JS/CSS (Chromium). No real Android device.
Covers: event types as 4 coloured rows, bold larger clock, summary after save (saved first,
OK / Aendern / Verwerfen), order team -> event -> number -> penalty, tap row -> detail view.
"""
from pathlib import Path
import json,os,sys
from playwright.sync_api import sync_playwright,expect
from test_ui import boot,state,digits,next_,skip_operator,confirm,assert_fit
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v16');OUT.mkdir(parents=True,exist_ok=True)
CHROMIUM=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None))
KEY='nev-spielnotiz-v0.1'

def roster():
    return {'version':8,'currentPeriod':1,'meta':{'date':'2026-10-18','number':'T_016','operatorName':'','operatorPrompted':True},
      'home':{'name':'Neusser EV','players':[{'id':'h30','number':'30','name':'Alex Torwart','isGoalie':True,'starter':True},{'id':'h35','number':'35','name':'Kim Ersatz','isGoalie':True},{'id':'h56','number':'56','name':'Max Beispiel','check':['Nur ein Wort']},{'id':'h18','number':'18','name':'Luca Muster'}],'startGoalie':'30'},
      'away':{'name':'Ratinger Ice Aliens','players':[{'id':'a20','number':'20','name':'Robin Gast'}],'startGoalie':''},'events':[]}
def game(p):p.get_by_role('button',name='Spiel',exact=True).click();skip_operator(p)
def start(p,clock,kind,team):
    p.locator('#new-event').click();digits(p,clock);next_(p)
    if p.locator('#time-jump-dialog').is_visible():p.locator('#time-jump-retro').click()
    p.locator('[data-type="'+kind+'"]').click();p.locator('[data-team="'+team+'"]').click()
def rows(p):return [(r.locator('dt').inner_text().strip().upper(),r.locator('dd').inner_text().strip()) for r in p.locator('#detail-sheet .detail-row').all()]
def labels(p):return [l for l,_ in rows(p)]
def dialog_fits(p):
    box=p.locator('#detail-dialog').bounding_box();vh=p.viewport_size['height']
    sz=p.locator('#detail-dialog').evaluate('n=>[n.clientHeight,n.scrollHeight]')
    assert box['y']>=-1 and box['y']+box['height']<=vh+1 and sz[1]<=sz[0]+1,(box,sz)

def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox']);errors=[]
    for size in [(320,480),(360,640),(412,915)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(roster())},auto_ok=False);game(p)
      # ---- Event types: four full-width rows, own colours, no scrolling.
      p.locator('#new-event').click();digits(p,'1012');next_(p);assert_fit(p)
      # 2.7: Tor and Strafe full-width rows; then two per row (Torwartwechsel|Timeout, Penalty|Notiz).
      boxes=[p.locator('[data-type="'+t+'"]').bounding_box() for t in ['goal','penalty','goalie','timeout','penaltyshot','note']]
      inner=p.locator('#wizard-content').evaluate('n=>n.clientWidth-parseFloat(getComputedStyle(n).paddingLeft)-parseFloat(getComputedStyle(n).paddingRight)')
      assert boxes[0]['width']>=inner-1 and boxes[1]['width']>=inner-1 and boxes[0]['y']<boxes[1]['y']<boxes[2]['y']<boxes[4]['y'],(boxes,inner)
      assert abs(boxes[2]['y']-boxes[3]['y'])<1 and abs(boxes[4]['y']-boxes[5]['y'])<1 and boxes[2]['x']<boxes[3]['x'],boxes
      bg=lambda t:p.locator('[data-type="'+t+'"]').evaluate('e=>getComputedStyle(e).backgroundColor')
      assert bg('goal')=='rgb(228, 245, 234)' and bg('penalty')=='rgb(255, 240, 224)' and bg('goalie')==bg('timeout')=='rgb(242, 244, 246)',(bg('goal'),bg('penalty'),bg('goalie'))
      if size==(360,640):p.screenshot(path=str(OUT/'ereignisart-360x640.png'))
      # ---- Goal: saved immediately, summary in order team, event, number, assists.
      p.locator('[data-type="goal"]').click();p.locator('[data-team="home"]').click();digits(p,'56');next_(p);digits(p,'18');next_(p);p.locator('[data-action="skip-assists"]').click()
      expect(p.locator('#detail-dialog')).to_be_visible();assert p.locator('#detail-title').inner_text()=='Ereignis gespeichert'
      assert len(state(p)['events'])==1,'saved before OK'
      assert p.locator('.detail-clock').inner_text()=='10:12' and '1. Drittel' in p.locator('.detail-band').inner_text()
      assert labels(p)==['TEAM','EREIGNIS','NUMMER','ASSIST 1'],rows(p)
      r=dict(rows(p));assert r['TEAM']=='Neusser EV' and r['EREIGNIS']=='Tor' and r['NUMMER'].startswith('#56') and 'Max Beispiel' in r['NUMMER'] and r['ASSIST 1'].startswith('#18')
      assert p.locator('.detail-band').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(216, 23, 42)'
      assert p.evaluate('document.activeElement.id')=='detail-title'
      assert [x.inner_text() for x in p.locator('#detail-actions button').all()]==['Verwerfen','Ändern','OK']
      dialog_fits(p)
      if size==(360,640):p.screenshot(path=str(OUT/'zusammenfassung-tor-360x640.png'))
      p.locator('#detail-ok').click();expect(p.locator('#detail-dialog')).not_to_be_visible()
      # ---- Clock in history: larger and bold.
      fw,fs=p.locator('.event-clock').first.evaluate('e=>[getComputedStyle(e).fontWeight,parseFloat(getComputedStyle(e).fontSize)]')
      assert int(fw)>=700 and fs>=17,(fw,fs)
      # ---- Penalty summary incl. type and duration; away colour.
      start(p,'1000','penalty','away');digits(p,'20');next_(p);p.locator('[data-penalty="Haken"]').click()
      assert labels(p)==['TEAM','EREIGNIS','NUMMER','STRAFE'],rows(p)
      r=dict(rows(p));assert r['STRAFE'].startswith('Haken') and '2 Min.' in r['STRAFE'] and r['TEAM']=='Ratinger Ice Aliens'
      assert p.locator('.detail-band').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(22, 91, 197)'
      dialog_fits(p)
      if size==(320,480):p.screenshot(path=str(OUT/'zusammenfassung-strafe-320x480.png'))
      # Verwerfen removes it, undo brings it back.
      p.locator('#detail-discard').click();expect(p.locator('#detail-dialog')).not_to_be_visible();assert len(state(p)['events'])==1
      p.locator('#undo').click();assert len(state(p)['events'])==2
      # ---- Bench penalty, timeout, goalie change summaries.
      start(p,'950','penalty','home');p.locator('[data-action="bench-penalty"]').click();p.locator('[data-penalty="Bandencheck"]').click();p.locator('[data-action="served-later"]').click()
      assert dict(rows(p))['NUMMER']=='Bank / Trainer';p.locator('#detail-ok').click()
      start(p,'900','timeout','home');assert labels(p)==['TEAM','EREIGNIS'] and dict(rows(p))['EREIGNIS']=='Timeout';p.locator('#detail-ok').click()
      start(p,'850','goalie','home');next_(p);assert labels(p)==['TEAM','EREIGNIS','RAUS','REIN'],rows(p)
      assert dict(rows(p))['RAUS'].startswith('#30') and dict(rows(p))['REIN'].startswith('#35');p.locator('#detail-ok').click()
      # ---- Tap a row: detail view (no pencil), Bearbeiten -> wizard, save -> 'Aenderung gespeichert'.
      assert p.locator('.event-edit').count()==0
      p.locator('[data-action="show-event"]').last.click();expect(p.locator('#detail-dialog')).to_be_visible()
      assert p.locator('#detail-title').inner_text()=='Ereignis' and [x.inner_text() for x in p.locator('#detail-actions button').all()]==['Bearbeiten','Schließen']
      assert p.locator('.detail-clock').inner_text()=='10:12'
      if size==(360,640):p.screenshot(path=str(OUT/'detail-ansicht-360x640.png'))
      p.locator('#detail-edit').click();expect(p.locator('#wizard')).to_be_visible()
      p.locator('[data-action="erase"]').click();digits(p,'1');p.locator('[data-action="save-existing"]').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      expect(p.locator('#detail-dialog')).to_be_visible();assert p.locator('#detail-title').inner_text()=='Änderung gespeichert'
      assert p.locator('.detail-clock').inner_text()=='10:11' and p.locator('#detail-discard').count()==0
      p.locator('#detail-ok').click()
      # Back button closes the detail view without changes.
      before=state(p)['events'];p.locator('[data-action="show-event"]').first.click();p.evaluate('window.egrepBack()')
      expect(p.locator('#detail-dialog')).not_to_be_visible();assert state(p)['events']==before
      # Yellow marks only in Aufstellung, not in the game screen or report.
      assert p.locator('#event-list .needs-check').count()==0 and p.locator('#report-sheet .needs-check').count()==0
      p.get_by_role('button',name='Aufstellung',exact=True).click();assert p.locator('#teams .needs-check').count()==1
      if size==(360,640):
        game(p);p.screenshot(path=str(OUT/'spielverlauf-360x640.png'))
      p.close()
    assert not errors,errors;b.close()
  print('V16 UI PASS: 4 coloured type rows, bold clock, summary after save (saved first; OK/Aendern/Verwerfen+Undo), order team/event/number/penalty, bench/timeout/goalie summaries, tap row detail + edit, back button, yellow marks only in Aufstellung, 3 viewports. Real Android not tested.')
if __name__=='__main__':main()
