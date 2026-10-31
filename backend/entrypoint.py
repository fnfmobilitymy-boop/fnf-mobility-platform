"""Drop root after preparing the persistent mount; one worker owns the SQLite outbox."""
import os
from pathlib import Path
path=Path(os.environ.get('DATA_DIR','/data'));path.mkdir(parents=True,exist_ok=True)
if hasattr(os,'geteuid') and os.geteuid()==0:
 os.chown(path,10001,10001);os.setgid(10001);os.setuid(10001)
os.execvp('uvicorn',['uvicorn','app.server:app','--host','0.0.0.0','--port',os.environ.get('PORT','10000'),'--workers','1','--proxy-headers','--forwarded-allow-ips','*'])
