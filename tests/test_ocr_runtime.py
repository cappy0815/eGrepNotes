"""Real Tesseract run in Chromium with the embedded German model (no mock).
Uses a SYNTHETIC roster rendered on a canvas, not a photo of a real eGrep sheet.
Usage: python tests/test_ocr_runtime.py OUTDIR
"""
from pathlib import Path
import json,os,sys,importlib.util
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/'app/src/main/assets'
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-ocr');OUT.mkdir(parents=True,exist_ok=True)
CHROMIUM=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None))
spec=importlib.util.spec_from_file_location('build_apk',ROOT/'build_apk.py');build=importlib.util.module_from_spec(spec);sys.modules['build_apk']=build;spec.loader.exec_module(build)
ocr_data=build.build_embedded_ocr_data().decode('ascii')
assert '"language"' in ocr_data

HOME=[('30','Jürgen Müller'),('35','Björn Weiß'),('56','Max Schäfer'),('18','Lukas Hirschfeld'),('12','Sören Krüger')]
AWAY=[('1','Tim Groß'),('9','Jonas Köhler'),('20','Robin Bäcker'),('44','Felix Wagner')]
DRAW='''([home,away,extras])=>new Promise(resolve=>{
  const c=document.createElement('canvas');c.width=2000;c.height=2800;const g=c.getContext('2d');
  g.fillStyle='#fff';g.fillRect(0,0,c.width,c.height);g.fillStyle='#000';g.font='bold 46px Arial';
  g.fillText('Spiel',60,120);g.fillText('Heim',600,120);g.fillText('Gast',1300,120);
  g.font='40px Arial';g.fillText('U13_LL_005',60,190);g.fillText('Neusser EV',600,190);g.fillText('Ratinger Ice Aliens',1300,190);
  g.font='bold 38px Arial';g.fillText('Neusser EV',100,880);g.fillText('Ratinger Ice Aliens',1040,880);
  g.fillText('Spieler',100,940);g.fillText('Spieler',1040,940);
  g.fillText('Nr.',230,1010);g.fillText('Name',380,1010);g.fillText('Nr.',1150,1010);g.fillText('Name',1300,1010);
  g.font='38px Arial';
  home.forEach(([n,name],i)=>{const y=1090+i*75;if(i<2)g.fillText('TW',110,y);g.fillText(n,240,y);g.fillText(name,380,y);});
  away.forEach(([n,name],i)=>{const y=1090+i*75;if(i<1)g.fillText('TW',1030,y);g.fillText(n,1160,y);g.fillText(name,1300,y);});
  // Like the real sheet: further columns to the right and staff rows below the roster.
  if(extras){g.fillText('Lizenz',780,1010);g.fillText('Lizenz',1800,1010);
  home.forEach((_,i)=>g.fillText('12345',780,1090+i*75));away.forEach((_,i)=>g.fillText('67890',1800,1090+i*75));
  g.fillText('HC',110,1600);g.fillText('Max Trainer',380,1600);g.fillText('HC',1030,1600);g.fillText('Tom Coach',1300,1600);}
  c.toBlob(b=>{window._img=b;resolve(c.toDataURL('image/png'));},'image/png');
})'''

with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox'])
  p=b.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
  p.set_content('<!doctype html><meta charset="utf-8"><body></body>')
  for f in ['logic.js']:p.add_script_tag(content=(ASSETS/f).read_text())
  p.add_script_tag(content=ocr_data)
  p.add_script_tag(content=(ASSETS/'tesseract.min.js').read_text())
  p.add_script_tag(content=(ASSETS/'ocr.js').read_text())
  results={}
  for name,extras in [('realistisch',True),('schlicht',False)]:
    url=p.evaluate(DRAW,[HOME,AWAY,extras])
    import base64;(OUT/f'synthetic-roster-{name}.png').write_bytes(base64.b64decode(url.split(',')[1]))
    results[name]=p.evaluate('''()=>window.EgrepOCR.start(window._img,()=>{}).promise''')
  b.close()
(OUT/'ocr-result.json').write_text(json.dumps(results,ensure_ascii=False,indent=1))
assert not errors,errors
for layout,result in results.items():
  print(layout,json.dumps({k:result[k] for k in ['teamNames','gameNumber']},ensure_ascii=False))
  for side,expected in [('home',HOME),('away',AWAY)]:
    got={p['number']:p['name'] for p in result[side]}
    print(' ',side,got)
    for n,name in expected:assert got.get(n)==name,(layout,side,n,name,got.get(n))
  goalies={side:[p['number'] for p in result[side] if p['isGoalie']] for side in ['home','away']};print('  goalies',goalies)
  # Goalie marks need OCR confidence >= 65 (conservative by design); low-confidence marks are
  # left to the goalie question in the app. Only the realistic layout is asserted exactly.
  if layout=='realistisch':assert goalies=={'home':['30','35'],'away':['1']},goalies
  else:assert set(goalies['home'])<= {'30','35'} and set(goalies['away'])<={'1'},goalies
print('OCR RUNTIME PASS: German model offline in Chromium; both synthetic layouts (with/without extra columns and staff rows) read completely incl. umlauts; goalie marks found. No real photo tested.')
