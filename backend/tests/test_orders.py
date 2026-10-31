import unittest,tempfile,secrets,json,hmac,hashlib,sys
from pathlib import Path
from io import BytesIO
from PIL import Image
import asyncio,httpx
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.main import create_app
from app.core import Settings,pw_hash,now,split_amount
async def inline_worker(fn,*args,**kwargs):return fn(*args)
class TestClient:
 """In-process ASGI adapter: the execution sandbox cannot wake worker threads via sockets."""
 def __init__(self,app):
  self.runner=asyncio.Runner();self.client=httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://testserver');self.cookies=self.client.cookies
 def get(self,url,**kwargs):return self.runner.run(self.client.get(url,**kwargs))
 def post(self,url,**kwargs):return self.runner.run(self.client.post(url,**kwargs))
 def close(self):self.runner.run(self.client.aclose());self.runner.close()
class OrdersTest(unittest.TestCase):
 def setUp(self):
  self.patch=patch('anyio.to_thread.run_sync',inline_worker);self.patch.start();self.tmp=tempfile.TemporaryDirectory();self.password=secrets.token_urlsafe(20);self.cfg=Settings(data=Path(self.tmp.name),secret=secrets.token_urlsafe(40),admin_hash=pw_hash(self.password),public_url='http://testserver',stripe_key='sk_test_fixture',webhook_secret='whsec_fixture');self.app=create_app(self.cfg);self.c=TestClient(self.app);self.db=self.app.state.db
 def tearDown(self):self.c.close();self.tmp.cleanup();self.patch.stop()
 def new(self,method='bank',extra=None):
  data={'items':[{'id':'essential','qty':1}],'name':'Client 测试','email':'qa@example.invalid','phone':'+60123456789','business':'Training centre','requirements':'Business website with gallery and enquiry form.','method':method,'language':'zh','consent':True,'idempotency':secrets.token_hex(32)}
  if extra:data.update(extra)
  r=self.c.post('/api/orders',json=data);self.assertEqual(r.status_code,201,r.text);o=r.json();o['payload']=data;o['headers']={'Authorization':'Bearer '+o['token']};return o
 def owner(self):
  r=self.c.post('/api/admin/login',json={'email':self.cfg.admin_email,'password':self.password});self.assertEqual(r.status_code,200,r.text);return {'X-CSRF-Token':r.json()['csrf']}
 def quote(self,o,method='bank'):
  h=self.owner();r=self.c.post('/api/admin/orders/'+o['id']+'/quote',headers=h,json={'version':1,'amount':'1000.01','scope':'Confirmed 1-page website with up to 6 sections and 2 revisions.','method':method,'usdt':['100','60','40'] if method=='usdt' else []});self.assertEqual(r.status_code,200,r.text);return h
 def get(self,o):return self.c.get('/api/orders/'+o['id'],headers=o['headers']).json()
 def test_server_catalogue_and_private_access(self):
  self.assertEqual(len(self.c.get('/api/catalogue').json()['items']),30)
  o=self.new(extra={'items':[{'id':'essential','qty':1},{'id':'addon-6','qty':2},{'id':'addon-8','qty':5}]});self.assertEqual(self.get(o)['estimate'],190000)
  self.assertEqual(self.c.get('/api/orders/'+o['id']).status_code,404)
  r=self.c.post('/api/orders',json={**o['payload'],'amount':'0.01'});self.assertEqual(r.status_code,422)
  self.assertEqual(self.c.post('/api/orders',json=o['payload']).json()['id'],o['id'])
  self.assertEqual(self.c.get('/api/admin/orders').status_code,401)
 def test_quote_csrf_docs_and_stage_locks(self):
  o=self.new();h=self.owner();body={'version':1,'amount':'1000.01','scope':'A confirmed business website with agreed scope.','method':'bank'}
  self.assertEqual(self.c.post('/api/admin/orders/'+o['id']+'/quote',json=body).status_code,403)
  self.assertEqual(self.c.post('/api/admin/orders/'+o['id']+'/quote',json=body,headers=h).status_code,200)
  data=self.get(o);self.assertEqual(sum(s['base'] for s in data['stages']),100001);self.assertEqual([s['status'] for s in data['stages']],['open','locked','locked']);self.assertEqual(len(data['documents']),3)
  r=self.c.get('/api/documents/'+data['documents'][0]['id']);self.assertTrue(r.content.startswith(b'%PDF'))
  self.assertEqual(self.c.post('/api/admin/orders/'+o['id']+'/quote',json=body,headers=h).status_code,409)
  self.assertEqual(self.c.post('/api/admin/orders/'+o['id']+'/release',headers=h,json={'phase':'second','note':'Preview approved by customer'}).status_code,409)
 def test_manual_receipt_real_storage_not_auto_paid(self):
  o=self.new();h=self.quote(o);buf=BytesIO();Image.new('RGB',(32,32),'white').save(buf,format='PNG');png=buf.getvalue();url='/api/orders/'+o['id']+'/stages/deposit/receipt'
  self.assertEqual(self.c.post(url,headers=o['headers'],data={'reference':'BANK-TEST'},files={'file':('bad.png',b'<script>evil</script>','image/png')}).status_code,422)
  r=self.c.post(url,headers=o['headers'],data={'reference':'BANK-TEST'},files={'file':('proof.png',png,'image/png')});self.assertEqual(r.status_code,200,r.text);rid=r.json()['id'];self.assertEqual(r.json()['status'],'pending');self.assertEqual(self.get(o)['stages'][0]['status'],'open');self.assertEqual(len(self.get(o)['documents']),3)
  review='/api/admin/receipts/'+rid+'/review';self.assertEqual(self.c.post(review,headers=h,json={'approve':True,'note':'Amount and recipient checked','confirmed_received':False}).status_code,422)
  self.assertEqual(self.c.post(review,headers=h,json={'approve':True,'note':'Exact funds confirmed in receiving account','confirmed_received':True}).status_code,200)
  self.assertEqual(self.get(o)['stages'][0]['status'],'paid');self.assertEqual(len(self.get(o)['documents']),4)
  self.assertEqual(self.c.post(review,headers=h,json={'approve':True,'note':'Repeated payment attempt','confirmed_received':True}).status_code,409)
  self.assertEqual(self.c.post('/api/admin/orders/'+o['id']+'/release',headers=h,json={'phase':'second','note':'Customer accepted the development preview'}).status_code,200)
  self.assertEqual(self.get(o)['stages'][1]['status'],'open')
  self.c.cookies.clear();self.assertEqual(self.c.get('/api/receipts/'+rid).status_code,404);self.assertEqual(self.c.get('/api/receipts/'+rid,headers=o['headers']).content,png)
  o2=self.new();self.assertEqual(self.c.get('/api/receipts/'+rid,headers=o2['headers']).status_code,404)
 def event(self,o,amount=53001,currency='myr',eid=None):
  stage=self.get(o)['stages'][0]
  with self.db.transaction() as c:c.execute('INSERT OR IGNORE INTO checkout(stage_id,session_id,url,created) VALUES(?,?,?,?)',(stage['id'],'cs_fixture','https://checkout.stripe.com/test',now()))
  return {'id':eid or 'evt_'+secrets.token_hex(8),'type':'checkout.session.completed','data':{'object':{'id':'cs_fixture','metadata':{'order_id':o['id'],'stage_id':stage['id']},'payment_status':'paid','currency':currency,'amount_total':amount,'livemode':False,'payment_intent':'pi_fixture'}}}
 def send_event(self,event,valid=True):
  body=json.dumps(event).encode();timestamp=str(now());sig=hmac.new(self.cfg.webhook_secret.encode(),timestamp.encode()+b'.'+body,hashlib.sha256).hexdigest();return self.c.post('/api/stripe/webhook',content=body,headers={'Stripe-Signature':'t='+timestamp+',v1='+(sig if valid else 'invalid'),'Content-Type':'application/json'})
 def test_stripe_signature_amount_currency_and_replay(self):
  o=self.new('stripe');self.quote(o,'stripe');stage=self.get(o)['stages'][0];self.assertEqual(stage['base'],50001);self.assertEqual(stage['fee'],3000);self.assertEqual(stage['total'],53001)
  self.assertEqual(self.send_event(self.event(o),False).status_code,400)
  self.assertEqual(self.send_event(self.event(o,amount=1)).status_code,409)
  self.assertEqual(self.send_event(self.event(o,currency='usd')).status_code,409)
  self.assertEqual(self.get(o)['stages'][0]['status'],'open')
  event=self.event(o);self.assertEqual(self.send_event(event).status_code,200);self.assertEqual(self.send_event(event).status_code,200);self.assertEqual(self.get(o)['stages'][0]['status'],'paid');self.assertEqual(len(self.get(o)['documents']),4)
 def test_persistence_and_file_auth(self):
  o=self.new();self.quote(o);app2=create_app(self.cfg);other=TestClient(app2);self.assertEqual(other.get('/api/orders/'+o['id'],headers=o['headers']).json()['status'],'quoted');other.close()
  self.assertEqual(self.c.post('/api/admin/login',json={'email':self.cfg.admin_email,'password':'wrong-password'}).status_code,401)
 def test_server_stripe_checkout_has_exact_amount(self):
  o=self.new('stripe');self.quote(o,'stripe');captured={}
  class FakeStripe:
   async def __aenter__(self):return self
   async def __aexit__(self,*args):pass
   async def post(self,url,**kwargs):
    captured.update(kwargs);return httpx.Response(200,json={'id':'cs_created','url':'https://checkout.stripe.com/test_fixture','expires_at':now()+3600})
  with patch('app.main.httpx.AsyncClient',lambda **kwargs:FakeStripe()):
   r=self.c.post('/api/orders/'+o['id']+'/stages/deposit/checkout',headers=o['headers'],json={'amount':1});self.assertEqual(r.status_code,200,r.text)
  self.assertEqual(captured['data']['line_items[0][price_data][unit_amount]'],'50001');self.assertEqual(captured['data']['line_items[1][price_data][unit_amount]'],'3000');self.assertEqual(self.get(o)['stages'][0]['status'],'open')
 def test_missing_stripe_credentials_and_large_body(self):
  o=self.new('stripe');self.quote(o,'stripe');self.cfg.stripe_key=''
  r=self.c.post('/api/orders/'+o['id']+'/stages/deposit/checkout',headers=o['headers']);self.assertEqual(r.status_code,503)
  r=self.c.post('/api/orders',content=b'{}',headers={'Content-Type':'application/json','Content-Length':str(13*1024*1024)});self.assertEqual(r.status_code,413)
 def test_usdt_is_not_a_guessed_conversion(self):
  o=self.new('usdt');self.quote(o,'usdt');s=self.get(o)['stages'][0];self.assertEqual(s['usdt'],'100');self.assertEqual(s['fee'],0)
  buf=BytesIO();Image.new('RGB',(16,16),'white').save(buf,format='PNG')
  r=self.c.post('/api/orders/'+o['id']+'/stages/deposit/receipt',headers=o['headers'],data={'reference':'not-a-tron-hash'},files={'file':('proof.png',buf.getvalue(),'image/png')});self.assertEqual(r.status_code,422)
 def test_static_assets_and_session_cookie(self):
  r=self.c.get('/');self.assertEqual(r.status_code,200);self.assertIn('Kenny Studio',r.text)
  for name in ['app.js','style.css','manrope.ttf','payments/stripe.svg']:self.assertEqual(self.c.get('/static/'+name).status_code,200,name)
  r=self.c.post('/api/admin/login',json={'email':self.cfg.admin_email,'password':self.password});self.assertIn('HttpOnly',r.headers['set-cookie']);self.assertIn('SameSite=strict',r.headers['set-cookie']);self.assertEqual(r.headers['x-robots-tag'],'noindex, nofollow')
 def test_test_mode_never_accepts_real_payments(self):
  self.cfg.test_mode=True;o=self.new('stripe');self.quote(o,'stripe');data=self.get(o)
  self.assertIsNone(data['paymentDetails']);self.assertFalse(data['stripeReady']);self.assertTrue(self.c.get('/api/config').json()['testMode'])
  self.assertEqual(self.c.post('/api/orders/'+o['id']+'/stages/deposit/checkout',headers=o['headers']).status_code,403)
  self.assertEqual(self.send_event(self.event(o)).status_code,403)
  pdf=self.c.get('/api/documents/'+data['documents'][0]['id']).content;self.assertTrue(pdf.startswith(b'%PDF'))
 def test_rounding(self):
  for total in range(10000,10100):self.assertEqual(sum(v for v,fee in split_amount(total,'stripe')),total)
if __name__=='__main__':unittest.main()
