"""Approved price catalogue; quantity units and special minimums are explicit."""
from pricing import PLANS,CARE,ADDONS,SEARCH,T

def catalogue(lang):
 items=[{'id':p['id'],'name':T(p['name'],lang),'price':p['price'],'setup':0,'min':1,'max':10,'unit':T(('projects','个项目','projek'),lang),'scope':T(p['items'][0],lang),'starting':True} for p in PLANS]
 for i,(name,price,scopes) in enumerate(CARE):items.append({'id':'care-'+str(i),'name':name,'price':price,'setup':0,'min':1,'max':12,'unit':T(('months · no automatic renewal','个月 · 不自动续订','bulan · tiada pembaharuan automatik'),lang),'scope':' / '.join(T(v,lang) for v in scopes),'starting':i==2})
 for i,(name,price,unit,scope,starting) in enumerate(ADDONS):
  items.append({'id':'addon-'+str(i),'name':T(name,lang),'price':150 if i==6 else price,'setup':500 if i==6 else 0,'min':5 if i==8 else 1,'max':100,'unit':T(('pages + RM500 setup','页＋RM500 设置费','halaman + persediaan RM500'),lang) if i==6 else T(unit,lang),'scope':T(scope,lang),'starting':starting})
 for i,(name,price,starting,unit,scope,form) in enumerate(SEARCH):items.append({'id':'search-'+str(i),'name':T(name,lang),'price':price,'setup':0,'min':1,'max':12 if i in [2,4] else 10,'unit':T(unit,lang),'scope':T(scope,lang),'starting':starting})
 return items
