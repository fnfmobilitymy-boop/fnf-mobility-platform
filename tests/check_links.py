from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin,urlparse,unquote
import re
ROOT=Path(__file__).resolve().parents[1];BASE='https://preview.invalid/studio/'
class Parser(HTMLParser):
 def __init__(self,s):super().__init__();self.links=[];self.ids=set();self.feed(s)
 def handle_starttag(self,t,a):
  a=dict(a)
  if 'id'in a:self.ids.add(a['id'])
  for k in ['href','src']:
   if a.get(k):self.links.append(a[k])
pages=[ROOT/'index.html',*ROOT.glob('services/**/index.html'),ROOT/'privacy/index.html',ROOT/'pricing/index.html',ROOT/'order/index.html',ROOT/'payment/index.html',ROOT/'cart/index.html'];bad=[];count=0
for file in pages:
 path=file.relative_to(ROOT).as_posix().replace('index.html','');p=Parser(file.read_text())
 for link in p.links:
  u=urlparse(urljoin(BASE+path,link))
  if u.scheme not in ['http','https'] or u.hostname!='preview.invalid':continue
  rel=unquote(u.path).removeprefix('/studio/');target=ROOT/rel
  if target.is_dir():target=target/'index.html'
  count+=1
  if not target.exists():bad.append((path,link,'missing path'));continue
  if u.fragment and target.suffix=='.html' and u.fragment not in Parser(target.read_text()).ids:bad.append((path,link,'missing anchor'))
for file in ROOT.glob('assets/*.css'):
 if not re.search(r'\.[0-9a-f]{10}\.css$',file.name):continue
 for link in re.findall(r'url\(["\']?([^\)"\']+)',file.read_text()):
  if link.startswith(('data:','#','http')):continue
  if not (file.parent/link).resolve().exists():bad.append((str(file),link,'missing CSS asset'))
assert not bad,bad
print('PASS',count,'internal HTML links/assets, section anchors and local CSS font URLs')
