"""Owner-only project operations. Internal data is never added to customer responses."""
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
import csv, io, json, zipfile
from fastapi import Depends
from fastapi.responses import Response, FileResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal
from .core import now
from .db import audit
from .countries import order_country,order_overview
from .revenue import revenue_report

class ToolInput(BaseModel):model_config=ConfigDict(extra='forbid')
class ProjectPlan(ToolInput):
 version:int=Field(ge=0)
 delivery:Literal['planning','building','review','delivered','on_hold']='planning'
 priority:Literal['normal','high','urgent']='normal'
 due_date:str=''
 @field_validator('due_date')
 @classmethod
 def valid_date(cls,value):
  if value and (len(value)!=10 or date.fromisoformat(value).isoformat()!=value):raise ValueError('Use YYYY-MM-DD')
  return value
class NoteInput(ToolInput):body:str=Field(min_length=1,max_length=4000)
class TaskInput(ToolInput):
 order_id:str=Field(min_length=1,max_length=64)
 title:str=Field(min_length=1,max_length=200)
 due_date:str=''
 _date=field_validator('due_date')(ProjectPlan.valid_date.__func__)
class TaskUpdate(ToolInput):done:bool;version:int=Field(ge=1)

def local_today():return datetime.now(timezone(timedelta(hours=8))).date().isoformat()
def csv_cell(value):
 text=str(value if value is not None else '')
 return "'"+text if text.lstrip().startswith(('=','+','-','@','\t','\r')) or text.startswith(('\t','\r','\n')) else text

