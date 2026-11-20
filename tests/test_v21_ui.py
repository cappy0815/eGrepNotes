"""2.1 UI: whole penalty list sorted by frequency, scrolls inside the fixed wizard (duration selector
stays in place), optional referee signals remembered per device. Chromium, no real Android."""
from pathlib import Path
import json,os,sys
from playwright.sync_api import sync_playwright,expect
from test_ui import boot,state,skip_operator,confirm,assert_fit
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v21');OUT.mkdir(parents=True,exist_ok=True)
CHROMIUM=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None))
KEY='nev-spielnotiz-v0.1'
def roster():
    return {'version':9,'currentPeriod':1,'meta':{'date':'2026-10-19','number':'T_021','operatorName':'','operatorPrompted':True},
      'home':{'name':'Neusser EV','players':[{'id':'h30','number':'30','name':'Alex Torwart','isGoalie':True,'starter':True},{'id':'h12','number':'12','name':'Neumann, Mia','isGoalie':False}],'startGoalie':'30'},
      'away':{'name':'EV Duisburg','players':[],'startGoalie':''},'events':[],'shootout':[]}
def start(p,clock,team):
    p.locator('#new-event').click()
    for x in clock:p.locator('[data-digit="'+x+'"]').click()
    p.locator('[data-action="next"]').click()
    if p.locator('#time-jump-dialog').is_visible():p.locator('#time-jump-retro').click()
    p.locator('[data-type="penalty"]').click();p.locator('[data-team="'+team+'"]').click()
def list_scroll(p):return p.locator('.penalty-list').evaluate('n=>[n.clientHeight,n.scrollHeight]')

def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox']);errors=[]
    for size in [(320,480),(360,640),(412,915)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(roster())},auto_ok=False);p.get_by_role('button',name='Spiel',exact=True).click();skip_operator(p)
      start(p,'1500','home');p.locator('[data-pick-number="12"]').click()
      names=p.locator('.penalty-list [data-penalty]').all_text_contents()
      L=p.evaluate('EgrepLogic.PENALTIES') if p.evaluate('typeof EgrepLogic')!='undefined' else None
      assert names[:3]==['Beinstellen','Haken','Unkorrekter Körperangriff'] and len(names)==31,names
      assert p.locator('.penalty-list [data-action="custom-penalty"]').count()==1 and p.locator('#penalty-list').count()==0
      assert p.locator('.penalty-list img').count()==0 and p.locator('[data-action="toggle-signs"]').get_attribute('aria-pressed')=='false'
      assert_fit(p);ch,sh=list_scroll(p);assert sh>ch,'list scrolls inside';
      dur=p.locator('[data-duration="2"]').bounding_box()
      if size==(360,640):p.screenshot(path=str(OUT/'strafliste-360x640.png'))
      # Scroll to the end: duration selector stays put, last entries reachable and tappable.
      p.locator('.penalty-list').evaluate('n=>n.scrollTop=n.scrollHeight');assert p.locator('[data-duration="2"]').bounding_box()==dur
      p.locator('[data-penalty="Schwalbe / Vortäuschen"]').click();ev=state(p)['events'][-1]
      assert (ev['penalty'],ev['penaltyDuration'],ev['player'])==('Schwalbe / Vortäuschen','2','12'),ev;p.locator('#detail-ok').click()
      # Signals on: pictograms in the list, entries without signal marked; remembered for the next penalty.
      start(p,'1400','away');p.locator('[data-digit="7"]').click();p.locator('[data-action="next"]').click()
      p.locator('[data-action="toggle-signs"]').click()
      assert p.locator('[data-action="toggle-signs"]').get_attribute('aria-pressed')=='true' and p.locator('.penalty-list.with-signs').count()==1
      assert p.locator('.penalty-list img').count()==21 and p.locator('.no-sign').count()==10,(p.locator('.penalty-list img').count(),p.locator('.no-sign').count())
      assert p.locator('[data-penalty="Beinstellen"] img').count()==1 and p.locator('[data-penalty="Torhüterbehinderung"] .no-sign').count()==1
      assert_fit(p);w=p.locator('[data-penalty="Haken"] img').evaluate('i=>[i.naturalWidth,i.getBoundingClientRect().width]');assert w[0]==176 and w[1]>=80,w
      # 2.3: labels stay inside their card (two lines, also with larger system font).
      for fs in [None,16]:
        if fs:p.add_style_tag(content='.penalty-item span{font-size:%dpx!important}'%fs)
        out=p.locator('.penalty-list.with-signs .penalty-item').evaluate_all('bs=>bs.filter(b=>{const r=b.getBoundingClientRect();return [...b.children].some(c=>{const q=c.getBoundingClientRect();return q.bottom>r.bottom+0.5||q.top<r.top-0.5||q.right>r.right+0.5;});}).map(b=>b.textContent)')
        assert not out,(size,fs,out)
      p.evaluate("document.querySelectorAll('style').forEach(s=>{if(s.textContent.includes('16px!important'))s.remove()})")
      if size in [(360,640),(320,480)]:p.screenshot(path=str(OUT/f'schirizeichen-{size[0]}x{size[1]}.png'))
      p.locator('[data-duration="5"]').click();p.locator('[data-penalty="Bandencheck"]').click();ev=state(p)['events'][-1]
      assert (ev['penalty'],ev['penaltyDuration'],ev['team'])==('Bandencheck','5','away'),ev;p.locator('#detail-ok').click()
      start(p,'1300','away');p.locator('[data-digit="8"]').click();p.locator('[data-action="next"]').click()
      assert p.locator('.penalty-list.with-signs').count()==1,'setting remembered';assert p.evaluate("localStorage.getItem('egrep-notes-schirizeichen')")=='1'
      # Custom text still works from the end of the list; signals off again.
      p.locator('[data-action="custom-penalty"]').click();p.locator('#custom-penalty').fill('Test Ansage');p.locator('[data-action="save-custom"]').click()
      assert state(p)['events'][-1]['penalty']=='Test Ansage';p.locator('#detail-ok').click()
      # Edit: current penalty highlighted.
      eid=[e for e in state(p)['events'] if e['penalty']=='Bandencheck'][0]['id']
      p.locator(f'[data-action="show-event"][data-id="{eid}"]').click();p.locator('#detail-edit').click()
      p.locator('[data-action="next"]').click();p.locator('[data-type="penalty"]').click();p.locator('[data-team="away"]').click();p.locator('[data-action="next"]').click()
      assert 'selected' in p.locator('[data-penalty="Bandencheck"]').get_attribute('class')
      p.locator('[data-action="toggle-signs"]').click();assert p.locator('.penalty-list img').count()==0
      p.locator('#wizard-close').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      p.close()
    assert not errors,errors;b.close()
  print('V21 UI PASS: 31 penalties sorted by frequency + Sonstige at end, list scrolls inside fixed wizard (durations stay), last entry tappable, signals toggle (21 pictograms, 10 marked without), remembered per device, duration + signal list, custom text, edit highlights current, 3 viewports. Real Android not tested.')
if __name__=='__main__':main()
