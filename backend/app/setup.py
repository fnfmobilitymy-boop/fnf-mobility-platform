"""Run locally; configure the generated values only in your hosting secret settings."""
import getpass,secrets
from .core import pw_hash
if __name__=='__main__':
 password=getpass.getpass('Choose an administrator password (12+ characters): ')
 if password!=getpass.getpass('Confirm password: '):raise SystemExit('Passwords do not match')
 print('APP_SECRET='+secrets.token_urlsafe(48));print('ADMIN_PASSWORD_HASH='+pw_hash(password))
