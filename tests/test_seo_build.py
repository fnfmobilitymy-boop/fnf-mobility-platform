import unittest,subprocess,os,tempfile,json,xml.etree.ElementTree as ET,re
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
class HTML(HTMLParser):
 def __init__(self,s):super().__init__();self.tags=[];self.text=[];self.script=False;self.feed(s)
 def handle_starttag(self,t,a):self.tags.append((t,dict(a)));self.script=t=='script' or self.script
 def handle_endtag(self,t):
  if t=='script':self.script=False
 def handle_data(self,s):
  if not self.script:self.text.append(s)
 def attrs(self,t):return [a for tag,a in self.tags if tag==t]
class SEOTests(unittest.TestCase):
 def run_build(self,d,**env):return subprocess.run(['python',str(ROOT/'scripts/build_site.py')],cwd=ROOT,env={**os.environ,'SITE_URL':'','SITE_URL_VERIFIED':'false','BUILD_INDEXABLE':'false','GOOGLE_SITE_VERIFICATION':'','GA4_MEASUREMENT_ID':'','GTM_CONTAINER_ID':'','OUTPUT_DIR':d,**env},capture_output=True,text=True)
 def test_preview_has_crawlable_unique_pages_and_no_guessed_domain(self):
  with tempfile.TemporaryDirectory() as d:
   result=self.run_build(d);self.assertEqual(result.returncode,0,result.stderr);out=Path(d)
   manifest=json.loads((out/'assets/build-manifest.json').read_text());titles=[];descriptions=[]
   for path in manifest['pages']:
    p=out/('index.html' if path=='/' else path.strip('/')+'/index.html');s=p.read_text();html=HTML(s)
    self.assertEqual(len(html.attrs('h1')),1,path);self.assertFalse(any(a.get('rel')=='canonical' for a in html.attrs('link')),path)
    self.assertTrue(any(a.get('name')=='robots' and 'noindex' in a.get('content','') for a in html.attrs('meta')))
    titles.append(re.search(r'<title>(.*?)</title>',s)[1]);descriptions.append(next(a['content'] for a in html.attrs('meta') if a.get('name')=='description'))
    self.assertGreater(len(' '.join(html.text)),700,path)
   self.assertEqual(len(set(titles)),6);self.assertEqual(len(set(descriptions)),6)
   self.assertIn('Disallow: /',(out/'robots.txt').read_text());self.assertFalse((out/'sitemap.xml').exists())
   self.assertIn('Website Designer in Malaysia',titles[0]);self.assertIn('Google Ads Management',(out/'index.html').read_text());self.assertIn('SEO Services',(out/'index.html').read_text())
 def test_indexable_build_guard_and_configuration_validation(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertNotEqual(self.run_build(d,BUILD_INDEXABLE='true').returncode,0)
   self.assertNotEqual(self.run_build(d,BUILD_INDEXABLE='true',SITE_URL='https://example.invalid').returncode,0)
   self.assertNotEqual(self.run_build(d,SITE_URL='http://example.invalid').returncode,0)
   self.assertNotEqual(self.run_build(d,GA4_MEASUREMENT_ID='fake').returncode,0)
   self.assertNotEqual(self.run_build(d,GA4_MEASUREMENT_ID='G-TESTONLY',GTM_CONTAINER_ID='GTM-TESTONLY').returncode,0)
 def test_production_canonical_sitemap_schema_and_real_token_hook(self):
  # A test-only reserved domain is never copied into repository/public outputs.
  with tempfile.TemporaryDirectory() as d:
   r=self.run_build(d,BUILD_INDEXABLE='true',SITE_URL='https://example.invalid/studio/',SITE_URL_VERIFIED='true',GOOGLE_SITE_VERIFICATION='test_only_verification');self.assertEqual(r.returncode,0,r.stderr)
   m=json.loads((Path(d)/'assets/build-manifest.json').read_text());urls=[]
   for path in m['pages']:
    html=HTML((Path(d)/('index.html' if path=='/' else path.strip('/')+'/index.html')).read_text());canonical=next(a['href'] for a in html.attrs('link') if a.get('rel')=='canonical');self.assertEqual(canonical,'https://example.invalid/studio'+path);urls.append(canonical)
    self.assertTrue(any(a.get('name')=='google-site-verification' for a in html.attrs('meta')))
    s=(Path(d)/('index.html' if path=='/' else path.strip('/')+'/index.html')).read_text();data=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',s,re.S)[1]);org=data['@graph'][0]
    self.assertEqual(org['email'],'kennystudio09@gmail.com');self.assertNotIn('address',org);self.assertNotIn('aggregateRating',s);self.assertNotIn('reviewCount',s)
   sitemap=ET.parse(Path(d)/'sitemap.xml');self.assertEqual([x[0].text for x in sitemap.getroot()],urls);self.assertNotIn('404',str(urls));self.assertNotIn('preview',str(urls));self.assertIn('https://example.invalid/studio/sitemap.xml',(Path(d)/'robots.txt').read_text())
 def test_existing_projects_contacts_and_budget_choices_preserved(self):
  source=max(re.findall(r'<script[^>]*>(.*?)</script>',(ROOT/'source/seo/legacy-export.html').read_text(),re.S),key=len);m=json.loads((ROOT/'assets/build-manifest.json').read_text());app=(ROOT/m['app']).read_text()
  self.assertEqual(set(re.findall(r'RM[\d,.–-]+',source)),set(re.findall(r'RM[\d,.–-]+',app)))
  projects=json.loads((ROOT/'media/projects/manifest.json').read_text());self.assertEqual(len(projects),20)
  for p in projects:self.assertTrue((ROOT/'media/projects'/f"{p['id']}.webp").exists());self.assertIn(p['id'],app)
  for contact in ['kennystudio09@gmail.com','DHXOYXRCJIKZK1','t.me/KennyStudio','+6011-6773 5644']:self.assertTrue(contact in app,contact)
  for name in ['Landing Pages','Personal Brand Websites','Business Websites','E-commerce Websites','Booking & Reservations','CMS & Admin Dashboards','Custom Web Systems','Backend & Integrations','Website Redesign','SEO, Launch & Care']:self.assertIn(name,app)
 def test_tracking_not_emitted_in_unapproved_preview(self):
  for p in [ROOT/'index.html',ROOT/'services/seo/index.html']:
   data=json.loads(re.search(r'<script type="application/json" id="site-options">(.*?)</script>',p.read_text(),re.S)[1]);self.assertEqual(data['tracking'],{'ga4':'','gtm':''})
if __name__=='__main__':unittest.main()
