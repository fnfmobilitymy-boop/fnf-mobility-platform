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

def verify_google_token(raw,certs,audience):
 # The official verifier checks the signature, audience, expiry and issue time.
 from google.auth import jwt
 return jwt.decode(raw,certs=certs,audience=audience)

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
 def google_ready():return bool(os.environ.get('GOOGLE_CLIENT_ID') and os.environ.get('GOOGLE_CLIENT_SECRET'))
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
 def config():return {'google':google_ready(),'email':cfg.test_mode or mail_ready(),'testMode':cfg.test_mode}
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
 @app.get('/api/account/google/start')
 def google_start(req:Request):
  if not google_ready():fail(503,'Google login is waiting for OAuth configuration.')
  state=secrets.token_urlsafe(32);nonce=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(48)
  with db.transaction() as c:
   limit(c,'google:'+str(req.client.host),20,900);c.execute('DELETE FROM google_flows WHERE created<?',(now()-600,));c.execute('INSERT INTO google_flows VALUES(?,?,?,?,?)',(digest(state),nonce,verifier,now(),digest(req.cookies.get('kenny_customer',''))))
  query={'client_id':os.environ['GOOGLE_CLIENT_ID'],'redirect_uri':cfg.public_url+'/api/account/google/callback','response_type':'code','scope':'openid email profile','state':state,'nonce':nonce,'code_challenge':base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('='),'code_challenge_method':'S256','prompt':'select_account'}
  response=RedirectResponse('https://accounts.google.com/o/oauth2/v2/auth?'+urlencode(query));response.set_cookie('kenny_google_state',state,max_age=600,httponly=True,secure=cfg.production,samesite='lax',path='/');return response
 @app.get('/api/account/google/callback')
 async def google_callback(req:Request,state:str='',code:str=''):
  if not state or not code or not hmac.compare_digest(state,req.cookies.get('kenny_google_state','')):fail(400,'Google sign-in state invalid. Close this window and retry.')
  with db.transaction() as c:
   flow=c.execute('SELECT * FROM google_flows WHERE state_hash=?',(digest(state),)).fetchone();c.execute('DELETE FROM google_flows WHERE state_hash=?',(digest(state),))
  if not flow or flow['created']<now()-600:fail(400,'Google sign-in expired')
  try:
   async with httpx.AsyncClient(timeout=20) as client:
    token=await client.post('https://oauth2.googleapis.com/token',data={'code':code,'client_id':os.environ['GOOGLE_CLIENT_ID'],'client_secret':os.environ['GOOGLE_CLIENT_SECRET'],'redirect_uri':cfg.public_url+'/api/account/google/callback','grant_type':'authorization_code','code_verifier':flow['verifier']});token.raise_for_status()
    certs=await client.get('https://www.googleapis.com/oauth2/v1/certs');certs.raise_for_status()
    claims=verify_google_token(token.json()['id_token'],certs.json(),os.environ['GOOGLE_CLIENT_ID'])
   if claims.get('aud')!=os.environ['GOOGLE_CLIENT_ID'] or claims.get('iss') not in ('accounts.google.com','https://accounts.google.com') or int(claims.get('exp',0))<=time.time() or claims.get('nonce')!=flow['nonce'] or str(claims.get('email_verified')).lower()!='true' or not claims.get('sub'):raise ValueError()
   address=email(claims['email'])
  except (httpx.HTTPError,KeyError,ValueError,TypeError):fail(400,'Google verification failed. Please try again.')
  with db.transaction() as c:
   r=c.execute('SELECT * FROM customers WHERE google_sub=?',(claims['sub'],)).fetchone()
   if not r:
    existing=c.execute('SELECT * FROM customers WHERE email=?',(address,)).fetchone()
    if existing:
     active=current(req,False)
     if not active or active['id']!=existing['id'] or not hmac.compare_digest(flow['session_binding'],digest(req.cookies.get('kenny_customer',''))):fail(409,'This email already has an account. Log in with your password first, then choose Google to link it.')
     c.execute('UPDATE customers SET google_sub=?,verified=1 WHERE id=?',(claims['sub'],existing['id']));cid=existing['id']
    else:
     cid=secrets.token_hex(16);c.execute('INSERT INTO customers VALUES(?,?,?,NULL,1,?,?)',(cid,address,str(claims.get('name',''))[:120],claims['sub'],now()))
    r=c.execute('SELECT * FROM customers WHERE id=?',(cid,)).fetchone()
  response=signed_in(dict(r));response.status_code=303;response.headers['location']='/account/google-complete';response.delete_cookie('kenny_google_state',path='/');return response
 app.state.customer=current
 return current
