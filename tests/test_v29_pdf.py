"""2.9: line-up from PDF (text layer -> direct; image-only -> render + OCR) in the real app page loaded from
its asset folder (pdf.js is loaded lazily like on the phone). Fixture: make_pdf_fixture.py (fantasy names,
layout of the official sheet). Not tested with a real eGrep PDF."""
import json,os,sys,subprocess,unicodedata,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent.parent;ASSETS=ROOT/'app/src/main/assets'
FIX=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-pdf');FIX.mkdir(parents=True,exist_ok=True)
CHROMIUM=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None))
subprocess.run([sys.executable,str(Path(__file__).parent/'make_pdf_fixture.py'),str(FIX)],check=True,capture_output=True)
T=json.load(open(FIX/'truth.json'));norm=lambda v:''.join(c for c in unicodedata.normalize('NFD',v.lower()) if c.isalpha())
def score(st,side):
    got=st[side]['players'];ok=sum(any(p['number']==n and norm(p['name'].split(',')[0])==norm(s) for p in got) for n,s,_ in T[side])
    gl=sum(any(p['number']==n and p['isGoalie'] for p in got) for n,_,g in T[side] if g);wrong=[p['number'] for p in got if p['isGoalie'] and p['number'] not in {n for n,_,g in T[side] if g}]
    return ok,gl,wrong
def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox','--allow-file-access-from-files'])
    results={}
    for name,need in [('aufstellung-text.pdf',1.0),('aufstellung-scan.pdf',.75)]:
      p=b.new_page(viewport={'width':360,'height':740});errs=[];p.on('pageerror',lambda e:errs.append(str(e)))
      p.goto((ASSETS/'index.html').as_uri());p.wait_for_function('typeof EgrepUI!=="undefined"')
      p.evaluate("()=>{try{localStorage.clear()}catch(e){}}");p.reload();p.wait_for_function('typeof EgrepUI!=="undefined"')
      assert p.evaluate('typeof pdfjsLib')=='undefined','pdf.js must not load at start'
      t0=time.time();p.locator('#photo-input').set_input_files(str(FIX/name))
      p.wait_for_function("/Spieler erkannt|keine Spieler|Fehler|nicht/i.test(document.getElementById('ocr-message').textContent)",timeout=240000)
      dt=time.time()-t0;st=json.loads(p.evaluate("localStorage.getItem('nev-spielnotiz-v0.1')"))
      assert p.locator('#pdf-name').is_visible() and name in p.locator('#pdf-name').inner_text() and not p.locator('#photo-preview').is_visible()
      h,a=score(st,'home'),score(st,'away');total=(h[0]+a[0])/(len(T['home'])+len(T['away']))
      results[name]=dict(home=f"{h[0]}/{len(T['home'])}",away=f"{a[0]}/{len(T['away'])}",goalies=f"{h[1]+a[1]}/7",wrong_goalies=h[2]+a[2],teams=[st['home']['name'],st['away']['name']],game=st['meta']['number'],seconds=round(dt,1))
      print(name,results[name])
      assert total>=need,(name,total);assert not (h[2]+a[2]),('wrong goalies',name)
      if name.endswith('text.pdf'):
        assert [st['home']['name'],st['away']['name']]==T['teams'] and st['meta']['number']==T['game'],results[name]
        assert h[1]+a[1]==7
      assert not errs,errs;p.close()
    b.close()
  print('V29 PDF PASS:',json.dumps(results,ensure_ascii=False))
if __name__=='__main__':main()
