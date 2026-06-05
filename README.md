# Strativ Poll

Internal photo voting platform for Strativ employees. Employees sign in with their `@strativ.se` Google account, vote on entries during Open events, and see ranked results when events close.

## Local development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edit: set DEBUG=True, add Google OAuth credentials
python manage.py migrate
python manage.py runserver
```

To test Google login locally, set the redirect URI in Google Cloud Console to:
`http://localhost:8000/accounts/google/login/callback/`

Then add a `SocialApp` via the Django admin at `http://localhost:8000/admin/`.

## Running tests

```bash
python manage.py test accounts events
```

## Deploy to Ubuntu server (first time)

**Prerequisites:** Ubuntu 22.04+, a domain pointing to the server, a Google OAuth client.

```bash
# As root — create system user and install packages
sudo adduser --system --group vote
sudo apt install -y python3-venv nginx certbot python3-certbot-nginx

# Clone and set up
sudo -u vote git clone <repo-url> /opt/vote
cd /opt/vote
sudo -u vote python3 -m venv .venv
sudo -u vote .venv/bin/pip install -r requirements.txt
sudo -u vote cp .env.example .env
# Edit /opt/vote/.env — fill in SECRET_KEY, GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET

sudo -u vote .venv/bin/python manage.py migrate
sudo -u vote .venv/bin/python manage.py collectstatic --noinput

# systemd
sudo cp deploy/vote.service /etc/systemd/system/vote.service
sudo systemctl daemon-reload
sudo systemctl enable --now vote.service

# nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/vote
sudo ln -s /etc/nginx/sites-available/vote /etc/nginx/sites-enabled/vote
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d vote.strativ.se
```

**After first deploy — manual steps:**

1. Open `https://vote.strativ.se/admin/` and sign in with Django superuser.
   *(Create one with `sudo -u vote .venv/bin/python manage.py createsuperuser` if needed.)*
2. Under **Social Applications → Add**, create a Google app with your OAuth client ID and secret.
   Redirect URI in Google Cloud Console: `https://vote.strativ.se/accounts/google/login/callback/`
3. After Sudipto logs in via Google for the first time, grant admin rights:

```bash
sudo -u vote /opt/vote/.venv/bin/python /opt/vote/manage.py shell -c \
  "from accounts.models import User; u = User.objects.get(email='sudipto@strativ.se'); u.is_staff=True; u.is_superuser=True; u.save()"
```

## Update flow

```bash
cd /opt/vote
sudo -u vote git pull
sudo -u vote .venv/bin/pip install -r requirements.txt
sudo -u vote .venv/bin/python manage.py migrate
sudo -u vote .venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart vote
```

Downtime during restart: ~2 seconds.

## Logs

```bash
journalctl -u vote -f          # gunicorn stdout/stderr
tail -f /var/log/nginx/error.log
```
