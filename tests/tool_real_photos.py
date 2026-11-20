"""Run the app's real OCR pipeline (ocr.js + embedded model) on real photos; dump result + TSVs.
Usage: python tests/tool_real_photos.py PROJECT_DIR OUTDIR photo1.jpg [photo2.jpg ...]
Optional scoring against a hand-made truth file: set TRUTH=truth.json
  {"home":[["2","Sommer","G"],...],"away":[...]}   (number, surname, "G" for goalie)
Photos and truth files contain personal data of players and are NOT part of the project.
"""
import sys,json,base64,os,importlib.util
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(sys.argv[1]);ASSETS=ROOT/'app/src/main/assets';OUT=Path(sys.argv[2]);OUT.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('build_apk',ROOT/'build_apk.py');build=importlib.util.module_from_spec(spec);sys.modules['build_apk']=build;spec.loader.exec_module(build)
ocr=build.build_embedded_ocr_data().decode()
src=(ASSETS/'ocr.js').read_text()
src=src.replace("const parsed=parseRosterFromTsv(result.data.tsv||'');","window._tsv=[result.data.tsv];const parsed=parseRosterFromTsv(result.data.tsv||'');")
src=src.replace("let parsed=parseRosterFromTsv(result.data.tsv||'');","window._tsv=[result.data.tsv];let parsed=parseRosterFromTsv(result.data.tsv||'');")
src=src.replace("const prepared=await prepareImage(file);","const prepared=await prepareImage(file);window._prep=prepared.toDataURL('image/png');")
src=src.replace("const prepared=await prepareImage(file,fullPage);","const prepared=await prepareImage(file,fullPage);window._prep=prepared.toDataURL('image/png');")
src=src.replace("meta=parseRosterFromTsv(metadata.data.tsv||'');","window._tsv.push(metadata.data.tsv);meta=parseRosterFromTsv(metadata.data.tsv||'');")
with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None)),headless=True,args=['--no-sandbox'])
  for img in sys.argv[3:]:
    p=b.new_page();p.set_content('<!doctype html><meta charset="utf-8"><body></body>')
    for c in [(ASSETS/'logic.js').read_text(),ocr,(ASSETS/'tesseract.min.js').read_text(),src]:p.add_script_tag(content=c)
    if os.environ.get('FULLPAGE'):p.evaluate('window.FULLPAGE=true')
    data=base64.b64encode(Path(img).read_bytes()).decode()
    res=p.evaluate('''d=>{const raw=atob(d),u=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)u[i]=raw.charCodeAt(i);return (window.FULLPAGE?EgrepOCR.startImage(new Blob([u],{type:'image/png'}),()=>{},{fullPage:true}):EgrepOCR.start(new Blob([u],{type:'image/jpeg'}),()=>{})).promise}''',data)
    tsv=p.evaluate('window._tsv');name=Path(img).stem
    prep=p.evaluate('window._prep');(OUT/f'{name}-prep.png').write_bytes(base64.b64decode(prep.split(',')[1]))
    (OUT/f'{name}-result.json').write_text(json.dumps(res,ensure_ascii=False,indent=1))
    (OUT/f'{name}_strip.json').write_text(json.dumps(p.evaluate('window._strip||[]'),ensure_ascii=False))
    for i,t in enumerate(tsv):(OUT/f'{name}-tsv{i}.txt').write_text(t)
    print('==',name,res['teamNames'],res['gameNumber'])
    for side in ['home','away']:print(' ',side,len(res[side]),[(x['number'],x['name'],'G' if x['isGoalie'] else '','S' if x['starter'] else '') for x in res[side]])
    p.close()
  b.close()

if os.environ.get('TRUTH'):
  import unicodedata
  T=json.load(open(os.environ['TRUTH']));norm=lambda v:''.join(c for c in unicodedata.normalize('NFD',v.lower()) if c.isalpha())
  for img in sys.argv[3:]:
    res=json.loads((OUT/f'{Path(img).stem}-result.json').read_text())
    for side in ['home','away']:
      ok=sum(any(p['number']==n and norm(p['name'].split(',')[0])==norm(sur) for p in res[side]) for n,sur,_ in T[side])
      g=sum(any(p['number']==n and p['isGoalie'] for p in res[side]) for n,_,gl in T[side] if gl)
      print(Path(img).name,side,f'{ok}/{len(T[side])} richtig, Torwarte {g}')
