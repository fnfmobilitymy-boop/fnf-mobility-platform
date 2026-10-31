import unittest, sqlite3
from datetime import datetime
from app.revenue import revenue_report, MYT

class RevenueTest(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');self.c.row_factory=sqlite3.Row
  self.c.executescript('CREATE TABLE orders(id TEXT,public_no TEXT,name TEXT);CREATE TABLE stages(id TEXT,order_id TEXT,phase TEXT,method TEXT,base INTEGER,fee INTEGER,total INTEGER,status TEXT,paid INTEGER);INSERT INTO orders VALUES("o","K-1","Customer");')
 def tearDown(self):self.c.close()
 def add(self,id,when,base=10001,fee=600,status='paid',method='stripe'):
  paid=int(datetime.fromisoformat(when).replace(tzinfo=MYT).timestamp()) if when else None
  self.c.execute('INSERT INTO stages VALUES(?,?,?,?,?,?,?,?,?)',(id,'o','deposit',method,base,fee,base+fee,status,paid))
 def test_malaysia_calendar_boundaries_zero_buckets_and_verified_only(self):
  self.add('old','2025-12-31T23:59:59');self.add('new','2026-01-01T00:00:00',20002,0,method='bank')
  self.add('pending',None,30003,0,status='open');self.add('locked',None,40004,0,status='locked')
  self.add('future','2026-01-02T00:00:00',50005)
  at=int(datetime(2026,1,1,0,15,tzinfo=MYT).timestamp());r=revenue_report(self.c,at)
  self.assertEqual(r['today']['revenue'],20002);self.assertEqual(r['month']['revenue'],20002);self.assertEqual(r['year']['revenue'],20002)
  self.assertEqual(r['lifetime'],{'revenue':30003,'collected':30603,'customer_fees':600,'payments':2})
  self.assertEqual(r['outstanding'],70007)
  self.assertEqual(len(r['periods']['30days']['buckets']),30);self.assertEqual(len(r['periods']['12months']['buckets']),12)
  self.assertEqual(r['periods']['12months']['buckets'][0]['label'],'2025-02')
  self.assertEqual(sum(b['revenue'] for b in r['periods']['12months']['buckets']),30003)
  self.assertEqual(r['periods']['month']['methods'],[{'method':'bank','revenue':20002,'payments':1}])
  self.assertEqual([v['method'] for v in r['periods']['month']['recent']],['bank'])
 def test_empty_report_and_usdt_book_value(self):
  at=int(datetime(2026,3,1,12,tzinfo=MYT).timestamp());r=revenue_report(self.c,at)
  self.assertEqual(r['lifetime']['revenue'],0);self.assertEqual(r['periods']['month']['buckets'],[{'label':'2026-03-01','revenue':0,'payments':0}])
  self.add('crypto','2026-02-28T19:30:00',12345,0,method='usdt')
  r=revenue_report(self.c,at);self.assertEqual(r['lifetime']['revenue'],12345);self.assertEqual(r['month']['revenue'],0)
  self.assertEqual(r['periods']['30days']['methods'][0]['method'],'usdt')
