from contextlib import contextmanager
from pathlib import Path
import sqlite3,json
from .core import now
class DB:
 def __init__(self,path):
  self.path=path
  with self.connect() as c:c.executescript(Path(__file__).with_name('schema.sql').read_text())
 @contextmanager
 def connect(self):
  c=sqlite3.connect(self.path,timeout=10,isolation_level=None);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=10000')
  try:yield c
  finally:c.close()
 @contextmanager
 def transaction(self):
  with self.connect() as c:
   c.execute('BEGIN IMMEDIATE')
   try:yield c;c.commit()
   except BaseException:c.rollback();raise

def audit(c,actor,oid,action,detail=''):c.execute('INSERT INTO audit(created,actor,order_id,action,detail) VALUES(?,?,?,?,?)',(now(),actor,oid,action,str(detail)[:4000]))
def number(c,prefix):
 from datetime import datetime,timezone
 name=prefix+'-'+str(datetime.now(timezone.utc).year)
 c.execute('INSERT INTO counters(name,value) VALUES(?,1) ON CONFLICT(name) DO UPDATE SET value=value+1',(name,))
 return name+'-'+str(c.execute('SELECT value FROM counters WHERE name=?',(name,)).fetchone()[0]).zfill(5)
def queue(c,to,subject,body):c.execute('INSERT INTO outbox(created,recipient,subject,body) VALUES(?,?,?,?)',(now(),to,subject,body))
