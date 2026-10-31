from fastapi import FastAPI,Request,HTTPException,UploadFile,File,Form,Depends
from fastapi.responses import FileResponse,Response,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field,ConfigDict
from typing import Literal
from contextlib import asynccontextmanager
from .security import BodyLimitMiddleware
from pathlib import Path
from io import BytesIO
import asyncio,os,json,secrets,hashlib,hmac,re,sqlite3,httpx
from PIL import Image
from .core import Settings,DETAILS,PHASES,now,digest,money,split_amount,validate_items,pw_check
from .db import DB,audit,queue,number
from .documents import render_pdf

class Strict(BaseModel):model_config=ConfigDict(extra='forbid')
class Item(Strict):id:str;qty:int=Field(strict=True)
class NewOrder(Strict):
 items:list[Item];name:str=Field(min_length=1,max_length=120);email:str=Field(min_length=3,max_length=254);phone:str=Field(min_length=3,max_length=40);business:str=Field(default='',max_length=150);requirements:str=Field(min_length=10,max_length=5000);language:Literal['en','zh','ms']='en';method:Literal['bank','tng','usdt','stripe']='bank';consent:Literal[True];idempotency:str=Field(pattern=r'^[a-f0-9]{64}$')
class Login(Strict):email:str;password:str=Field(max_length=1024)
class Quote(Strict):version:int;amount:str;scope:str=Field(min_length=10,max_length=5000);method:Literal['bank','tng','usdt','stripe'];usdt:list[str]=Field(default_factory=list,max_length=3)
class Release(Strict):phase:Literal['second','balance'];note:str=Field(min_length=5,max_length=1000)
class Review(Strict):approve:bool;note:str=Field(min_length=5,max_length=1000);confirmed_received:bool=False

