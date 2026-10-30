from pathlib import Path
from playwright.sync_api import sync_playwright
import json
BASE='http://127.0.0.1:8164/'
OUT=Path('/workspace/deliverables/checkout-preview');OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width in [1440,1024,768,390,360]:
  page=b.new_page(viewport={'width':width,'height':1050},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(BASE+'payment/?payment=success');assert page.locator('[data-payment-gate]').is_visible();assert page.locator('[data-payment-checkout]').is_hidden()
  page.goto(BASE+'cart/?add=essential');assert page.locator('.cart-item').count()==1;assert page.locator('[data-cart-total]').inner_text()=='RM1,000.00';page.reload();assert page.locator('.cart-item').count()==1
  page.select_option('#cart-package','addon-6');page.locator('[data-cart-add]').click();assert page.locator('[data-cart-total]').inner_text()=='RM1,650.00'
  page.select_option('#cart-package','addon-8');page.locator('[data-cart-add]').click();assert page.locator('[data-cart-total]').inner_text()=='RM1,750.00';assert page.locator('.cart-item input').nth(2).input_value()=='5'
  page.locator('#cart-requirements').fill('Training centre / 中文要求 <script>alert(1)</script>')
  for lang in ['zh','ms','en']:
   page.select_option('#page-language',lang);assert page.locator('#cart-requirements').input_value().startswith('Training');assert page.locator('.cart-item').count()==3;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,lang,'cart overflow')
  if width in [1440,390]:page.screenshot(path=str(OUT/f'cart-{width}.png'),full_page=True)
  page.locator('[data-cart-checkout]').click();page.wait_for_selector('#payment-calculator');assert page.locator('[name=amount]').input_value()=='1750.00';assert page.locator('[data-payment-unlocked]').is_hidden()
  page.locator('[name=client]').fill('Test 客户 <script>');page.locator('[name=email]').fill('test@example.invalid');page.locator('[name=phone]').fill('+60123456789');assert page.locator('[name=details]').input_value().startswith('Training');page.locator('[name=reference]').fill('QUOTE-TEST-001');page.locator('[name=confirmed]').check();page.locator('#payment-calculator button[type=submit]').click();assert page.locator('[data-payment-unlocked]').is_visible();assert '27401009500' in page.locator('[data-payment-unlocked]').inner_text()
  page.locator('[data-prepare-receipt]').click();assert page.locator('[data-send-receipt]').is_hidden();assert page.locator('[data-payment-error]').inner_text()
  # Real local attachment; must never be represented as uploaded or paid.
  page.locator('#payment-proof').set_input_files({'name':'receipt.png','mimeType':'image/png','buffer':bytes([137,80,78,71,13,10,26,10])+b'fixture'})
  page.wait_for_function("document.querySelector('[data-proof-status]').textContent.includes('receipt.png')")
  page.locator('[data-prepare-receipt]').click();assert page.locator('[data-send-receipt]').is_visible();assert 'NOT uploaded' in page.locator('[data-proof-status]').inner_text()
  page.locator('[name=method][value=stripe]').check();assert page.locator('[data-payment-unlocked]').is_hidden();page.locator('#payment-calculator button[type=submit]').click();assert page.locator('[data-payment-base]').inner_text()=='RM875.00';assert page.locator('[data-payment-fee]').inner_text()=='RM52.50';assert page.locator('[data-payment-total]').inner_text()=='RM927.50'
  # Changing languages retains quote/customer/stage/method and receipt memory.
  for lang in ['zh','ms','en']:
   page.select_option('#page-language',lang);assert page.locator('[name=client]').input_value()=='Test 客户 <script>';assert page.locator('[name=method][value=stripe]').is_checked();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,lang,'payment overflow')
  page.locator('[name=phase]').select_option('second');page.locator('#payment-calculator button[type=submit]').click();assert page.locator('[data-payment-total]').inner_text()=='RM556.50'
  for phase in ['deposit','second','balance']:
   with page.expect_download() as event:page.locator('[data-invoice-phase='+phase+']').click()
   download=event.value;path=OUT/f'notice-{width}-{phase}.pdf';download.save_as(path);assert path.read_bytes().startswith(b'%PDF-1.4');assert path.stat().st_size>10000
  page.locator('[name=method][value=usdt]').check();page.locator('#payment-calculator button[type=submit]').click();page.locator('[data-prepare-receipt]').click();assert page.locator('[data-send-receipt]').is_hidden();page.locator('#payment-transaction').fill('test-transaction-hash');page.locator('[data-prepare-receipt]').click();assert page.locator('[data-send-receipt]').is_visible();assert 'TDp1jRv52pC1bGqbpkZHmXsMEEWGdgEbNd' in page.locator('[data-payment-unlocked]').inner_text()
  if width in [1440,390]:page.screenshot(path=str(OUT/f'payment-{width}.png'),full_page=True)
  assert page.locator('meta[name=robots]').get_attribute('content')=='noindex, follow';assert not errors,errors;print('PASS',width,'basket services/quantity/fee/languages/gating/receipts/3 PDFs/no false paid',flush=True);page.close()
 b.close()
