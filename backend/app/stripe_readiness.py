"""Read-only Stripe checks. Never return keys, customer data or account identifiers."""
import httpx

async def verify_stripe(cfg):
 result={'keyConfigured':bool(cfg.stripe_key),'signingSecretConfigured':bool(cfg.webhook_secret),'signingSecretFormat':cfg.webhook_secret.startswith('whsec_'),'liveKey':cfg.stripe_key.startswith('sk_live_'),'authenticated':False,'chargesEnabled':False,'webhookEndpointReady':False}
 if not cfg.stripe_key or not cfg.webhook_secret:return result
 try:
  async with httpx.AsyncClient(timeout=15) as client:
   account=await client.get('https://api.stripe.com/v1/account',auth=(cfg.stripe_key,''))
   result['accountHTTP']=account.status_code
   if account.status_code!=200:return result
   result['authenticated']=True;result['chargesEnabled']=bool(account.json().get('charges_enabled'))
   hooks=await client.get('https://api.stripe.com/v1/webhook_endpoints',params={'limit':100},auth=(cfg.stripe_key,''))
   result['webhookHTTP']=hooks.status_code
   if hooks.status_code==200:
    expected={'checkout.session.completed','checkout.session.async_payment_succeeded'}
    result['webhookEndpointReady']=any(e.get('url')==cfg.public_url+'/api/stripe/webhook' and e.get('status')=='enabled' and (expected.issubset(set(e.get('enabled_events',[]))) or '*' in e.get('enabled_events',[])) and bool(e.get('livemode'))==result['liveKey'] for e in hooks.json().get('data',[]))
 except (httpx.HTTPError,ValueError,TypeError):result['verificationError']='provider unavailable or invalid response'
 return result
