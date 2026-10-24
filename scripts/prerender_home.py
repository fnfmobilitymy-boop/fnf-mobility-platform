#!/usr/bin/env python3
"""Regenerate crawlable English HTML from the retained React app; no client hydration assumptions."""
from pathlib import Path
import threading,http.server,functools,subprocess
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-webgl'])
  page=b.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce');page.add_init_script('localStorage.setItem("kenny-language","en");localStorage.setItem("kenny-music","off")')
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='domcontentloaded');page.wait_for_selector('.skill-card');page.wait_for_timeout(500)
  assert not errors,errors;assert page.locator('.skill-card').count()==12
  html=page.locator('#root').evaluate('''root=>{const clone=root.cloneNode(true);clone.querySelectorAll('[data-reveal],.hero-title-line>span').forEach(el=>{for(const key of ['opacity','visibility','transform','translate','rotate','scale'])el.style.removeProperty(key)});clone.querySelectorAll('.motion-reduced').forEach(el=>el.classList.remove('motion-reduced'));clone.querySelectorAll('video,audio,source').forEach(el=>{el.removeAttribute('src');el.setAttribute('preload','none')});clone.querySelectorAll('canvas').forEach(el=>el.removeAttribute('data-frame'));clone.querySelectorAll('input,textarea').forEach(el=>{el.removeAttribute('value');if(el.tagName==='TEXTAREA')el.textContent=''});clone.querySelectorAll('form').forEach(el=>{el.setAttribute('inert','');el.querySelectorAll('button,input,select,textarea').forEach(input=>input.setAttribute('disabled',''))});clone.querySelectorAll('.brief-preview,.music-notice').forEach(el=>el.remove());const globe=clone.querySelector('.world-mount');if(globe)globe.innerHTML='<div class="world-heading"><span class="eyebrow">BASED IN MALAYSIA. CONNECTED WORLDWIDE.</span><h2>Your next website. Anywhere in the world.</h2><p>Remote website design and development for Malaysian and international businesses. The interactive country directory is available with JavaScript.</p></div>';return clone.innerHTML}''')
  (ROOT/'source/seo/home.html').write_text(html);print('Prerendered',len(html),'bytes; 12 services and current project directory retained.');b.close()
finally:server.shutdown()
subprocess.run(['python',str(ROOT/'scripts/build_site.py')],cwd=ROOT,check=True)
