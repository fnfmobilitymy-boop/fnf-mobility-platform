"""New owner-approved prices and legacy signed-quote payment compatibility."""
import test_orders as fixtures
from app.core import split_amount
from unittest.mock import patch
from pricing import PLANS
class PriceRevisionTest(fixtures.OrdersTest):
 def test_all_package_prices_and_optional_maintenance(self):
  expected={'essential':(999,199),'personal':(1299,299),'business':(1888,398),'booking':(2488,398),'ecommerce':(2888,598),'signature':(4999,698),'booking-backend':(4888,698),'membership':(5888,798),'admin-dashboard':(6888,898),'crm':(7888,998),'saas':(12888,1288)}
  for lang in ('en','zh','ms'):
   items={p['id']:p for p in self.c.get('/api/catalogue?language='+lang).json()['items']}
   self.assertEqual(len(items),48)
   for id,(price,monthly) in expected.items():
    self.assertEqual((items[id]['price'],items[id]['monthly']),(price,monthly))
    self.assertEqual(items['maintenance-'+id]['price'],monthly)
  o=self.new();self.assertEqual(self.get(o)['estimate'],99900);self.assertEqual(len(self.get(o)['items']),1)
 def test_starting_price_cannot_be_auto_closed(self):
  from policy import VERSION
  with patch.dict('os.environ',{'AI_STANDARD_SALES_ENABLED':'true'}):
   # The fixed-price package can close, while every custom starting price must be quoted.
   for plan in PLANS:
    if plan['starting']:
     self.customer_login()
     import secrets
     r=self.c.post('/api/orders',json={'items':[{'id':plan['id'],'qty':1}],'name':'QA','email':'qa@example.invalid','phone':'123456','requirements':'Custom feature scope pending written quote','method':'bank','language':'en','consent':True,'idempotency':secrets.token_hex(32),'standard_order':True,'policy_version':VERSION})
     self.assertEqual(r.status_code,422)
 def test_rounding_and_two_stage_release(self):
  self.assertEqual(split_amount(99900,'bank'),[(49950,0),(49950,0)])
  self.assertEqual(sum(v for v,_ in split_amount(100001,'stripe')),100001)
  o=self.new();h=self.quote(o);data=self.get(o)
  self.assertEqual([s['phase'] for s in data['stages']],['deposit','balance'])
  self.assertEqual([s['base'] for s in data['stages']],[50001,50000])
  self.assertEqual(self.c.post('/api/admin/orders/'+o['id']+'/release',headers=h,json={'phase':'balance','note':'Project completed'}).status_code,409)
  with self.db.transaction() as c:c.execute("UPDATE stages SET status='paid' WHERE order_id=? AND phase='deposit'",(o['id'],))
  self.assertEqual(self.c.post('/api/admin/orders/'+o['id']+'/release',headers=h,json={'phase':'balance','note':'Project completed'}).status_code,200)
 def test_legacy_three_stage_quote_stays_payable(self):
  o=self.new();h=self.quote(o)
  with self.db.transaction() as c:
   c.execute("UPDATE stages SET status='paid',base=50000,total=50000 WHERE order_id=? AND phase='deposit'",(o['id'],))
   c.execute("UPDATE stages SET base=20001,total=20001 WHERE order_id=? AND phase='balance'",(o['id'],))
   c.execute("INSERT INTO stages(id,order_id,phase,base,fee,total,method,status) VALUES('legacy-second',?,'second',30000,0,30000,'bank','locked')",(o['id'],))
  self.assertEqual(self.c.post('/api/admin/orders/'+o['id']+'/release',headers=h,json={'phase':'balance','note':'Must wait for second'}).status_code,409)
  self.assertEqual(self.c.post('/api/admin/orders/'+o['id']+'/release',headers=h,json={'phase':'second','note':'Old preview approved'}).status_code,200)
  with self.db.transaction() as c:c.execute("UPDATE stages SET status='paid' WHERE id='legacy-second'")
  self.assertEqual(self.c.post('/api/admin/orders/'+o['id']+'/release',headers=h,json={'phase':'balance','note':'Old acceptance complete'}).status_code,200)
  self.assertEqual([s['base'] for s in self.get(o)['stages']],[50000,30000,20001])
for name in fixtures.OrdersTest.__dict__:
 if name.startswith('test_'):setattr(PriceRevisionTest,name,None)
