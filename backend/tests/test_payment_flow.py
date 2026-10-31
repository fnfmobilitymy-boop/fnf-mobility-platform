"""Payment acceptance checks against the real application with isolated provider fixtures."""
import test_orders as fixtures
import secrets,httpx
from unittest.mock import patch
from app.core import now

class PaymentFlowTest(fixtures.OrdersTest):
 def linked_order(self):
  data={'items':[{'id':'essential','qty':1}],'name':'PAYMENT ACCEPTANCE','email':'qa@example.invalid','phone':'+60123456789','requirements':'Payment acceptance fixture only; no real payment.','method':'stripe','language':'en','consent':True,'idempotency':secrets.token_hex(32)}
  r=self.c.post('/api/orders',json=data);self.assertEqual(r.status_code,201,r.text);return r.json()
 def test_all_three_stages_owned_order_stripe_fee_and_receipts(self):
  o=self.linked_order();h=self.owner();r=self.c.post('/api/admin/orders/'+o['id']+'/quote',headers=h,json={'version':1,'amount':'1000.00','scope':'Confirmed test scope for isolated payment acceptance.','method':'stripe'});self.assertEqual(r.status_code,200,r.text)
  phases=['deposit','second','balance'];charges=[53000,31800,21200];created=[]
  class Stripe:
   async def __aenter__(self):return self
   async def __aexit__(self,*a):pass
   async def post(self,url,**kw):
    created.append(kw);ident='cs_acceptance_'+str(len(created));return httpx.Response(200,json={'id':ident,'url':'https://checkout.stripe.com/'+ident,'expires_at':now()+3600})
  for i,phase in enumerate(phases):
   stages=self.c.get('/api/orders/'+o['id']).json()['stages'];stage=next(s for s in stages if s['phase']==phase)
   if i:
    self.assertEqual(self.c.post('/api/orders/'+o['id']+'/stages/'+phase+'/checkout',json={}).status_code,409)
    self.assertEqual(self.c.post('/api/admin/orders/'+o['id']+'/release',headers=h,json={'phase':phase,'note':'Previous payment verified; milestone accepted.'}).status_code,200)
   endpoint='/api/orders/'+o['id']+'/stages/'+phase+'/checkout'
   with patch('app.main.httpx.AsyncClient',lambda **kw:Stripe()):
    r=self.c.post(endpoint,json={});self.assertEqual(r.status_code,200,r.text);self.assertEqual(self.c.post(endpoint,json={}).json()['url'],r.json()['url'])
   self.assertEqual(len(created),i+1);payload=created[-1]['data'];self.assertEqual(int(payload['line_items[0][price_data][unit_amount]'])+int(payload['line_items[1][price_data][unit_amount]']),charges[i])
   event={'id':'evt_acceptance_'+str(i),'type':'checkout.session.completed','data':{'object':{'id':'cs_acceptance_'+str(i+1),'metadata':{'order_id':o['id'],'stage_id':stage['id']},'payment_status':'unpaid','currency':'myr','amount_total':charges[i],'livemode':False,'payment_intent':'pi_acceptance_'+str(i)}}}
   self.assertEqual(self.send_event(event).status_code,200);self.assertEqual(next(s for s in self.c.get('/api/orders/'+o['id']).json()['stages'] if s['phase']==phase)['status'],'open')
   event['data']['object']['payment_status']='paid'
   self.assertEqual(self.send_event(event,False).status_code,400)
   for field,value in [('amount_total',1),('currency','usd'),('livemode',True),('id','cs_other')]:
    obj=event['data']['object'];old=obj[field];obj[field]=value;self.assertEqual(self.send_event(event).status_code,409);obj[field]=old
   self.assertEqual(self.send_event(event).status_code,200);self.assertEqual(self.send_event(event).status_code,200)
   snapshot=self.c.get('/api/orders/'+o['id']).json();receipts=[d for d in snapshot['documents'] if d['kind']=='receipt'];self.assertEqual(len(receipts),i+1)
   doc=receipts[-1];self.assertTrue(self.c.get('/api/documents/'+doc['id']).content.startswith(b'%PDF'))
   anonymous=fixtures.TestClient(self.app)
   try:self.assertEqual(anonymous.get('/api/documents/'+doc['id']).status_code,401)
   finally:anonymous.close()
  final=self.c.get('/api/orders/'+o['id']).json();self.assertEqual(final['status'],'completed');self.assertEqual([s['status'] for s in final['stages']],['paid']*3);self.assertEqual(sum(s['fee'] for s in final['stages']),6000);self.assertEqual(len(final['documents']),6)
 def test_expired_session_already_paid_prevents_another_checkout(self):
  o=self.linked_order();self.quote(o,'stripe');stage=self.c.get('/api/orders/'+o['id']).json()['stages'][0]
  with self.db.transaction() as c:c.execute('INSERT INTO checkout VALUES(?,?,?,?,?,?)',(stage['id'],'cs_old','https://checkout.stripe.com/old',now()-4000,now()-1,1))
  class Stripe:
   async def __aenter__(self):return self
   async def __aexit__(self,*a):pass
   async def get(self,*a,**kw):return httpx.Response(200,json={'status':'complete','payment_status':'paid'})
   async def post(self,*a,**kw):raise AssertionError('Never create a second payment while a paid session awaits its webhook')
  with patch('app.main.httpx.AsyncClient',lambda **kw:Stripe()):r=self.c.post('/api/orders/'+o['id']+'/stages/deposit/checkout',json={});self.assertEqual(r.status_code,409,r.text)
  self.assertEqual(self.c.get('/api/orders/'+o['id']).json()['stages'][0]['status'],'open')

for name in list(fixtures.OrdersTest.__dict__):
 if name.startswith('test_') and name not in PaymentFlowTest.__dict__:setattr(PaymentFlowTest,name,None)
