"""Period selection regression tests against the shipped UI, not a reimplementation.
Includes persistence via serialized state; native browser storage reload is attempted when policy permits.
No physical Android device or emulator is used.
"""
from pathlib import Path
import json, sys, threading, http.server, functools
from playwright.sync_api import sync_playwright, expect
from test_ui import skip_operator, boot, state, digits, next_, no_assists, confirm, cancel_choice, cancel_draft, assert_fit, ROOT, LOGO
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/egrep_v12_tests/period')
OUT.mkdir(parents=True,exist_ok=True)
KEY='nev-spielnotiz-v0.1'

def event(id,clock,period=1,order=1):
    return dict(id=id,order=order,time=clock,period=period,clock=clock.replace(':',''),team='home',type='goal',player='56',assist1='',assist2='')
def fixture(period,events):
    return {KEY:json.dumps(dict(currentPeriod=period,meta={'number':'TEST_012','date':'2026-10-07'},home={'name':'Neusser EV','players':[]},away={'name':'Gast Beispiel','players':[]},events=events))}
def game(page):page.get_by_role('button',name='Spiel',exact=True).click();skip_operator(page)
def open_new(page,clock=None):
    game(page);page.locator('#new-event').click()
    if clock is not None:digits(page,clock)
def save_goal(page,number='56'):
    page.locator('[data-type="goal"]').click();page.locator('[data-team="home"]').click();no_assists(page,number)
def select_live(page,p):page.locator('[data-current-period="'+str(p)+'"]').click()
def change_local(page,p):
    page.locator('[data-action="toggle-period"]').click();page.locator('[data-period="'+str(p)+'"]').click()

