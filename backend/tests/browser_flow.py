"""Local browser integration with isolated fake data, no external payment/email."""
from playwright.sync_api import sync_playwright
from pathlib import Path
from io import BytesIO
from PIL import Image
import os
BASE=os.environ.get('BACKEND_TEST_URL','http://127.0.0.1:8188');EMAIL='qa@example.invalid';PASSWORD='Test-Only-2026!';OUT=Path('/workspace/deliverables/order-backend/browser');OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width,height in [(1440,1000),(390,844)]:
  context=b.new_context(viewport={'width':width,'height':height},accept_downloads=True);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(BASE+'/?add=essential');page.wait_for_selector('#request-form');assert page.locator('#test-banner').is_visible();assert page.locator('#catalogue option').count()==30
  for name,value in [('name','TEST ONLY / QA '+str(width)),('email','customer@example.invalid'),('phone','+60123456789'),('business','TEST BUSINESS')]:page.locator('[name='+name+']').fill(value)
  page.locator('[name=requirements]').fill('TEST ONLY: business website with a gallery and enquiry form.')
  for lang in ['zh','ms','en']:
   page.select_option('#language',lang);page.wait_for_timeout(100);assert page.locator('[name=name]').input_value()=='TEST ONLY / QA '+str(width);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  page.screenshot(path=str(OUT/f'cart-{width}.png'),full_page=True);page.locator('[name=consent]').check();page.locator('#request-form button[type=submit]').click();page.wait_for_url('**/order/**');page.locator('.tag.requested').wait_for();oid=page.url.split('/order/')[1].split('?')[0].split('#')[0]
  owner_context=b.new_context(viewport={'width':width,'height':height},accept_downloads=True);owner=owner_context.new_page();owner.on('pageerror',lambda e:errors.append(str(e)));owner.goto(BASE+'/admin');owner.wait_for_selector('#login');owner.locator('[name=email]').fill(EMAIL);owner.locator('[name=password]').fill(PASSWORD);owner.locator('#login button').click();owner.locator('[data-order="'+oid+'"]').wait_for();owner.locator('[data-order="'+oid+'"]').click();owner.wait_for_selector('#quote');owner.locator('[name=amount]').fill('1000.00');owner.locator('[name=scope]').fill('TEST ONLY: agreed one-page website, six sections, two revisions.');owner.locator('#quote input[type=checkbox]').check();owner.locator('#quote button[type=submit]').click();owner.wait_for_selector('#admin-detail [data-document]');page.locator('[data-action=refresh]').click();page.locator('[data-upload=deposit]').wait_for();assert page.locator('.tag.locked').count()==2
  for index,phase in enumerate(['deposit','second','balance']):
   if index:
    owner.once('dialog',lambda d:d.accept('TEST ONLY customer accepted milestone'));owner.locator('[data-release='+phase+']').click();owner.wait_for_selector('[data-release='+phase+']',state='detached');page.locator('[data-action=refresh]').click();page.locator('[data-upload='+phase+']').wait_for()
   buf=BytesIO();Image.new('RGB',(40,40),(int(oid[:2],16),int(oid[2:4],16),index*70)).save(buf,format='PNG');form=page.locator('[data-upload='+phase+']');form.locator('[name=reference]').fill('TEST-TRANSFER-'+phase);form.locator('[type=file]').set_input_files({'name':'TEST-receipt-'+phase+'.png','mimeType':'image/png','buffer':buf.getvalue()});form.locator('button[type=submit]').click();page.wait_for_selector('[data-upload='+phase+'] button[type=submit]:not(:disabled)');owner.locator('[data-order="'+oid+'"]').click();review=owner.locator('[data-review]').last;review.wait_for();review.locator('[name=note]').fill('TEST ONLY: simulated funds confirmation');review.locator('[name=confirmed]').check();review.locator('button[value=yes]').click();owner.wait_for_selector('[data-review]',state='detached');page.locator('[data-action=refresh]').click();page.wait_for_timeout(150)
  page.locator('.tag.completed').wait_for();assert page.locator('.tag.paid').count()==3;assert page.locator('[data-document]').count()==6
  with page.expect_download() as event:page.locator('[data-document]').last.click()
  event.value.save_as(OUT/f'receipt-{width}.pdf');assert (OUT/f'receipt-{width}.pdf').read_bytes().startswith(b'%PDF')
  for target in [page,owner]:assert target.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  page.screenshot(path=str(OUT/f'customer-{width}.png'),full_page=True);owner.screenshot(path=str(OUT/f'admin-{width}.png'),full_page=True);assert not errors,errors
  print('PASS',width,'EN/ZH/MS, real order save, owner quote, 3 receipt uploads/reviews/releases and six PDF documents',flush=True);context.close();owner_context.close()
 b.close()
