#!/usr/bin/env python3
"""An isolated chapter/font preview. Do not replace the live homepage."""
from pathlib import Path
import re,json,hashlib
R=Path(__file__).resolve().parents[1];m=json.loads((R/'assets/build-manifest.json').read_text())
app=(R/m['app']).read_text()
for directory in ['media','services','pricing','privacy']:
 app=app.replace('./'+directory+'/', '/'+directory+'/')
app=app.replace('new URL("frames/globe/', 'new URL("/frames/globe/')
name='app.'+hashlib.sha256(app.encode()).hexdigest()[:10]+'.js'
out=R/'scroll-demo';out.mkdir(exist_ok=True);(out/name).write_text(app)
html=(R/'index.html').read_text();html=html.replace('<head>','<head><base href="/scroll-demo/">',1)
html=re.sub(r'<meta name="robots" content="[^"]*">','<meta name="robots" content="noindex, nofollow">',html)
html=re.sub(r'<link rel="canonical"[^>]*>','',html)
html=re.sub(r'<script type="application/ld\+json">.*?</script>','',html,flags=re.S)
for directory in ['assets','media','frames','services','pricing','privacy']:
 html=html.replace('./'+directory+'/', '/'+directory+'/')
html=html.replace('/'+m['app'],name)
html=html.replace('</body>','<span style="position:fixed;z-index:29;right:18px;bottom:50px;font:8px monospace;letter-spacing:.12em;color:#aa98c2;pointer-events:none">SCROLL + TYPE PREVIEW</span></body>')
(out/'index.html').write_text(html)
files=['scroll-demo/index.html','scroll-demo/'+name,m['css'],'assets/fonts/manrope-variable.ttf','assets/fonts/Manrope-OFL.txt']
(R/'chapter-demo-files.json').write_text(json.dumps(files,indent=2)+'\n');print('Chapter preview package:',len(files),'files; production home untouched')
