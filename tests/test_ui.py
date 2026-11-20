"""UI tests use actual shipped JS/CSS with Chromium; Android host is tested separately.
The in-memory storage adapter is intentional for environments blocking file/http navigation.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import base64, json, re, sys
ROOT=Path(__file__).resolve().parents[1]/'app/src/main/assets'
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/egrep_tests')
OUT.mkdir(exist_ok=True,parents=True)
LOGO='data:image/png;base64,'+base64.b64encode((ROOT/'nev-logo.png').read_bytes()).decode()

def boot(page,saved=None,ocr_mock=False,operator_prompt=False,auto_ok=True):
    html=re.sub(r'<script[^>]*src="([^"]+)"[^>]*></script>','',(ROOT/'index.html').read_text())
    html=html.replace('<link rel="stylesheet" href="styles.css">','').replace('src="nev-logo.png"','src="'+LOGO+'"')
    page.set_content(html)
    page.evaluate('''saved=>{window._saved=saved||{};Object.defineProperty(window,'localStorage',{value:{getItem:k=>window._saved[k]||null,setItem:(k,v)=>window._saved[k]=String(v),removeItem:k=>delete window._saved[k]}});window.fetch=()=>Promise.reject(new Error('kein Netz im Test'))}''',saved)
    page.add_style_tag(content=(ROOT/'styles.css').read_text())
    for file in ['logic.js','signs.js','teamlogos.js','clubs.js','roster.js','ocr.js','app.js']:page.add_script_tag(content=(ROOT/file).read_text())
    page.wait_for_timeout(190)
    if not operator_prompt:skip_operator(page)
    # 1.6: every save shows a summary first. Older flows acknowledge it with OK automatically.
    if auto_ok:page.add_locator_handler(page.locator('#detail-dialog[open][data-mode="new"], #detail-dialog[open][data-mode="saved"]'),lambda:page.locator('#detail-ok').click())

def skip_operator(page):
    if page.locator('#operator-dialog').is_visible():page.locator('#operator-later').click()

def state(page):return page.evaluate('window.EgrepUI.getState()')
def digits(page,n):
    # 1.9: with a known roster the number grid comes first; keypad tests go via "Andere Nummer".
    if page.locator('[data-action="other-number"]').is_visible():page.locator('[data-action="other-number"]').click()
    for x in str(n):page.locator('[data-digit="'+x+'"]').click()
def next_(page):page.locator('[data-action="next"]').click()
def begin(page,clock,team='home',kind='goal',period=1):
    page.get_by_role('button',name='Spiel',exact=True).click();skip_operator(page)
    page.locator('[data-current-period="'+str(period)+'"]').click();page.locator('#new-event').click()
    assert page.locator('.event-period-selector').count()==0
    assert str(period)+'. Drittel' in page.locator('#wizard-title').inner_text()
    digits(page,clock);next_(page)
    if page.locator('#time-jump-dialog').is_visible():page.locator('#time-jump-retro').click()
    # 1.5 order: time -> type -> team.
    page.locator('[data-type="'+kind+'"]').click();page.locator('[data-team="'+team+'"]').click()
def no_assists(page,number):
    digits(page,number);next_(page);page.locator('[data-action="skip-assists"]').click()
def select_setup(page):page.get_by_role('button',name='Aufstellung',exact=True).click()
def add_player(page,side,number,name):
    page.locator('#new-number-'+side).fill(number);page.locator('#new-name-'+side).fill(name);page.locator('[data-action="add-player"][data-side="'+side+'"]').click()
def edit_goalie(page,side,index,starter=False):
    page.locator('[data-action="edit-player"][data-side="'+side+'"]').nth(index).click()
    page.locator('#player-goalie').check()
    if starter:page.locator('#player-starter').check()
    page.locator('#player-form button[type="submit"]').click()
def confirm(page):page.locator('#choice-confirm').click()
def cancel_choice(page):page.locator('#choice-cancel').click()
def cancel_draft(page):
    page.locator('#wizard-close').click();confirm(page)
def assert_fit(page):
    box=page.locator('#wizard').bounding_box()
    assert box['y']>=-1 and box['y']+box['height']<=page.viewport_size['height']+1,box
    size=page.locator('#wizard-content').evaluate('(n)=>[n.clientHeight,n.scrollHeight,n.clientWidth,n.scrollWidth]')
    assert size[1]<=size[0]+1 and size[3]<=size[2]+1,size

def main():
  with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=__import__('os').environ.get('CHROMIUM',next((p for p in ['/usr/bin/chromium','/opt/pw-browsers/chromium'] if __import__('os').path.exists(p)),None)),args=['--no-sandbox'],headless=True)
    page=browser.new_page(viewport={'width':360,'height':640});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));boot(page)
    select_setup(page)
    add_player(page,'home','30','Alex Beispiel');add_player(page,'home','35','Kim Muster')
    edit_goalie(page,'home',0,True);edit_goalie(page,'home',1)
    add_player(page,'home','56','Max Beispiel');add_player(page,'home','18','Luca Muster');add_player(page,'home','12','Sam Beispiel')
    assert len(state(page)['home']['players'])==5
    add_player(page,'home','56','Duplicate');expect(page.locator('#choice-dialog')).to_be_visible();confirm(page);assert len(state(page)['home']['players'])==5
    page.locator('[data-team-name="away"]').fill('Ratinger Ice Aliens');page.locator('[data-team-name="away"]').press('Tab')
    page.locator('#game-number').fill('TEST_U13_005');page.locator('#game-number').press('Tab')
    # Goal with two named assists.
    begin(page,'1012');assert_fit(page);digits(page,'56');next_(page);digits(page,'18');next_(page);digits(page,'12');next_(page)
    assert len(state(page)['events'])==1 and state(page)['events'][0]['assist2']=='12'
    assert page.locator('#event-list').inner_text().find('1012')>=0
    # No away list: no false warning.
    begin(page,'905','away');no_assists(page,'20');expect(page.locator('#wizard')).not_to_be_visible();assert len(state(page)['events'])==2
    assert page.locator('#score-away').inner_text()=='1'
    # Earlier event: warning and chronological placement.
    begin(page,'1010','away','penalty');digits(page,'48');next_(page);page.locator('[data-penalty]').first.click()
    expect(page.locator('#choice-dialog')).not_to_be_visible()  # Time already reviewed before team choice.
    assert len(state(page)['events'])==3
    assert page.locator('.event-clock').all_text_contents()==['1010','905','1012']  # 1.5: last entered on top
    # Unknown home player warning, cancel then correct in draft.
    begin(page,'850');no_assists(page,'99');assert 'Nummer' in page.locator('#choice-title').inner_text();cancel_choice(page)
    assert len(state(page)['events'])==3;cancel_draft(page)
    # Starting goalie and unique substitute offered; subsequent switch reverses them.
    begin(page,'800','home','goalie');assert_fit(page)
    assert page.locator('[data-goalie-field="goalieOut"] strong').inner_text()=='#30'
    assert page.locator('[data-goalie-field="goalieIn"] strong').inner_text()=='#35'
    page.screenshot(path=str(OUT/'goalie.png'));next_(page)
    begin(page,'700','home','goalie');assert page.locator('[data-goalie-field="goalieOut"] strong').inner_text()=='#35';next_(page)
    assert state(page)['events'][-1]['goalieIn']=='30';assert page.locator('#score-home').inner_text()=='1'
    # Sonstige, custom input.
    begin(page,'600','away','penalty');digits(page,'9');next_(page);page.locator('[data-action="custom-penalty"]').click()
    page.locator('#custom-penalty').fill('Besondere Ansage');page.locator('[data-action="save-custom"]').click();assert state(page)['events'][-1]['penalty']=='Besondere Ansage'
    # Team/bench penalty avoids invented jersey number.
    begin(page,'500','home','penalty');page.locator('[data-action="bench-penalty"]').click();page.locator('[data-penalty]').first.click();page.locator('[data-action="served-later"]').click();assert state(page)['events'][-1]['bench']
    # Invalid duplicated participant is prevented.
    begin(page,'400');digits(page,'56');next_(page);digits(page,'56');next_(page);page.locator('[data-action="skip-assists"]').click();assert 'unterschiedliche' in page.locator('#wizard-error').inner_text();cancel_draft(page)
    # Edit, delete, undo using actual UI.
    before=len(state(page)['events']);page.locator('[data-action="show-event"]').last.click();page.locator('#detail-edit').click();page.locator('[data-action="delete-event"]').click();confirm(page);assert len(state(page)['events'])==before-1
    page.locator('#undo').click();assert len(state(page)['events'])==before
    # Power: native callback and session manual override.
    page.evaluate('window.egrepPower(true)');assert page.locator('#keep-screen').is_checked()
    page.locator('#keep-screen').uncheck();page.evaluate('window.egrepPower(true)');assert not page.locator('#keep-screen').is_checked()
    page.locator('#screen-auto').click();assert page.locator('#keep-screen').is_checked()
    page.evaluate('window.egrepPower(false)');assert not page.locator('#keep-screen').is_checked()
    # Render logo after dynamic report rendering, then output real HTML print PDF.
    page.get_by_role('button',name='Bericht',exact=True).click()
    page.evaluate('uri=>document.querySelectorAll(\'img[src="nev-logo.png"]\').forEach(n=>n.src=uri)',LOGO)
    assert 'Alex Beispiel' in page.evaluate('window.EgrepUI.reportText()')
    page.screenshot(path=str(OUT/'report-screen.png'),full_page=True)
    page.pdf(path=str(OUT/'eGrep-Notes-Druckmuster.pdf'),format='A4',prefer_css_page_size=True,print_background=True)
    saved=page.evaluate('window._saved');(OUT/'sample-state.json').write_text(json.dumps(saved,ensure_ascii=False))
    # Verify restart reconstruction with the exact JSON that was persisted.
    restored=browser.new_page(viewport={'width':360,'height':640});boot(restored,saved);assert len(state(restored)['events'])==before
    # Two confirmations; cancellation is non-destructive, photo removed on final reset.
    page.evaluate('''()=>{window.EgrepOCR.start=()=>({promise:new Promise(()=>{}),cancel:()=>{window._wasCanceled=true}})}''')
    select_setup(page);page.locator('#photo-input').set_input_files(str(ROOT/'nev-logo.png'));expect(page.locator('#ocr-panel')).to_be_visible()
    page.get_by_role('button',name='Bericht',exact=True).click();page.locator('#reset-game').click();cancel_choice(page);assert len(state(page)['events'])==before
    page.locator('#reset-game').click();confirm(page);  # 2.0: one step + archive
    assert state(page)['events']==[];assert state(page)['currentPeriod'] is None;assert page.evaluate('window._wasCanceled')
    expect(page.locator('#ocr-panel')).not_to_be_visible();assert page.locator('#photo-preview').get_attribute('src') is None
    # Missing metadata popup is tested against mocked OCR output, not claimed as image-recognition test.
    page.evaluate('''()=>{window.EgrepOCR.start=()=>({promise:Promise.resolve({home:[],away:[],teamNames:[],gameNumber:''}),cancel:()=>{}})}''')
    page.locator('#photo-input').set_input_files(str(ROOT/'nev-logo.png'));expect(page.locator('#metadata-dialog')).to_be_visible()
    page.locator('#metadata-away').fill('Gast Beispiel');page.locator('#metadata-number').fill('TEST_002');page.locator('#metadata-form button[type="submit"]').click()
    assert state(page)['away']['name']=='Gast Beispiel' and state(page)['meta']['number']=='TEST_002'
    # Responsive wizard checks for every interactive numeric stage.
    for size in [(320,480),(320,568),(360,640),(390,844)]:
      pg=browser.new_page(viewport={'width':size[0],'height':size[1]});boot(pg,saved)
      pg.get_by_role('button',name='Spiel',exact=True).click();skip_operator(pg);pg.locator('#new-event').click();assert_fit(pg)
      digits(pg,'1000');pg.locator('[data-action="toggle-period"]').click();pg.locator('[data-period="2"]').click();next_(pg);assert_fit(pg)
      pg.locator('[data-type="goal"]').click();assert_fit(pg);pg.locator('[data-team="home"]').click();assert_fit(pg)
      digits(pg,'56');next_(pg);assert_fit(pg);digits(pg,'18');next_(pg);assert_fit(pg)
      pg.close()
    assert errors==[],errors
    print('UI PASS: roster, goal/assist, unknowns, penalties, chronology, goalie sequence, edit/delete/undo, power callbacks, print, reset, OCR fallback, four viewport sizes. Real Android not tested.')
    browser.close()
if __name__=='__main__': main()
