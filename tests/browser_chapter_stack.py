"""A chapter must hold while its successor enters, release afterwards, and stay navigable."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import os
BASE=os.environ.get('PREVIEW_URL','http://127.0.0.1:8164/');OUT=Path('/workspace/deliverables/chapter-preview');OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-webgl'])
 for width,height in [(1440,900),(1024,900),(768,1024),(390,844),(360,800)]:
  page=b.new_page(viewport={'width':width,'height':height},is_mobile=width<700,has_touch=width<700);errs=[];bad=[];page.on('pageerror',lambda e:errs.append(str(e)));page.on('response',lambda r:bad.append((r.status,r.url)) if r.status>=400 else None)
  page.add_init_script('if(!localStorage.getItem("kenny-language"))localStorage.setItem("kenny-language","en");localStorage.setItem("kenny-music","off");')
  page.goto(BASE,wait_until='domcontentloaded');page.wait_for_selector('.chapter-stack-enabled');page.wait_for_selector('#kenny-entry-intro',state='detached');page.evaluate('document.fonts.ready');page.wait_for_timeout(250)
  assert page.locator('main > .chapter-shell').count()==10;assert page.locator('h1').count()==1;assert page.locator('.skill-card').count()==12
  assert page.locator('#hero-title').evaluate('e=>getComputedStyle(e).fontFamily.includes("KennyGeometric")')
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),width
  page.screenshot(path=str(OUT/f'hero-{width}.png'))
  # Scrolling one half viewport moves incoming page but holds the outgoing page.
  page.evaluate('scrollTo(0,innerHeight*.52)');page.wait_for_timeout(500)
  assert abs(page.locator('#home').evaluate('e=>e.getBoundingClientRect().top'))<2,width
  top=page.locator('#index').evaluate('e=>e.getBoundingClientRect().top');assert 0<top<height,(width,top)
  page.screenshot(path=str(OUT/f'transition-{width}.png'))
  # Every chapter is reachable through its natural-flow shell, including long sections.
  for section in ['projects','profile','timeline','skills','coverage','badge','contact','project-brief']:
   page.locator('#'+section).evaluate('e=>e.closest(".chapter-shell").scrollIntoView({behavior:"instant",block:"start"})');page.wait_for_timeout(700)
   if section=='coverage':page.locator('.world-list button').first.wait_for();page.wait_for_timeout(300)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,section)
   assert page.locator('#'+section).evaluate('e=>Math.abs(e.getBoundingClientRect().top)<3'),(width,section)
  # Services can scroll all the way down before the globe replaces them.
  page.locator('#skills').evaluate('e=>scrollTo(0,e.parentElement.getBoundingClientRect().top+scrollY+e.offsetHeight-innerHeight)');page.wait_for_timeout(300)
  assert abs(page.locator('#skills').evaluate('e=>e.getBoundingClientRect().bottom-innerHeight'))<3
  # Reverse to the beginning through the real fixed header, not element.scrollIntoView.
  if width<700:
   menu=page.locator('.menu-toggle');
   if menu.count():menu.click()
  home=page.locator('.main-nav a[href="#home"]');
  if home.is_visible():home.click();page.wait_for_timeout(1700)
  else:page.evaluate('scrollTo(0,0)');page.wait_for_timeout(400)
  assert page.evaluate('scrollY<5'),(width,'navigation')
  # Locale changes keep React wrapper ownership and recalculate taller content.
  for lang in ['zh','ms','en']:
   page.locator('.site-language-button').click();page.get_by_role('menuitemradio',name={'zh':'中文','ms':'Bahasa Melayu','en':'English'}[lang],exact=False).click();page.wait_for_timeout(500)
   assert page.locator('main >.chapter-shell').count()==10
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,lang)
   heading=page.locator('#hero-title');assert heading.evaluate('e=>e.scrollWidth<=e.clientWidth+2'),(width,lang,'title overflow')
   if width in [1440,390]:page.screenshot(path=str(OUT/f'hero-{width}-{lang}.png'))
  page.emulate_media(reduced_motion='reduce');page.wait_for_selector('.chapter-stack-enabled',state='detached');assert page.locator('#home').evaluate('e=>getComputedStyle(e).position')=='relative'
  page.emulate_media(reduced_motion='no-preference');page.wait_for_selector('.chapter-stack-enabled');assert page.locator('main >.chapter-shell').count()==10
  assert not errs,errs;assert not bad,bad;print('PASS',width,'chapter hold/cover/release, long content, reverse/nav, EN/ZH/MS, reduced motion, no missing assets/errors',flush=True);page.close()
 b.close()
