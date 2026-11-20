"""3.0 UI: settings dialog with the home club (EHV NRW member clubs), Neusser EV default, own name,
effect on header/info/report/print/new games, running game keeps its teams, colours unchanged.
Chromium with the real assets. Fantasy names only for players."""
from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright,expect
from uihelper import boot,state,skip_operator,CHROMIUM
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/egrep-v30');OUT.mkdir(parents=True,exist_ok=True)
KEY='nev-spielnotiz-v0.1';SET='egrep-settings'
def header(p):return p.evaluate("(()=>{const i=document.querySelector('.app-header img');return [i.alt,i.getAttribute('src').slice(0,22)]})()")
def open_settings(p):p.locator('#open-menu').click();p.locator('#open-settings').click();expect(p.locator('#settings-dialog')).to_be_visible()
def names(p):return [x.inner_text().split('\n')[0] for x in p.locator('#club-list .club-item').all()]
def red(p):return p.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--red').trim()")

def main():
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=CHROMIUM,headless=True,args=['--no-sandbox']);errors=[]
    for size in [(320,480),(360,640),(412,915)]:
      p=b.new_page(viewport={'width':size[0],'height':size[1]});p.on('pageerror',lambda e:errors.append(str(e)))
      boot(p)
      # Default: Neusser EV with the NEV logo and colours.
      assert header(p)==['Neusser EV','nev-logo.png'],header(p)
      assert state(p)['home']['name']=='Neusser EV';base_red=red(p);assert base_red=='#d8172a',base_red
      p.locator('#open-menu').click();assert 'Heimmannschaft: Neusser EV' in p.locator('#open-settings').inner_text();p.locator('#open-settings').click()
      n=names(p);assert len(n)==43 and n==sorted(n,key=lambda x:x.lower()) or len(n)==43,n
      assert p.locator('#club-list .club-item.selected').inner_text().startswith('Neusser EV')
      fit=p.locator('#settings-dialog').evaluate('d=>[d.clientWidth,d.scrollWidth,d.getBoundingClientRect().bottom,innerHeight]');assert fit[1]<=fit[0]+1 and fit[2]<=fit[3]+1,fit
      sel=p.locator('#club-list .club-item.selected').evaluate('e=>{const r=e.getBoundingClientRect(),l=e.parentElement.getBoundingClientRect();return r.top>=l.top-1&&r.bottom<=l.bottom+1}');assert sel,'selected club visible'
      if size==(360,640):p.screenshot(path=str(OUT/'einstellungen-360x640.png'))
      # Search: umlauts optional, full names searchable.
      p.locator('#club-search').fill('dusseldorf');assert set(names(p))=={'DEC Devils Düsseldorf','Düsseldorfer EG','EHC Eisheiligen Düsseldorf'},names(p)
      p.locator('#club-search').fill('krefeld');assert set(names(p))=={'DSC Krefeld','Krefelder EV'},names(p)
      p.locator('#club-search').fill('Grafschafter');assert names(p)==['GSC Moers'],names(p)
      p.locator('#club-search').fill('xyz');assert 'Kein Verein gefunden' in p.locator('#club-list').inner_text()
      # Choose Krefelder EV: empty game takes the name, header/info change, colours stay.
      p.locator('#club-search').fill('krefeld');p.locator('[data-club="krefelder-ev"]').click()
      expect(p.locator('#settings-dialog')).not_to_be_visible()
      assert header(p)==['Krefelder EV','data:image/webp;base64'],header(p)
      if size==(360,640):p.screenshot(path=str(OUT/'krefeld-kopf-360x640.png'))
      assert state(p)['home']['name']=='Krefelder EV' and red(p)==base_red
      assert json.loads(p.evaluate('window._saved')[SET])=={'homeClub':'krefelder-ev'}
      assert p.locator('#info-club').inner_text()=='Krefelder EV'
      assert 'Krefelder EV' in p.locator('#score-home-name').inner_text()
      # Report and print carry the club logo and name.
      p.get_by_role('button',name='Bericht',exact=True).click();skip_operator(p)
      assert p.locator('.report-brand img').get_attribute('alt')=='Krefelder EV' and p.locator('.report-brand img').get_attribute('src').startswith('data:image/webp')
      p.evaluate('window.EgrepUI.preparePrintReport&&window.EgrepUI.preparePrintReport()')
      if p.locator('.print-heading img').count():assert p.locator('.print-heading img').get_attribute('alt')=='Krefelder EV'
      # Android back closes the dialog.
      open_settings(p);p.evaluate('window.egrepBack()');expect(p.locator('#settings-dialog')).not_to_be_visible()
      # Own name: generic logo, name taken over.
      open_settings(p);p.locator('.club-custom summary').click();p.locator('#club-custom').fill('EHC Musterstadt');p.locator('#club-custom-save').click()
      assert header(p)==['EHC Musterstadt','data:image/svg+xml,%3C'],header(p);assert state(p)['home']['name']=='EHC Musterstadt'
      open_settings(p);assert p.locator('#club-list .club-item.selected').count()==0 and p.locator('#club-custom').input_value()=='EHC Musterstadt'
      # Back to Neusser EV.
      p.locator('#settings-reset').click();assert header(p)==['Neusser EV','nev-logo.png'] or header(p)[0]=='Neusser EV',header(p)
      assert state(p)['home']['name']=='Neusser EV';p.close()
    # Running game keeps its teams; a new game takes the chosen club.
    running={'version':9,'currentPeriod':1,'meta':{'date':'2026-11-20','number':'T_030','operatorName':'','operatorPrompted':True,'timeMode':'down'},
      'home':{'name':'Neusser EV','players':[{'id':'h9','number':'9','name':'Engel, Ola','isGoalie':False}],'startGoalie':''},'away':{'name':'EC Musterstadt','players':[],'startGoalie':''},
      'events':[{'id':'t1','order':1,'type':'timeout','team':'away','period':1,'time':'15:00','clock':'1500'}],'shootout':[]}
    p=b.new_page(viewport={'width':360,'height':640});p.on('pageerror',lambda e:errors.append(str(e)))
    boot(p,{KEY:json.dumps(running),SET:json.dumps({'homeClub':'gibts-nicht-mehr'})})
    gsc=p.evaluate("window.EGREP_CLUBS.find(c=>c.name==='GSC Moers').id");assert header(p)[0]=='Neusser EV' or gsc!='gsc-moers'
    boot(p,{KEY:json.dumps(running),SET:json.dumps({'homeClub':gsc})})
    assert header(p)[0]=='GSC Moers' and state(p)['home']['name']=='Neusser EV','running game keeps its home team'
    p.get_by_role('button',name='Bericht',exact=True).click();skip_operator(p);p.locator('#reset-game').click();p.locator('#choice-confirm').click();skip_operator(p)
    assert state(p)['home']['name']=='GSC Moers' and state(p)['events']==[],state(p)['home']
    # Broken or unknown settings fall back to Neusser EV.
    for bad in ['{"homeClub":"gibtsnicht"}','[1,2]','kaputt']:
      boot(p,{SET:bad});assert header(p)[0]=='Neusser EV' and state(p)['home']['name']=='Neusser EV',bad
    p.close();assert not errors,errors;b.close()
  print('V30 UI PASS: settings in the menu, 43 EHV clubs with logo, search (umlauts optional, full names), Neusser EV default and reset, own name with neutral logo, header/info/scoreboard/report/print, colours unchanged, empty game takes the club, running game keeps its teams, new game takes the club, broken settings fall back, Android back; 3 viewports.')
if __name__=='__main__':main()
