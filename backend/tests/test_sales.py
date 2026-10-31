import test_orders as fixtures
from unittest.mock import patch,AsyncMock
from app.sales import Reply
from policy import VERSION
import secrets
class SalesTest(fixtures.OrdersTest):
 # Inherit the established DB/auth fixture, not its test methods.
 def answer(self,custom=False):return Reply(reply='Puedo ayudarte. Revisemos el alcance antes de pagar.',reply_language='es',brief='顾客经营培训中心，希望英文落地页用于 WhatsApp 咨询。预算 RM1000，有文字与图片，无参考网站，不要求额外后台；排期待确认。',recommended_plan='essential',qualified=not custom,needs_custom=custom)
 def start(self):
  r=self.c.post('/api/sales/sessions',json={'language':'zh','consent':True});self.assertEqual(r.status_code,200,r.text);s=r.json();s['headers']={'Authorization':'Bearer '+s['token']};return s
 def send(self,s,nonce=None):return self.c.post('/api/sales/sessions/'+s['id']+'/message',headers=s['headers'],json={'text':'I need an English training centre landing page, budget RM1000, no custom features.','nonce':nonce or secrets.token_hex(16)})
 def checkout(self,s,**extra):return self.c.post('/api/sales/sessions/'+s['id']+'/order',headers=s['headers'],json={'name':'QA AI CUSTOMER','email':'ai@example.invalid','phone':'+60123456789','business':'QA TRAINING','method':'bank','accept_standard':True,'consent':True,'policy_version':VERSION,**extra})
 def test_sales_disabled_without_keys(self):
  with patch.dict('os.environ',{'AI_SALES_ENABLED':'true','OPENAI_API_KEY':''}):
   self.assertFalse(self.c.get('/api/sales/config').json()['enabled']);self.assertEqual(self.c.post('/api/sales/sessions',json={'consent':True}).status_code,503)
 def test_sales_private_multilingual_idempotent_standard_close(self):
  with patch.dict('os.environ',{'AI_SALES_ENABLED':'true','AI_STANDARD_SALES_ENABLED':'true','OPENAI_API_KEY':'fixture-not-real'}),patch('app.sales.generate_reply',new_callable=AsyncMock,return_value=self.answer()) as model:
   self.assertNotIn('fixture-not-real',self.c.get('/api/sales/config').text)
   s=self.start();nonce=secrets.token_hex(16);r=self.send(s,nonce);self.assertEqual(r.status_code,200,r.text);self.assertEqual(r.json()['reply_language'],'es');self.assertTrue(r.json()['can_standard_checkout']);self.assertEqual(self.send(s,nonce).status_code,200);self.assertEqual(model.await_count,1)
   self.assertIn('Never claim to have inspected a URL',model.call_args.args[1]['input'][0]['content']);self.assertFalse(model.call_args.args[1]['store'])
   other=self.start();self.assertEqual(self.c.get('/api/sales/sessions/'+s['id'],headers=other['headers']).status_code,404)
   self.assertEqual(self.c.get('/api/admin/sales').status_code,401)
   bad=self.checkout(s,amount='1');self.assertEqual(bad.status_code,422)
   r=self.checkout(s);self.assertEqual(r.status_code,200,r.text);o=r.json();o['headers']={'Authorization':'Bearer '+o['token']};order=self.get(o);self.assertEqual(order['quote'],100000);self.assertEqual(order['status'],'quoted');self.assertEqual([x['base'] for x in order['stages']],[50000,30000,20000]);self.assertEqual([x['status'] for x in order['stages']],['open','locked','locked']);self.assertEqual(len(order['documents']),3);self.assertEqual(self.checkout(s).json()['id'],o['id'])
   self.owner();inbox=self.c.get('/api/admin/tools').json();self.assertEqual(inbox['sales'][0]['brief'],self.answer().brief);self.assertEqual(len(self.c.get('/api/admin/sales/'+s['id']).json()['messages']),2)
   with self.db.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],1)
 def test_sales_custom_requires_owner_quote_and_provider_failure_is_safe(self):
  with patch.dict('os.environ',{'AI_SALES_ENABLED':'true','AI_STANDARD_SALES_ENABLED':'true','OPENAI_API_KEY':'fixture-not-real'}),patch('app.sales.generate_reply',new_callable=AsyncMock,return_value=self.answer(True)):
   s=self.start();self.assertEqual(self.send(s).status_code,200);self.assertEqual(self.checkout(s).status_code,409);r=self.checkout(s,accept_standard=False);self.assertEqual(r.status_code,200);o=r.json();o['headers']={'Authorization':'Bearer '+o['token']};self.assertEqual(self.get(o)['status'],'requested');self.assertEqual(self.get(o)['documents'],[])
  with patch.dict('os.environ',{'AI_SALES_ENABLED':'true','OPENAI_API_KEY':'fixture-not-real'}),patch('app.sales.generate_reply',new_callable=AsyncMock,side_effect=ValueError('provider refusal')):
   s=self.start();self.assertEqual(self.send(s).status_code,503)
   with self.db.connect() as c:self.assertEqual(c.execute('SELECT busy_until FROM sales_sessions WHERE id=?',(s['id'],)).fetchone()[0],0)
 def test_unconfigured_whatsapp_never_sends(self):
  from app.notifications import deliver_once
  o=self.new()
  with patch.dict('os.environ',{'WHATSAPP_ACCESS_TOKEN':''}),patch('app.notifications.httpx.post') as send:
   deliver_once(self.db);send.assert_not_called()
# Keep only the new tests in this subclass; baseline is executed from test_orders.py.
for name in list(fixtures.OrdersTest.__dict__):
 if name.startswith('test_') and name not in SalesTest.__dict__:setattr(SalesTest,name,None)
