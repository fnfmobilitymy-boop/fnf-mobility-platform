import test_orders as fixtures
from unittest.mock import patch,AsyncMock
from urllib.parse import urlparse,parse_qs
from app.core import now
from app.sales import Reply
from policy import VERSION
import secrets,httpx

class AccountTest(fixtures.OrdersTest):
 def setUp(self):
  super().setUp();self.cfg.test_mode=True;self.c.cookies.clear();self.c.client.headers.pop('X-Customer-CSRF',None)
 def register(self,address='customer@example.invalid'):
  data={'email':address,'password':'A long test password 123!','name':'Customer 测试'}
  r=self.c.post('/api/account/register',json=data);self.assertEqual(r.status_code,200,r.text)
  return data,r.json()
 def verify(self,address='customer@example.invalid'):
  data,ch=self.register(address);r=self.c.post('/api/account/verify',json={'challenge':ch['challenge'],'code':ch['testCode']});self.assertEqual(r.status_code,200,r.text);self.c.client.headers['X-Customer-CSRF']=r.json()['csrf'];return data,r.json()
 def payload(self,address='customer@example.invalid'):
  return {'items':[{'id':'essential','qty':1}],'name':'Customer','email':address,'phone':'+60123456789','requirements':'Business site with enquiry form','method':'bank','language':'zh','consent':True,'idempotency':secrets.token_hex(32)}
 def test_checkout_requires_verified_identity_csrf_and_owned_email(self):
  body=self.payload();self.assertEqual(self.c.post('/api/orders',json=body).status_code,401)
  data,ch=self.register();self.assertEqual(self.c.post('/api/orders',json=body).status_code,401)
  r=self.c.post('/api/account/verify',json={'challenge':ch['challenge'],'code':ch['testCode']});self.assertEqual(r.status_code,200)
  self.assertEqual(self.c.post('/api/orders',json=body).status_code,403)
  self.c.client.headers['X-Customer-CSRF']=r.json()['csrf']
  self.assertEqual(self.c.post('/api/orders',json={**body,'email':'victim@example.invalid'}).status_code,422)
  o=self.c.post('/api/orders',json=body);self.assertEqual(o.status_code,201,o.text);o=o.json()
  self.assertEqual(self.c.post('/api/orders',json=body).json()['id'],o['id'])
  self.assertEqual(self.c.get('/api/account/orders').json()['orders'][0]['id'],o['id'])
  self.c.post('/api/account/logout',json={});self.assertEqual(self.c.get('/api/orders/'+o['id'],headers={'Authorization':'Bearer '+o['token']}).status_code,401)
  _,other=self.verify('other@example.invalid');self.assertEqual(self.c.get('/api/orders/'+o['id'],headers={'Authorization':'Bearer '+o['token']}).status_code,404)
  self.assertEqual(self.c.get('/api/account/orders').json()['orders'],[])
  self.assertEqual(self.c.post('/api/orders',json={**body,'email':other['email']}).status_code,409)
  self.c.post('/api/account/logout',json={});login=self.c.post('/api/account/login',json=data);self.assertEqual(login.status_code,200)
  self.assertEqual(self.c.get('/api/orders/'+o['id']).status_code,200)
 def test_otp_limits_replay_expiry_and_password_reset_invalidate_sessions(self):
  data,ch=self.register();bad='000000' if ch['testCode']!='000000' else '111111'
  for _ in range(5):self.assertEqual(self.c.post('/api/account/verify',json={'challenge':ch['challenge'],'code':bad}).status_code,400)
  self.assertEqual(self.c.post('/api/account/verify',json={'challenge':ch['challenge'],'code':ch['testCode']}).status_code,400)
  with self.db.connect() as c:self.assertEqual(c.execute('SELECT attempts FROM account_challenges WHERE id=?',(ch['challenge'],)).fetchone()[0],5)
  # An attacker cannot overwrite the password of an unverified account.
  self.assertEqual(self.c.post('/api/account/register',json={**data,'password':'Different password 123!'}).status_code,409)
  ch=self.c.post('/api/account/login',json=data).json()
  with self.db.transaction() as c:c.execute('UPDATE account_challenges SET expires=? WHERE id=?',(now()-1,ch['challenge']))
  self.assertEqual(self.c.post('/api/account/verify',json={'challenge':ch['challenge'],'code':ch['testCode']}).status_code,400)
  ch=self.c.post('/api/account/login',json=data).json();v={'challenge':ch['challenge'],'code':ch['testCode']};r=self.c.post('/api/account/verify',json=v);self.assertEqual(r.status_code,200)
  old_token=self.c.cookies.get('kenny_customer');self.assertEqual(self.c.post('/api/account/verify',json=v).status_code,400)
  ch=self.c.post('/api/account/reset/request',json={'email':data['email']}).json();new='Changed long password 456!';r=self.c.post('/api/account/reset',json={'challenge':ch['challenge'],'code':ch['testCode'],'password':new});self.assertEqual(r.status_code,200)
  fresh=self.c.cookies.get('kenny_customer');self.c.cookies.clear();self.c.cookies.set('kenny_customer',old_token);self.assertIsNone(self.c.get('/api/account/session').json()['customer'])
  self.c.cookies.clear();self.assertEqual(self.c.post('/api/account/login',json=data).status_code,401);self.assertEqual(self.c.post('/api/account/login',json={**data,'password':new}).status_code,200)
 def test_real_email_delivery_is_never_faked(self):
  self.cfg.test_mode=False
  with patch.dict('os.environ',{'SMTP_HOST':'','GOOGLE_CLIENT_ID':'','GOOGLE_CLIENT_SECRET':''}):
   self.assertFalse(self.c.get('/api/account/config').json()['email']);self.assertFalse(self.c.get('/api/account/config').json()['google'])
   self.assertEqual(self.c.post('/api/account/register',json={'email':'a@example.invalid','password':'a sufficiently long password'}).status_code,503)
 def google_flow(self,address='google@example.invalid',sub='google-sub',nonce_bad=False):
  r=self.c.get('/api/account/google/start',follow_redirects=False);self.assertEqual(r.status_code,307,r.text);q=parse_qs(urlparse(r.headers['location']).query)
  claims={'aud':'test-client','iss':'https://accounts.google.com','exp':now()+3600,'nonce':'bad' if nonce_bad else q['nonce'][0],'sub':sub,'email':address,'email_verified':'true','name':'Google Test'}
  class Google:
   async def __aenter__(self):return self
   async def __aexit__(self,*a):pass
   async def post(self,url,**kw):return httpx.Response(200,json={'id_token':'verified-via-google'},request=httpx.Request('POST',url))
   async def get(self,url,**kw):return httpx.Response(200,json=claims,request=httpx.Request('GET',url))
  with patch('app.accounts.httpx.AsyncClient',lambda **kw:Google()),patch('app.accounts.verify_google_token',return_value=claims):r=self.c.get('/api/account/google/callback',params={'state':q['state'][0],'code':'test-code'},follow_redirects=False)
  return r,q
 def test_google_state_nonce_no_silent_email_merge_and_explicit_link(self):
  with patch.dict('os.environ',{'GOOGLE_CLIENT_ID':'test-client','GOOGLE_CLIENT_SECRET':'test-only'}):
   self.assertEqual(self.c.get('/api/account/google/callback?state=bad&code=bad').status_code,400)
   r,_=self.google_flow(nonce_bad=True);self.assertEqual(r.status_code,400)
   r,q=self.google_flow();self.assertEqual(r.status_code,303,r.text)
   self.assertEqual(self.c.get('/api/account/session').json()['email'],'google@example.invalid')
   self.assertEqual(self.c.get('/api/account/google/callback',params={'state':q['state'][0],'code':'replay'}).status_code,400)
   self.c.cookies.clear();data,user=self.verify('existing@example.invalid');self.c.post('/api/account/logout',json={})
   r,_=self.google_flow('existing@example.invalid','second-sub');self.assertEqual(r.status_code,409)
   self.c.post('/api/account/login',json=data);r,_=self.google_flow('existing@example.invalid','second-sub');self.assertEqual(r.status_code,303,r.text)
 def test_ai_checkout_cannot_bypass_customer_login(self):
  with patch.dict('os.environ',{'AI_SALES_ENABLED':'true','AI_STANDARD_SALES_ENABLED':'true','OPENAI_API_KEY':'test-only'}),patch('app.sales.generate_reply',new_callable=AsyncMock,return_value=Reply(reply='Ready',reply_language='en',brief='Business landing page with a WhatsApp enquiry link',recommended_plan='essential',qualified=True,needs_custom=False)):
   s=self.c.post('/api/sales/sessions',json={'language':'en','consent':True}).json();h={'Authorization':'Bearer '+s['token']};self.c.post('/api/sales/sessions/'+s['id']+'/message',headers=h,json={'text':'Business landing page RM1000 standard scope','nonce':secrets.token_hex(16)})
   endpoint='/api/sales/sessions/'+s['id']+'/order';body={'name':'Customer','email':'customer@example.invalid','phone':'+60123456789','method':'bank','accept_standard':True,'consent':True,'policy_version':VERSION}
   self.assertEqual(self.c.post(endpoint,headers=h,json=body).status_code,401)
   self.verify();r=self.c.post(endpoint,headers=h,json=body);self.assertEqual(r.status_code,200,r.text);self.assertEqual(self.c.get('/api/account/orders').json()['orders'][0]['id'],r.json()['id'])
   self.c.cookies.clear();self.assertEqual(self.c.post(endpoint,headers=h,json=body).status_code,401)

for name in list(fixtures.OrdersTest.__dict__):
 if name.startswith('test_') and name not in AccountTest.__dict__:setattr(AccountTest,name,None)
