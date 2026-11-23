"""Duration selection, report names, team colours; actual shipped DOM/JS/CSS."""
from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright,expect
from test_ui import boot,state,begin,digits,next_,add_player,select_setup,confirm,assert_fit
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/egrep_v14_tests/penalty')
OUT.mkdir(parents=True,exist_ok=True)
KEY='nev-spielnotiz-v0.1'
def keep(page):
    # 1.9: with a roster, the already chosen player is tapped again in the number grid.
    if page.locator('.pick-btn.selected').count():page.locator('.pick-btn.selected').click()
    else:next_(page)
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=__import__('os').environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if __import__('os').path.exists(p)),None)),headless=True,args=['--no-sandbox'])
 p=b.new_page(viewport={'width':390,'height':844});errors=[];p.on('pageerror',lambda e:errors.append(str(e)));boot(p)
 add_player(p,'home','56','Alex Beispiel');add_player(p,'away','18','Kim Muster')
 # Defaults are per new event, not last selected duration.
 begin(p,'1012','home','penalty');digits(p,'56');next_(p);assert_fit(p)
 assert p.locator('[data-duration="2"]').get_attribute('aria-pressed')=='true'
 p.locator('[data-penalty]').first.click();assert state(p)['events'][-1]['penaltyDuration']=='2'
 begin(p,'1000','away','penalty');digits(p,'18');next_(p);p.locator('[data-duration="5"]').click();assert_fit(p)
 p.screenshot(path=str(OUT/'strafe-5-minuten.png'));p.locator('[data-penalty="Haken"]').click()
 assert state(p)['events'][-1]['penaltyDuration']=='5'
 begin(p,'905','home','penalty');digits(p,'56');next_(p)
 assert p.locator('[data-duration="2"]').get_attribute('aria-pressed')=='true'
 p.locator('[data-duration="game"]').click();p.locator('[data-action="custom-penalty"]').click()
 p.locator('#custom-penalty').fill('Eigener Text <b>unveraendert</b>')
 p.locator('[data-duration="5"]').click();assert p.locator('#custom-penalty').input_value()=='Eigener Text <b>unveraendert</b>'
 p.locator('[data-duration="game"]').click();p.locator('[data-action="save-custom"]').click()
 assert state(p)['events'][-1]['penaltyDuration']=='game'
 assert 'Spieldauer' in p.locator('#event-list').inner_text() and p.locator('#event-list small b').count()==0
 # Duration survives edit, can be changed alone and undone, including current period.
 p.locator('[data-action="show-event"]').nth(1).click();p.locator('#detail-edit').click();next_(p);p.locator('[data-type="penalty"]').click();p.locator('[data-team="away"]').click();keep(p)
 assert p.locator('[data-duration="5"]').get_attribute('aria-pressed')=='true'
 p.locator('[data-duration="game"]').click();p.locator('[data-action="save-existing"]').click()
 assert state(p)['events'][1]['penaltyDuration']=='game';p.locator('#undo').click();assert state(p)['events'][1]['penaltyDuration']=='5'
 # Report shows names (not print-only), duration and unambiguous team colours.
 p.get_by_role('button',name='Bericht',exact=True).click()
 expect(p.locator('#report-sheet .pen-who, #report-sheet .event-names').first).to_be_visible()  # 3.3: penalties as who/what lines
 assert 'Alex Beispiel' in p.locator('#report-sheet').inner_text() and 'Kim Muster' in p.locator('#report-sheet').inner_text()
 assert '2 Min.' in p.locator('#report-sheet').inner_text() and '5 Min.' in p.locator('#report-sheet').inner_text()
 home=p.locator('#report-sheet tr.penalty.home').first.evaluate('(e)=>getComputedStyle(e).backgroundColor')
 away=p.locator('#report-sheet tr.penalty.away').first.evaluate('(e)=>getComputedStyle(e).backgroundColor')
 assert home=='rgb(255, 241, 242)' and away=='rgb(240, 246, 255)',(home,away)
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 p.screenshot(path=str(OUT/'bericht-mit-namen.png'),full_page=True)
 saved=p.evaluate('window._saved');q=b.new_page();boot(q,saved);assert [x['penaltyDuration'] for x in state(q)['events']]==['2','5','game'];q.close()
 # A legacy penalty stays unknown when only its time is saved. Then may be explicitly assigned.
 s=state(p);s['events']=[dict(s['events'][0])];s['events'][0].pop('penaltyDuration');saved_old={KEY:json.dumps(s)}
 q=b.new_page(viewport={'width':320,'height':480});boot(q,saved_old)
 assert state(q)['events'][0]['penaltyDuration']==''
 q.locator('[data-action="show-event"]').first.click();q.locator('#detail-edit').click();q.locator('[data-action="save-existing"]').click();assert state(q)['events'][0]['penaltyDuration']==''
 q.close()
 # Common penalty form and editing form fit small portrait screens without scrolling.
 for size in [(320,480),(320,568),(360,640),(390,844),(412,915)]:
  q=b.new_page(viewport={'width':size[0],'height':size[1]});boot(q)
  begin(q,'1012','away','penalty');digits(q,'18');next_(q);assert_fit(q)
  q.screenshot(path=str(OUT/f'strafe-{size[0]}x{size[1]}.png'))
  q.locator('[data-duration="game"]').click();q.locator('[data-penalty]').first.click();assert state(q)['events'][-1]['penaltyDuration']=='game'
  q.locator('[data-action="show-event"]').first.click();q.locator('#detail-edit').click();next_(q);q.locator('[data-type="penalty"]').click();q.locator('[data-team="away"]').click();keep(q);assert_fit(q)
  q.close()
 assert not errors,errors;b.close()
print('PASS penalties 2/5/game: defaults, custom text, edit/undo/reload/legacy migration, visible report names, home-red/away-blue, five no-scroll penalty forms.')