def install_admin_tools(app,db,cfg,admin,order,fail):
 @app.get('/api/admin/tools')
 def tools(actor=Depends(admin)):
  with db.connect() as c:
   contracts=c.execute('SELECT coalesce(sum(quote),0) FROM orders WHERE quote IS NOT NULL').fetchone()[0]
   finance=dict(c.execute("SELECT coalesce(sum(CASE WHEN status='paid' THEN base ELSE 0 END),0) settled_project_value,coalesce(sum(CASE WHEN status!='paid' THEN base ELSE 0 END),0) outstanding_project_value,coalesce(sum(CASE WHEN status='paid' AND method='stripe' THEN fee ELSE 0 END),0) verified_stripe_fees,coalesce(sum(CASE WHEN status='open' THEN total ELSE 0 END),0) open_payments FROM stages").fetchone())
   finance['contract_value']=contracts
   receipts=[dict(r) for r in c.execute("SELECT r.id,r.order_id,r.stage_id,r.created,r.name,r.mime,r.reference,r.status,r.note,o.public_no,o.name customer,s.phase,s.total,s.method FROM receipts r JOIN orders o ON o.id=r.order_id JOIN stages s ON s.id=r.stage_id WHERE r.status='pending' ORDER BY r.created LIMIT 500")]
   tasks=[dict(r) for r in c.execute('SELECT t.*,o.public_no,o.name customer FROM project_tasks t JOIN orders o ON o.id=t.order_id ORDER BY t.done,CASE WHEN t.due_date=\'\' THEN 1 ELSE 0 END,t.due_date,t.created DESC LIMIT 500')]
   projects=[dict(r) for r in c.execute("SELECT o.id,o.public_no,o.name,o.status,coalesce(p.delivery,'planning') delivery,coalesce(p.priority,'normal') priority,coalesce(p.due_date,'') due_date FROM orders o LEFT JOIN project_plans p ON p.order_id=o.id ORDER BY CASE coalesce(p.priority,'normal') WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 ELSE 2 END,o.created DESC LIMIT 500")]
   clients=[dict(r) for r in c.execute('SELECT lower(email) email,count(*) orders,coalesce(sum(quote),0) contract_value,max(created) last_order FROM orders GROUP BY lower(email) ORDER BY last_order DESC LIMIT 500')]
   for client in clients:
    latest=c.execute('SELECT id,name,phone,business FROM orders WHERE lower(email)=? ORDER BY created DESC LIMIT 1',(client['email'],)).fetchone();client.update({k:latest[k] for k in ['name','phone','business']});client.update(order_country(c,latest['id']))
   sales=[dict(r) for r in c.execute('SELECT id,updated,language,turns,brief,recommendation,qualified,custom,order_id FROM sales_sessions ORDER BY updated DESC LIMIT 100')]
   from .notifications import whatsapp_ready
   notification_status={'whatsappReady':whatsapp_ready(),'whatsappQueued':c.execute("SELECT count(*) FROM owner_notifications WHERE status='queued'").fetchone()[0]}
   counts={r['status']:r['n'] for r in c.execute('SELECT status,count(*) n FROM orders GROUP BY status')}
   counts['pending_receipts']=c.execute("SELECT count(*) FROM receipts WHERE status='pending'").fetchone()[0]
   counts['open_tasks']=c.execute('SELECT count(*) FROM project_tasks WHERE done=0').fetchone()[0]
   counts['overdue_tasks']=c.execute("SELECT count(*) FROM project_tasks WHERE done=0 AND due_date!='' AND due_date<?",(local_today(),)).fetchone()[0]
   return {'revenue':revenue_report(c,now()),'finance':finance,'sales':sales,'notifications':notification_status,'counts':counts,'receipts':receipts,'tasks':tasks,'projects':projects,'clients':clients,'today':local_today(),'testMode':cfg.test_mode,'listLimit':500}

 @app.get('/api/admin/orders/{oid}/workspace')
 def workspace(oid:str,actor=Depends(admin)):
  with db.connect() as c:
   order(c,oid);row=c.execute('SELECT * FROM project_plans WHERE order_id=?',(oid,)).fetchone()
   return {'plan':dict(row) if row else {'order_id':oid,'version':0,'delivery':'planning','priority':'normal','due_date':''},'notes':[dict(r) for r in c.execute('SELECT id,created,body FROM project_notes WHERE order_id=? ORDER BY id DESC LIMIT 100',(oid,))],'tasks':[dict(r) for r in c.execute('SELECT * FROM project_tasks WHERE order_id=? ORDER BY done,created DESC LIMIT 100',(oid,))]}
 @app.post('/api/admin/orders/{oid}/plan')
 def save_plan(oid:str,data:ProjectPlan,actor=Depends(admin)):
  with db.transaction() as c:
   order(c,oid);old=c.execute('SELECT version FROM project_plans WHERE order_id=?',(oid,)).fetchone()
   if (old['version'] if old else 0)!=data.version:fail(409,'Project plan changed in another tab. Reopen the order before saving.')
   c.execute('INSERT INTO project_plans(order_id,delivery,priority,due_date,version) VALUES(?,?,?,?,?) ON CONFLICT(order_id) DO UPDATE SET delivery=excluded.delivery,priority=excluded.priority,due_date=excluded.due_date,version=excluded.version',(oid,data.delivery,data.priority,data.due_date,data.version+1));audit(c,actor,oid,'project_plan_updated',json.dumps(data.model_dump()))
  return {'ok':True}
 @app.post('/api/admin/orders/{oid}/notes')
 def add_note(oid:str,data:NoteInput,actor=Depends(admin)):
  if not data.body.strip():fail(422,'Write a note first')
  with db.transaction() as c:
   order(c,oid);c.execute('INSERT INTO project_notes(order_id,created,body) VALUES(?,?,?)',(oid,now(),data.body.strip()));audit(c,actor,oid,'internal_note_added')
  return {'ok':True}
 @app.post('/api/admin/tasks')
 def add_task(data:TaskInput,actor=Depends(admin)):
  if not data.title.strip():fail(422,'Write a task title')
  with db.transaction() as c:
   order(c,data.order_id);cursor=c.execute('INSERT INTO project_tasks(order_id,title,due_date,created) VALUES(?,?,?,?)',(data.order_id,data.title.strip(),data.due_date,now()));audit(c,actor,data.order_id,'task_created',data.title)
  return {'id':cursor.lastrowid}
 @app.post('/api/admin/tasks/{tid}/status')
 def task_status(tid:int,data:TaskUpdate,actor=Depends(admin)):
  with db.transaction() as c:
   task=c.execute('SELECT * FROM project_tasks WHERE id=?',(tid,)).fetchone()
   if not task:fail(404,'Task not found')
   if task['version']!=data.version:fail(409,'Task changed. Reopen before updating.')
   c.execute('UPDATE project_tasks SET done=?,version=version+1 WHERE id=?',(int(data.done),tid));audit(c,actor,task['order_id'],'task_completed' if data.done else 'task_reopened',task['title'])
  return {'ok':True}
 @app.get('/api/admin/export/orders.csv')
 def export_csv(actor=Depends(admin)):
  output=io.StringIO(newline='');writer=csv.writer(output);writer.writerow(['Order','Customer','Email','Phone','Business','Status','Quoted MYR','Settled project value MYR','Outstanding project value MYR','Delivery','Priority','Due date','Country','Country source','Payment status'])
  with db.connect() as c:
   for o in c.execute("SELECT o.*,coalesce(p.delivery,'planning') delivery,coalesce(p.priority,'normal') priority,coalesce(p.due_date,'') due_date FROM orders o LEFT JOIN project_plans p ON p.order_id=o.id ORDER BY o.created DESC"):
    settled=c.execute("SELECT coalesce(sum(base),0) FROM stages WHERE order_id=? AND status='paid'",(o['id'],)).fetchone()[0]
    overview=order_overview(c,o['id'])
    writer.writerow([csv_cell(v) for v in [o['public_no'],o['name'],o['email'],o['phone'],o['business'],o['status'],f"{o['quote']/100:.2f}" if o['quote'] is not None else '',f'{settled/100:.2f}',f"{(o['quote']-settled)/100:.2f}" if o['quote'] is not None else '',o['delivery'],o['priority'],o['due_date'],overview['country_code'],overview['country_source'],overview['payment_status']]])
  return Response(('\ufeff'+output.getvalue()).encode(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="kenny-orders.csv"'})
 @app.get('/api/admin/export/files.zip')
 def export_files(actor=Depends(admin)):
  # Export business records and files, never environment secrets, session tokens or login data.
  with NamedTemporaryFile(suffix='.zip',delete=False) as tmp:path=Path(tmp.name)
  try:
   with db.connect() as c,zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
    c.execute('BEGIN');records={}
    for table in ['orders','stages','receipts','documents','project_plans','project_notes','project_tasks','sales_sessions','sales_messages','owner_notifications','order_countries','audit']:
     records[table]=[{k:v for k,v in dict(r).items() if k not in ['pdf','path','idempotency','payload_hash']} for r in c.execute('SELECT * FROM '+table)]
    for r in c.execute('SELECT id,path FROM receipts'):
     receipt=Path(r['path'])
     if receipt.is_file() and receipt.parent.resolve()==(cfg.data/'uploads').resolve():archive.write(receipt,'receipts/'+r['id'])
     else:fail(409,'An uploaded file is missing; export stopped to avoid an incomplete archive.')
    for d in c.execute('SELECT number,pdf FROM documents'):archive.writestr('documents/'+d['number']+'.pdf',d['pdf'])
    archive.writestr('records.json',json.dumps({'exportedAt':now(),'testMode':cfg.test_mode,'records':records},ensure_ascii=False,indent=2));archive.writestr('README.txt','Kenny Studio business data export. Contains private customer details. Keep securely.\nThis is a records archive, not an automatic server restore or an export of credentials.\nReceipt files use their IDs; look up the original filename and MIME type in records.json.\nProject amounts are MYR book values; USDT transaction amounts remain in stage records.\n')
   with db.transaction() as c:audit(c,actor,None,'business_files_exported')
   return FileResponse(path,media_type='application/zip',filename='kenny-business-records.zip',background=BackgroundTask(path.unlink,missing_ok=True))
  except BaseException:path.unlink(missing_ok=True);raise
