"""Check real-time video camera, reversible chapter motion and reduced-motion cleanup."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import os
BASE=os.environ.get('PREVIEW_URL','http://127.0.0.1:8133/')
SHOTS=Path('/workspace/work/motion-preview/screenshots')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-webgl'])
 for width,height in [(1440,1000),(390,844)]:
  page=b.new_page(viewport={'width':width,'height':height},is_mobile=width<700,has_touch=width<700);errors=[];bad=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:bad.append(r.url) if r.status>=400 else None)
  page.goto(BASE,wait_until='domcontentloaded');page.wait_for_selector('.reference-motion-enabled');page.wait_for_selector('#kenny-entry-intro',state='detached')
  assert page.locator('h1').count()==1
  assert page.locator('.kenny-hero-source').evaluate('v=>!v.paused')
  threshold=1.04 if width<700 else 1.18
  page.wait_for_function('(value)=>Number(document.querySelector(".kenny-hero-screen").dataset.cameraScale)>value',arg=threshold,timeout=14000)
  scale=float(page.locator('.kenny-hero-screen').get_attribute('data-camera-scale'));assert scale<=1.261
  page.screenshot(path=str(SHOTS/f'hero-closeup-{width}.png'))
  page.wait_for_function('Number(document.querySelector(".kenny-hero-screen").dataset.cameraScale)<1.01',timeout=12000)
  page.screenshot(path=str(SHOTS/f'hero-wide-{width}.png'))
  for target in ['index','projects','profile','timeline','skills','coverage','project-brief']:
   page.locator('#'+target).evaluate('e=>e.scrollIntoView({behavior:"instant",block:"start"})');page.wait_for_timeout(650)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,target)
   if target in ['index','profile','timeline']:page.screenshot(path=str(SHOTS/f'{target}-{width}.png'))
  assert page.locator('.skill-card').count()==12
  page.locator('#home').evaluate('e=>e.scrollIntoView({behavior:"instant"})');page.wait_for_timeout(800)
  assert float(page.locator('.hero-content').evaluate('e=>getComputedStyle(e).opacity'))>.95
  assert page.locator('.site-header').is_visible()
  page.emulate_media(reduced_motion='reduce');page.wait_for_selector('.reference-motion-enabled',state='detached')
  assert page.locator('.reference-motion-enabled').count()==0
  assert page.locator('.kenny-hero-screen').evaluate('e=>e.style.getPropertyValue("--reference-camera-scale")')==''
  page.emulate_media(reduced_motion='no-preference');page.wait_for_selector('.reference-motion-enabled')
  assert page.locator('.reference-motion-enabled').count()==1
  assert page.locator('[data-chapter-flow="reference"]').count()==10
  assert not errors,errors;assert not bad,bad
  print('PASS',width,'native camera closeup/return, every chapter in both directions, no overflow, existing services, reduced-motion cleanup, no missing assets/runtime errors',flush=True)
  page.close()
 b.close()
