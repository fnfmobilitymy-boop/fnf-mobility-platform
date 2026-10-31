import test_orders as fixtures
import secrets

class RolesCountryTest(fixtures.OrdersTest):
 def owned(self):
  data={'items':[{'id':'essential','qty':1}],'name':'Role country fixture','email':'qa@example.invalid','phone':'+60123456789','requirements':'A customer-owned test order for access isolation.','method':'stripe','language':'en','consent':True,'idempotency':secrets.token_hex(32)}
  r=self.c.post('/api/orders',json=data);self.assertEqual(r.status_code,201,r.text);o=r.json();o['headers']={};return o
 def test_role_pages_assets_cookies_and_private_downloads_are_separate(self):
  public=self.c.get('/').text;owner=self.c.get('/admin').text
  self.assertIn('/static/customer-app.js',public);self.assertNotIn('admin-tools.js',public);self.assertNotIn('href="/admin"',public)
  self.assertIn('/static/owner-app.js',owner);self.assertNotIn('customer-account.js',owner);self.assertNotIn('sales-chat.js',owner);self.assertNotIn('href="/"',owner);self.assertNotIn('href="/account"',owner)
  customer_js=self.c.get('/static/customer-app.js').text;owner_js=self.c.get('/static/owner-app.js').text
  self.assertNotIn("'/admin/",customer_js);self.assertNotIn('window.KennyAccount',owner_js);self.assertNotIn('data-client-link',owner_js)
  o=self.owned();h=self.quote(o,'stripe');data=self.c.get('/api/admin/orders/'+o['id']).json();doc=data['documents'][0]['id']
  self.assertTrue(self.c.get('/api/admin/documents/'+doc).content.startswith(b'%PDF'))
  customer=fixtures.TestClient(self.app);customer.cookies.set('kenny_customer',self.c.cookies.get('kenny_customer'))
  try:
   self.assertEqual(customer.get('/api/admin/orders').status_code,401);self.assertEqual(customer.get('/api/admin/documents/'+doc).status_code,401)
   self.assertEqual(customer.get('/api/orders/'+o['id']).status_code,200)
  finally:customer.close()
  self.assertEqual(self.c.post('/api/account/logout',json={}).status_code,200)
  self.assertEqual(self.c.get('/api/orders/'+o['id']).status_code,401);self.assertEqual(self.c.get('/api/documents/'+doc).status_code,401)
  self.assertEqual(self.c.get('/api/admin/orders/'+o['id']).status_code,200)
  self.assertEqual(self.c.get('/api/admin/orders/'+o['id']+'/link').status_code,404)
  login=self.c.post('/api/admin/login',json={'email':self.cfg.admin_email,'password':self.password});self.assertTrue(any('Path=/api/admin' in v for v in login.headers.get_list('set-cookie')))
 def test_registration_and_stripe_country_and_payment_status_are_automatic(self):
  self.cfg.test_mode=True;self.c.cookies.clear()
  r=self.c.post('/api/account/register',json={'email':'qa@example.invalid','password':'Country payment password 123!','name':'Country fixture','country':'US'})
  self.assertEqual(r.status_code,409) # existing fixture account cannot be overwritten
  r=self.c.post('/api/account/register',json={'email':'new-country@example.invalid','password':'Country payment password 123!','name':'Country fixture','country':'US'});self.assertEqual(r.status_code,200,r.text)
  ch=r.json();v=self.c.post('/api/account/verify',json={'challenge':ch['challenge'],'code':ch['testCode']});self.assertEqual(v.status_code,200);self.assertEqual(v.json()['country'],'US');self.c.client.headers['X-Customer-CSRF']=v.json()['csrf']
  self.cfg.test_mode=False
  body={'items':[{'id':'essential','qty':1}],'name':'Country fixture','email':'new-country@example.invalid','phone':'+60123456789','requirements':'Country and automatic payment acceptance fixture.','method':'stripe','language':'en','consent':True,'idempotency':secrets.token_hex(32)}
  r=self.c.post('/api/orders',json=body);self.assertEqual(r.status_code,201,r.text);o=r.json();o['headers']={};self.owner()
  row=self.c.get('/api/admin/orders').json()['orders'][0];self.assertEqual((row['country_code'],row['country_source'],row['payment_status']),('US','registration','not_invoiced'))
  self.quote(o,'stripe');row=self.c.get('/api/admin/orders').json()['orders'][0];self.assertEqual(row['payment_status'],'unpaid');self.assertEqual(row['amount_due'],53001)
  event=self.event(o);event['data']['object']['customer_details']={'address':{'country':'SG'}};self.assertEqual(self.send_event(event).status_code,200)
  row=self.c.get('/api/admin/orders').json()['orders'][0];self.assertEqual(row['payment_status'],'partial');self.assertEqual(row['paid_project_value'],50001);self.assertEqual(row['amount_due'],0);self.assertEqual((row['country_code'],row['country_source']),('SG','stripe_billing'))
  self.assertEqual(self.c.get('/api/account/session').json()['country'],'US')
  report=self.c.get('/api/admin/tools').json()['revenue'];self.assertEqual(report['lifetime']['revenue'],50001);self.assertEqual(report['lifetime']['customer_fees'],3000);self.assertEqual(report['lifetime']['payments'],1)
  self.assertEqual(self.send_event(event).status_code,200);self.assertEqual(self.c.get('/api/admin/tools').json()['revenue']['lifetime']['payments'],1)
  exported=self.c.get('/api/admin/export/orders.csv').text;self.assertIn('Country source',exported);self.assertIn('stripe_billing',exported)

for name in list(fixtures.OrdersTest.__dict__):
 if name.startswith('test_') and name not in RolesCountryTest.__dict__:setattr(RolesCountryTest,name,None)
