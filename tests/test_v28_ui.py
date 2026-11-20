"""2.8 UI: quick menu in the header (Schiri-Zeichen, Archiv with count, Info) on every tab;
tap outside / Back closes; header fits. Chromium only, no real Android."""
from pathlib import Path
import json,os,re,sys
from playwright.sync_api import sync_playwright,expect
from test_ui import boot,state,skip_operator,confirm
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v28');OUT.mkdir(parents=True,exist_ok=True)
CHROMIUM=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None))
KEY='nev-spielnotiz-v0.1';AKEY='egrep-notes-archiv-v1'
def st():
    return {'version':9,'currentPeriod':1,'meta':{'date':'2026-11-13','number':'T_028','operatorName':'','operatorPrompted':True,'timeMode':'down'},
      'home':{'name':'Neusser EV','players':[],'startGoalie':''},'away':{'name':'Grefrather EG','players':[],'startGoalie':''},
      'events':[{'id':'e1','order':1,'type':'goal','team':'home','period':1,'time':'15:00','clock':'1500','player':'8'}],'shootout':[]}
def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox']);errors=[]
    for size in [(320,480),(360,640),(412,915)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(st())},auto_ok=False)
      hdr=p.locator('.app-header').evaluate('n=>[n.clientWidth,n.scrollWidth]');assert hdr[1]<=hdr[0]+1,hdr
      assert p.locator('.app-header #show-signs').count()==0 and p.locator('.app-header #show-info').count()==0,'old buttons moved into the menu'
      for tab in ['Aufstellung','Spiel','Bericht']:
        p.get_by_role('button',name=tab,exact=True).click();skip_operator(p)
        p.locator('#open-menu').click();expect(p.locator('#quick-menu')).to_be_visible()
        items=[x.locator(':scope > span:last-child').evaluate('e=>e.firstChild.textContent.trim()') for x in p.locator('#quick-menu .menu-item').all()];assert items==['Schiri-Zeichen','Archiv','Einstellungen','Info'],items  # 3.0: Einstellungen
        box=p.locator('#quick-menu').bounding_box();assert box['x']>=0 and box['x']+box['width']<=size[0]+1 and box['y']+box['height']<=size[1],box
        if size==(360,640) and tab=='Spiel':p.screenshot(path=str(OUT/'schnellmenue-360x640.png'))
        p.evaluate('window.egrepBack()');expect(p.locator('#quick-menu')).not_to_be_visible()
      # Each entry opens its target and closes the menu.
      p.locator('#open-menu').click();p.locator('#show-signs').click();expect(p.locator('#signs-dialog')).to_be_visible();assert not p.locator('#quick-menu').is_visible()
      p.evaluate('window.egrepBack()');expect(p.locator('#signs-dialog')).not_to_be_visible()
      p.locator('#open-menu').click();p.locator('#show-info').click();expect(p.locator('#info-dialog')).to_be_visible();assert re.search(r'Version [23]\.', p.locator('#info-version').inner_text());assert p.locator('#project-link').get_attribute('href')=='https://cappy0815.github.io/' and p.locator('#project-link').is_visible();p.locator('#close-info').click()
      p.locator('#open-menu').click();p.locator('#menu-archive').click();expect(p.locator('#archive-dialog')).to_be_visible();p.locator('#close-archive').click()
      # Tap outside closes; archive count shown in the menu after a game was archived.
      p.locator('#open-menu').click();p.mouse.click(10,size[1]-10);expect(p.locator('#quick-menu')).not_to_be_visible()
      p.get_by_role('button',name='Bericht',exact=True).click();p.locator('#reset-game').click();confirm(p)
      p.locator('#open-menu').click();assert p.locator('#menu-archive-label').inner_text()=='Archiv (1)',p.locator('#menu-archive-label').inner_text()
      p.locator('#menu-archive').click();assert p.locator('.archive-item').count()==1 and 'Grefrather EG' in p.locator('.archive-item').first.inner_text()
      p.locator('#close-archive').click();p.close()
    assert not errors,errors;b.close()
  print('V28 UI PASS: header fits with menu button; menu on all tabs with Schiri-Zeichen/Archiv/Info; each opens its dialog and closes the menu; Back and tap outside close; archive count; project link in Info; 3 viewports. Real Android not tested.')
if __name__=='__main__':main()
