#!/usr/bin/env python3
"""Package isolated noindex checkout demo; never replace production home or pricing."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1]
for route in ['pricing','cart','payment']:
 html=(R/route/'index.html').read_text()
 html=re.sub(r'<meta name="robots" content="[^"]*">','<meta name="robots" content="noindex, nofollow">',html)
 html=re.sub(r'<link rel="canonical"[^>]*>','',html)
 html=re.sub(r'<script type="application/ld\+json">.*?</script>','',html,flags=re.S)
 for name in ['cart','payment','pricing']:html=html.replace('../'+name+'/', '/checkout-demo/'+name+'/')
 for name in ['assets','media','services','privacy']:html=html.replace('../'+name+'/', '/'+name+'/')
 html=html.replace('../#','/#').replace('href="../"','href="/"').replace('href=\\"../\\"','href=\\"/\\"')
 html=html.replace('https://kennystudio.cfd/'+route+'/', 'https://kennystudio.cfd/checkout-demo/'+route+'/')
 out=R/'checkout-demo'/route/'index.html';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(html)
(R/'checkout-demo/index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex, nofollow"><meta http-equiv="refresh" content="0;url=cart/"><title>Checkout Preview | Kenny Studio</title></head><body><a href="cart/">Open checkout preview</a></body></html>')
manifest=json.loads((R/'assets/build-manifest.json').read_text())
files=['checkout-demo/index.html',*[f'checkout-demo/{x}/index.html' for x in ['cart','pricing','payment']],manifest['runtime'],manifest['extra_css'],'media/payments/hongleongbank.svg','media/payments/usdt.svg']
(R/'checkout-demo-files.json').write_text(json.dumps(files,indent=2)+'\n')
print('Isolated checkout demo:',len(files),'explicit files; no production pages replaced')
