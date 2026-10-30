"""Verify owner-approved prices, responsive localisations and real project-brief routes."""
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright
import os,json,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source/seo'))
from pricing import PLANS,CARE,ADDONS,SEARCH
BASE=os.environ.get('PREVIEW_URL','http://127.0.0.1:8164/');OUT=Path('/workspace/deliverables/pricing-page');OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-webgl'])
 for width in [1440,1024,768,390,360]:
  page=b.new_page(viewport={'width':width,'height':1000});errors=[];bad=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:bad.append((r.status,r.url)) if r.status>=400 else None)
  response=page.goto(BASE+'pricing/',wait_until='domcontentloaded');assert response.status==200
  for lang in ['en','zh','ms']:
   page.select_option('#page-language',lang)
   assert page.locator('h1').count()==1
   assert page.locator('.pricing-packages .pricing-plan').count()==5
   assert page.locator('.pricing-care .pricing-plan').count()==3
   assert page.locator('.pricing-table tbody tr').count()==17
   assert page.locator('.pricing-search-row').count()==5
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,lang,'overflow')
   prices=page.locator('.pricing-packages .pricing-amount strong').all_text_contents();assert prices==['RM1,000','RM1,800','RM1,800','RM2,500','RM4,500'],prices
   assert page.locator('.pricing-care .pricing-amount strong').all_text_contents()==['RM150','RM300','RM600']
   for a in page.locator('a[href^="#"]').all():assert page.locator(a.get_attribute('href')).count(),a.get_attribute('href')
   if width in [1440,390]:
    page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/f'{width}-{lang}.png'))
  page.select_option('#page-language','en')
  if width<=1120:
   page.locator('.service-menu').click();assert page.locator('.service-nav').is_visible();page.keyboard.press('Escape');assert page.locator('.service-menu').get_attribute('aria-expanded')=='false'
  page.emulate_media(reduced_motion='reduce');page.wait_for_timeout(150);assert page.locator('[data-pricing-video]').evaluate('v=>v.paused')
  page.select_option('#page-language','zh');assert page.locator('[data-pricing-toggle]').get_attribute('aria-pressed')=='true';page.locator('[data-pricing-toggle]').click();assert page.locator('[data-pricing-toggle]').get_attribute('aria-pressed')=='false'
  cta=page.locator('.pricing-packages .service-button').all()
  assert [parse_qs(urlparse(a.get_attribute('href')).query)['package'][0] for a in cta]==['essential','signature','personal','business','ecommerce']
  pdf=page.request.get(BASE+'media/kenny-studio-pricing-en-zh.pdf');assert pdf.status==200 and pdf.body().startswith(b'%PDF')
  page.locator('.pricing-packages .service-button').nth(4).click();page.wait_for_selector('#order-request-form');assert page.locator('[name=package]').input_value()=='ecommerce';page.goto(BASE,wait_until='domcontentloaded');page.wait_for_selector('#kenny-entry-intro',state='detached')
  assert page.locator('#projects a[href^="https://"]').evaluate_all('els=>new Set(els.map(a=>a.href)).size')==23
  assert page.locator('a[href="./pricing/"]').count()>=2
  assert not errors,errors;assert not bad,bad
  print('PASS',width,'EN/ZH/MS, all fees, PDF, menu, reduced motion, language video reinit, e-commerce CTA, 23 projects',flush=True);page.close()
 c=b.new_context(java_script_enabled=False);page=c.new_page();page.goto(BASE+'pricing/');assert page.locator('h1').count()==1;assert page.locator('.pricing-plan').count()==8;assert 'RM1,000' in page.locator('main').inner_text();assert page.locator('link[rel=canonical]').get_attribute('href')=='https://kennystudio.cfd/pricing/'
 data=json.loads(page.locator('script[type="application/ld+json"]').text_content());catalog=next(x for x in data['@graph'] if x['@type']=='OfferCatalog');assert [x['priceSpecification']['minPrice'] for x in catalog['itemListElement']]==[1000,1800,1800,2500,4500]
 print('PASS crawlable pricing, canonical, factual offer catalog; tracking remains off',flush=True);b.close()
