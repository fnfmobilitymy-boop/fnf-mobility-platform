from playwright.sync_api import sync_playwright
from urllib.parse import urljoin,urlparse,parse_qs
from pathlib import Path
import json,os
BASE=os.environ.get('PREVIEW_URL','http://127.0.0.1:8126/fnf-mobility-platform/');ROOT=Path(__file__).resolve().parents[1];SHOTS=Path('/workspace/work/seo-review');SHOTS.mkdir(exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-webgl','--autoplay-policy=no-user-gesture-required'])
 for w,h in [(1440,1000),(1024,900),(768,1024),(390,844),(360,800)]:
  c=b.new_context(viewport={'width':w,'height':h},is_mobile=w<700,has_touch=w<700);page=c.new_page();errors=[];bad=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:bad.append((r.status,r.url)) if r.status>=400 else None)
  page.add_init_script('localStorage.setItem("kenny-language","en");localStorage.setItem("kenny-music","off");window.__cls=0;new PerformanceObserver(l=>l.getEntries().forEach(e=>{if(!e.hadRecentInput)window.__cls+=e.value})).observe({type:"layout-shift",buffered:true})')
  for path in ['','services/','services/website-design/','services/google-ads-management/','services/seo/','privacy/']:
   r=page.goto(urljoin(BASE,path),wait_until='domcontentloaded');page.wait_for_timeout(700);assert r.status==200
   if path=='':page.wait_for_selector('#kenny-entry-intro',state='detached')
   assert page.locator('h1').count()==1,(w,path)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(w,path)
   assert page.title() and page.locator('meta[name=description]').get_attribute('content')
   assert not page.locator('script[src*="googletagmanager"]').count()
   if path=='':
    assert page.locator('.skill-card').count()==12
    assert page.locator('video').first.evaluate('v=>!v.paused&&v.currentTime>0')
    assert page.locator('#brief-type option[value="google-ads"]').count()==1
    assert page.locator('.client-project-directory a').count()==15 or page.locator('a[href="https://bloomthis.co"]').count()>0
    page.evaluate('document.getElementById("skills").scrollIntoView({behavior:"instant"})');page.wait_for_timeout(200)
    assert page.locator('.seo-service-links a[href="./services/google-ads-management/"]').count()>0
   else:
    for lang in ['zh','ms','en']:
     page.locator('#page-language').select_option(lang);assert page.locator('h1').count()==1;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(w,path,lang)
    if w<=900:
     page.locator('.service-menu').click();assert page.locator('.service-menu').get_attribute('aria-expanded')=='true';assert page.locator('.service-nav').is_visible();page.keyboard.press('Escape');assert page.locator('.service-menu').get_attribute('aria-expanded')=='false'
   if w in [1440,390] and path in ['services/','services/google-ads-management/','services/seo/']:
    page.screenshot(path=str(SHOTS/(('desktop-' if w==1440 else 'mobile-')+path.strip('/').replace('/','-')+'.png')),full_page=True)
   assert not errors,errors;assert not bad,bad
  page.goto(urljoin(BASE,'services/google-ads-management/'),wait_until='domcontentloaded');page.locator('.service-hero .service-button').click();page.wait_for_selector('#brief-type');page.wait_for_selector('#kenny-entry-intro',state='detached');page.wait_for_timeout(400);assert page.locator('#brief-type').input_value()=='google-ads'
  page.locator('#brief-name').fill('Preview client');page.locator('#brief-description').fill('Search ads for my training centre.');page.locator('.brief-submit').click();message=parse_qs(urlparse(page.locator('.brief-whatsapp').get_attribute('href')).query)['text'][0];assert 'Google Ads management' in message and 'Preview client' in message
  page.locator('#brief-language').select_option('zh');assert page.locator('#brief-name').input_value()=='Preview client';page.locator('#brief-language').select_option('en')
  page.evaluate('scrollTo(0,0)');page.wait_for_timeout(250)
  if w in [1440,390]:page.screenshot(path=str(SHOTS/f'homepage-{w}.png'))
  assert not errors,errors;assert not bad,bad
  print('PASS',w,'all routes, 3-language service content, mobile menu, video, 12 services, typed quote CTA/form, no missing assets/errors',flush=True);c.close()
 # A crawler with JavaScript disabled sees the actual homepage and service copy.
 c=b.new_context(java_script_enabled=False);page=c.new_page()
 for path in ['','services/google-ads-management/','services/seo/']:
  page.goto(urljoin(BASE,path));assert page.locator('h1').count()==1;assert len(page.locator('main').inner_text())>500
  if not path:assert page.locator('.brief-form').get_attribute('inert') is not None
 print('PASS no-JavaScript crawlable content and safe disabled interactive form',flush=True)
 b.close()
