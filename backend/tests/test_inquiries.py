import test_orders as fixtures
from unittest.mock import patch
import secrets

class InquiryTest(fixtures.OrdersTest):
 def payload(self):return {'name':'咨询顾客','phone':'+60 12-345 6789','service':'business','message':'I need a company website with an enquiry form.','language':'zh','idempotency':secrets.token_hex(32)}
 def test_real_save_private_inbox_confirmation_and_idempotent_retry(self):
  self.c.cookies.clear();p=self.payload();r=self.c.post('/api/inquiries',json=p,headers={'Origin':'https://kennystudio.cfd'});self.assertEqual(r.status_code,201,r.text);saved=r.json();self.assertTrue(saved['saved'])
  with self.db.connect() as c:
   row=c.execute('SELECT * FROM inquiries WHERE id=?',(saved['reference'],)).fetchone();self.assertEqual(row['phone'],p['phone']);self.assertEqual(row['message'],p['message'])
   self.assertEqual(c.execute("SELECT count(*) FROM outbox WHERE subject LIKE 'New website enquiry%'").fetchone()[0],1)
  confirmation=self.c.get('/api/inquiries/confirmation',params={'receipt':saved['receipt']});self.assertEqual(confirmation.status_code,200);self.assertEqual(confirmation.json(),{'verified':True,'reference':saved['reference']})
  self.assertEqual(self.c.get('/api/inquiries/confirmation',params={'receipt':saved['receipt']+'x'}).status_code,404)
  replay=self.c.post('/api/inquiries',json=p);self.assertEqual(replay.status_code,200);self.assertEqual(replay.json()['reference'],saved['reference'])
  self.assertEqual(self.c.post('/api/inquiries',json={**p,'message':'Changed project details beyond the original request.'}).status_code,409)
  self.assertEqual(self.c.get('/api/admin/inquiries').status_code,401);self.owner();self.assertEqual(self.c.get('/api/admin/inquiries').json()['inquiries'][0]['name'],p['name']);self.assertEqual(self.c.get('/api/admin/tools').json()['inquiries'][0]['id'],saved['reference'])
  with self.db.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM inquiries').fetchone()[0],1)
 def test_invalid_origin_fields_and_rate_limit_never_report_success(self):
  p=self.payload();self.assertEqual(self.c.post('/api/inquiries',json=p,headers={'Origin':'https://untrusted.invalid'}).status_code,403)
  preflight=self.c.client # fixture exposes the underlying AsyncClient, so use its runner for OPTIONS
  r=self.c.runner.run(preflight.options('/api/inquiries',headers={'Origin':'https://kennystudio.cfd','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type'}));self.assertEqual(r.headers.get('access-control-allow-origin'),'https://kennystudio.cfd')
  for change in [{'phone':'invalid'},{'name':'   '},{'message':'   too  '},{'service':'invalid'},{'website':'spam.invalid'}]:self.assertEqual(self.c.post('/api/inquiries',json={**p,**change}).status_code,422)
  for _ in range(5):self.assertEqual(self.c.post('/api/inquiries',json=self.payload()).status_code,201)
  self.assertEqual(self.c.post('/api/inquiries',json=self.payload()).status_code,429)
 def test_storage_transaction_failure_does_not_confirm_or_leave_partial_record(self):
  with patch('app.inquiries.queue',side_effect=RuntimeError('fixture storage failure')):
   with self.assertRaises(Exception):self.c.post('/api/inquiries',json=self.payload())
  with self.db.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM inquiries').fetchone()[0],0)

for name in list(fixtures.OrdersTest.__dict__):
 if name.startswith('test_') and name not in InquiryTest.__dict__:setattr(InquiryTest,name,None)
