"""Local-only integration tests. Synthetic analytics fixtures never contact Google."""
from pathlib import Path
import tempfile,subprocess,os,threading,http.server,functools,json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];BASE='http://127.0.0.1:8126/fnf-mobility-platform/'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-webgl'])
 page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.add_init_script('localStorage.setItem("kenny-music","off");localStorage.setItem("kenny-language","en");window.cls=0;new PerformanceObserver(l=>l.getEntries().forEach(e=>{if(!e.hadRecentInput)cls+=e.value})).observe({type:"layout-shift",buffered:true})')
 page.goto(BASE,wait_until='domcontentloaded');page.wait_for_timeout(1600);cls=page.evaluate('cls');assert cls<.1,cls
 page.locator('#coverage').evaluate('e=>e.scrollIntoView({behavior:"instant"})');canvas=page.locator('.world-stage canvas');canvas.wait_for();canvas.scroll_into_view_if_needed();page.wait_for_timeout(300);assert page.locator('.world-list button').count()==250
 r=canvas.bounding_box();page.mouse.move(r['x']+r['width']/2,r['y']+r['height']/2);before=float(canvas.get_attribute('data-zoom'));page.mouse.wheel(0,-120);page.wait_for_timeout(150);assert float(canvas.get_attribute('data-zoom'))>before
 page.locator('#world-search').fill('JP');page.locator('[data-code=JP]').click();assert page.locator('.world-mount').get_attribute('data-selected')=='JP'
 page.emulate_media(reduced_motion='reduce');page.wait_for_timeout(120);assert page.locator('.world-auto').is_disabled();assert 'motion-reduced' in page.locator('.kenny-portfolio').get_attribute('class')
 assert not errors,errors;print('PASS homepage initial CLS',round(cls,4),'globe wheel/selection, reduced motion',flush=True)
 b.close()
 # Check actual WebGL gallery controls with Chromium software GL, rather than only fallback markup.
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1366,'height':900});page.add_init_script('localStorage.setItem("kenny-music","off")');page.goto(BASE+'#projects',wait_until='domcontentloaded');page.wait_for_selector('.work-gallery.has-webgl');before=page.locator('.work-orbit-caption h3').inner_text() if page.locator('.work-orbit-caption h3').count() else ''
 stage=page.locator('.work-orbit-stage');stage.focus();stage.press('End');page.wait_for_function('document.querySelector("#projects").innerText.includes("London Medical")',timeout=12000);print('PASS curved WebGL renderer and keyboard project navigation',flush=True);b.close()
 for mode in ['GA4','GTM']:
  with tempfile.TemporaryDirectory() as d:
   env={**os.environ,'OUTPUT_DIR':d,'SITE_URL':'https://example.invalid','SITE_URL_VERIFIED':'true','BUILD_INDEXABLE':'true','GA4_MEASUREMENT_ID':'G-TESTONLY' if mode=='GA4' else '', 'GTM_CONTAINER_ID':'GTM-TESTONLY' if mode=='GTM' else ''}
   subprocess.run(['python',str(ROOT/'scripts/build_site.py')],env=env,check=True,capture_output=True)
   class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
   server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=d));threading.Thread(target=server.serve_forever,daemon=True).start()
   try:
    b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();requests=[]
    page.route('https://www.googletagmanager.com/**',lambda route:(requests.append(route.request.url),route.fulfill(status=200,content_type='application/javascript',body='')))
    page.goto(f'http://127.0.0.1:{server.server_port}/privacy/',wait_until='domcontentloaded');page.wait_for_timeout(150);assert requests==[]
    page.locator('.analytics-banner button').filter(has_text='Essential only').click();assert requests==[]
    page.locator('.analytics-settings').first.click();page.locator('.analytics-banner button').filter(has_text='Allow analytics').click();page.wait_for_timeout(150);assert len(requests)==1
    consent=page.evaluate('dataLayer.filter(x=>x[0]==="consent").map(x=>Array.from(x))');assert consent[0][2]['ad_storage']=='denied';assert consent[1][2]['analytics_storage']=='granted'
    page.locator('.analytics-settings').first.click();page.locator('.analytics-banner button').filter(has_text='Essential only').click();page.wait_for_timeout(300);assert len(requests)==1
    print('PASS',mode,'no external request before consent; opt-in loading, ad consent denied, withdrawal persists',flush=True);b.close()
   finally:server.shutdown()
