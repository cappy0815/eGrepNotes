"""2.6 UI: long team names do not shift score, logos or goalies (shared grid), names max. 2 lines on
the scoreboard, report logos 40 px in one row with the score, no colour ring. Chromium only."""
from pathlib import Path
import json,os,sys
from playwright.sync_api import sync_playwright
from test_ui import boot,skip_operator
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v26');OUT.mkdir(parents=True,exist_ok=True)
CHROMIUM=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None))
KEY='nev-spielnotiz-v0.1'
def st(home,away,goalie_away='Roth, Lenny'):
    return {'version':9,'currentPeriod':3,'meta':{'date':'2026-10-31','number':'U15_LL_035','operatorName':'Muster, Max','operatorPrompted':True,'timeMode':'down'},
      'home':{'name':home,'players':[{'id':'h1','number':'1','name':'Becker, Lena','isGoalie':True,'starter':True}],'startGoalie':'1'},
      'away':{'name':away,'players':[{'id':'a67','number':'67','name':goalie_away,'isGoalie':True,'starter':True}],'startGoalie':'67'},
      'events':[{'id':'e1','order':1,'type':'goal','team':'home','period':1,'time':'18:48','clock':'1848','player':'8'}],'shootout':[]}
CASES=[('Spg Neusser EV GSC Moers','TuS Wiehl'),('TuS Wiehl','SpG ESV Grizzlys Bergkamen / ESC Rheine Young Cats'),('Neusser EV','EV Duisburg'),('Phantasie Pinguine ohne Logo mit langem Namen','Gast')]
def mid(b):return b['y']+b['height']/2
def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox']);errors=[]
    for size in [(320,480),(360,640),(412,915)]:
      for home,away in CASES:
        p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
        boot(p,{KEY:json.dumps(st(home,away))},auto_ok=False);p.get_by_role('button',name='Spiel',exact=True).click();skip_operator(p)
        q=lambda s:p.locator(s).bounding_box()
        sh,sa,co=q('#score-home'),q('#score-away'),q('.score-colon')
        assert abs(mid(sh)-mid(sa))<=1 and abs(mid(sh)-mid(co))<=2,(size,home,away,sh,sa)
        gh,ga=q('#home-goalie'),q('#away-goalie');assert abs(gh['y']-ga['y'])<=1,(size,home,away,gh,ga)
        for side in ['home','away']:
          lg=p.locator(f'#score-{side}-logo')
          if lg.is_visible():assert abs(mid(lg.bounding_box())-mid(sh))<=1.5,(size,side)
          nm=p.locator(f'#score-{side}-name').evaluate('e=>[e.getBoundingClientRect().height,parseFloat(getComputedStyle(e).lineHeight)||15.6]')
          assert nm[0]<=2*nm[1]+1,('max two lines',size,side,nm)
          assert p.locator(f'#score-{side}-logo').evaluate('e=>getComputedStyle(e).boxShadow')=='none'
        row=p.locator('.scoreboard').evaluate('n=>[n.clientWidth,n.scrollWidth]');assert row[1]<=row[0]+1,row
        if size==(360,640) and home.startswith('Spg'):p.locator('.scoreboard').screenshot(path=str(OUT/'tafel-lange-namen-360.png'))
        if size==(320,480) and away.startswith('SpG ESV'):p.locator('.scoreboard').screenshot(path=str(OUT/'tafel-zwei-lange-namen-320.png'))
        # Report: logos 40 px in the score row, names complete below.
        p.get_by_role('button',name='Bericht',exact=True).click()
        imgs=p.locator('.report-match img.team-logo').all();sc=q('.report-match strong')
        for im in imgs:
          bb=im.bounding_box();assert abs(bb['width']-40)<=0.5 and abs(mid(bb)-mid(sc))<=2,(size,bb,sc)
          assert im.evaluate('e=>getComputedStyle(e).boxShadow')=='none'
        names=p.locator('.report-match .rm-name').all_text_contents();assert names==[home,away],names
        nh,na=q('.rm-name.rm-home'),q('.rm-name.rm-away');assert abs(nh['y']-na['y'])<=1 and nh['y']>=sc['y']+sc['height']-1
        if size==(360,640) and home.startswith('Spg'):p.locator('.report-sheet').screenshot(path=str(OUT/'bericht-lange-namen-360.png'))
        p.close()
    assert not errors,errors;b.close()
  print('V26 UI PASS: scores/colon/logos on one line and goalies aligned for long/short/no-logo names, names max. 2 lines, no overflow, no ring; report logos 40 px beside score, full names aligned below; 4 name cases x 3 viewports. Real Android not tested.')
if __name__=='__main__':main()
