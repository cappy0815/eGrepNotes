"""2.5 UI: referee signal reference from the header, corrected Cross-Check/Haken pictures, club logos
(team choice, scoreboard, report, print) with club colour only as ring; red/blue unchanged. Chromium only."""
from pathlib import Path
import json,os,sys,base64,io
from playwright.sync_api import sync_playwright,expect
from test_ui import boot,state,skip_operator,confirm
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v25');OUT.mkdir(parents=True,exist_ok=True)
CHROMIUM=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None))
KEY='nev-spielnotiz-v0.1'
def roster(home='Neusser EV',away='EV Duisburg'):
    return {'version':9,'currentPeriod':1,'meta':{'date':'2026-11-02','number':'T_025','operatorName':'','operatorPrompted':True,'timeMode':'down'},
      'home':{'name':home,'players':[{'id':'h12','number':'12','name':'Neumann, Mia'}],'startGoalie':''},
      'away':{'name':away,'players':[],'startGoalie':''},'events':[],'shootout':[]}
def game(p):p.get_by_role('button',name='Spiel',exact=True).click();skip_operator(p)
def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox']);errors=[]
    for size in [(320,480),(360,640),(412,915)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(roster())},auto_ok=False);game(p)
      # ---- Header button fits; opens the reference on every screen.
      hdr=p.locator('.app-header').evaluate('n=>[n.clientWidth,n.scrollWidth]');assert hdr[1]<=hdr[0]+1,hdr
      bb=p.locator('#open-menu').bounding_box();assert bb['x']+bb['width']<=size[0] and bb['width']>=28,bb
      for tab in ['Aufstellung','Bericht','Spiel']:
        p.get_by_role('button',name=tab,exact=True).click();skip_operator(p);p.locator('#open-menu').click();p.locator('#show-signs').click();expect(p.locator('#signs-dialog')).to_be_visible()
        if tab!='Spiel':p.locator('#close-signs').click()
      names=p.locator('.sign-card span').all_text_contents();assert len(names)==21 and names[:3]==['Beinstellen','Haken','Unkorrekter Körperangriff'],names
      box=p.locator('#signs-dialog').bounding_box();assert box['y']>=-1 and box['y']+box['height']<=size[1]+1,box
      off=p.locator('.sign-card').evaluate_all('bs=>bs.map(b=>{const r=b.getBoundingClientRect();return Math.max(...[...b.children].map(c=>{const i=c.getBoundingClientRect();return Math.max(Math.abs((i.left-r.left)-(r.right-i.right)),i.bottom>r.bottom+0.5?99:0);}));})')
      assert max(off)<=1.5,(size,max(off))
      if size==(360,640):p.screenshot(path=str(OUT/'schirizeichen-uebersicht-360x640.png'))
      # Tap enlarges (one at a time), tap again shrinks; Android back closes.
      c=p.locator('.sign-card[data-sign="Stockcheck / Cross-Check"]');c.click();assert 'big' in c.get_attribute('class')
      w=c.locator('img').bounding_box()['width'];assert w>=min(220,size[0]*0.65),w
      if size==(360,640):p.screenshot(path=str(OUT/'schirizeichen-gross-360x640.png'))
      p.locator('.sign-card[data-sign="Haken"]').click();assert p.locator('.sign-card.big').count()==1 and 'big' not in c.get_attribute('class')
      p.locator('.sign-card[data-sign="Haken"]').click();assert p.locator('.sign-card.big').count()==0
      p.evaluate('window.egrepBack()');expect(p.locator('#signs-dialog')).not_to_be_visible()
      # ---- Club logos: scoreboard, team choice, report, print; ring = club colour; borders stay red/blue.
      for side in ['home','away']:
        img=p.locator(f'#score-{side}-logo');assert img.is_visible() and img.get_attribute('src').startswith('data:image/webp'),side
        assert img.evaluate('e=>getComputedStyle(e).boxShadow')=='none','2.6: no colour ring'
      p.locator('#new-event').click();[p.locator(f'[data-digit="{x}"]').click() for x in '1500'];p.locator('[data-action="next"]').click();p.locator('[data-type="goal"]').click()
      assert p.locator('.team-choice.away img.team-logo').count()==1 and p.locator('.team-choice.home img.team-logo').count()==1
      bl=p.locator('.team-choice.away').evaluate('e=>getComputedStyle(e).borderLeftColor');assert bl=='rgb(22, 91, 197)',bl
      if size==(360,640):p.screenshot(path=str(OUT/'teamauswahl-logos-360x640.png'))
      p.locator('#wizard-close').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      if size==(360,640):p.screenshot(path=str(OUT/'anzeigetafel-logos-360x640.png'))
      p.get_by_role('button',name='Bericht',exact=True).click();assert p.locator('.report-match img.team-logo').count()==2
      p.evaluate('EgrepUI.preparePrintReport()');assert p.locator('#print-output .print-match img.team-logo').count()==2
      p.close()
      # Unknown club -> initial / no logo; Neuss variants keep a logo; age group suffix matches.
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(roster('Neusser EV U15','Phantasie Pinguine'))},auto_ok=False);game(p)
      assert p.locator('#score-home-logo').is_visible() and p.locator('#score-away-logo').is_hidden()
      p.locator('#new-event').click();[p.locator(f'[data-digit="{x}"]').click() for x in '1500'];p.locator('[data-action="next"]').click();p.locator('[data-type="goal"]').click()
      assert p.locator('.team-choice.away .team-initial').inner_text()=='G';p.locator('#wizard-close').click()
      if p.locator('#choice-dialog').is_visible():confirm(p)
      p.close()
    assert not errors,errors;b.close()
  print('V25 UI PASS: header signal button fits and works on all tabs, 21 signals in frequency order centred, enlarge/shrink, back closes; club logos in scoreboard/team choice/report/print without ring (2.6), red/blue borders unchanged, unknown club -> initial, age group suffix matches; 3 viewports. Real Android not tested.')
if __name__=='__main__':main()
