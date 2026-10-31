"""Owner WhatsApp template notifications. Never sent in test mode or without Cloud API setup."""
import os,httpx
from .core import now

def whatsapp_ready():return all(os.environ.get(k) for k in ['WHATSAPP_ACCESS_TOKEN','WHATSAPP_PHONE_NUMBER_ID','WHATSAPP_NOTIFY_TO','WHATSAPP_TEMPLATE_NAME','WHATSAPP_TEMPLATE_LANGUAGE','WHATSAPP_API_VERSION'])
def queue_owner(c,oid,summary):
 c.execute('INSERT OR IGNORE INTO owner_notifications(order_id,created,summary) VALUES(?,?,?)',(oid,now(),summary[:6000]))
def deliver_once(db):
 if os.environ.get('APP_TEST_MODE','false').lower()=='true' or not whatsapp_ready():return
 version=os.environ['WHATSAPP_API_VERSION'];phone=os.environ['WHATSAPP_PHONE_NUMBER_ID'];recipient=os.environ['WHATSAPP_NOTIFY_TO']
 if not phone.isdigit() or not recipient.lstrip('+').isdigit() or not __import__('re').fullmatch(r'v\d+\.\d+',version):return
 with db.connect() as c:rows=c.execute("SELECT * FROM owner_notifications WHERE status='queued' AND attempts<3 AND next_attempt<=? ORDER BY id LIMIT 5",(now(),)).fetchall()
 for row in rows:
  payload={'messaging_product':'whatsapp','to':recipient.lstrip('+'),'type':'template','template':{'name':os.environ['WHATSAPP_TEMPLATE_NAME'],'language':{'code':os.environ['WHATSAPP_TEMPLATE_LANGUAGE']},'components':[{'type':'body','parameters':[{'type':'text','text':' '.join(row['summary'].split())[:900]}]}]}}
  try:
   response=httpx.post('https://graph.facebook.com/'+version+'/'+phone+'/messages',headers={'Authorization':'Bearer '+os.environ['WHATSAPP_ACCESS_TOKEN']},json=payload,timeout=15);response.raise_for_status()
   mid=response.json()['messages'][0]['id']
   with db.transaction() as c:c.execute("UPDATE owner_notifications SET status='accepted',provider_id=?,attempts=attempts+1,error='' WHERE id=?",(mid,row['id']))
  except (httpx.HTTPError,KeyError,ValueError):
   with db.transaction() as c:c.execute("UPDATE owner_notifications SET attempts=attempts+1,next_attempt=?,error='Cloud API request failed; check account, template and credentials' WHERE id=?",(now()+300*2**row['attempts'],row['id']))
