"""Shared helpers for the UI tests (3.0). The real shipped HTML/CSS/JS run in Chromium; localStorage is
replaced by an in-memory adapter (window._saved). OCR runtime data is not loaded (OCR is tested separately)."""
from pathlib import Path
import base64,os,re
ROOT=Path(__file__).resolve().parents[1]/'app/src/main/assets'
CHROMIUM=os.environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if os.path.exists(p)),None))
LOGO='data:image/png;base64,'+base64.b64encode((ROOT/'nev-logo.png').read_bytes()).decode()
SCRIPTS=['logic.js','signs.js','teamlogos.js','clubs.js','ocr.js','app.js']
def boot(page,saved=None,operator_prompt=False):
    html=re.sub(r'<script[^>]*src="([^"]+)"[^>]*></script>','',(ROOT/'index.html').read_text())
    html=html.replace('<link rel="stylesheet" href="styles.css">','').replace('src="nev-logo.png"','src="'+LOGO+'"')
    page.set_content(html)
    page.evaluate('''saved=>{window._saved=saved||{};Object.defineProperty(window,'localStorage',{value:{getItem:k=>window._saved[k]??null,setItem:(k,v)=>window._saved[k]=String(v),removeItem:k=>delete window._saved[k]}})}''',saved)
    page.add_style_tag(content=(ROOT/'styles.css').read_text())
    for f in SCRIPTS:page.add_script_tag(content=(ROOT/f).read_text())
    page.wait_for_timeout(200)
    if not operator_prompt:skip_operator(page)
def skip_operator(page):
    if page.locator('#operator-dialog').is_visible():page.locator('#operator-later').click()
def state(page):return page.evaluate('window.EgrepUI.getState()')
