"""Server-authoritative November 2026 catalogue; stored order snapshots are immutable."""
from pricing import PLANS,MONTHLY,BACKEND,EXTRAS,UPGRADES,T,TERMS
def catalogue(lang):
 items=[dict(id=p['id'],name=T(p['name'],lang),price=p['price'],setup=0,min=1,max=10,unit=T(('projects','个项目','projek'),lang),scope=T(p['items'][0],lang),starting=p['starting'],monthly=p['monthly'],monthlyStarting=p['monthly_starting']) for p in PLANS]
 for p in PLANS:items.append(dict(id='maintenance-'+p['id'],name=T(p['name'],lang)+' / '+T(('Optional maintenance','可选维护','Penyelenggaraan pilihan'),lang),price=p['monthly'],setup=0,min=1,max=12,unit=T(('months · optional, no automatic renewal','个月 · 可选，不自动续订','bulan · pilihan, tiada pembaharuan automatik'),lang),scope=T(TERMS[0],lang),starting=p['monthly_starting']))
 for rows,monthly in [(MONTHLY,True),(BACKEND,True),(EXTRAS,False),(UPGRADES,False)]:
  for id,name,price,starting in rows:items.append(dict(id=id,name=T(name,lang),price=price,setup=0,min=1,max=12 if monthly else 100,unit=T(('months · optional, no automatic renewal','个月 · 可选，不自动续订','bulan · pilihan, tiada pembaharuan automatik') if monthly else ('one-off','一次性','sekali'),lang),scope=T(TERMS[0] if monthly else TERMS[2],lang),starting=starting))
 return items
