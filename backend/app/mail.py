"""Durable transactional outbox. Disabled until the owner configures real SMTP."""
import asyncio,os,smtplib,ssl
from email.message import EmailMessage
from email.utils import formatdate,make_msgid,parseaddr
import json
from .core import now

def deliver_once(db):
 if not all(os.environ.get(k) for k in ['SMTP_HOST','SMTP_USERNAME','SMTP_PASSWORD','SMTP_FROM']):return
 with db.connect() as c:rows=c.execute("SELECT * FROM outbox WHERE status='queued' AND attempts<5 AND next_attempt<=? ORDER BY id LIMIT 10",(now(),)).fetchall()
 for row in rows:
  try:
   msg=EmailMessage();msg['From']=os.environ['SMTP_FROM'];msg['To']=row['recipient'];msg['Subject']=row['subject'];msg['Date']=formatdate(usegmt=True);msg['Message-ID']=make_msgid(domain=parseaddr(os.environ['SMTP_FROM'])[1].split('@')[-1]);msg.set_content(row['body'])
   use_ssl=os.environ.get('SMTP_SSL','false').lower()=='true';cls=smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
   with cls(os.environ['SMTP_HOST'],int(os.environ.get('SMTP_PORT','587')),timeout=15,**({'context':ssl.create_default_context()} if use_ssl else {})) as smtp:
    if not use_ssl:smtp.starttls(context=ssl.create_default_context())
    smtp.login(os.environ['SMTP_USERNAME'],os.environ['SMTP_PASSWORD']);smtp.send_message(msg)
   with db.transaction() as c:c.execute("UPDATE outbox SET status='sent',attempts=attempts+1,error=NULL WHERE id=?",(row['id'],))
   print('Mail delivery: id='+str(row['id'])+' status=accepted',flush=True)
  except Exception as exc:
   code=getattr(exc,'smtp_code',None)
   if code is None and isinstance(exc,smtplib.SMTPRecipientsRefused):code=','.join(str(v[0]) for v in exc.recipients.values())
   print('Mail delivery: id='+str(row['id'])+' status=failed error='+type(exc).__name__+' smtp='+str(code or 'n/a'),flush=True)
   with db.transaction() as c:c.execute('UPDATE outbox SET attempts=attempts+1,next_attempt=?,error=? WHERE id=?',(now()+min(3600,60*2**row['attempts']),type(exc).__name__,row['id']))
async def deliver_loop(db):
 while True:
  try:
   await asyncio.to_thread(deliver_once,db)
   from .notifications import deliver_once as deliver_whatsapp
   await asyncio.to_thread(deliver_whatsapp,db)
  except asyncio.CancelledError:raise
  except Exception:pass
  await asyncio.sleep(30)


def verify_smtp():
 """Authenticate without sending mail; emit only safe readiness metadata."""
 if not all(os.environ.get(k) for k in ['SMTP_HOST','SMTP_USERNAME','SMTP_PASSWORD','SMTP_FROM']):
  print('SMTP verification: missing configuration',flush=True);return False
 try:
  use_ssl=os.environ.get('SMTP_SSL','false').lower()=='true';cls=smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
  with cls(os.environ['SMTP_HOST'],int(os.environ.get('SMTP_PORT','587')),timeout=15,**({'context':ssl.create_default_context()} if use_ssl else {})) as smtp:
   if not use_ssl:smtp.starttls(context=ssl.create_default_context())
   smtp.login(os.environ['SMTP_USERNAME'],os.environ['SMTP_PASSWORD'])
  print('SMTP verification: authenticated TLS; no email sent',flush=True);return True
 except Exception as exc:
  print('SMTP verification: failed '+type(exc).__name__+' code='+str(getattr(exc,'smtp_code','n/a')),flush=True);return False


def mail_diagnostics(db):
 """Operational counts only; never log recipients, bodies, passwords or OTPs."""
 with db.connect() as c:
  counts={r['status']:r['total'] for r in c.execute('SELECT status,count(*) AS total FROM outbox WHERE created>? GROUP BY status',(now()-3600,))}
  errors=[r[0] for r in c.execute("SELECT DISTINCT error FROM outbox WHERE created>? AND error IS NOT NULL",(now()-3600,))]
 info={'spacemail':os.environ.get('SMTP_HOST','').strip().lower()=='mail.spacemail.com','senderHello':parseaddr(os.environ.get('SMTP_FROM',''))[1].lower()=='hello@kennystudio.cfd','loginHello':os.environ.get('SMTP_USERNAME','').strip().lower()=='hello@kennystudio.cfd','lastHour':counts,'errorTypes':errors}
 print('Mail diagnostics: '+json.dumps(info,sort_keys=True),flush=True)
