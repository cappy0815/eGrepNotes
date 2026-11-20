"""Builds a line-up PDF in the layout of the official EHV NRW "Offizielle Mannschaftsaufstellung"
(fantasy names only) with Chromium: one PDF with a text layer, one image-only ("scanned") PDF.
Not the real eGrep PDF - only the layout seen on Michas screenshots."""
import sys,io,json
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=True)
SUR=['Adler','Becker','Conrad','Dorn','Eberle','Falk','Gruber','Hahn','Iser','Jansen','Krause','Lorenz','Maurer','Neumann','Ott','Pohl','Quast','Roth','Seidel','Thiel','Ullrich','Vogel','Weber','Xander','Yilmaz','Zeller','Arnold','Brandt']
FIRST=['Tim','Lena','Max','Mia','Ben','Ole','Ida','Paul','Emma','Jan','Noah','Lea','Finn','Ella','Tom','Nina','Luca','Mila','Jonas','Lina','Elias','Pia','Leon','Anna','Theo','Sara','Felix','Clara']
def team(n,offset,goalies,defs):
    rows=[];nums=sorted({(i*37+offset*5)%98+1 for i in range(n*4)})[:n]
    for i in range(n):
        pos='G' if i<goalies else ('D' if i<goalies+defs else 'F')
        rows.append([pos,str(nums[i]),SUR[(i+offset)%len(SUR)].upper()+', '+FIRST[(i*3+offset)%len(FIRST)],str(126000+i*37+offset),'%02d.%02d.2013'%(i%28+1,i%12+1),'X' if i==0 else ''])
    return rows
home=team(22,3,3,7);away=team(26,11,4,7)
def table(name,rows):
    body='';last=None
    for r in rows:
        if last and r[0]!=last:body+='<tr class="gap"><td></td><td></td><td></td><td></td><td></td><td></td></tr>'
        last=r[0];body+='<tr>'+''.join(f'<td>{c}</td>' for c in r)+'</tr>'
    return f'<div class="t"><div class="th">{name}</div><div class="cnt">{len(rows)} Spieler</div><table><tr class="h"><td>Pos.</td><td>Nr.</td><td>Name</td><td>Lizenz</td><td>Geburtsdatum</td><td>Start</td></tr>{body}</table></div>'
html=f'''<!doctype html><meta charset="utf-8"><style>body{{font-family:Verdana,Arial;font-size:11px;margin:18px}}h1{{font-style:italic;font-size:18px;margin:0 0 6px}}
.top td{{border:1px solid #999;padding:2px 6px;vertical-align:top}}.top small{{display:block;color:#333}}.wrap{{display:flex;gap:0;margin-top:14px;border:1px solid #999}}.t{{flex:1;border-right:1px solid #999}}
.th{{font-weight:bold;padding:6px;border-bottom:1px solid #999}}.cnt{{padding:6px;border-bottom:1px solid #999}}table{{border-collapse:collapse;width:100%}}td{{border-bottom:1px solid #ddd;padding:3px 4px;white-space:nowrap}}tr.gap td{{height:14px}}tr.h td{{font-weight:normal}}
.foot{{margin-top:16px;display:flex;justify-content:space-around;font-weight:bold}}</style>
<h1>Offizielle Mannschaftsaufstellung</h1><table class="top" style="width:auto"><tr><td><small>Spiel</small><b>U15_LL_099</b></td><td><small>Bewerb</small><b>NRW - U15 Landesliga</b></td><td><small>Heim</small><b>Phantasie EV Nord</b></td><td><small>Gast</small><b>EC Musterstadt</b></td></tr>
<tr><td><small>Datum</small><b>21.11.2026</b></td><td><small>Start</small><b>18:00</b></td><td colspan="2"><small>Spielort</small><b>Musterhalle</b></td></tr></table>
<div class="wrap">{table("Phantasie EV Nord",home)}{table("EC Musterstadt",away)}</div><div class="foot"><span>Punktrichter</span><span>Zeitnehmer</span><span>Strafbankbetreuer</span></div>'''
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path='/opt/pw-browsers/chromium',args=['--no-sandbox']);p=b.new_page(viewport={'width':1100,'height':1400})
    p.set_content(html);p.pdf(path=str(OUT/'aufstellung-text.pdf'),format='A4',print_background=True,margin={'top':'8mm','bottom':'8mm','left':'8mm','right':'8mm'},scale=.78)
    p.screenshot(path=str(OUT/'aufstellung.png'),full_page=True);b.close()
from PIL import Image
Image.open(OUT/'aufstellung.png').convert('RGB').save(OUT/'aufstellung-scan.pdf','PDF',resolution=130)
json.dump({'home':[[r[1],r[2].split(',')[0].title(),'G' if r[0]=='G' else ''] for r in home],'away':[[r[1],r[2].split(',')[0].title(),'G' if r[0]=='G' else ''] for r in away],'teams':['Phantasie EV Nord','EC Musterstadt'],'game':'U15_LL_099'},open(OUT/'truth.json','w'),ensure_ascii=False)
print('PDF-Testdaten:',len(home),'+',len(away),'Spieler')