def main():
  with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=__import__('os').environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if __import__('os').path.exists(p)),None)),args=['--no-sandbox'],headless=True)
    errors=[]
    def pg(saved=None,size=(360,640)):
        page=browser.new_page(viewport={'width':size[0],'height':size[1]})
        page.on('pageerror',lambda e:errors.append(str(e)));boot(page,saved);return page
    # Fresh match: no selected period. Time alone cannot continue. The initial popup choice establishes live period.
    p=pg();game(p);assert p.locator('[data-current-period].active').count()==0
    assert p.locator('#undo').is_disabled();assert p.locator('#undo').inner_text()=='R\u00fcckg\u00e4ngig'
    p.screenshot(path=str(OUT/'spiel-neu.png'))
    open_new(p,'1012');assert p.locator('[data-action="next"]').is_disabled()
    p.locator('[data-period="1"]').click();assert state(p)['currentPeriod']==1
    assert p.locator('.event-period-selector').count()==0;assert '1. Drittel' in p.locator('#wizard-title').inner_text()
    next_(p);save_goal(p);assert len(state(p)['events'])==1
    open_new(p,'0900');assert p.locator('.event-period-selector').count()==0
    next_(p);save_goal(p);assert [e['period'] for e in state(p)['events']]==[1,1]
    assert not p.locator('#time-jump-dialog').is_visible()
    # Explicit live change persists across views; undo never changes it back.
    select_live(p,3);p.get_by_role('button',name='Aufstellung',exact=True).click();game(p)
    assert p.locator('[data-current-period="3"]').get_attribute('aria-pressed')=='true'
    saved=p.evaluate('window._saved');q=pg(saved);game(q);assert state(q)['currentPeriod']==3
    assert q.locator('#undo').is_disabled() # Undo history is session-only, as before.
    # Edit an earlier event in a later live period. Local change is allowed; global selection is untouched.
    p.locator('[data-action="show-event"]').last.click();p.locator('#detail-edit').click();assert '1. Drittel' in p.locator('#wizard-title').inner_text()  # 1.5: oldest entry is at the bottom
    digits(p,'1020');p.locator('[data-action="save-existing"]').click()
    assert not p.locator('#wizard').is_visible();assert state(p)['currentPeriod']==3
    assert state(p)['events'][0]['period']==1
    p.locator('#undo').click();assert state(p)['events'][0]['time']=='10:12';assert state(p)['currentPeriod']==3
    # A manual per-event period in the popup must not change the live period.
    open_new(p,'0800');change_local(p,1);assert state(p)['currentPeriod']==3
    next_(p);save_goal(p);assert state(p)['events'][-1]['period']==1;assert state(p)['currentPeriod']==3
    p.screenshot(path=str(OUT/'spiel-drittel-3.png'))
    # Higher remaining time: no automatic switching. Cancel preserves typed time and selected period.
    p=pg(fixture(1,[event('a','0:50')]));open_new(p,'1830');next_(p)
    expect(p.locator('#time-jump-dialog')).to_be_visible();assert state(p)['currentPeriod']==1
    assert p.locator('#time-jump-next').is_visible();p.screenshot(path=str(OUT/'zeit-sicherheit.png'))
    p.locator('#time-jump-cancel').click();assert '18:30' in p.locator('.number-display').inner_text();assert state(p)['currentPeriod']==1
    # Confirm beginning next period: stored for future events and used by this candidate.
    next_(p);p.locator('#time-jump-next').click();assert state(p)['currentPeriod']==2
    save_goal(p);assert state(p)['events'][-1]['period']==2;assert state(p)['events'][-1]['time']=='18:30'
    open_new(p);assert '2. Drittel' in p.locator('#wizard-title').inner_text();p.screenshot(path=str(OUT/'uhrzeit-drittel-2.png'))
    p.locator('#wizard-close').click();assert not p.locator('#wizard').is_visible()
    # Retro path acknowledges the chronology once, without switching the live period.
    p=pg(fixture(1,[event('a','0:50')]));open_new(p,'1830');next_(p);p.locator('#time-jump-retro').click()
    save_goal(p);assert not p.locator('#choice-dialog').is_visible();assert len(state(p)['events'])==2
    assert state(p)['currentPeriod']==1 and state(p)['events'][-1]['period']==1
    assert p.locator('.event-clock').all_text_contents()==['1830','050']
    # Editing time after acknowledgment prompts again; approval is not a permanent bypass.
    p=pg(fixture(1,[event('a','0:50')]));open_new(p,'1830');next_(p);p.locator('#time-jump-retro').click()
    p.locator('#wizard-back').click();digits(p,'1700');next_(p)
    expect(p.locator('#time-jump-dialog')).to_be_visible();p.locator('#time-jump-retro').click();save_goal(p)
    # Equal timestamps are normal at a whistle, never a new-period warning.
    p=pg(fixture(1,[event('a','0:50')]));open_new(p,'0050');next_(p)
    assert not p.locator('#time-jump-dialog').is_visible();save_goal(p);assert len(state(p)['events'])==2
    # The third period must never offer a nonexistent fourth period.
    p=pg(fixture(3,[event('a','0:50',3)]));open_new(p,'1900');next_(p)
    assert p.locator('#time-jump-next').is_hidden();p.locator('#time-jump-retro').click();save_goal(p)
    assert state(p)['currentPeriod']==3
    # Editing an event's period never switches live period, including after Undo.
    p=pg(fixture(3,[event('a','10:12')]));game(p);p.locator('[data-action="show-event"]').first.click();p.locator('#detail-edit').click()
    change_local(p,2);p.locator('[data-action="save-existing"]').click();assert state(p)['events'][0]['period']==2
    assert state(p)['currentPeriod']==3;p.locator('#undo').click();assert state(p)['events'][0]['period']==1;assert state(p)['currentPeriod']==3
    # Cancelled reset is nondestructive. Confirmed reset and next startup both have no chosen period.
    p.get_by_role('button',name='Bericht',exact=True).click();p.locator('#reset-game').click();cancel_choice(p);assert state(p)['currentPeriod']==3
    p.locator('#reset-game').click();confirm(p);  # 2.0: one step + archive
    assert state(p)['currentPeriod'] is None and state(p)['events']==[]
    r=pg(p.evaluate('window._saved'));game(r);assert r.locator('[data-current-period].active').count()==0
    # No horizontal overflow, and numeric steps fit without scrolling on supported small screens.
    for size in [(320,480),(320,568),(360,640),(390,844),(412,915)]:
      r=pg(size=size);game(r)
      assert r.evaluate('document.documentElement.scrollWidth<=innerWidth'),size
      # The entire header including Undo has non-overlapping, in-viewport bounds.
      boxes=[r.locator(sel).bounding_box() for sel in ['.app-header img','.brand','#undo','#open-menu']]
      for b in boxes:assert b['x']>=0 and b['x']+b['width']<=size[0]+1,(size,b)
      for x,y in zip(boxes,boxes[1:]):assert x['x']+x['width']<=y['x']+1,(size,boxes)
      open_new(r,'1012');assert_fit(r);r.locator('[data-period="1"]').click();assert_fit(r)
      r.screenshot(path=str(OUT/f'zeit-{size[0]}x{size[1]}.png'))
      next_(r);assert_fit(r);save_goal(r);r.locator('[data-action="show-event"]').first.click();r.locator('#detail-edit').click();assert_fit(r)
      r.locator('[data-action="toggle-period"]').click();assert_fit(r);r.close()
    # Verify the actual browser localStorage path via same-origin reload, without the test adapter.
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
      def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(ROOT)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
      r=browser.new_page(viewport={'width':360,'height':640});r.on('pageerror',lambda e:errors.append(str(e)))
      try:
        r.goto('http://127.0.0.1:'+str(server.server_port)+'/index.html');r.wait_for_function('!!window.EgrepUI')
        game(r);select_live(r,2);assert state(r)['currentPeriod']==2;r.reload();r.wait_for_function('!!window.EgrepUI')
        game(r);assert state(r)['currentPeriod']==2;open_new(r);assert '2. Drittel' in r.locator('#wizard-title').inner_text()
        print('Native browser localStorage reload PASS')
      except Exception as exc:
        if 'ERR_BLOCKED_BY_ADMINISTRATOR' not in str(exc):raise
        print('SKIPPED native browser localStorage reload: navigation blocked by environment policy. Serialized-state restart tests above passed.')
      finally:r.close()
    finally:server.shutdown();server.server_close();thread.join(timeout=5)
    assert not errors,errors
    browser.close()
    print('PERIOD UI PASS: first choice, persistence/reload, local edits, undo isolation, next-period/retro/correction paths, equal clocks, no period 4, reset, five viewport sizes. No real Android test.')
if __name__=='__main__':main()
