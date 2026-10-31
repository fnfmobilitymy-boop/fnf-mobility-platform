"""Verified project receipts, in integer MYR cents and Malaysia calendar time."""
from datetime import datetime, timedelta, timezone

MYT = timezone(timedelta(hours=8))
METHODS = ('stripe', 'bank', 'tng', 'usdt')

def revenue_report(c, timestamp):
 current = datetime.fromtimestamp(timestamp, MYT)
 today = current.replace(hour=0, minute=0, second=0, microsecond=0)
 month = today.replace(day=1)
 year = month.replace(month=1)
 first_month_index = current.year * 12 + current.month - 1 - 11
 first_month = datetime(first_month_index // 12, first_month_index % 12 + 1, 1, tzinfo=MYT)
 end = timestamp + 1
 def totals(start=0):
  row = c.execute("SELECT coalesce(sum(base),0) revenue,coalesce(sum(total),0) collected,coalesce(sum(fee),0) customer_fees,count(*) payments FROM stages WHERE status='paid' AND paid>=? AND paid<?", (start, end)).fetchone()
  return dict(row)
 lifetime = totals()
 unpaid = c.execute("SELECT coalesce(sum(base),0) FROM stages WHERE status!='paid'").fetchone()[0]
 periods = {}
 for key, start, monthly in [('month', month, False), ('30days', today-timedelta(days=29), False), ('12months', first_month, True)]:
  start_ts = int(start.timestamp())
  fmt = '%Y-%m' if monthly else '%Y-%m-%d'
  grouped = {r['bucket']:dict(r) for r in c.execute("SELECT strftime(?,paid,'unixepoch','+8 hours') bucket,sum(base) revenue,count(*) payments FROM stages WHERE status='paid' AND paid>=? AND paid<? GROUP BY bucket", (fmt, start_ts, end))}
  buckets = []
  cursor = start
  while cursor <= today:
   label = cursor.strftime(fmt)
   buckets.append({'label':label, 'revenue':grouped.get(label,{}).get('revenue',0), 'payments':grouped.get(label,{}).get('payments',0)})
   if monthly:
    index = cursor.year*12+cursor.month
    cursor = cursor.replace(year=index//12,month=index%12+1)
   else: cursor += timedelta(days=1)
  breakdown = [dict(r) for r in c.execute("SELECT method,sum(base) revenue,count(*) payments FROM stages WHERE status='paid' AND paid>=? AND paid<? GROUP BY method ORDER BY revenue DESC,method",(start_ts,end))]
  recent = [dict(r) for r in c.execute("SELECT o.id order_id,o.public_no,o.name customer,s.phase,s.method,s.base,s.fee,s.total,s.paid FROM stages s JOIN orders o ON o.id=s.order_id WHERE s.status='paid' AND s.paid>=? AND s.paid<? ORDER BY s.paid DESC,s.id DESC LIMIT 20",(start_ts,end))]
  periods[key] = {'start':start.date().isoformat(), 'end':today.date().isoformat(), 'summary':totals(start_ts), 'buckets':buckets, 'methods':breakdown, 'recent':recent}
 return {'currency':'MYR','timezone':'Asia/Kuala_Lumpur','today':totals(int(today.timestamp())), 'month':totals(int(month.timestamp())), 'year':totals(int(year.timestamp())), 'lifetime':lifetime,'outstanding':unpaid,'periods':periods}