def create_app(settings=None):
 cfg=settings or Settings();cfg.validate();db=DB(cfg.data/'orders.sqlite3')
 @asynccontextmanager
 async def lifespan(app):
  from .mail import deliver_loop
  task=asyncio.create_task(deliver_loop(db))
  try:yield
  finally:
   task.cancel()
   try:await task
   except asyncio.CancelledError:pass
 app=FastAPI(title='Kenny Studio Orders',docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)
 app.add_middleware(BodyLimitMiddleware)
 app.state.cfg=cfg;app.state.db=db
 with db.transaction() as c:c.execute('DELETE FROM sessions')
 app.add_middleware(CORSMiddleware,allow_origins=[cfg.origin,cfg.public_url],allow_methods=['GET','POST'],allow_headers=['Authorization','Content-Type','X-CSRF-Token'],allow_credentials=False)
 def fail(code,message):raise HTTPException(code,message)
 def order(c,oid):
  row=c.execute('SELECT * FROM orders WHERE id=?',(oid,)).fetchone()
  if not row:fail(404,'Order not found')
  return dict(row)
 def session(req):
  raw=req.cookies.get('kenny_admin','')
  with db.connect() as c:row=c.execute('SELECT * FROM sessions WHERE token_hash=? AND expires>?',(digest(raw),now())).fetchone()
  return raw if row else None
 def admin(req:Request):
  raw=session(req)
  if not raw:fail(401,'Please sign in')
  if req.method not in ('GET','HEAD'):
   if req.headers.get('origin') and req.headers['origin']!=cfg.public_url:fail(403,'Invalid origin')
   if not hmac.compare_digest(req.headers.get('x-csrf-token',''),cfg.csrf(raw)):fail(403,'Refresh your session and try again')
  return cfg.admin_email
 def customer(req,record):
  expected=cfg.token(record['id'],record['access_version']);actual=req.headers.get('authorization','').removeprefix('Bearer ')
  if not hmac.compare_digest(expected,actual):fail(404,'Order not found or private link invalid')
 def access(req,record):
  if not session(req):customer(req,record)
 def limit(c,key,maximum,seconds):
  c.execute('DELETE FROM limits WHERE created<?',(now()-86400,))
  if c.execute('SELECT count(*) FROM limits WHERE key=? AND created>?',(key,now()-seconds)).fetchone()[0]>=maximum:fail(429,'Too many attempts. Please try later')
  c.execute('INSERT INTO limits VALUES(?,?)',(key,now()))
 def emit_document(c,o,s,kind):
  existing=c.execute('SELECT id FROM documents WHERE stage_id=? AND kind=?',(s['id'],kind)).fetchone()
  if existing:return existing[0]
  ident=secrets.token_hex(16);num=number(c,'RCPT' if kind=='receipt' else 'INV');issued=now();pdf=render_pdf(o,s,kind,num,issued)
  c.execute('INSERT INTO documents(id,order_id,stage_id,kind,number,created,pdf) VALUES(?,?,?,?,?,?,?)',(ident,o['id'],s['id'],kind,num,issued,pdf));return ident
 def notify(c,o,subject,text):
  queue(c,cfg.admin_email,subject,text+'\n\nAdmin: '+cfg.public_url+'/admin')
  queue(c,o['email'],subject,text+'\n\nYour private project link (keep private):\n'+cfg.link(o['id'],o['access_version']))
 def settle(c,o,s,reference,actor):
  if s['status']=='paid':return
  c.execute('UPDATE stages SET status=?,paid=?,reference=? WHERE id=?',('paid',now(),reference,s['id']));s={**s,'status':'paid','reference':reference,'paid':now()};emit_document(c,o,s,'receipt');count=c.execute("SELECT count(*) FROM stages WHERE order_id=? AND status='paid'",(o['id'],)).fetchone()[0]
  c.execute('UPDATE orders SET status=?,updated=?,version=version+1 WHERE id=?',('completed' if count==3 else 'in_progress',now(),o['id']));audit(c,actor,o['id'],'payment_verified',s['phase']+': '+reference);notify(c,o,'Payment verified · '+o['public_no'],s['phase']+' payment was verified. Your receipt is available in your project portal.')
 @app.middleware('http')
 async def guards(req,call_next):
  if req.method=='POST' and req.url.path!='/api/stripe/webhook':
   origin=req.headers.get('origin')
   if origin and origin not in [cfg.origin,cfg.public_url]:return JSONResponse({'detail':'Invalid origin'},403)
  response=await call_next(req)
  for k,v in {'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY','X-Robots-Tag':'noindex, nofollow','Cache-Control':'no-store','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; connect-src 'self'; font-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"}.items():response.headers[k]=v
  return response
 @app.exception_handler(ValueError)
 async def value_error(req,exc):return JSONResponse({'detail':str(exc)},422)
 @app.get('/api/health')
 def health():return {'status':'ok'}
 @app.get('/api/catalogue')
 def get_catalogue(language:Literal['en','zh','ms']='en'):
  from .core import catalogue
  return {'items':catalogue(language),'currency':'MYR','stripeFeePercent':6}
 @app.post('/api/orders',status_code=201)
 def new_order(data:NewOrder,req:Request):
  if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',data.email):fail(422,'Enter a valid email')
  if not data.name.strip() or not data.requirements.strip():fail(422,'Complete your name and project requirements')
  payload=data.model_dump();items=validate_items(payload['items'],data.language);payload_hash=digest(json.dumps(payload,sort_keys=True));oid=secrets.token_hex(16)
  with db.transaction() as c:
   old=c.execute('SELECT * FROM orders WHERE idempotency=?',(data.idempotency,)).fetchone()
   if old:
    if old['payload_hash']!=payload_hash:fail(409,'This submission key already belongs to a different request')
    return {'id':old['id'],'number':old['public_no'],'url':cfg.link(old['id'],old['access_version']),'token':cfg.token(old['id'],old['access_version'])}
   limit(c,'order:'+str(req.client.host),10,3600);num=number(c,'KS');estimate=sum(p['lineCents'] for p in items)
   c.execute('INSERT INTO orders(id,public_no,created,updated,status,language,name,email,phone,business,requirements,items,estimate,method,idempotency,payload_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(oid,num,now(),now(),'requested',data.language,data.name.strip(),data.email.strip(),data.phone.strip(),data.business.strip(),data.requirements.strip(),json.dumps(items,ensure_ascii=False),estimate,data.method,data.idempotency,payload_hash))
   o=order(c,oid);audit(c,'customer',oid,'order_requested','Request-data processing consent v1 accepted');notify(c,o,'New project request · '+num,'Your project request has been saved. Kenny will review your scope and confirm a quotation before payment.\n\n'+data.requirements)
  return {'id':oid,'number':num,'url':cfg.link(oid),'token':cfg.token(oid)}
 @app.get('/api/orders/{oid}')
 def get_order(oid:str,req:Request):
  with db.connect() as c:
   o=order(c,oid);access(req,o);o.pop('idempotency');o.pop('payload_hash');o['items']=json.loads(o['items']);o['stages']=[dict(r) for r in c.execute('SELECT * FROM stages WHERE order_id=? ORDER BY rowid',(oid,))];o['receipts']=[dict(r) for r in c.execute('SELECT id,stage_id,created,name,mime,reference,status,note FROM receipts WHERE order_id=? ORDER BY created DESC',(oid,))];o['documents']=[dict(r) for r in c.execute('SELECT id,stage_id,kind,number,created FROM documents WHERE order_id=?',(oid,))];o['paymentDetails']=DETAILS if o['quote'] else None;o['stripeReady']=bool(cfg.stripe_key and cfg.webhook_secret);return o
 @app.post('/api/admin/login')
 def login(data:Login,req:Request):
  with db.transaction() as c:limit(c,'login:'+str(req.client.host),15,900)
  if not hmac.compare_digest(data.email.lower(),cfg.admin_email.lower()) or not pw_check(data.password,cfg.admin_hash):fail(401,'Invalid email or password')
  token=secrets.token_urlsafe(40)
  with db.transaction() as c:
   c.execute('DELETE FROM sessions WHERE expires<?',(now(),));c.execute('INSERT INTO sessions VALUES(?,?)',(digest(token),now()+28800))
  response=JSONResponse({'csrf':cfg.csrf(token),'email':cfg.admin_email});response.set_cookie('kenny_admin',token,httponly=True,secure=cfg.production,samesite='strict',max_age=28800,path='/');return response
 @app.get('/api/admin/session')
 def get_session(req:Request,actor=Depends(admin)):return {'email':actor,'csrf':cfg.csrf(session(req))}
 @app.post('/api/admin/logout')
 def logout(req:Request,actor=Depends(admin)):
  with db.transaction() as c:c.execute('DELETE FROM sessions WHERE token_hash=?',(digest(session(req)),))
  response=JSONResponse({'ok':True});response.delete_cookie('kenny_admin',path='/');return response
 @app.get('/api/admin/orders')
 def list_orders(actor=Depends(admin)):
  with db.connect() as c:return {'orders':[dict(r) for r in c.execute('SELECT id,public_no,created,updated,status,name,email,estimate,quote,method FROM orders ORDER BY created DESC LIMIT 500')],'mailReady':all(os.environ.get(k) for k in ['SMTP_HOST','SMTP_USERNAME','SMTP_PASSWORD','SMTP_FROM']),'stripeReady':bool(cfg.stripe_key and cfg.webhook_secret),'queuedMail':c.execute("SELECT count(*) FROM outbox WHERE status!='sent'").fetchone()[0]}
 @app.post('/api/admin/orders/{oid}/quote')
 def approve_quote(oid:str,data:Quote,actor=Depends(admin)):
  total=money(data.amount);amounts=split_amount(total,data.method)
  if data.method=='usdt' and (len(data.usdt)!=3 or any(not re.fullmatch(r'\d{1,10}(?:\.\d{1,6})?',v) or float(v)<=0 for v in data.usdt)):fail(422,'Confirm three exact USDT stage amounts (TRC20), not a guessed exchange rate')
  with db.transaction() as c:
   o=order(c,oid)
   if o['status']!='requested' or o['version']!=data.version:fail(409,'Order changed or quotation already issued. Refresh before continuing')
   c.execute('UPDATE orders SET quote=?,scope=?,method=?,status=?,updated=?,version=version+1 WHERE id=?',(total,data.scope,data.method,'quoted',now(),oid));o=order(c,oid)
   for index,(phase,(base,fee)) in enumerate(zip(PHASES,amounts)):
    sid=secrets.token_hex(16);c.execute('INSERT INTO stages(id,order_id,phase,base,fee,total,method,status,released,usdt) VALUES(?,?,?,?,?,?,?,?,?,?)',(sid,oid,phase,base,fee,base+fee,data.method,'open' if index==0 else 'locked',now() if index==0 else None,data.usdt[index] if data.method=='usdt' else None));s=dict(c.execute('SELECT * FROM stages WHERE id=?',(sid,)).fetchone());emit_document(c,o,s,'invoice')
   audit(c,actor,oid,'quote_approved',data.scope);notify(c,o,'Quotation ready · '+o['public_no'],'Kenny has confirmed your project scope. Review your three-stage invoices; only the 50% deposit is currently open.\n\nScope:\n'+data.scope)
  return {'ok':True}
 @app.post('/api/admin/orders/{oid}/release')
 def release(oid:str,data:Release,actor=Depends(admin)):
  with db.transaction() as c:
   o=order(c,oid);prev=PHASES[PHASES.index(data.phase)-1];row=c.execute('SELECT * FROM stages WHERE order_id=? AND phase=?',(oid,prev)).fetchone()
   if not row or row['status']!='paid':fail(409,'Verify the previous payment first')
   current=c.execute('SELECT * FROM stages WHERE order_id=? AND phase=?',(oid,data.phase)).fetchone()
   if current['status']!='locked':fail(409,'Stage already released')
   c.execute('UPDATE stages SET status=?,released=? WHERE id=?',('open',now(),current['id']));audit(c,actor,oid,'milestone_released',data.phase+': '+data.note);notify(c,o,'Next payment stage ready · '+o['public_no'],data.phase+' milestone was confirmed by Kenny.\n'+data.note)
  return {'ok':True}
 @app.post('/api/orders/{oid}/stages/{phase}/receipt')
 async def upload(oid:str,phase:str,req:Request,reference:str=Form(...,min_length=3,max_length=160),file:UploadFile=File(...)):
  with db.connect() as c:
   o=order(c,oid);customer(req,o);s=c.execute('SELECT * FROM stages WHERE order_id=? AND phase=?',(oid,phase)).fetchone()
   if not s or s['status']!='open' or s['method']=='stripe':fail(409,'This transfer stage is not open')
   if s['method']=='usdt' and not re.fullmatch(r'[A-Fa-f0-9]{64}',reference):fail(422,'Enter the 64-character TRON transaction hash')
  content=await file.read(10*1024*1024+1)
  if not 10<=len(content)<=10*1024*1024:fail(422,'Receipt must be at most 10 MB')
  mime='application/pdf' if content.startswith(b'%PDF-') and b'%%EOF' in content[-2048:] else None
  if not mime:
   try:
    image=Image.open(BytesIO(content));image.verify()
    if image.format not in ['JPEG','PNG']:raise ValueError()
    mime={'JPEG':'image/jpeg','PNG':'image/png'}[image.format]
   except Exception:fail(422,'Only valid JPG, PNG or PDF receipts are accepted')
  ident=secrets.token_hex(16);path=cfg.data/'uploads'/ident;sha=hashlib.sha256(content).hexdigest();path.write_bytes(content);os.chmod(path,0o600)
  try:
   with db.transaction() as c:
    fresh=c.execute('SELECT status FROM stages WHERE id=?',(s['id'],)).fetchone()
    if fresh['status']!='open':fail(409,'Stage already settled')
    if c.execute("SELECT count(*) FROM receipts WHERE stage_id=? AND status='pending'",(s['id'],)).fetchone()[0]>=3:fail(409,'Three receipts already await review')
    c.execute('INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?,?,?,?)',(ident,oid,s['id'],now(),Path(file.filename or 'receipt').name[:150],mime,str(path),sha,reference,'pending',''));audit(c,'customer',oid,'receipt_uploaded',ident);queue(c,cfg.admin_email,'Receipt needs review · '+o['public_no'],'A receipt was uploaded. Verify actual funds before approval.\n'+cfg.public_url+'/admin')
  except BaseException:path.unlink(missing_ok=True);raise
  return {'id':ident,'status':'pending','message':'Receipt uploaded. Payment is not yet verified.'}
 @app.get('/api/receipts/{rid}')
 def receipt_file(rid:str,req:Request):
  with db.connect() as c:
   r=c.execute('SELECT * FROM receipts WHERE id=?',(rid,)).fetchone()
   if not r:fail(404,'Receipt not found')
   access(req,order(c,r['order_id']));return FileResponse(r['path'],media_type=r['mime'],filename=r['name'])
 @app.post('/api/admin/receipts/{rid}/review')
 def review(rid:str,data:Review,actor=Depends(admin)):
  try:
   with db.transaction() as c:
    r=c.execute('SELECT * FROM receipts WHERE id=?',(rid,)).fetchone()
    if not r or r['status']!='pending':fail(409,'Receipt has already been reviewed')
    o=order(c,r['order_id']);s=dict(c.execute('SELECT * FROM stages WHERE id=?',(r['stage_id'],)).fetchone())
    if data.approve:
     if not data.confirmed_received:fail(422,'Confirm that you checked the actual receiving account and amount')
     if s['status']!='open':fail(409,'Stage is not open or already paid')
     if s['method']=='usdt' and c.execute("SELECT 1 FROM receipts WHERE reference=? AND status='approved'",(r['reference'],)).fetchone():fail(409,'Transaction already used')
     c.execute('UPDATE receipts SET status=?,note=? WHERE id=?',('approved',data.note,rid));settle(c,o,s,r['reference'],actor)
    else:
     c.execute('UPDATE receipts SET status=?,note=? WHERE id=?',('rejected',data.note,rid));notify(c,o,'Receipt needs attention · '+o['public_no'],data.note)
    audit(c,actor,o['id'],'receipt_reviewed',rid+': '+data.note)
  except sqlite3.IntegrityError:fail(409,'This payment receipt was already used')
  return {'ok':True}
 @app.get('/api/documents/{did}')
 def document(did:str,req:Request):
  with db.connect() as c:
   row=c.execute('SELECT * FROM documents WHERE id=?',(did,)).fetchone()
   if not row:fail(404,'Document not found')
   access(req,order(c,row['order_id']));return Response(row['pdf'],media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="'+row['number']+'.pdf"'})
 @app.post('/api/orders/{oid}/stages/{phase}/checkout')
 async def checkout(oid:str,phase:str,req:Request):
  if not cfg.stripe_key or not cfg.webhook_secret:fail(503,'Stripe API and webhook credentials have not been configured. No payment was created.')
  with db.connect() as c:
   o=order(c,oid);customer(req,o);s=c.execute('SELECT * FROM stages WHERE order_id=? AND phase=?',(oid,phase)).fetchone()
   if not s or s['method']!='stripe' or s['status']!='open':fail(409,'This Stripe payment stage is not open')
   old=c.execute('SELECT * FROM checkout WHERE stage_id=?',(s['id'],)).fetchone()
   if old and old['expires']>now()+60:return {'url':old['url']}
  payload={'mode':'payment','client_reference_id':oid,'success_url':cfg.public_url+'/order/'+oid+'?checkout=returned','cancel_url':cfg.public_url+'/order/'+oid,'metadata[order_id]':oid,'metadata[stage_id]':s['id'],'customer_email':o['email']}
  for index,(name,cents) in enumerate([('Kenny Studio · '+phase,s['base']),('Stripe service fee · 6%',s['fee'])]):
   payload.update({f'line_items[{index}][price_data][currency]':'myr',f'line_items[{index}][price_data][product_data][name]':name,f'line_items[{index}][price_data][unit_amount]':str(cents),f'line_items[{index}][quantity]':'1'})
  generation=(old['generation']+1) if old else 1
  payload['expires_at']=str(now()+3600)
  async with httpx.AsyncClient(timeout=20) as client:
   if old:
    prior=await client.get('https://api.stripe.com/v1/checkout/sessions/'+old['session_id'],auth=(cfg.stripe_key,''))
    if prior.status_code>=400:fail(502,'Could not safely check the previous Stripe session. Please retry later.')
    previous=prior.json()
    if previous.get('payment_status')=='paid' or previous.get('status')=='complete':fail(409,'Stripe payment is awaiting verified webhook confirmation. Do not pay again.')
    if previous.get('status')=='open':
     expired=await client.post('https://api.stripe.com/v1/checkout/sessions/'+old['session_id']+'/expire',auth=(cfg.stripe_key,''))
     if expired.status_code>=400:fail(409,'Previous checkout could not be closed safely. Please refresh before paying.')
   result=await client.post('https://api.stripe.com/v1/checkout/sessions',data=payload,auth=(cfg.stripe_key,''),headers={'Idempotency-Key':'kenny-'+s['id']+'-'+str(generation)})
  if result.status_code>=400:fail(502,'Stripe could not create a checkout. No payment has been confirmed.')
  answer=result.json();url=answer.get('url','')
  if not url.startswith('https://checkout.stripe.com/') or type(answer.get('expires_at'))!=int or answer['expires_at']<=now():fail(502,'Unexpected Stripe response')
  with db.transaction() as c:
   current=c.execute('SELECT status FROM stages WHERE id=?',(s['id'],)).fetchone()
   if current['status']!='open':fail(409,'Stage was settled while checkout was being prepared')
   c.execute('INSERT INTO checkout VALUES(?,?,?,?,?,?) ON CONFLICT(stage_id) DO UPDATE SET session_id=excluded.session_id,url=excluded.url,created=excluded.created,expires=excluded.expires,generation=excluded.generation',(s['id'],answer['id'],url,now(),answer['expires_at'],generation))
  return {'url':url}
 @app.post('/api/stripe/webhook')
 async def stripe_webhook(req:Request):
  if not cfg.webhook_secret:fail(503,'Webhook not configured')
  body=await req.body()
  if len(body)>1000000:fail(413,'Payload too large')
  parts=req.headers.get('stripe-signature','').split(',');ts=next((p[2:] for p in parts if p.startswith('t=')),'');signatures=[p[3:] for p in parts if p.startswith('v1=')]
  if not ts.isdigit() or abs(now()-int(ts))>300:fail(400,'Invalid signature timestamp')
  expected=hmac.new(cfg.webhook_secret.encode(),ts.encode()+b'.'+body,hashlib.sha256).hexdigest()
  if not any(hmac.compare_digest(expected,sig) for sig in signatures):fail(400,'Invalid webhook signature')
  event=json.loads(body);obj=event.get('data',{}).get('object',{})
  if event.get('type') not in ['checkout.session.completed','checkout.session.async_payment_succeeded'] or obj.get('payment_status')!='paid':return {'received':True}
  if not isinstance(event.get('id'),str):fail(400,'Missing event ID')
  with db.transaction() as c:
   if c.execute('SELECT 1 FROM stripe_events WHERE id=?',(event['id'],)).fetchone():return {'received':True}
   sid=obj.get('metadata',{}).get('stage_id');s=c.execute('SELECT * FROM stages WHERE id=?',(sid,)).fetchone();attempt=c.execute('SELECT * FROM checkout WHERE stage_id=?',(sid,)).fetchone()
   if not s or not attempt or attempt['session_id']!=obj.get('id') or s['method']!='stripe' or obj.get('currency')!='myr' or type(obj.get('amount_total'))!=int or obj['amount_total']!=s['total'] or not obj.get('payment_intent') or obj.get('metadata',{}).get('order_id')!=s['order_id']:fail(409,'Payment does not match the approved stage')
   if bool(obj.get('livemode'))!=cfg.stripe_key.startswith('sk_live_'):fail(409,'Stripe live/test mode mismatch')
   o=order(c,s['order_id'])
   if s['status']=='locked':fail(409,'Stage is not released')
   settle(c,o,dict(s),obj['payment_intent'],'stripe-webhook');c.execute('INSERT INTO stripe_events VALUES(?,?,?)',(event['id'],now(),'processed'))
  return {'received':True}
 @app.get('/api/admin/orders/{oid}/link')
 def customer_link(oid:str,actor=Depends(admin)):
  with db.connect() as c:
   o=order(c,oid);return {'url':cfg.link(oid,o['access_version'])}
 @app.get('/api/admin/audit/{oid}')
 def audit_log(oid:str,actor=Depends(admin)):
  with db.connect() as c:return {'events':[dict(r) for r in c.execute('SELECT * FROM audit WHERE order_id=? ORDER BY id DESC',(oid,))]}
 @app.post('/api/admin/mail/retry')
 def retry_mail(actor=Depends(admin)):
  with db.transaction() as c:
   c.execute("UPDATE outbox SET attempts=0,next_attempt=0,error=NULL WHERE status='queued'");audit(c,actor,None,'mail_retry_requested')
  return {'ok':True}
 @app.get('/api/admin/mail')
 def mail_status(actor=Depends(admin)):
  with db.connect() as c:return {'messages':[dict(r) for r in c.execute('SELECT id,created,recipient,subject,status,attempts,error FROM outbox ORDER BY id DESC LIMIT 100')]}
 app.mount('/static',StaticFiles(directory=Path(__file__).resolve().parents[1]/'static'),name='static')
 @app.get('/')
 @app.get('/admin')
 @app.get('/order/{oid}')
 def shell():return FileResponse(Path(__file__).resolve().parents[1]/'static/index.html')
 return app
