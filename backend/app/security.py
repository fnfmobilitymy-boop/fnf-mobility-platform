"""Bound request bodies before JSON/multipart parsing, including chunked requests."""
from starlette.responses import JSONResponse
class BodyLimitMiddleware:
 def __init__(self,app,max_bytes=12*1024*1024):self.app=app;self.max_bytes=max_bytes
 async def __call__(self,scope,receive,send):
  if scope['type']!='http' or scope['method'] not in ('POST','PUT','PATCH'):
   return await self.app(scope,receive,send)
  headers=dict(scope.get('headers',[]));length=headers.get(b'content-length',b'')
  if length.isdigit() and int(length)>self.max_bytes:return await JSONResponse({'detail':'Request too large'},413)(scope,receive,send)
  messages=[];total=0
  while True:
   message=await receive()
   if message['type']=='http.disconnect':return
   total+=len(message.get('body',b''))
   if total>self.max_bytes:return await JSONResponse({'detail':'Request too large'},413)(scope,receive,send)
   messages.append(message)
   if not message.get('more_body',False):break
  index=0
  async def replay():
   nonlocal index
   if index<len(messages):
    msg=messages[index];index+=1;return msg
   return await receive()
  await self.app(scope,replay,send)
