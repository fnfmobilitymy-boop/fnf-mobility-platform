"""Server-side prices, integer MYR amounts, access capabilities and configuration."""
from dataclasses import dataclass,field
from pathlib import Path
from decimal import Decimal,InvalidOperation
import os,sys,json,hashlib,hmac,secrets,base64,re,time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'source/seo'))
from catalogue import catalogue
DETAILS=json.loads((ROOT/'source/seo/payment-details.json').read_text())
PHASES=('deposit','second','balance')
def now():return int(time.time())
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def money(raw):
 if not isinstance(raw,str) or not re.fullmatch(r'\d{1,7}(?:\.\d{1,2})?',raw):raise ValueError('Enter a MYR amount with at most two decimals')
 result=int(Decimal(raw)*100)
 if not 1<=result<=100000000:raise ValueError('Amount must be RM0.01–RM1,000,000')
 return result
def split_amount(cents,method):
 first=(cents*50+50)//100;second=(cents*30+50)//100
 values=(first,second,cents-first-second)
 if min(values)<1:raise ValueError('Quote too small for three payment stages')
 return [(v,(v*600+5000)//10000 if method=='stripe' else 0) for v in values]
def validate_items(items,lang):
 if not isinstance(items,list) or not 1<=len(items)<=30:raise ValueError('Choose 1–30 catalogue items')
 plans={p['id']:p for p in catalogue(lang)};seen=set();result=[]
 for item in items:
  p=plans.get(item.get('id'));qty=item.get('qty')
  if not p or type(qty)!=int or not p['min']<=qty<=p['max'] or p['id'] in seen:raise ValueError('Invalid catalogue item or quantity')
  seen.add(p['id']);result.append({**p,'qty':qty,'lineCents':(p['setup']+p['price']*qty)*100})
 return result
def pw_hash(password,salt=None):
 if len(password)<12:raise ValueError('Use at least 12 characters')
 salt=salt or secrets.token_hex(16)
 return 'scrypt$'+salt+'$'+hashlib.scrypt(password.encode(),salt=salt.encode(),n=16384,r=8,p=1).hex()
def pw_check(password,encoded):
 try:
  _,salt,_=encoded.split('$');return hmac.compare_digest(pw_hash(password,salt),encoded)
 except (ValueError,TypeError):return False
@dataclass
class Settings:
 data:Path=field(default_factory=lambda:Path(os.environ.get('DATA_DIR','/tmp/kenny-orders-dev')))
 secret:str=field(default_factory=lambda:os.environ.get('APP_SECRET',''))
 admin_hash:str=field(default_factory=lambda:os.environ.get('ADMIN_PASSWORD_HASH',''))
 admin_email:str=field(default_factory=lambda:os.environ.get('ADMIN_EMAIL','hello@kennystudio.cfd'))
 public_url:str=field(default_factory=lambda:(os.environ.get('PUBLIC_URL') or os.environ.get('RENDER_EXTERNAL_URL') or 'http://127.0.0.1:8188').rstrip('/'))
 origin:str=field(default_factory=lambda:os.environ.get('MAIN_SITE_ORIGIN','https://kennystudio.cfd').rstrip('/'))
 test_mode:bool=field(default_factory=lambda:os.environ.get('APP_TEST_MODE','false').lower()=='true')
 production:bool=field(default_factory=lambda:os.environ.get('APP_ENV')=='production')
 stripe_key:str=field(default_factory=lambda:os.environ.get('STRIPE_SECRET_KEY',''))
 webhook_secret:str=field(default_factory=lambda:os.environ.get('STRIPE_WEBHOOK_SECRET',''))
 def validate(self):
  if not self.admin_hash and os.environ.get('ADMIN_PASSWORD'):self.admin_hash=pw_hash(os.environ['ADMIN_PASSWORD'])
  if len(self.secret)<32 or not self.admin_hash.startswith('scrypt$'):raise RuntimeError('Configure APP_SECRET (32+ characters) and ADMIN_PASSWORD_HASH; run python -m app.setup')
  if self.production and not self.public_url.startswith('https://'):raise RuntimeError('Production PUBLIC_URL must use HTTPS')
  self.data.mkdir(parents=True,exist_ok=True);(self.data/'uploads').mkdir(exist_ok=True)
 def token(self,order_id,version=1):return hmac.new(self.secret.encode(),f'order:{order_id}:{version}'.encode(),hashlib.sha256).hexdigest()
 def link(self,order_id,version=1):return self.public_url+'/order/'+order_id+'#token='+self.token(order_id,version)
 def csrf(self,session):return hmac.new(self.secret.encode(),('csrf:'+session).encode(),hashlib.sha256).hexdigest()
