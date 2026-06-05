# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Strativ Poll** is an internal photo voting platform for Strativ employees. Authenticated `@strativ.se` Google account holders vote on entries during open events and view ranked leaderboards when events close. It has a public voting interface and a staff management dashboard.

**Stack:** Django 6.0.6 · SQLite · Google OAuth (django-allauth) · Pillow + easy-thumbnails · Django Templates + Tailwind CSS (CDN) + HTMX · Gunicorn + Nginx (production)

## Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add DEBUG=True and Google OAuth credentials
python manage.py migrate
python manage.py runserver  # http://localhost:8000

# Database
python manage.py makemigrations
python manage.py migrate

# Tests
python manage.py test                      # all tests
python manage.py test accounts events      # specific apps
python manage.py test events.tests.test_voting  # single module

# Production
python manage.py collectstatic --noinput
```

There is no npm/build step — the frontend is server-rendered templates with Tailwind via CDN.

## Architecture

### Apps

- **`accounts/`** — Custom `User` model (email-based, no username). `StrativOnlyAdapter` (adapters.py) enforces `@strativ.se` domain during Google OAuth signup.
- **`events/`** — All voting logic: `Event`, `Entry`, `EntryImage`, `Vote` models; function-based views; URL routing for both public and staff routes.

### Models

- `Event` — status lifecycle: `draft → open → closed` (reopenable). Protected FK to creating user.
- `Entry` — belongs to Event; `hero` property returns the first `is_hero` image (or first image).
- `EntryImage` — multiple images per entry; `is_hero` flag; `order` field for sorting.
- `Vote` — unique_together (user, entry) prevents duplicates. Vote counts via `Count("votes")` aggregation.

### URL Structure

Public routes (`/`, `/events/<id>/`, `/events/<id>/entries/<id>/vote/`) are in `events/urls.py`. Staff management routes are under `/manage/` and gated by a custom `_staff_check()` decorator (not Django's built-in `@staff_member_required`). Auth routes handled by django-allauth at `/accounts/`.

### Frontend Patterns

- Template inheritance: `base.html → vote/*.html` or `manage/*.html`
- HTMX handles the vote toggle: button POSTs to `/toggle_vote/` and receives updated button HTML (`_vote_button.html` partial).
- `with_ranks` template filter (events/templatetags/rank_extras.py) implements competition ranking (ties share rank; next rank skips).
- Image thumbnails use easy-thumbnails aliases: `card` (600×600) and `detail` (1200×1200) with smart crop.

### Key Behaviors

- Submitter names are hidden during open events; revealed only after an event closes.
- Staff views return 403 (not redirect) for non-staff users.
- Voting on a closed/draft event returns 403.
- `prefetch_related("images")` is used throughout to avoid N+1 on entry queries.

## Settings & Environment

`vote/settings.py` uses `django-environ`. Key env vars:

| Variable | Notes |
|---|---|
| `SECRET_KEY` | Required in production |
| `DEBUG` | Set `True` locally |
| `ALLOWED_HOSTS` | Defaults to localhost; set to `vote.strativ.se` in production |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth credentials |

Production also requires a `SocialApp` entry created in Django admin (allauth → Social applications) pointing to the Google OAuth credentials.

## Production Deployment

Deployed on Ubuntu 22.04 as a systemd service (`deploy/vote.service`): Gunicorn with 3 workers on a Unix socket, behind Nginx (`deploy/nginx.conf`) with Let's Encrypt TLS.

Update flow (minimal downtime):
```bash
cd /opt/vote
sudo -u vote git pull
sudo -u vote .venv/bin/pip install -r requirements.txt
sudo -u vote .venv/bin/python manage.py migrate
sudo -u vote .venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart vote
```
