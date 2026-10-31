"""Declared and billing country metadata; not an IP-location or identity guarantee."""
import json
from pathlib import Path
COUNTRIES=json.loads((Path(__file__).resolve().parents[1]/'static/countries.json').read_text())
COUNTRY_CODES={code for code,_ in COUNTRIES}
def order_country(c,oid):
 r=c.execute('SELECT country_code,country_source FROM order_countries WHERE order_id=?',(oid,)).fetchone()
 if r:return dict(r)
 r=c.execute("SELECT p.country_code,'registration' country_source FROM customer_orders co JOIN customer_profiles p ON p.customer_id=co.customer_id WHERE co.order_id=?",(oid,)).fetchone()
 return dict(r) if r else {'country_code':'','country_source':''}
def order_overview(c,oid):
 r=dict(c.execute("SELECT count(*) stage_count,coalesce(sum(CASE WHEN status='paid' THEN 1 ELSE 0 END),0) paid_count,coalesce(sum(CASE WHEN status='paid' THEN base ELSE 0 END),0) paid_project_value,coalesce(sum(CASE WHEN status='open' THEN total ELSE 0 END),0) amount_due FROM stages WHERE order_id=?",(oid,)).fetchone())
 r['payment_status']='not_invoiced' if not r['stage_count'] else 'paid' if r['paid_count']==r['stage_count'] else 'partial' if r['paid_count'] else 'unpaid'
 return {**r,**order_country(c,oid)}
