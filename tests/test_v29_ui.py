"""2.9 UI: "Wer sitzt die Strafe ab?" for goalie and bench penalties, label "Bank / Trainer",
app shortcut entry (#signs / window.egrepOpenSigns). Chromium only, no real Android (the Android
shortcut itself on the launcher is not testable here). Fantasy names only."""
from pathlib import Path
import json,os,sys
from playwright.sync_api import sync_playwright,expect
from uihelper import boot,state,skip_operator,CHROMIUM
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v29');OUT.mkdir(parents=True,exist_ok=True)
ASSETS=Path(__file__).resolve().parents[1]/'app/src/main/assets'
KEY='nev-spielnotiz-v0.1'
HOME=[('2','Sommer, Tim',True),('1','Becker, Lena',True),('9','Engel, Ola',False),('12','Neumann, Mia',False),('16','Maier, Max',False),('23','Wenz, Luca',False)]
def roster():
    return {'version':9,'currentPeriod':1,'meta':{'date':'2026-11-15','number':'T_029','operatorName':'','operatorPrompted':True,'timeMode':'down'},
      'home':{'name':'Phantasie EV Nord','players':[{'id':'h'+n,'number':n,'name':nm,'isGoalie':g,'starter':n=='2'} for n,nm,g in HOME],'startGoalie':'2'},
      'away':{'name':'EC Musterstadt','players':[],'startGoalie':''},
      'events':[{'id':'g0','order':1,'type':'goalie','team':'away','period':1,'time':'20:00','clock':'2000','player':'','goalieOut':'','goalieIn':'30'}],'shootout':[]}
def game(p):p.get_by_role('button',name='Spiel',exact=True).click();skip_operator(p)
def start(p,clock,kind,team):
    p.locator('#new-event').click()
    for x in clock:p.locator('[data-digit="'+x+'"]').click()
    p.locator('[data-action="next"]').click()
    if p.locator('#time-jump-dialog').is_visible():p.locator('#time-jump-retro').click()
    p.locator('[data-type="'+kind+'"]').click();p.locator('[data-team="'+team+'"]').click()
def last(p):return state(p)['events'][-1]
def ok(p):p.locator('#detail-ok').click();expect(p.locator('#detail-dialog')).not_to_be_visible()

