"""Version 1.3 browser regressions for optional author, photo actions and larger clocks."""
from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright,expect
from test_ui import boot,state,begin,no_assists,add_player,select_setup,confirm,LOGO
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/egrep_v13_tests/new')
OUT.mkdir(parents=True,exist_ok=True)
KEY='nev-spielnotiz-v0.1'

def game(p):p.get_by_role('button',name='Spiel',exact=True).click()
def report(p):p.get_by_role('button',name='Bericht',exact=True).click()
def main():
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path=__import__('os').environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if __import__('os').path.exists(p)),None)),args=['--no-sandbox'],headless=True);errors=[]
  def page(saved=None,size=(360,640)):
   p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)));boot(p,saved,operator_prompt=True);return p
  p=page();assert state(p)['meta']['operatorName']=='' and not state(p)['meta']['operatorPrompted']
  # Once per match, not at every switch. Skipping is persisted too.
  game(p);expect(p.locator('#operator-dialog')).to_be_visible();p.screenshot(path=str(OUT/'bediener-abfrage.png'))
  p.locator('#operator-later').click();assert state(p)['meta']['operatorPrompted'];report(p);game(p);expect(p.locator('#operator-dialog')).not_to_be_visible()
  q=page(p.evaluate('window._saved'));game(q);expect(q.locator('#operator-dialog')).not_to_be_visible();q.close()
  # A roster snapshot predating the operator setting must not undo the later name.
  select_setup(p);add_player(p,'home','56','Alex Beispiel')
  game(p);p.locator('#edit-operator-game').click();p.locator('#operator-name').fill('  Max Muster  ');p.locator('#operator-form button[type=submit]').click()
  assert state(p)['meta']['operatorName']=='Max Muster';p.locator('#undo').click();assert state(p)['meta']['operatorName']=='Max Muster'
  assert state(p)['home']['players']==[]
  begin(p,'1012','home','goal',1);no_assists(p,'56')
  assert len(state(p)['events'])==1
  assert float(p.locator('.event-clock').evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)'))>=13  # 1.5: newest row larger
  assert p.locator('.event-clock').inner_text()=='1012'
  p.screenshot(path=str(OUT/'spiel-groessere-uhrzeit.png'))
  report(p);assert 'Spielbericht erstellt von: Max Muster' in p.locator('#report-sheet').inner_text()
  assert 'Spielbericht erstellt von: Max Muster' in p.evaluate('EgrepUI.reportText()')
  assert float(p.locator('.time-clock').evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)'))==13
  p.evaluate('uri=>document.querySelectorAll(\'img[src="nev-logo.png"]\').forEach(n=>n.src=uri)',LOGO)
  p.screenshot(path=str(OUT/'bericht-groessere-uhrzeit.png'))
  p.pdf(path=str(OUT/'druckmuster-v1.3.pdf'),prefer_css_page_size=True,print_background=True)
  # Names are treated as text, never interpreted as markup. Editing updates all outputs.
  p.locator('#edit-operator-report').click();p.locator('#operator-name').fill('<b>Max & Klara</b>');p.locator('#operator-form button[type=submit]').click()
  assert '<b>Max & Klara</b>' in p.locator('.report-operator').inner_text()
  assert p.locator('.report-operator strong b').count()==0
  p.locator('#edit-operator-report').click();p.locator('#operator-name').fill('Not saved');p.evaluate('window.egrepBack()')
  assert state(p)['meta']['operatorName']=='<b>Max & Klara</b>'
  saved=p.evaluate('window._saved');q=page(saved);assert state(q)['meta']['operatorName']=='<b>Max & Klara</b>';expect(q.locator('#operator-dialog')).not_to_be_visible();q.close()
  # Both photo inputs go through the existing OCR pipeline (mocked, not a real OCR test).
  select_setup(p);assert p.locator('#camera-input').get_attribute('capture')=='environment';assert p.locator('#photo-input').get_attribute('capture') is None
  p.evaluate("""()=>{window.photoCount=0;EgrepOCR.start=(file,progress)=>{window.photoCount++;window.photoSize=file.size;progress(100,'Test');return {cancel(){},promise:Promise.resolve({home:[],away:[],teamNames:['Neusser EV','Gast Beispiel'],gameNumber:'TEST_13'})}}}""")
  p.locator('#photo-input').set_input_files(str(Path(__file__).resolve().parents[1]/'app/src/main/assets/nev-logo.png'));p.wait_for_timeout(100)
  assert p.evaluate('photoCount')==1 and p.locator('#ocr-panel').is_visible()
  p.locator('#camera-input').set_input_files(str(Path(__file__).resolve().parents[1]/'app/src/main/assets/nev-logo.png'));p.wait_for_timeout(100)
  assert p.evaluate('photoCount')==2 and p.evaluate('photoSize')>10000
  assert state(p)['meta']['operatorName']=='<b>Max & Klara</b>'
  p.locator('#remove-photo').click();expect(p.locator('#ocr-panel')).not_to_be_visible()
  # Two confirmed reset steps clear author and prompt flag, as well as roster/photo.
  report(p);p.locator('#reset-game').click();confirm(p)  # 2.0: one step, game goes to the archive
  assert state(p)['meta']['operatorName']=='' and not state(p)['meta']['operatorPrompted']
  game(p);expect(p.locator('#operator-dialog')).to_be_visible();p.evaluate('window.egrepBack()');assert state(p)['meta']['operatorPrompted']
  # Previously stored v1.2 data are retained; first game visit asks for the missing author.
  old={KEY:json.dumps({'version':4,'currentPeriod':2,'meta':{'date':'2026-10-07','number':'OLD'},'home':{'name':'Neusser EV','players':[]},'away':{'name':'Test Gast','players':[]},'events':[{'id':'old','team':'away','type':'penalty','player':'18','penalty':'Beinstellen','period':2,'time':'10:00','clock':'1000'}]})}
  q=page(old);expect(q.locator('#operator-dialog')).to_be_visible();q.locator('#operator-name').fill('Sam Beispiel');q.locator('#operator-form button[type=submit]').click()
  assert state(q)['currentPeriod']==2 and len(state(q)['events'])==1 and state(q)['events'][0]['time']=='10:00';q.close()
  # Photo action row, optional one-time form and clock labels stay in bounds.
  for size in [(320,480),(320,568),(360,640),(390,844),(412,915)]:
   q=page(size=size)
   for sel in ['.photo-actions .camera-button','.photo-actions .photo-button:not(.camera-button)']:
    box=q.locator(sel).bounding_box();assert box['x']>=0 and box['x']+box['width']<=size[0]
   q.screenshot(path=str(OUT/f'aufstellung-{size[0]}x{size[1]}.png'))
   game(q);box=q.locator('#operator-dialog').bounding_box();assert box['y']>=0 and box['y']+box['height']<=size[1]+1
   q.locator('#operator-later').click();begin(q,'1012','away','goal',1);no_assists(q,'56');report(q)
   assert q.evaluate('document.documentElement.scrollWidth<=innerWidth')
   assert q.locator('.time-clock').bounding_box()['width']>25
   q.close()
  assert not errors,errors;b.close()
 print('PASS operator once per game, skip/reload/edit/undo/reset, escaped names, text/PDF inclusion, old state migration, both photo inputs, OCR handoff, 13px clock labels, five mobile viewports. No Android camera device test.')
if __name__=='__main__':main()
