#!/usr/bin/env python3
"""Create a clean static review/release directory; never include internal source pages."""
from pathlib import Path
import json,shutil,os,zipfile
ROOT=Path(__file__).resolve().parents[1];DEST=Path(os.environ.get('PACKAGE_DIR',str(ROOT/'dist'))).resolve();
if DEST.exists():shutil.rmtree(DEST)
DEST.mkdir(parents=True,exist_ok=True)
manifest=json.loads((ROOT/'assets/build-manifest.json').read_text())
files=[Path('index.html'),Path('robots.txt'),Path('404.html'),Path('.nojekyll'),Path('kenny-studio-share-20261021.jpg')]
files += [Path(p.strip('/'))/'index.html' for p in manifest['pages'] if p!='/']
files += [Path(manifest[k]) for k in ['app','css','runtime','extra_css']]
files += [p.relative_to(ROOT) for p in (ROOT/'assets/fonts').glob('*.woff2')]
files += [p.relative_to(ROOT) for p in (ROOT/'frames/globe').rglob('*') if p.is_file()]
for p in (ROOT/'media').rglob('*'):
 if p.is_file() and (p.suffix!='.mp4' or p.stem.endswith('-web') or p.name=='kenny-hero-mask.mp4'):files.append(p.relative_to(ROOT))
if (ROOT/'sitemap.xml').exists():files.append(Path('sitemap.xml'))
for rel in files:
 target=DEST/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,target)
archive=DEST.parent/'kenny-studio-seo-preview.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in DEST.rglob('*'):
  if p.is_file():z.write(p,p.relative_to(DEST))
print('Clean preview:',DEST,'; ZIP:',archive,';',round(archive.stat().st_size/1e6,1),'MB')
