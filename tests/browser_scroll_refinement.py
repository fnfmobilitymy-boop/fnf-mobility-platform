"""Regression: first globe bitmap, resize/re-entry, input-safe normal flow, real form geometry."""
from playwright.sync_api import sync_playwright
from pathlib import Path
BASE='http://127.0.0.1:8164/scroll-demo/';OUT=Path('/workspace/deliverables/chapter-refinement');OUT.mkdir(parents=True,exist_ok=True)
PIXELS='''c=>{const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let lit=0;for(let n=0;n<d.length;n+=400)if(d[n]+d[n+1]+d[n+2]>80)lit++;return lit}'''
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-webgl'])
 for width,height,dpr in [(1440,900,2),(1340,912,1.25),(1024,900,1),(768,1024,1),(390,844,2),(360,800,2)]:
  page=b.new_page(viewport={'width':width,'height':height},device_scale_factor=dpr,is_mobile=width<700,has_touch=width<700);errs=[];bad=[];page.on('pageerror',lambda e:errs.append(str(e)));page.on('response',lambda r:bad.append((r.status,r.url)) if r.status>=400 else None)
  page.add_init_script('localStorage.setItem("kenny-language","zh");localStorage.setItem("kenny-music","off")');page.goto(BASE);page.wait_for_selector('.chapter-stack-enabled');page.wait_for_selector('#kenny-entry-intro',state='detached')
  page.locator('#coverage').evaluate('e=>e.parentElement.scrollIntoView({behavior:"instant"})');canvas=page.locator('.world-stage canvas');canvas.wait_for();page.wait_for_function('document.querySelector(".world-stage canvas").dataset.renderState==="ready"');assert canvas.evaluate(PIXELS)>50,'First canvas is blank'
  canvas.scroll_into_view_if_needed();page.wait_for_timeout(200);assert canvas.evaluate(PIXELS)>50
  assert page.locator('#coverage').evaluate('e=>getComputedStyle(e).position')=='relative'
  assert page.locator('.kenny-portfolio').evaluate('e=>e.classList.contains("chapter-interaction-active")')
  frame=int(canvas.get_attribute('data-frame'));page.wait_for_timeout(300);assert int(canvas.get_attribute('data-frame'))>frame
  if width>=700:
   rect=canvas.bounding_box();page.mouse.move(rect['x']+rect['width']/2,rect['y']+rect['height']/2);before=float(canvas.get_attribute('data-zoom'));page.mouse.wheel(0,-100);page.wait_for_timeout(150);assert float(canvas.get_attribute('data-zoom'))>before
  else:
   canvas.evaluate('''c=>{const r=c.getBoundingClientRect(),t=(id,x)=>new Touch({identifier:id,target:c,clientX:r.left+x,clientY:r.top+150});c.dispatchEvent(new TouchEvent('touchstart',{touches:[t(1,100),t(2,200)],bubbles:true,cancelable:true}));c.dispatchEvent(new TouchEvent('touchmove',{touches:[t(1,80),t(2,230)],bubbles:true,cancelable:true}));c.dispatchEvent(new TouchEvent('touchend',{touches:[],bubbles:true,cancelable:true}))}''');page.wait_for_timeout(100);assert float(canvas.get_attribute('data-zoom'))>1
  for step in ['home','coverage']:
   page.locator('#'+step).evaluate('e=>e.parentElement.scrollIntoView({behavior:"instant"})');page.wait_for_timeout(200)
  assert canvas.evaluate(PIXELS)>50
  page.set_viewport_size({'width':width+8,'height':height});page.wait_for_timeout(150);assert canvas.evaluate(PIXELS)>50;page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150);assert canvas.evaluate(PIXELS)>50
  canvas.evaluate('c=>{c.dispatchEvent(new Event("contextlost",{cancelable:true}));c.dispatchEvent(new Event("contextrestored"))}');page.wait_for_timeout(100);assert canvas.evaluate(PIXELS)>50
  page.locator('#world-search').fill('JP');page.locator('[data-code=JP]').click();assert page.locator('.world-mount').get_attribute('data-selected')=='JP';page.locator('#world-search').fill('')
  page.locator('#project-brief').evaluate('e=>e.parentElement.scrollIntoView({behavior:"instant"})');page.wait_for_timeout(250)
  for lang in ['zh','ms','en']:
   page.locator('.site-language-button').click();page.get_by_role('menuitemradio',name={'zh':'中文','ms':'Bahasa Melayu','en':'English'}[lang],exact=False).click();page.wait_for_timeout(200)
   rects=page.locator('#project-brief').evaluate('e=>({intro:e.querySelector(".brief-intro").getBoundingClientRect().toJSON(),form:e.querySelector(".brief-card").getBoundingClientRect().toJSON(),display:getComputedStyle(e).display})')
   assert rects['display']=='grid'
   if width>900:assert rects['intro']['right']+10<rects['form']['left'],(width,lang,rects)
   else:assert rects['intro']['bottom']<=rects['form']['top']+2,(width,lang,rects)
   assert page.locator('.brief-intro').evaluate('e=>getComputedStyle(e).position')=='static'
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,lang)
  page.locator('#brief-name').fill('Preview test');page.select_option('#brief-type','business');page.locator('#brief-description').fill('Business website, service pages and enquiry form.');page.locator('.brief-submit').click();page.locator('.brief-whatsapp').wait_for();assert 'Preview%20test' in page.locator('.brief-whatsapp').get_attribute('href') or 'Preview' in page.locator('.brief-whatsapp').get_attribute('href')
  if width in [1340,390]:page.screenshot(path=str(OUT/f'form-{width}.png'),full_page=True)
  assert not errs,errs;assert not bad,bad;print('PASS',width,'first bitmap/re-entry/resize/restore, globe controls, unclipped bilingual/trilingual form, no overlaps or errors',flush=True);page.close()
 b.close()
