#!/usr/bin/env python3
"""Static build around the actual retained React export; no framework migration."""
from pathlib import Path
from html import escape as E
from urllib.parse import urlparse
import os,re,json,hashlib,base64,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source/seo'))
from content import SERVICES,CONTACT,HOME_TITLE,HOME_DESCRIPTION
from ui import UI
from cart import render as render_cart
from ordering import render as render_order
from payments import render as render_payment
from pricing import render as render_pricing, PLANS as PRICING_PLANS
OUT=Path(os.environ.get('OUTPUT_DIR',str(ROOT))).resolve();OUT.mkdir(parents=True,exist_ok=True)
ORIGIN=os.environ.get('SITE_URL','').strip().rstrip('/')
INDEXABLE=os.environ.get('BUILD_INDEXABLE','false').lower()=='true'
VERIFIED=os.environ.get('SITE_URL_VERIFIED','false').lower()=='true'
if ORIGIN:
 u=urlparse(ORIGIN)
 if u.scheme!='https' or not u.hostname or u.query or u.fragment or u.username:raise SystemExit('SITE_URL must be a clean HTTPS base URL, optionally with a deployment path.')
if INDEXABLE and (not ORIGIN or not VERIFIED):raise SystemExit('Indexable build blocked: set SITE_URL and confirm SITE_URL_VERIFIED=true after checking production DNS/hosting.')
GSC=os.environ.get('GOOGLE_SITE_VERIFICATION','').strip();GA=os.environ.get('GA4_MEASUREMENT_ID','').strip();GTM=os.environ.get('GTM_CONTAINER_ID','').strip()
if GSC and not re.fullmatch(r'[A-Za-z0-9_-]{10,300}',GSC):raise SystemExit('Invalid Search Console verification token.')
if GA and not re.fullmatch(r'G-[A-Z0-9]+',GA):raise SystemExit('Invalid GA4 measurement ID.')
if GTM and not re.fullmatch(r'GTM-[A-Z0-9]+',GTM):raise SystemExit('Invalid GTM container ID.')
if GA and GTM:raise SystemExit('Configure GA4 or GTM, not both, to avoid duplicate measurement.')
# Preview builds never load optional analytics, even when deployment credentials are present.
TRACKING={'ga4':GA if INDEXABLE else '', 'gtm':GTM if INDEXABLE else ''}
PAGES={'/':(HOME_TITLE,HOME_DESCRIPTION),'/services/':('Website Design, Google Ads & SEO Services | Kenny Studio','Explore website design, Google Ads management and SEO services from Kenny Studio in Malaysia. Clear deliverables and project-specific quotes for your business.'),**{f'/services/{k}/':(v['title'],v['description']) for k,v in SERVICES.items()},'/pricing/':('Website Design Packages & Pricing Malaysia | Kenny Studio','Website packages from RM1,000: landing pages, personal brands, business websites and e-commerce. Compare monthly care, add-ons, SEO and Google Ads fees.'),'/privacy/':('Privacy & Analytics Choices | Kenny Studio','How Kenny Studio enquiry forms, local preferences and optional consent-based analytics work. Contact Kenny about your information and privacy choices.')}
def j(v):return json.dumps(v,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
def write(path,text):
 p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
def asset(name,content):
 suffix=hashlib.sha256(content.encode()).hexdigest()[:10];p=f'assets/{name.rsplit(".",1)[0]}.{suffix}.{name.rsplit(".",1)[1]}';write(p,content);return p
legacy=(ROOT/'source/seo/legacy-export.html').read_text()
css='\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',legacy,re.S))
# Preserve the original direct-child layout rules with React-owned chapter shells.
# Duplicate full selectors rather than weakening them to arbitrary descendants.
def chapter_selectors(match):
 selector=match.group(1)
 patched=re.sub(r'main\s*>\s*section', 'main>.chapter-shell>section', selector)
 return selector+(','+patched if patched!=selector else '')+'{'
css=re.sub(r'(?:^|(?<=[{}]))([^{}]+)\{',chapter_selectors,css)
if (ROOT/'assets/reference-motion.css').exists():css+='\n'+(ROOT/'assets/reference-motion.css').read_text()
font_count=0
font_files=[]
def font(m):
 global font_count
 data=base64.b64decode(m[1]);name=f'font-{hashlib.sha256(data).hexdigest()[:10]}.woff2';p=OUT/'assets/fonts'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);font_count+=1;font_files.append('assets/fonts/'+name);return 'url("./fonts/'+name+'")'
