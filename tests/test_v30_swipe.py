"""3.0: swipe between Aufstellung / Spiel / Bericht with simulated touch events (Chromium, touch enabled).
Checks direction, ends of the row, thresholds (short, slow, diagonal), inputs, open dialogs and the switch."""
from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright
from uihelper import boot,skip_operator,CHROMIUM
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-swipe');OUT.mkdir(parents=True,exist_ok=True)
SWIPE='''([sel,dx,dy,ms])=>new Promise(res=>{const el=document.querySelector(sel),r=el.getBoundingClientRect(),x=r.left+r.width/2,y=Math.min(r.top+r.height/2,innerHeight/2);
 const t=(cx,cy)=>new Touch({identifier:1,target:el,clientX:cx,clientY:cy});
 el.dispatchEvent(new TouchEvent('touchstart',{touches:[t(x,y)],changedTouches:[t(x,y)],bubbles:true}));
 setTimeout(()=>{el.dispatchEvent(new TouchEvent('touchend',{touches:[],changedTouches:[t(x+dx,y+dy)],bubbles:true}));res();},ms);})'''
def active(p):return p.evaluate("document.querySelector('.screen.active').id")
def swipe(p,dx,dy=0,ms=150,sel='.screen.active .section-head, .screen.active h2, .screen.active'):
    target=p.evaluate("s=>{for(const q of s.split(', ')){if(document.querySelector(q))return q}}",sel)
    p.evaluate(SWIPE,[target,dx,dy,ms]);p.wait_for_timeout(60);skip_operator(p)
def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox']);errors=[]
    for size in [(320,480),(412,915)]:
      ctx=b.new_context(viewport={'width':size[0],'height':size[1]},has_touch=True);p=ctx.new_page();p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p)
      assert active(p)=='setup'
      swipe(p,80);assert active(p)=='setup','right swipe on the first screen does nothing'
      swipe(p,-120);assert active(p)=='game',active(p)
      assert p.locator('.tab.active').inner_text()=='Spiel'
      swipe(p,-120);assert active(p)=='report'
      swipe(p,-120);assert active(p)=='report','no wrap-around'
      swipe(p,120);assert active(p)=='game';swipe(p,120);assert active(p)=='setup'
      # Thresholds: too short, too slow, too steep -> no change (scrolling stays scrolling).
      swipe(p,-30);assert active(p)=='setup'
      swipe(p,-120,ms=900);assert active(p)=='setup'
      swipe(p,-100,dy=80);assert active(p)=='setup'
      # Not from inputs (cursor moves / text selection).
      swipe(p,-120,sel='#setup input');assert active(p)=='setup'
      # Not while a dialog is open.
      p.locator('#open-menu').click();swipe(p,-120,sel='main');assert active(p)=='setup';p.keyboard.press('Escape');p.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
      # Switch in the settings, stored per device; club choice keeps it.
      p.locator('#open-menu').click();p.locator('#open-settings').click();assert p.locator('#swipe-toggle').is_checked()
      p.locator('#swipe-toggle').uncheck();assert json.loads(p.evaluate('window._saved')['egrep-settings'])['swipe'] is False
      p.locator('[data-club="krefelder-ev"]').click();assert json.loads(p.evaluate('window._saved')['egrep-settings'])=={'homeClub':'krefelder-ev','swipe':False}
      swipe(p,-120);assert active(p)=='setup','switched off'
      p.locator('#open-menu').click();p.locator('#open-settings').click();p.locator('#swipe-toggle').check();p.locator('#close-settings').click()
      swipe(p,-120);assert active(p)=='game'
      ctx.close()
    assert not errors,errors;b.close()
  print('V30 SWIPE PASS: left/right between Aufstellung, Spiel, Bericht, no wrap-around, ignores short/slow/diagonal moves, inputs and open dialogs, switch in settings (kept with club choice); 2 viewports, simulated touch.')
if __name__=='__main__':main()
