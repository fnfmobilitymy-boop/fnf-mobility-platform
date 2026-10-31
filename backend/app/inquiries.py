"""Public enquiries saved atomically; confirmation receipts expose no customer data."""
import hashlib, hmac, json, re, secrets
from typing import Literal
from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .core import now, digest
from .db import audit, queue

Service=Literal['landing','personal','business','ecommerce','booking','admin','system','backend','redesign','maintenance','google-ads','seo','other']
class Inquiry(BaseModel):
 model_config=ConfigDict(extra='forbid')
 name:str=Field(min_length=1,max_length=120)
 phone:str=Field(min_length=6,max_length=40)
 service:Service
 message:str=Field(min_length=10,max_length=3000)
 business:str=Field(default='',max_length=150)
 budget:Literal['unsure','under1500','1500-3000','3000-6000','6000-10000','above10000']='unsure'
 features:list[Literal['login','admin','booking','payments','data','notifications']]=Field(default_factory=list,max_length=6)
 language:Literal['en','zh','ms']='en'
 idempotency:str=Field(pattern=r'^[a-f0-9]{64}$')
 website:str=Field(default='',max_length=200)
 @field_validator('name','phone','message','business')
 @classmethod
 def trim(cls,v):return v.strip()
 @field_validator('name')
 @classmethod
 def name_present(cls,v):
  if not v:raise ValueError('Enter your name')
  return v
 @field_validator('phone')
 @classmethod
 def valid_phone(cls,v):
  if not re.fullmatch(r'[+()0-9 .-]+',v) or not 6<=len(re.sub(r'\D','',v))<=20:raise ValueError('Enter a valid contact number')
  return v
 @field_validator('message')
 @classmethod
 def message_present(cls,v):
  if len(v)<10:raise ValueError('Please provide at least 10 characters about your enquiry')
  return v

def install_inquiries(app,db,cfg,admin,fail,limit):
 def receipt(ident):
  payload=ident+'.'+str(now()+86400)
  return payload+'.'+hmac.new(cfg.secret.encode(),('inquiry:'+payload).encode(),hashlib.sha256).hexdigest()
 @app.post('/api/inquiries')
 def submit(data:Inquiry,req:Request):
  if data.website:fail(422,'Unable to submit this enquiry')
  values=data.model_dump(exclude={'idempotency','website'});fingerprint=digest(json.dumps(values,sort_keys=True,ensure_ascii=False));key=digest(data.idempotency)
  with db.transaction() as c:
   old=c.execute('SELECT id,payload_hash FROM inquiries WHERE idempotency=?',(key,)).fetchone()
   if old:
    if old['payload_hash']!=fingerprint:fail(409,'This enquiry changed. Please submit it again.')
    ident=old['id'];created=False
   else:
    limit(c,'inquiry:'+str(req.client.host),5,3600);limit(c,'inquiry-global',100,86400)
    ident=secrets.token_hex(16);created=True
    c.execute('INSERT INTO inquiries(id,created,name,phone,service,message,business,budget,features,language,idempotency,payload_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(ident,now(),data.name,data.phone,data.service,data.message,data.business,data.budget,json.dumps(data.features),data.language,key,fingerprint))
    audit(c,'website',None,'inquiry_submitted',ident)
    queue(c,cfg.admin_email,'New website enquiry · '+ident[:8],f'Name: {data.name}\nPhone: {data.phone}\nService: {data.service}\nBusiness: {data.business}\nBudget: {data.budget}\n\n{data.message}\n\nOwner workspace: {cfg.public_url}/admin')
  # The transaction has committed before a success response/receipt is produced.
  return JSONResponse({'saved':True,'reference':ident,'receipt':receipt(ident)},status_code=201 if created else 200)
 @app.get('/api/inquiries/confirmation')
 def confirm(receipt:str=''):
  parts=receipt.split('.')
  if len(receipt)>200 or len(parts)!=3 or not re.fullmatch(r'[a-f0-9]{32}',parts[0]) or not re.fullmatch(r'[0-9]{1,12}',parts[1]):fail(404,'Confirmation not found')
  payload='.'.join(parts[:2]);expected=hmac.new(cfg.secret.encode(),('inquiry:'+payload).encode(),hashlib.sha256).hexdigest()
  if not hmac.compare_digest(parts[2],expected) or int(parts[1])<now():fail(404,'Confirmation expired or invalid')
  with db.connect() as c:
   if not c.execute('SELECT 1 FROM inquiries WHERE id=?',(parts[0],)).fetchone():fail(404,'Confirmation not found')
  return {'verified':True,'reference':parts[0]}

 @app.get('/api/admin/inquiries')
 def inbox(actor=Depends(admin)):
  with db.connect() as c:
   return {'inquiries':[dict(r) for r in c.execute('SELECT id,created,name,phone,service,message,business,budget,features,language FROM inquiries ORDER BY created DESC,id DESC LIMIT 500')],'total':c.execute('SELECT count(*) FROM inquiries').fetchone()[0]}
