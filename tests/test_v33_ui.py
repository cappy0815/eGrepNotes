"""3.3: score after each goal in report, text and print (game-time order, scored penalty shots count,
missed ones not), read clock time right-aligned. Chromium, fantasy names."""
from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright
from uihelper import boot,skip_operator,CHROMIUM
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v33');OUT.mkdir(parents=True,exist_ok=True)
KEY='nev-spielnotiz-v0.1'
def ev(i,typ,team,period,clock,**k):return dict({'id':'e'+str(i),'order':i,'type':typ,'team':team,'period':period,'clock':clock,'time':clock[:2]+':'+clock[2:],'player':'9'},**k)
# entered out of order on purpose: the score follows the game time, not the input order
EV=[ev(1,'goal','away',1,'1500',player='4'),ev(2,'goal','home',1,'1800',player='9',assist1='7'),ev(3,'penalty','away',1,'1000',player='4',penalty='Haken',penaltyDuration='2'),
    ev(4,'penaltyshot','home',2,'1200',player='7',scored=True),ev(5,'penaltyshot','away',2,'0900',player='4',scored=False),ev(6,'goal','home',3,'0130',player='23'),ev(7,'timeout','away',3,'0100')]
G={'version':9,'currentPeriod':3,'meta':{'date':'2026-11-23','number':'U13_LL_033','operatorName':'','operatorPrompted':True,'timeMode':'down'},
   'home':{'name':'Neusser EV','players':[{'id':'h9','number':'9','name':'Engel, Ola','isGoalie':False},{'id':'h7','number':'7','name':'Muster, Kai','isGoalie':False},{'id':'h23','number':'23','name':'Wenz, Luca','isGoalie':False}],'startGoalie':''},
   'away':{'name':'EC Musterstadt','players':[{'id':'a4','number':'4','name':'Gast, Gina','isGoalie':False}],'startGoalie':''},'events':EV,'shootout':[]}
EXPECT={'e2':'1:0','e1':'1:1','e4':'2:1','e6':'3:1'}
def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox']);errors=[]
    for size in [(320,640),(412,915)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(G)})
      assert p.evaluate('window.EgrepLogic?1:0') in (0,1)
      run=p.evaluate("window.EgrepLogic? EgrepLogic.runningScores(window.EgrepUI.getState()) : null") if p.evaluate("!!window.EgrepLogic") else None
      p.get_by_role('button',name='Bericht',exact=True).click();skip_operator(p)
      rows=p.locator('#report-sheet tbody tr')
      scores=[(r.get_attribute('class').split()[0],r.locator('.report-score').inner_text() if r.locator('.report-score').count() else '') for r in rows.all()]
      assert [s for t,s in scores if s]==['1:0','1:1','2:1','3:1'],scores
      assert all(not s for t,s in scores if t in ('penalty','timeout')) and sum(1 for t,s in scores if t=='penaltyshot' and s)==1,scores
      # read clock right-aligned within its cell, game time stays left
      geo=p.evaluate("""[...document.querySelectorAll('#report-sheet tbody td:first-child')].map(td=>{const c=td.getBoundingClientRect(),cs=getComputedStyle(td),k=td.querySelector('.time-clock'),m=td.querySelector('.time-main');
        const r=document.createRange();r.selectNodeContents(k);const kr=r.getBoundingClientRect();r.selectNodeContents(m);const mr=r.getBoundingClientRect();
        return [c.right-parseFloat(cs.paddingRight)-kr.right, mr.left-(c.left+parseFloat(cs.paddingLeft))]})""")
      assert all(abs(a)<=1.5 and abs(m)<=1.5 for a,m in geo),geo
      fit=p.locator('#report-sheet').evaluate('n=>[n.clientWidth,n.scrollWidth]');assert fit[1]<=fit[0]+1,fit
      p.locator('#report-sheet table').screenshot(path=str(OUT/f'bericht-spielstand-{size[0]}.png'))
      # penalties: line 1 number + name, line 2 duration · penalty (report and print)
      row=p.locator('#report-sheet tbody tr.penalty').first
      assert row.locator('.pen-who').inner_text()=='#4 Gast, Gina' and row.locator('.pen-what').inner_text()=='2 Min. · Haken',row.inner_text()
      y1,y2=[row.locator(c).evaluate('n=>n.getBoundingClientRect().top') for c in ('.pen-who','.pen-what')];assert y2>y1+5
      text=p.evaluate('window.EgrepUI.reportText()')
      for needle in ['| Tor 1:0 |','| Tor 1:1 |','| Penalty 2:1 |','| Tor 3:1 |']:assert needle in text,(needle,text)
      assert '| Strafe |' in text and '| Penalty |' in text,text
      p.evaluate('window.EgrepUI.preparePrintReport()');p.emulate_media(media='print')
      kinds=[x.text_content() for x in p.locator('#print-output .print-kind').all()]
      assert [k for k in kinds if any(c.isdigit() for c in k)]==['Tor 1:0','Tor 1:1','Penalty 2:1','Tor 3:1'],kinds
      pr=p.locator('#print-output tr.penalty td').nth(2);lines=[l.strip() for l in pr.inner_text().split('\n') if l.strip()]
      assert lines==['Strafe #4 Gast, Gina','2 Min. · Haken'],lines
      geo=p.evaluate("""[...document.querySelectorAll('#print-output .print-time')].map(td=>{const c=td.getBoundingClientRect(),cs=getComputedStyle(td),k=td.querySelector('.print-clock').getBoundingClientRect();return c.right-parseFloat(cs.paddingRight)-k.right})""")
      assert all(abs(x)<=1.5 for x in geo),geo
      assert geo and any(abs(x)>0 for x in [p.evaluate("document.querySelector('#print-output .print-time').getBoundingClientRect().width")]),'print visible'
      if size==(412,915):p.locator('#print-output').screenshot(path=str(OUT/'druck-spielstand.png'))
      p.emulate_media(media='screen')
      p.close()
    assert not errors,errors;b.close()
  print('V33 UI PASS: penalties in two lines (number+name / duration · penalty) in report and print; score after each goal in report/text/print in game-time order (input order irrelevant), scored penalty shot counts, missed one/penalty/timeout without score; read clock right-aligned (report and print), game time left; 320/412 px without overflow.')
if __name__=='__main__':main()
