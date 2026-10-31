"""Customer identity, isolated from owner sessions and legacy order capabilities."""
import os,re,secrets,hmac,hashlib,base64,time
from urllib.parse import urlencode
import httpx
from fastapi import Request,HTTPException
from fastapi.responses import JSONResponse,RedirectResponse
from pydantic import BaseModel,Field,ConfigDict
from .core import now,digest,pw_hash,pw_check
from .db import queue

class Credentials(BaseModel):
 model_config=ConfigDict(extra='forbid')
 email:str=Field(max_length=254)
 password:str=Field(min_length=12,max_length=128)
 name:str=Field(default='',max_length=120)
class Verification(BaseModel):
 challenge:str=Field(max_length=64)
 code:str=Field(pattern=r'^\d{6}$')
class Email(BaseModel):
 email:str=Field(max_length=254)
class Reset(Verification):
 password:str=Field(min_length=12,max_length=128)

def install_accounts(app,db,cfg,limit):
 def fail(code,msg):raise HTTPException(code,msg)
 def email(value):
  value=value.strip().lower()
  if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value):fail(422,'Enter a valid email')
  return value
 def csrf(raw):return hmac.new(cfg.secret.encode(),('customer-csrf:'+raw).encode(),hashlib.sha256).hexdigest()
 def current(req,required=True,mutation=False):
  raw=req.cookies.get('kenny_customer','')
  with db.connect() as c:r=c.execute('SELECT c.* FROM customers c JOIN customer_sessions s ON s.customer_id=c.id WHERE s.token_hash=? AND s.expires>? AND c.verified=1',(digest(raw),now())).fetchone()
  if not r:
   if required:fail(401,'Please register or log in before ordering / 请先注册或登录')
   return None
  if mutation:
   if req.headers.get('origin') and req.headers['origin']!=cfg.public_url:fail(403,'Invalid origin')
   if not hmac.compare_digest(req.headers.get('x-customer-csrf',''),csrf(raw)):fail(403,'Refresh your customer login and try again')
  return dict(r)
 def profile(r,raw):return {'id':r['id'],'email':r['email'],'name':r['name'],'csrf':csrf(raw)}
 def signed_in(r):
  token=secrets.token_urlsafe(40)
  with db.transaction() as c:
   c.execute('DELETE FROM customer_sessions WHERE expires<?',(now(),));c.execute('INSERT INTO customer_sessions VALUES(?,?,?)',(digest(token),r['id'],now()+2592000))
  response=JSONResponse(profile(r,token));response.set_cookie('kenny_customer',token,max_age=2592000,httponly=True,secure=cfg.production,samesite='lax',path='/');return response
 def throttle(req,key):
  with db.transaction() as c:limit(c,'account:'+key+':'+str(req.client.host),12,900)
 def mail_ready():return all(os.environ.get(k) for k in ['SMTP_HOST','SMTP_USERNAME','SMTP_PASSWORD','SMTP_FROM'])
 def challenge(cid,address,kind):
  if not cfg.test_mode and not mail_ready():fail(503,'Email verification is not configured yet. Please contact Kenny.')
  ident=secrets.token_hex(24);code=str(secrets.randbelow(1000000)).zfill(6)
  hashed=hmac.new(cfg.secret.encode(),(ident+':'+code).encode(),hashlib.sha256).hexdigest()
  with db.transaction() as c:
   c.execute('UPDATE account_challenges SET used=1 WHERE customer_id=? AND kind=?',(cid,kind))
   c.execute('INSERT INTO account_challenges VALUES(?,?,?,?,?,?,0,0)',(ident,cid,kind,hashed,now()+600,now()))
   if not cfg.test_mode:queue(c,address,'Kenny Studio · Verification code',f'Your {kind} code is {code}. It expires in 10 minutes. If you did not request this, ignore this email.')
  return {'challenge':ident,'testCode':code if cfg.test_mode else None,'message':'TEST ONLY: use the displayed code; no email was sent.' if cfg.test_mode else 'Check your email for a verification code.'}
 def consume(data,kind,password=None):
  error=False;cid=None
  with db.transaction() as c:
   r=c.execute('SELECT * FROM account_challenges WHERE id=?',(data.challenge,)).fetchone()
   if not r or r['kind']!=kind or r['used'] or r['expires']<now() or r['attempts']>=5:error=True
   else:
    c.execute('UPDATE account_challenges SET attempts=attempts+1 WHERE id=?',(data.challenge,))
    expected=hmac.new(cfg.secret.encode(),(data.challenge+':'+data.code).encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(r['code_hash'],expected):error=True
    else:
     cid=r['customer_id'];c.execute('UPDATE account_challenges SET used=1 WHERE customer_id=?',(cid,))
     c.execute('UPDATE customers SET verified=1 WHERE id=?',(cid,))
     if password:
      c.execute('UPDATE customers SET password_hash=? WHERE id=?',(password,cid));c.execute('DELETE FROM customer_sessions WHERE customer_id=?',(cid,))
  if error:fail(400,'Invalid or expired code. Request a new code after five failed attempts.')
  with db.connect() as c:return dict(c.execute('SELECT * FROM customers WHERE id=?',(cid,)).fetchone())
 @app.get('/api/account/config')
 def config():return {'email':cfg.test_mode or mail_ready(),'testMode':cfg.test_mode}
 @app.get('/api/account/session')
 def session(req:Request):
  r=current(req,False);return profile(r,req.cookies['kenny_customer']) if r else {'customer':None}
 @app.post('/api/account/register')
 def register(data:Credentials,req:Request):
  throttle(req,'register');address=email(data.email)
  if not cfg.test_mode and not mail_ready():fail(503,'Email verification is not configured yet.')
  hashed=pw_hash(data.password)
  with db.transaction() as c:
   old=c.execute('SELECT * FROM customers WHERE email=?',(address,)).fetchone()
   if old:
    # Never replace an unverified account password using only knowledge of its email.
    if old['verified'] or not pw_check(data.password,old['password_hash'] or ''):fail(409,'This email is registered. Log in or reset your password.')
    cid=old['id']
   else:
    cid=secrets.token_hex(16);c.execute('INSERT INTO customers VALUES(?,?,?,?,?,NULL,?)',(cid,address,data.name.strip(),hashed,0,now()))
  return challenge(cid,address,'verify')
 @app.post('/api/account/verify')
 def verify(data:Verification,req:Request):throttle(req,'verify');return signed_in(consume(data,'verify'))
 @app.post('/api/account/login')
 def login(data:Credentials,req:Request):
  throttle(req,'login');address=email(data.email)
  with db.connect() as c:r=c.execute('SELECT * FROM customers WHERE email=?',(address,)).fetchone()
  if not r or not pw_check(data.password,r['password_hash'] or ''):fail(401,'Invalid email or password')
  if not r['verified']:return challenge(r['id'],address,'verify')
  return signed_in(dict(r))
 @app.post('/api/account/reset/request')
 def reset_request(data:Email,req:Request):
  throttle(req,'reset');address=email(data.email)
  with db.connect() as c:r=c.execute('SELECT * FROM customers WHERE email=?',(address,)).fetchone()
  return challenge(r['id'],address,'reset') if r else {'challenge':secrets.token_hex(24),'message':'If this email is registered, a code will be sent.'}
 @app.post('/api/account/reset')
 def reset(data:Reset,req:Request):throttle(req,'reset-verify');return signed_in(consume(data,'reset',pw_hash(data.password)))
 @app.post('/api/account/logout')
 def logout(req:Request):
  current(req,mutation=True)
  with db.transaction() as c:c.execute('DELETE FROM customer_sessions WHERE token_hash=?',(digest(req.cookies.get('kenny_customer','')),))
  response=JSONResponse({'ok':True});response.delete_cookie('kenny_customer',path='/');return response
 @app.get('/api/account/orders')
 def orders(req:Request):
  r=current(req)
  with db.connect() as c:return {'orders':[dict(o) for o in c.execute('SELECT o.id,o.public_no,o.status,o.created,o.estimate,o.quote FROM orders o JOIN customer_orders co ON co.order_id=o.id WHERE co.customer_id=? ORDER BY o.created DESC',(r['id'],))]}
 app.state.customer=current
 return current
