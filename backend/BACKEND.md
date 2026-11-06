# Finesse Backend + Dashboard

A Django backend for the Finesse website, with SQLite for local development and optional PostgreSQL / shared cache support for production.

- **Dashboard** (graphical, password protected): read messages from the contact form, see statistics, **add / edit / hide / delete projects** with photos.
- **Projects page** on the website loads its projects from the database, in 4 languages.
- **Contact form** saves every message in the database and emails the team.
- **Database options:** SQLite for local development; PostgreSQL through `DATABASE_URL` for production.
- **Cache options:** local-memory for development; database or Redis cache for shared production login throttling.

## The pages

| Address | What it is |
|---|---|
| `/dashboard/` | Overview: new messages, chart of the last 14 days, latest messages |
| `/dashboard/messages/` | All messages: search, filter, reply by email, mark replied, delete |
| `/dashboard/projects/` | Your projects: **Add**, **Edit**, **Hide/Show**, **Delete** |
| `/manage-finesse/` | Technical admin (only to create more staff users). The name comes from `ADMIN_URL` in `.env` |
| `/api/projects/` | What the website reads (public, only projects marked visible) |
| `/api/contact/` | What the contact form sends to |

## Run it on your computer

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows   (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt

copy .env.example .env            # Mac/Linux: cp .env.example .env
python manage.py migrate
python manage.py createsuperuser  # this is your dashboard login
python manage.py runserver
```

Open **http://127.0.0.1:8000/dashboard/** and sign in. Open **http://127.0.0.1:8000/** to see the website.

First time: on the Projects screen click **Load the 6 sample projects** (they are the ones that were written by hand in the old `projects.html`). Then edit or delete them and add your real ones.

Check everything with the automated tests: `python manage.py test`

## Emails: why you saw messages in the terminal

If `EMAIL_HOST_PASSWORD` in `.env` is empty, Django does **not** send email; it only prints it in the terminal, so you can test. The message is still saved in the dashboard. To send **real** emails:

1. Google Account → Security → turn on **2-Step Verification**.
2. Search **App passwords**, create one named "Finesse website", copy the 16 letters.
3. In `.env` set `EMAIL_HOST_USER=finesse.researchmc@gmail.com` and `EMAIL_HOST_PASSWORD=` (the 16 letters, no spaces).
4. Test it: `python manage.py send_test_email your-own-address@gmail.com`
   It says **Done.** if it really sent, or shows the exact error. Check the inbox (and spam).

The dashboard Overview shows a yellow warning until email is configured, and again if any email failed to send. Failed ones can be re-sent with `python manage.py retry_notifications`.

## Put it online

The website (HTML/CSS/JS) and the backend can be in two places:

1. **Backend:** a Python host (Render, Railway, PythonAnywhere, a VPS). Set the variables from `.env.example` with `DJANGO_DEBUG=False`, a long random `DJANGO_SECRET_KEY`, your real `DJANGO_ALLOWED_HOSTS`, and `CORS_ALLOWED_ORIGINS=https://your-website-domain`. Prefer PostgreSQL and set `DATABASE_URL` to the provider's private connection URL. Start command: `gunicorn config.wsgi:application`. First time: `python manage.py migrate`, `python manage.py collectstatic --noinput`, then `python manage.py createsuperuser`.
2. **Shared login-throttle cache:** set `DJANGO_CACHE_BACKEND=database` and run `python manage.py createcachetable` once, or set `DJANGO_CACHE_BACKEND=redis` and configure `REDIS_URL`. Do not rely on local-memory cache with multiple production workers; each worker would have a separate lockout counter.
2. **Website:** any static host (GitHub Pages, Netlify...). In `JS/config.js` set `window.FINESSE_API_BASE = "https://your-backend-domain"`.

Generate a secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

**Persistent storage and backups:** keep uploaded `media/` files on persistent storage or object storage. If you stay on SQLite, `db.sqlite3` must also live on a persistent disk and be backed up. PostgreSQL is recommended for a production company site; configure automated database backups with the database provider. Back up media separately.

Use a host with a persistent disk, and back up both regularly.

## Security measures

- Dashboard needs a login; 5 wrong passwords lock that visitor for 15 minutes
- All changes (add, delete, hide) are POST-only with CSRF protection; delete asks for confirmation
- Uploaded photos are checked to be real images, resized, and stripped of hidden metadata (e.g. GPS)
- Visitor text is always escaped (no script injection in the dashboard)
- Contact form: server-side validation, honeypot, rate limit (5/hour per visitor), duplicate check, allowed-websites list
- IP addresses are stored only as a one-way hash
- HTTPS-only cookies, HSTS and redirect when `DJANGO_DEBUG=False`

## Production readiness notes

- PostgreSQL is optional through `DATABASE_URL`; SQLite remains the local default.
- Production login throttling should use the database or Redis cache, not per-process local memory.
- Configure HTTPS, real `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, email credentials, persistent media storage, database backups, and a monitored error log before launch.
- Run `python manage.py check --deploy` with production environment variables and resolve all warnings before go-live.

## Not included yet

- Two-factor login
- Editing the other pages (About, Services) from the dashboard
- Automatic "we received your message" email to the visitor
- Moving email sending to a background queue (only matters at high volume)