css=re.sub(r'url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)\)',font,css)
CSS=asset('portfolio.css',css);EXTRA=asset('services.css',(ROOT/'assets/service-pages.css').read_text())
app=max(re.findall(r'<script[^>]*>(.*?)</script>',legacy,re.S),key=len)
# Keep reference motion editable apart from the retained bundled export.
motion=ROOT/'source/motion/chapter-flow.js'
if motion.exists():
 start=app.rfind('function ol(e,t,n){');assert start>=0
 end=app.index('},[t])}',start)+len('},[t])}')
 app=app[:start]+motion.read_text()+app[end:]
def replace(old,new,count=1):
 global app
 if old not in app:raise SystemExit('Legacy patch marker missing: '+old[:70])
 app=app.replace(old,new,count)
replace('document.title=`Kenny Studio — Web Design & Development`','document.title='+j(HOME_TITLE))
replace('`Distinctive websites built with character. Explore Kenny’s selected work and get in touch to create your next website.`',j(HOME_DESCRIPTION))
old='I’m Kenny, an independent web designer with 2 years of experience. I create distinctive websites with clear content and an intuitive experience.'
new='I’m Kenny, a freelance website designer based in Malaysia. I build landing pages, business websites and e-commerce experiences, with Google Ads management and SEO services available to support your next stage.'
replace('`'+old+'`','`'+new+'`',count=1)
replace('`> INDEPENDENT DESIGN & DEVELOPMENT · 2026`','`> FREELANCE WEBSITE DESIGNER IN MALAYSIA · 2026`')
replace("import('./frames/globe/globe.js?v=zoom1')",'import(new URL("frames/globe/globe.js?v=stability2",document.baseURI).href)')
# Keep every original service and add two; no original budget/price strings are changed.
marker=']],w=!!(Q.contact.email'
replace(marker,'],[`11`,`Google Ads Management`,`↗`,b?`搜索广告建立、关键词、预算与咨询追踪，按实际数据持续优化，广告费用与管理费分开。`:`Search campaign setup, keyword research, budget monitoring and lead tracking, with separate ad spend and management fees.`],[`12`,`SEO Services`,`◎`,b?`网站审查、技术与页面优化、搜索设置及表现报告，按实际业务另行评估本地商家资料。`:`Website audits, technical and on-page SEO, search setup and reporting, with local business-profile work scoped separately.`]],w=!!(Q.contact.email')
replace('{id:`contact`,label:`CONTACT`,zh:`联系我`}','{id:`pricing`,label:`PRICING`,zh:`套餐价格`,href:`./pricing/`},{id:`google-ads`,label:`GOOGLE ADS`,zh:`Google 广告`,href:`./services/google-ads-management/`},{id:`seo-service`,label:`SEO`,zh:`SEO 优化`,href:`./services/seo/`},{id:`contact`,label:`CONTACT`,zh:`联系我`}')
replace('href:`#${e.id}`,"aria-current":a===e.id','href:e.href||`#${e.id}`,"aria-current":a===e.id')
replace('onClick:t=>{t.preventDefault(),S(e.id)}','onClick:t=>{if(e.href)return;t.preventDefault(),S(e.id)}')
replace('const c=dictionaries[lang]||dictionaries.en;',"const originalCopy=dictionaries[lang]||dictionaries.en,c={...originalCopy,types:[...originalCopy.types.slice(0,-1),...({en:['Google Ads management','SEO services'],zh:['Google Ads 广告管理','SEO 搜索优化'],ms:['Pengurusan Google Ads','Perkhidmatan SEO']}[lang]),originalCopy.types.at(-1)]};")
replace("'maintenance','other'],featureIds", "'maintenance','google-ads','seo','other'],featureIds")
replace(" const update=(key,value)"," y.useEffect(()=>{const requested=new URLSearchParams(location.search).get('service');if(typeIds.includes(requested))setFields(old=>({...old,type:requested}))},[]);\n const update=(key,value)")
# Safe JSX-level enrichment keeps React ownership of the DOM and existing animation behaviour.
replace("props={...props};if(props.id==='hero-title'", "props={...props};if(type==='img'){props.decoding='async';if(props.className?.includes('kenny-hero-origin')){props.fetchPriority='high';props.loading='eager'}else if(!props.loading)props.loading='lazy';if(props.src?.includes('/projects/')&&props.alt)props.alt=({en:'Homepage screenshot of ',zh:'网站首页截图：',ms:'Tangkapan skrin laman utama '}[KENNY_LOCALE])+props.alt}if(props.className==='skills-heading')props.children=[props.children,kennyServiceLinks()];if(props.className==='skill-card'){const number=String(props.children?.[0]?.props?.children||'');const slug=number==='11'?'google-ads-management':number==='12'||number==='10'?'seo':'website-design';props.children=[...props.children,y.createElement('a',{className:'seo-card-link',href:'./services/'+slug+'/'},kennyText('Explore service')+' ↗')]}if(props.id==='hero-title'")
replace('kennyJsx(Z.jsx,KennyProjectBrief,{language:siteLanguage})','kennyJsx(Z.jsx,KennyProjectBrief,{language:siteLanguage}),kennyJsx(Z.jsx,`nav`,{className:`seo-service-links seo-footer-links`,"aria-label":`Service and privacy links`,children:[kennyJsx(Z.jsx,`a`,{href:`./pricing/`,children:`Packages & Pricing`}),kennyJsx(Z.jsx,`a`,{href:`./services/`,children:`All services`}),kennyJsx(Z.jsx,`a`,{href:`./services/google-ads-management/`,children:`Google Ads Management`}),kennyJsx(Z.jsx,`a`,{href:`./services/seo/`,children:`SEO Services`}),kennyJsx(Z.jsx,`a`,{href:`./privacy/`,children:`Privacy & analytics`})]})')
translations={'zh':{'Google Ads Management':'Google Ads 广告管理','SEO Services':'SEO 搜索优化','GOOGLE ADS':'Google 广告','SEO':'SEO 优化','Explore service':'了解服务','All services':'全部服务','Privacy & analytics':'隐私与分析设置',new:'我是 Kenny，一名立足马来西亚的独立网页设计师。提供落地页、企业网站、电商体验，也可按需求提供 Google Ads 管理与 SEO 服务。','> FREELANCE WEBSITE DESIGNER IN MALAYSIA · 2026':'> 马来西亚独立网页设计师 · 2026'},'ms':{'Google Ads Management':'Pengurusan Google Ads','SEO Services':'Perkhidmatan SEO','Explore service':'Terokai perkhidmatan','All services':'Semua perkhidmatan','Privacy & analytics':'Privasi & analitik',new:'Saya Kenny, pereka laman web bebas di Malaysia. Saya membina halaman pendaratan, laman perniagaan dan e-dagang, serta menyediakan pengurusan Google Ads dan SEO mengikut keperluan.','> FREELANCE WEBSITE DESIGNER IN MALAYSIA · 2026':'> PEREKA LAMAN WEB BEBAS DI MALAYSIA · 2026','Search campaign setup, keyword research, budget monitoring and lead tracking, with separate ad spend and management fees.':'Persediaan kempen, kajian kata kunci, pemantauan bajet dan penjejakan pertanyaan, dengan belanja iklan serta fi pengurusan berasingan.','Website audits, technical and on-page SEO, search setup and reporting, with local business-profile work scoped separately.':'Audit, SEO teknikal dan pada halaman, tetapan carian serta laporan; skop profil tempatan dinilai berasingan.'}}
translations['ms'].update({'RESTAURANT DEMO':'DEMO RESTORAN','Restaurant concept demo. Explore the website.':'Demo konsep restoran. Terokai laman web.'})
translations['ms'].update({'CREATIVE LANDING PAGE DEMO':'DEMO HALAMAN PENDARATAN KREATIF','Journey to the West character collection landing page demo.':'Demo halaman pendaratan koleksi watak bertemakan Journey to the West.'})
translations['ms'].update({'TRANSPORT & TRAVEL WEBSITE':'LAMAN WEB PENGANGKUTAN & PELANCONGAN','Private chauffeur, airport transfer and travel website.':'Laman web pemandu persendirian, pemindahan lapangan terbang dan pelancongan.'})
translations['ms'].update({'FURNITURE SERVICE DEMO':'DEMO PERKHIDMATAN PERABOT','Furniture restoration and sofa upholstery website demo.':'Demo laman web pemulihan perabot dan upholsteri sofa.'})
translations['ms'].update({'PROPERTY AGENT PERSONAL WEBSITE DEMO':'DEMO LAMAN PERIBADI EJEN HARTANAH','Property agent personal brand website demo with property listings and enquiry journeys.':'Demo laman jenama peribadi ejen hartanah dengan senarai hartanah dan aliran pertanyaan.'})
translations['ms'].update({'E-COMMERCE WEBSITE DEMO':'DEMO LAMAN WEB E-DAGANG','Footwear e-commerce concept demo with product browsing, shopping bag and checkout journeys.':'Demo konsep e-dagang kasut dengan pelayaran produk, beg beli-belah dan aliran pembayaran.'})
translations['ms'].update({'HAIR SALON LANDING PAGE DEMO':'DEMO HALAMAN PENDARATAN SALUN RAMBUT','Hair salon landing page concept demo with services, styling lookbook and appointment planning.':'Demo konsep halaman pendaratan salun rambut dengan perkhidmatan, galeri gaya dan perancangan janji temu.'})
translations['ms'].update({'BARBER SHOP LANDING PAGE DEMO':'DEMO HALAMAN PENDARATAN KEDAI GUNTING','Barber shop landing page concept demo with cinematic video, grooming services and a booking experience.':'Demo konsep halaman pendaratan kedai gunting dengan video sinematik, perkhidmatan dandanan dan pengalaman tempahan.'})
translations['zh'].update({'Packages & Pricing':'套餐与价格','PRICING':'套餐价格'})
translations['ms'].update({'Packages & Pricing':'Pakej & Harga','PRICING':'HARGA'})
helper=''.join('Object.assign(KENNY_TRANSLATIONS.'+lang+','+j(v)+');' for lang,v in translations.items())+'''function kennyServiceLinks(){return y.createElement('nav',{className:'seo-service-links','aria-label':kennyText('All services')},...[['./pricing/','Packages & Pricing'],['./services/','All services'],['./services/website-design/','Website Design'],['./services/google-ads-management/','Google Ads Management'],['./services/seo/','SEO Services']].map(([href,text])=>y.createElement('a',{href,key:href},kennyText(text)+' ↗')))}'''
replace('function Al(){',helper+'function Al(){')
# React owns chapter wrappers so language changes and unmount cleanup stay safe.
replace('return factory(type,props,key)',"const node=factory(type,props,key);return type==='section'&&props?.id?factory('div',{className:'chapter-shell','data-chapter-id':props.id,children:node},key):node")
replace('return y.createElement(type,props,...children)',"const node=y.createElement(type,props,...children);return type==='section'&&props?.id?y.createElement('div',{className:'chapter-shell','data-chapter-id':props.id,key:props.key},node):node")
app=app.replace('main > section[id]','main > .chapter-shell > section[id], main > section[id]')
replace("return y.createElement('section',{id:'coverage'","return kennyElement('section',{id:'coverage'")
# The fluid simulation sleeps over interactive chapters and during page scrolling.
replace('let touchDevice=matchMedia',"const kennyMotionRoot=r.closest('.kenny-portfolio');let touchDevice=matchMedia")
replace('if(C=0,document.hidden||e-T>1850)',"if(C=0,document.hidden||kennyMotionRoot?.matches('.is-scrolling,.chapter-interaction-active')||e-T>1850)")
replace('if(![`mouse`,`pen`,`touch`].includes(e.pointerType)||document.hidden)return;',"if(![`mouse`,`pen`,`touch`].includes(e.pointerType)||document.hidden||kennyMotionRoot?.matches('.is-scrolling,.chapter-interaction-active'))return;")
APP=asset('portfolio.js',app)
# Shared static page behaviour and consent loading. Tracking IDs remain empty by default.
RUNTIME=asset('site.js',(ROOT/'assets/site-runtime.js').read_text()+'\n'+(ROOT/'source/payments/calculation.js').read_text()+'\n'+(ROOT/'source/payments/payment-runtime.js').read_text()+'\n'+(ROOT/'source/payments/cart-runtime.js').read_text()+'\n'+(ROOT/'source/payments/invoice-runtime.js').read_text())
favicon=re.search(r'<link rel="icon"[^>]*>',legacy)[0]
def url(path):return ORIGIN+path if ORIGIN else None
def graph(path,title,kind):
 if not INDEXABLE:return None
 org={'@type':'Organization','@id':url('/#organization'),'name':'Kenny Studio','url':url('/'),'email':CONTACT['email'],'telephone':CONTACT['phone'],'areaServed':[{'@type':'Country','name':'Malaysia'}]}
 site={'@type':'WebSite','@id':url('/#website'),'name':'Kenny Studio','url':url('/'),'publisher':{'@id':url('/#organization')}}
 nodes=[org,site,{'@type':'WebPage','@id':url(path+'#page'),'url':url(path),'name':title,'isPartOf':{'@id':url('/#website')}}]
 if kind in SERVICES:nodes.append({'@type':'Service','@id':url(path+'#service'),'name':SERVICES[kind]['type'],'serviceType':SERVICES[kind]['type'],'url':url(path),'provider':{'@id':url('/#organization')},'areaServed':{'@type':'Country','name':'Malaysia'},'description':SERVICES[kind]['description']})
 if kind=='pricing':
  nodes.append({'@type':'OfferCatalog','name':'Kenny Studio Website Packages','itemListElement':[{'@type':'Offer','name':p['name'][0],'url':url('/pricing/#website-packages'),'priceSpecification':{'@type':'PriceSpecification','minPrice':p['price'],'priceCurrency':'MYR'},'itemOffered':{'@type':'Service','name':p['name'][0],'provider':{'@id':url('/#organization')}}} for p in PRICING_PLANS]})
 if path!='/':
  labels=[('Home','/'),('Services','/services/')]+([(SERVICES[kind]['type'],path)] if kind in SERVICES else []) if path.startswith('/services') else [('Home','/'),('Packages & Pricing' if kind=='pricing' else 'Start an Order Request' if kind=='order' else 'Payment Instructions' if kind=='payment' else 'Privacy',path)]
  nodes.append({'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i+1,'name':name,'item':url(p)} for i,(name,p) in enumerate(labels)]})
 return {'@context':'https://schema.org','@graph':nodes}
def head(path,title,desc,prefix,kind=''):
 canonical=url(path) if INDEXABLE else None;image=url('/kenny-studio-share-20261021.jpg') if ORIGIN else None
 out='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#08070d">'
 out+='<title>'+E(title)+'</title><meta name="description" content="'+E(desc,quote=True)+'"><meta name="robots" content="'+('index, follow, max-image-preview:large' if INDEXABLE and path not in ['/order/','/payment/','/cart/'] else 'noindex, follow')+'">'
 if canonical:out+='<link rel="canonical" href="'+E(canonical)+'">'
 tags={'og:type':'website','og:site_name':'Kenny Studio','og:locale':'en_MY','og:title':title,'og:description':desc}
 if canonical:tags['og:url']=canonical
 if image:tags.update({'og:image':image,'og:image:secure_url':image,'og:image:type':'image/jpeg','og:image:width':'1200','og:image:height':'630','og:image:alt':'Kenny Studio website design portfolio.'})
 out+=''.join('<meta property="'+k+'" content="'+E(v,quote=True)+'">' for k,v in tags.items())
 out+='<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="'+E(title,quote=True)+'"><meta name="twitter:description" content="'+E(desc,quote=True)+'">'
 if image:out+='<meta name="twitter:image" content="'+E(image)+'"><meta name="twitter:image:alt" content="Kenny Studio website design portfolio.">'
 if GSC:out+='<meta name="google-site-verification" content="'+E(GSC)+'">'
 data=graph(path,title,kind)
 if data:out+='<script type="application/ld+json">'+j(data)+'</script>'
 out+=favicon+('<link rel="preload" as="font" type="font/woff2" crossorigin href="'+prefix+font_files[0]+'">' if font_files else '')+'<link rel="stylesheet" href="'+prefix+CSS+'"><link rel="stylesheet" href="'+prefix+EXTRA+'">'
 if path=='/':out+='<link rel="preload" as="font" href="'+prefix+'assets/fonts/manrope-variable.ttf" type="font/ttf" crossorigin><link rel="stylesheet" href="./frames/globe/globe.css"><link rel="preload" as="image" href="./media/play-first.webp" fetchpriority="high">'
 out+='<script type="application/json" id="site-options">'+j({'tracking':TRACKING,'ui':UI})+'</script><script defer src="'+prefix+RUNTIME+'"></script>'
 if path=='/':out+='<script defer src="./'+APP+'"></script>'
 return out+'</head>'
def href(prefix,path):return prefix+path.lstrip('/') if path!='/' else prefix or './'
def cta(prefix,kind,lang):
 d=SERVICES[kind]['locales'][lang];return '<a class="service-button" href="'+prefix+'?service='+SERVICES[kind]['form']+'#project-brief">'+E(d['cta'])+' <span aria-hidden="true">↗</span></a>'
def crumbs(prefix,kind,lang):
 u=UI[lang];items=[('<a href="'+href(prefix,'/')+'">'+u['home']+'</a>')]
 if kind in SERVICES:items+=['<a href="'+href(prefix,'/services/')+'">'+u['services']+'</a>',SERVICES[kind]['locales'][lang]['label']]
 else:items+=[u['privacy'] if kind=='privacy' else u['services']]
 return '<nav aria-label="Breadcrumb"><ol class="service-crumbs">'+''.join('<li>'+x+'</li>' for x in items)+'</ol></nav>'
def cards(prefix,lang,exclude=None):
 return '<div class="service-related">'+''.join('<article class="service-card"><span>'+s['number']+' / '+E(s['locales'][lang]['eyebrow'])+'</span><h3>'+E(s['locales'][lang]['label'])+'</h3><p>'+E(s['locales'][lang]['intro'])+'</p><a class="service-text-link" href="'+href(prefix,'/services/'+k+'/')+'">'+E(UI[lang]['view'])+' ↗</a></article>' for k,s in SERVICES.items() if k!=exclude)+'</div>'
def contact(prefix,lang):
 u=UI[lang];return '<section class="service-section"><div class="service-contact"><span class="service-eyebrow">KENNY STUDIO / MALAYSIA</span><h2>'+E(u['next'])+'</h2><p>'+E(u['nextBody'])+'</p><div class="service-actions"><a class="service-button" href="'+prefix+'#project-brief">'+E(u['quote'])+' ↗</a><a class="service-text-link" href="mailto:'+CONTACT['email']+'">'+CONTACT['email']+'</a></div></div></section>'
def page_body(kind,prefix,lang):
 u=UI[lang]
 if kind=='pricing':return render_pricing(prefix,lang)
 out=crumbs(prefix,kind,lang)
 if kind=='privacy':return out+'<section class="service-section"><span class="service-eyebrow">KENNY STUDIO / PRIVACY</span><h1>'+E(u['privacyTitle'])+'</h1>'+''.join('<p>'+E(p)+'</p>' for p in u['privacyBody'])+'<button type="button" class="analytics-settings">'+E(u['analytics'])+'</button></section>'
 if kind=='services':
  out+='<section class="service-hero"><div><span class="service-eyebrow">KENNY STUDIO / MALAYSIA</span><h1>'+E(u['allTitle'])+'</h1><p class="service-lead">'+E(u['allIntro'])+'</p></div><div class="service-orbit" aria-hidden="true"><strong>K+</strong><span>DESIGN / SEARCH / EXPERIENCE</span></div></section>'+cards(prefix,lang)
  for extra in ['google-ads-management','seo']:
   d=SERVICES[extra]['locales'][lang];out+='<section id="'+extra+'" class="service-section"><span class="service-eyebrow">'+E(d['eyebrow'])+'</span><h2>'+E(d['label'])+'</h2><p>'+E(d['intro'])+'</p><ul class="service-inclusions">'+''.join('<li>'+E(name)+'</li>' for name,_ in d['items'])+'</ul><aside class="service-note">'+E(d['note'])+'</aside><div class="service-actions">'+cta(prefix,extra,lang)+'<a class="service-text-link" href="'+href(prefix,'/services/'+extra+'/')+'">'+E(u['view'])+' ↗</a></div></section>'
  out+='<section class="service-section"><h2>'+E(u['existing'])+'</h2><p>'+E(u['existingIntro'])+'</p><div class="service-grid">'
  names=['Landing Pages','Personal Brand Websites','Business Websites','E-commerce Websites','Booking & Reservations','CMS & Admin Dashboards','Custom Web Systems','Backend & Integrations','Website Redesign','SEO, Launch & Care']
  if lang=='zh':names=['落地页设计','个人品牌网站','企业网站','电商网站','预约与预订','内容管理与后台','定制网站系统','后端与整合','网站改版','搜索优化、上线与维护']
  if lang=='ms':names=['Halaman pendaratan','Jenama peribadi','Laman perniagaan','E-dagang','Tempahan','CMS & papan pemuka','Sistem tersuai','Backend & integrasi','Reka bentuk semula','SEO, pelancaran & penjagaan']
  out+=''.join('<article class="service-card"><span>'+str(i+1).zfill(2)+'</span><h3>'+E(n)+'</h3><a class="service-text-link" href="'+href(prefix,'/services/website-design/')+'">'+E(u['view'])+' ↗</a></article>' for i,n in enumerate(names))+'</div></section>'
 else:
  s=SERVICES[kind];d=s['locales'][lang]
  out+='<section class="service-hero"><div><span class="service-eyebrow">'+E(d['eyebrow'])+'</span><h1>'+E(d['h1'])+'</h1><p class="service-lead">'+E(d['intro'])+'</p><div class="service-actions">'+cta(prefix,kind,lang)+'<a class="service-text-link" href="'+href(prefix,'/#projects')+'">'+E(u['back'])+' ↗</a></div></div><div class="service-orbit" aria-hidden="true"><strong>'+s['number']+'</strong><span>'+E(d['label'])+'</span></div></section>'
  out+='<section class="service-section"><span class="service-eyebrow">'+E(u['scope'])+'</span><h2>'+E(d['scope'])+'</h2><div class="service-grid">'+''.join('<article class="service-card"><span>'+str(i+1).zfill(2)+'</span><h3>'+E(n)+'</h3><p>'+E(p)+'</p></article>' for i,(n,p) in enumerate(d['items']))+'</div><aside class="service-note">'+E(d['note'])+'</aside></section>'
  out+='<section class="service-section service-split"><div><h2>'+E(d['outcome'])+'</h2><p>'+E(d['body'])+'</p></div><div><h2>'+E(u['process'])+'</h2>'+''.join('<div class="service-step"><span>'+str(i+1).zfill(2)+'</span><div><h3>'+E(n)+'</h3><p>'+E(p)+'</p></div></div>' for i,(n,p) in enumerate(u['processItems']))+'</div></section>'
  out+='<section class="service-section"><h2>'+E(u['audience'])+'</h2><p>'+E(u['audienceBody'])+'</p></section><section class="service-section"><h2>'+E(u['faq'])+'</h2>'+''.join('<details class="service-faq"><summary>'+E(n)+'</summary><p>'+E(p)+'</p></details>' for n,p in d['faq'])+'</section>'
  if kind=='website-design':
   projects=json.loads((ROOT/'source/seo/project-previews.json').read_text());out+='<section class="service-section"><h2>'+E(u['back'])+'</h2><div class="service-projects">'+''.join('<a href="'+E(x['url'])+'" target="_blank" rel="noopener noreferrer"><img src="'+prefix+'media/projects/'+x['slug']+'.webp" alt="'+E('Homepage screenshot of '+x['name'])+'" width="'+str(x['width'])+'" height="'+str(x['height'])+'" loading="lazy" decoding="async"><h3>'+E(x['name'])+' ↗</h3></a>' for x in projects)+'</div></section>'
  out+='<section class="service-section"><h2>'+E(u['related'])+'</h2><p>'+E(u['relatedIntro'])+'</p>'+cards(prefix,lang,kind)+'</section>'
 out+='<section class="service-section service-price-entry"><span class="service-eyebrow">KENNY STUDIO / '+E(u['pricing'])+'</span><h2>'+E(u['pricingTitle'])+'</h2><p>'+E(u['pricingBody'])+'</p><a class="service-button" href="'+href(prefix,'/pricing/')+'">'+E(u['pricing'])+' ↗</a></section>'
 return out+contact(prefix,lang)
def header(prefix,kind):
 return '<a class="skip-link" href="#service-content">Skip to content</a><header class="service-header"><div class="service-header-inner"><a class="service-brand" href="'+href(prefix,'/')+'"><i aria-hidden="true">K+</i> KENNY STUDIO</a><nav class="service-nav" id="service-navigation" aria-label="Main navigation">'+''.join('<a data-ui="'+k+'" href="'+href(prefix,p)+'"'+(' aria-current="page"' if k==kind else '')+'>'+E(UI['en'][k])+'</a>' for k,p in [('home','/'),('services','/services/'),('website-design','/services/website-design/'),('google-ads-management','/services/google-ads-management/'),('seo','/services/seo/'),('pricing','/pricing/'),('contact','/#project-brief')])+'</nav><div class="service-tools"><a class="basket-nav" href="'+href(prefix,'/cart/')+'" aria-label="Shopping basket">🛒</a><label class="sr-only" for="page-language">Website language</label><select id="page-language" aria-label="Website language"><option value="en">English</option><option value="zh">中文</option><option value="ms">Bahasa Melayu</option></select><button class="service-menu" type="button" aria-controls="service-navigation" aria-expanded="false" data-ui="menu">Menu</button></div></div></header>'
def footer(prefix):return '<footer class="service-footer"><span data-ui="copyright">'+UI['en']['copyright']+'</span><div><a data-ui="pricing" href="'+href(prefix,'/pricing/')+'">Packages & Pricing</a><a data-ui="services" href="'+href(prefix,'/services/')+'">Services</a><a data-ui="privacy" href="'+href(prefix,'/privacy/')+'">Privacy & analytics</a><button type="button" class="analytics-settings" data-ui="analytics">Analytics preferences</button></div></footer>'
for path,(title,desc) in PAGES.items():
 if path=='/':
  markup=(ROOT/'source/seo/home.html').read_text() if (ROOT/'source/seo/home.html').exists() else ''
  intro_match=re.search(r'<!-- kenny-entry-start -->.*?<!-- kenny-entry-end -->',legacy,re.S)
  intro=intro_match.group(0) if intro_match else ''
  html=head(path,title,desc,'./')+'<body><div id="root">'+markup+'</div>'+intro+'<noscript><style>.main-nav{display:flex!important;position:static!important;flex-wrap:wrap;background:#100b19;padding:15px}.menu-toggle,.assistant-orb{display:none!important}</style><p style="padding:20px;color:#d6c7e6">Interactive controls and the project form need JavaScript. You can still browse the portfolio and <a href="mailto:hello@kennystudio.cfd">email Kenny</a> or <a href="https://wa.me/message/DHXOYXRCJIKZK1">contact Kenny on WhatsApp</a>.</p></noscript></body></html>'
 else:
  prefix='../'*(len(path.strip('/').split('/')));kind='services' if path=='/services/' else 'privacy' if path=='/privacy/' else path.strip('/').split('/')[-1]
  bodies={l:('' if INDEXABLE else '<span class="preview-label" data-ui="notice">'+UI[l]['notice']+'</span>')+page_body(kind,prefix,l) for l in UI};html=head(path,title,desc,prefix,kind)+'<body class="service-page'+(' pricing-page' if kind=='pricing' else '')+'">'+header(prefix,kind)+'<main id="service-content" class="service-main">'+bodies['en']+'</main>'+footer(prefix)+'<script id="page-copy" type="application/json">'+j(bodies)+'</script></body></html>'
 write('index.html' if path=='/' else path.strip('/')+'/index.html',html)
# Utility order-request route stays out of the search sitemap and never implies successful payment.
path='/order/';prefix='../';title='Start a Website Order Request | Kenny Studio';desc='Choose a website package, review your project details and request a confirmed quotation from Kenny Studio before payment.'
bodies={l:render_order(prefix,l) for l in UI}
write('order/index.html',head(path,title,desc,prefix,'order')+'<body class="service-page order-page">'+header(prefix,'order')+'<main id="service-content" class="service-main">'+bodies['en']+'</main>'+footer(prefix)+'<script id="page-copy" type="application/json">'+j(bodies)+'</script></body></html>')

path='/cart/';prefix='../';title='Shopping Basket | Kenny Studio';desc='Review a non-binding website package shortlist before quotation confirmation and payment.'
bodies={l:render_cart(prefix,l) for l in UI}
write('cart/index.html',head(path,title,desc,prefix,'cart')+'<body class="service-page cart-page">'+header(prefix,'cart')+'<main id="service-content" class="service-main">'+bodies['en']+'</main>'+footer(prefix)+'<script id="page-copy" type="application/json">'+j(bodies)+'</script></body></html>')

# Receiving instructions/calculator is a utility; never indexed or treated as a payment-success endpoint.
path='/payment/';prefix='../';title='Payment Instructions | Kenny Studio';desc='Review your confirmed quote, payment stage and receiving details. Stripe carries a disclosed 6% service fee; transfers require funds verification.'
bodies={l:render_payment(prefix,l) for l in UI}
write('payment/index.html',head(path,title,desc,prefix,'payment')+'<body class="service-page payment-page">'+header(prefix,'payment')+'<main id="service-content" class="service-main">'+bodies['en']+'</main>'+footer(prefix)+'<script id="page-copy" type="application/json">'+j(bodies)+'</script></body></html>')

# An explicit not-found document; it is never listed in the sitemap.
write('404.html','<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>Page Not Found | Kenny Studio</title></head><body><main><h1>That page could not be found.</h1><p><a href="'+E(url('/') if ORIGIN else '/')+'">Return to Kenny Studio</a></p></main></body></html>')
ns='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',ns);tree=ET.Element('{'+ns+'}urlset')
if INDEXABLE:
 for path in PAGES:ET.SubElement(ET.SubElement(tree,'{'+ns+'}url'),'{'+ns+'}loc').text=url(path)
if INDEXABLE:write('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(tree,encoding='unicode'))
elif (OUT/'sitemap.xml').exists():(OUT/'sitemap.xml').unlink()
robots='User-agent: *\n'+('Allow: /\nDisallow: /source/\nDisallow: /scripts/\nDisallow: /tests/\nDisallow: /docs/\nDisallow: /admin/\nDisallow: /preview/\nSitemap: '+url('/sitemap.xml')+'\n' if INDEXABLE else 'Disallow: /\n')
write('robots.txt',robots)
# Preserve the approved custom-domain binding in the clean Pages release.
if INDEXABLE and not urlparse(ORIGIN).hostname.endswith('.github.io'):write('CNAME',urlparse(ORIGIN).hostname+'\n')
elif (OUT/'CNAME').exists():(OUT/'CNAME').unlink()
write('assets/build-manifest.json',json.dumps({'indexable':INDEXABLE,'origin':ORIGIN or None,'pages':list(PAGES),'utility_pages':['/order/','/payment/','/cart/'],'css':CSS,'app':APP,'runtime':RUNTIME,'extra_css':EXTRA},indent=2))
print('Built',len(PAGES),'static pages; indexable =',INDEXABLE,'; production origin =',ORIGIN or '(unset)')
