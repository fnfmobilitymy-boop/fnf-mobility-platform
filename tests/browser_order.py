"""Unconfigured payments must never look like a successful payment or accepted order."""
from pathlib import Path
from urllib.parse import urlparse,parse_qs,unquote
from playwright.sync_api import sync_playwright
import json,os
BASE=os.environ.get('PREVIEW_URL','http://127.0.0.1:8164/');OUT=Path('/workspace/deliverables/pricing-page');OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width in [1440,768,390,360]:
  page=b.new_page(viewport={'width':width,'height':1100});errors=[];bad=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:bad.append((r.status,r.url)) if r.status>=400 else None)
  page.goto(BASE+'order/?package=ecommerce&payment=success',wait_until='networkidle');assert page.locator('[name=package]').input_value()=='ecommerce';assert page.locator('[data-order-price]').inner_text()=='RM4,500';assert page.locator('[data-order-deposit]').inner_text()=='RM2,250'
  assert page.locator('#order-review').is_hidden()
  assert page.locator('.order-method img').count()==4
  assert page.locator('.order-method img').evaluate_all('els=>els.every(e=>e.complete&&e.naturalWidth>0)')
  assert page.locator('a[href^="https://buy.stripe.com"]').count()==0
  page.locator('[name=name]').fill('QA <script>Tester</script>');page.locator('[name=email]').fill('client@example.invalid');page.locator('[name=phone]').fill('+60123456789');page.locator('[name=business]').fill('Client brand');page.locator('[name=details]').fill('A website for our training centre.');page.locator('[name=agreement]').check();page.locator('[name=payment][value=tng]').check()
  for lang in ['zh','ms','en']:
   page.select_option('#page-language',lang);assert page.locator('[name=name]').input_value()=='QA <script>Tester</script>';assert page.locator('[name=payment][value=tng]').is_checked();assert page.locator('[name=agreement]').is_checked();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,lang)
  page.locator('button[type=submit]').click();assert page.locator('#order-review').is_visible();assert 'QA <script>Tester</script>' in page.locator('#order-review').inner_text();assert page.locator('#order-review script').count()==0
  link=page.locator('[data-order-send]').get_attribute('href');msg=parse_qs(urlparse(link).query)['text'][0];assert 'RM4,500' in msg and 'QA <script>Tester</script>' in msg and 'Touch' in msg
  page.locator('[data-order-edit]').click();assert page.locator('#order-request-form').is_visible()
  page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/f'order-{width}.png'))
  assert not errors,errors;assert not bad,bad
  assert page.locator('meta[name=robots]').get_attribute('content')=='noindex, follow'
  print('PASS order',width,'package/estimate, four real icons, language data retention, escaped review, WhatsApp handoff, no false success',flush=True);page.close()
 b.close()