def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox','--allow-file-access-from-files']);errors=[]
    for size in [(320,480),(360,640),(412,915)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p,{KEY:json.dumps(roster())});game(p)
      # 1) Goalie #2 (TW in roster): ask who serves; grid without goalies and without #2.
      start(p,'1900','penalty','home');p.locator('[data-pick-number="2"]').click();p.locator('[data-penalty="Bandencheck"]').click()
      expect(p.locator('#wizard-title')).to_have_text('Wer sitzt die Strafe ab?')
      nums=[x.get_attribute('data-served-number') for x in p.locator('[data-served-number]').all()];assert nums==['9','12','16','23'],nums
      assert 'Torwart' in p.locator('.wizard-summary').inner_text()
      fit=p.locator('#wizard-content').evaluate('n=>[n.clientWidth,n.scrollWidth]');assert fit[1]<=fit[0]+1,fit
      if size==(360,640):p.screenshot(path=str(OUT/'wer-sitzt-ab-360x640.png'))
      # Back returns to the penalty list, the choice is kept.
      p.locator('#wizard-back').click();expect(p.locator('#wizard-title')).to_have_text('Welche Strafe?');p.locator('[data-penalty="Bandencheck"]').click()
      p.locator('[data-served-number="9"]').click()
      e=last(p);assert e['player']=='2' and e['servedBy']=='9' and not e['servedLater'],e
      sheet=p.locator('#detail-sheet').inner_text();assert 'sitzt ab' in sheet.lower() and '#9' in sheet and 'Engel' in sheet,sheet
      # +10 as second entry: served player left open (may be someone else).
      p.locator('#detail-plus10').click();e=last(p);assert e['penalty']=='Disziplinarstrafe' and e['servedBy']=='' and e['servedLater'],e
      assert 'offen' in p.locator('#detail-sheet').inner_text();ok(p)
      # 2) Field player: saved directly, no question.
      start(p,'1800','penalty','home');p.locator('[data-pick-number="9"]').click();p.locator('[data-penalty="Bandencheck"]').click()
      expect(p.locator('#detail-dialog')).to_be_visible();e=last(p);assert e['player']=='9' and e['servedBy']=='' and not e['servedLater'],e;ok(p)
      # 3) Bench penalty: label "Bank / Trainer", other number via keypad.
      start(p,'1700','penalty','home');expect(p.locator('[data-action="bench-penalty"]')).to_have_text('Bank / Trainer')
      p.locator('[data-action="bench-penalty"]').click();assert 'Bank / Trainer' in p.locator('.wizard-hint').first.inner_text()
      p.locator('[data-penalty="Bandencheck"]').click();expect(p.locator('#wizard-title')).to_have_text('Wer sitzt die Strafe ab?')
      p.locator('[data-action="served-other"]').click();p.locator('[data-digit="1"]').click();p.locator('[data-digit="2"]').click();p.locator('[data-action="next"]').click()
      e=last(p);assert e['bench'] and e['servedBy']=='12',e;assert 'Bank / Trainer' in p.locator('#detail-sheet').inner_text();ok(p)
      # 4) Bench penalty, "Später eintragen": marked as open.
      start(p,'1600','penalty','home');p.locator('[data-action="bench-penalty"]').click();p.locator('[data-penalty="Bandencheck"]').click()
      p.locator('[data-action="served-later"]').click();e=last(p);assert e['bench'] and e['servedBy']=='' and e['servedLater'],e;ok(p)
      # 5) Away without roster: #30 is in goal (goalie change) -> keypad question directly.
      start(p,'1500','penalty','away');p.locator('[data-digit="3"]').click();p.locator('[data-digit="0"]').click();p.locator('[data-action="next"]').click()
      p.locator('[data-penalty="Bandencheck"]').click();expect(p.locator('#wizard-title')).to_have_text('Wer sitzt die Strafe ab?')
      assert p.locator('[data-served-number]').count()==0
      p.locator('[data-digit="1"]').click();p.locator('[data-digit="7"]').click();p.locator('[data-action="next"]').click()
      e=last(p);assert e['team']=='away' and e['player']=='30' and e['servedBy']=='17',e;ok(p)
      # History, report text and print show who served it.
      hist=p.locator('#history').inner_text() if p.locator('#history').count() else p.locator('body').inner_text()
      assert 'Abgesessen von #9' in hist and 'Absitzender offen' in hist,hist
      text=p.evaluate('window.EgrepUI.reportText()')
      assert 'Sitzt ab: #9 Engel, Ola' in text or 'Sitzt ab: #9' in text,text
      assert 'abgesessen von #12' in text and 'Absitzender offen' in text and 'abgesessen von #17' in text,text
      pr=p.evaluate('window.EgrepUI.preparePrintReport()||document.body.innerHTML')
      html=p.content();assert 'abgesessen von' in html and 'Absitzender offen' in html
      # Reload keeps the fields.
      saved=p.evaluate('window._saved');s=json.loads(saved[KEY]);pen=[x for x in s['events'] if x['type']=='penalty']
      assert [x.get('servedBy') for x in pen]==['9','','','12','','17'],[x.get('servedBy') for x in pen]
      # Shortcut hook: opens the signs, closes the quick menu, harmless when called twice.
      p.locator('#open-menu').click();p.evaluate('window.egrepOpenSigns();window.egrepOpenSigns()')
      expect(p.locator('#signs-dialog')).to_be_visible();assert not p.locator('#quick-menu').is_visible()
      assert p.locator('#signs-list .sign-card').count()==21;p.locator('#close-signs').click();p.close()
    # Real page via file:// with #signs (as the Android shortcut starts it).
    p=b.new_page(viewport={'width':360,'height':640});p.on('pageerror',lambda e:errors.append(str(e)))
    p.goto((ASSETS/'index.html').as_uri()+'#signs');expect(p.locator('#signs-dialog')).to_be_visible()
    assert p.evaluate('location.hash')=='',p.evaluate('location.hash')
    p.screenshot(path=str(OUT/'shortcut-signs-360x640.png'));p.close()
    p=b.new_page(viewport={'width':360,'height':640});p.goto((ASSETS/'index.html').as_uri());p.wait_for_timeout(400);assert not p.locator('#signs-dialog').is_visible();p.close()
    assert not errors,errors;b.close()
  print('V29 UI PASS: goalie (TW and in goal) and bench penalties ask who serves it; grid without goalies, other number, later (marked open), back keeps choice; field player saved directly; +10 leaves it open; detail/history/text/print/storage; "Bank / Trainer"; shortcut #signs and egrepOpenSigns; 3 viewports. Android launcher shortcut not tested.')
if __name__=='__main__':main()
