"""Actual shipped HTML/CSS print-fit regression. Does not claim an Android printer test."""
from pathlib import Path
import json,re,sys
import fitz
from playwright.sync_api import sync_playwright
from uihelper import boot,state
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/egrep_v14_tests/print')
OUT.mkdir(parents=True,exist_ok=True)
KEY='nev-spielnotiz-v0.1'

def fixture(count,long=False):
 home=[{'id':'h56','number':'56','name':'Alex Beispiel-Muster','isGoalie':False}, {'id':'h18','number':'18','name':'Sam Beispiel','isGoalie':False}]
 away=[{'id':'a56','number':'56','name':'Kim Muster-Beispiel','isGoalie':False},{'id':'a18','number':'18','name':'Robin Muster','isGoalie':False}]
 if long:
  home[0]['name']='Alexandria Beispiel-Mustermann mit einem besonders langen Doppelnamen'
  away[0]['name']='Kim Maximilian Muster-Beispiel mit einem besonders langen Doppelnamen'
 events=[]
 for i in range(count):
  elapsed=int(i*3599/max(1,count-1));period=min(3,elapsed//1200+1);remaining=1200-(elapsed-(period-1)*1200)
  m,sec=divmod(remaining,60);clock=str(m).zfill(2)+str(sec).zfill(2)
  events.append({'id':'e'+str(i),'order':i+1,'team':'away' if i%2 else 'home','type':'penalty' if i%3 else 'goal', 'period':period,'time':f'{m}:{sec:02d}','clock':clock,'player':'56','assist1':'' if i%3 else '18','assist2':'', 'penalty':f'E{i:03d} '+('Ein langer Freitext mit genauer Beschreibung der angesagten Strafe, ohne ausgelassene Inhalte, damit die Verdichtung auch Umbrueche beruecksichtigt.' if long else 'Check gegen Kopf / Nacken'),'penaltyDuration':['2','5','game'][(i//3)%3]})
 s={'version':6,'currentPeriod':3,'meta':{'date':'2026-10-08','number':'DRUCKTEST_'+str(count),'operatorName':'Max Mustermann','operatorPrompted':True},'home':{'name':'Neusser EV','players':home},'away':{'name':'Gastmannschaft Muster','players':away},'events':events}
 return s

def inspect(path,s,one=True):
 d=fitz.open(path);text=' '.join(''.join(pg.get_text() for pg in d).split())
 assert len(d)==1 if one else len(d)>1,(path,len(d))
 assert 'Spielbericht erstellt von: Max Mustermann' in text
 assert f"{len(s['events'])} Ereignisse" in text
 assert '2 Min.' in text or len(s['events'])==0 or all(e['type']!='penalty' or e['penaltyDuration']!='2' for e in s['events'])
 for side in ['home','away']:
  name=s[side]['players'][0]['name'];expect=sum(e['team']==side for e in s['events'])
  assert text.count(name)==expect,(path,name,expect,text.count(name))
 for i,e in enumerate(s['events']):
  if e['type']=='penalty':assert f'E{i:03d}' in text,(path,i)
 for i,pg in enumerate(d):
  for w in pg.get_text('words'):
   assert w[0]>=30 and w[2]<=pg.rect.width-30 and w[1]>=30 and w[3]<=pg.rect.height-30,(path,i,w)
 if one:d[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(str(path.with_suffix('.png')))
 return len(d)

with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=__import__('os').environ.get('CHROMIUM','/usr/bin/chromium'),headless=True,args=['--no-sandbox']);results=[]
 for count,long in [(0,False),(12,False),(30,False),(60,False),(120,False),(45,True)]:
  print('START',count,long,flush=True)
  s=fixture(count,long);p=b.new_page(viewport={'width':360,'height':640});boot(p,{KEY:json.dumps(s)})
  p.get_by_role('button',name='Bericht',exact=True).click();r=p.evaluate('EgrepUI.preparePrintReport()')
  assert r['fits'] and r['onePage'] and r['eventCount']==count,r
  assert p.locator('#print-output tbody tr[data-print-event]').count()==count
  path=OUT/f'print-{count}{"-long" if long else ""}.pdf'
  print('FIT',r,flush=True)
  p.pdf(path=str(path),prefer_css_page_size=True,print_background=True)
  print('PDF',path.name,flush=True)
  pages=inspect(path,s);results.append({'fixture':path.name,'pages':pages,**r})
  if count==60 and not long:
   # Option is explicit and functional, not a hidden loss of event data.
   p.locator('#print-single-page').uncheck();p.pdf(path=str(OUT/'print-readable.pdf'),prefer_css_page_size=True,print_background=True)
   assert inspect(OUT/'print-readable.pdf',s,one=False)>1
   p.locator('#print-single-page').check()
  if count==120:
   # A strong reduction is explained before handing over to system printing.
   p.evaluate('window.print=()=>{window._printed=true}')
   p.locator('#print-report').click();assert p.locator('#choice-dialog').is_visible()
   p.locator('#choice-confirm').click();p.wait_for_timeout(300);assert p.evaluate('!!window._printed')
  assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
  p.close()
 b.close()
(OUT/'results.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2));print('PASS one A4 page, all events/names retained, 0/12/30/60/120 + long text, page bounds, readable multipage option and small-print warning.')
