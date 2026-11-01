# Cynbit Project Discovery (assessment prototype)

An improved **project-inquiry experience** for [cynbit.in](https://www.cynbit.in/contact), built with Django.
It replaces a single generic contact form with a guided three-step brief, gives visitors a reference number and a
status tracker, and gives the team a staff dashboard to triage the briefs.

> Independent prototype for the *Full Stack Developer Intern: Improve Cynbit's Website* task. It is not connected to
> Cynbit's systems. Contact details and FAQ text were copied from the public site so the demo feels real.

## The problem (what I found on the live site)

The public contact page presents a short generic inquiry form for name, email, optional company and industry, plus a free-text message.
It does not ask **which service** is needed, the **budget**, the **timeline**, or anything specific to the service, so the
team has to run a back-and-forth before a first useful conversation. The visitor also gets no reference number and no way
to see what happens to the message.

## What this prototype adds

| Area | Improvement |
|---|---|
| Guided brief | 3 steps (Contact, Project, Scope) with progress bar and a clickable stepper |
| Service-aware | Choose one of Cynbit's four service areas (or "not sure"); the prompt and placeholder change to ask the right questions |
| Qualification data | Service, project name, requirements, budget range, timeline, industry, phone |
| Validation | Instant, friendly inline errors in the browser **and** the same rules enforced on the server |
| Confidence | Reference number (`CY-XXXXXXXX`), a private thank-you page, a confirmation email |
| Visitor tracking | `/track/`: reference + email shows the status (New, Reviewed, In progress, Completed) |
| Team tools | `/manage/` dashboard (staff only): stats, search, filters, pagination, detail page, status + internal notes, CSV export |
| Notifications | Optional email to the team on each new brief |
| Abuse protection | Honeypot field, per-visitor rate limit (5 briefs/hour), CSRF, CSV formula-injection guard |
| Accessibility | Labelled fields, `aria-live` errors, keyboard-friendly step controls, skip link, reduced-motion support |
| Theme | Light teal look matched to cynbit.in: `#006067` primary, tracked uppercase navigation, pill buttons, very rounded inputs, numbered step badges |

## Tech stack and why

* **Django 5 + SQLite/PostgreSQL**: forms, validation, authentication and an ORM out of the box; one deployable service.
* **Server-rendered templates + vanilla JavaScript**: fast first paint, no build step, works even if the JS fails
  (the server validates everything again).
* **WhiteNoise + Gunicorn**: static files and production serving without extra infrastructure.
* **dj-database-url**: the same code runs on SQLite locally and on hosted Postgres.

## Run it on your computer (Windows)

```bat
py -3.14 -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
set DEBUG=True
set DJANGO_SECRET_KEY=django-insecure-local-development-key-change-me
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

macOS/Linux: use `source venv/bin/activate` and `export DEBUG=True`.

* Public site: http://127.0.0.1:8000/
* Staff dashboard: http://127.0.0.1:8000/manage/ (log in with the superuser you created)
* Django admin: http://127.0.0.1:8000/admin/

Emails are printed in the terminal by default, so nothing is ever sent to a real inbox by accident. Navigation stays inside this prototype; it does not redirect visitors to Cynbit’s live website. The prototype is independently built and does not submit data to Cynbit.

## Run the tests

```bat
set DEBUG=True
python manage.py test
```

16 tests cover validation, the honeypot, the rate limit, emails, the private thank-you page, tracking, staff-only access,
filters, status updates, XSS escaping and CSV formula-injection protection.

## Configuration (environment variables)

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | **Required** when `DEBUG` is not `True`. Generate a long random string. |
| `DEBUG` | `True` only on your own computer. Default is `False`. |
| `ALLOWED_HOSTS` | Comma-separated host names (Render's host is added automatically). |
| `DATABASE_URL` | Hosted Postgres URL. If unset, SQLite is used. |
| `INQUIRY_NOTIFY_EMAIL` | Address that receives a copy of every new brief (optional). |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Real email sending (optional). |
| `INQUIRY_RATE_LIMIT` | Briefs allowed per hour per visitor (default 5). |

No secret is stored in the repository. Copy `.env.example` into your hosting dashboard, never into git.

## Deploy on Render (free tier)

1. Push this repository to GitHub (public).
2. Create a hosted **PostgreSQL** database (Render, Neon or Supabase) and copy its connection string.
   SQLite on a free web service is wiped on each redeploy, so use Postgres for the live demo.
3. On Render choose **New > Blueprint** (it reads `render.yaml`) or **New > Web Service** and set:
   * Build command: `./build.sh`
   * Start command: `gunicorn config.wsgi:application`
4. Add the environment variables: `DJANGO_SECRET_KEY`, `DEBUG=False`, `DATABASE_URL`, `DJANGO_SUPERUSER_USERNAME`,
   `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD` (a strong password) and, optionally, `INQUIRY_NOTIFY_EMAIL`.
5. Open the live URL, submit a test brief, then log in at `/manage/` and check it appears.
6. Free services sleep when idle. Open the URL once just before you submit it.

## How this would connect to the real website

This prototype is deliberately standalone. In production, the same logic can be exposed as a small JSON endpoint
(`POST /api/inquiries`) that the existing site's form calls, or the form can be embedded as a component that posts to it.
The model, validation, notification and dashboard code would stay the same.

## Known limits

* The logo is a text-and-curve approximation; replace it with Cynbit's official SVG if you have it.
* Fonts load from Google Fonts (Manrope) and fall back to the system font when offline.
* Rate limiting uses the server's memory, so it resets on restart and is per instance. Use Redis for a multi-server setup.
* No file attachments and no CRM integration yet (natural next steps).

## Repository layout

```
config/            settings, URLs, WSGI/ASGI
inquiries/         model, form, views, email helper, admin, tests, migration
templates/         base layout, home (the guided form), thank-you, track, dashboard, detail, 404
static/            css/style.css (theme) and js/main.js (steps, validation, menu)
docs/              TECHNICAL_REPORT.md and screenshots
build.sh, render.yaml, requirements.txt, .env.example
```

## Suggested commit history

```bash
git init && git add .gitignore requirements.txt manage.py config/ && git commit -m "chore: scaffold Django project with env-driven settings"
git add inquiries/models.py inquiries/migrations inquiries/apps.py inquiries/__init__.py && git commit -m "feat: add Inquiry model with reference numbers and status workflow"
git add inquiries/forms.py && git commit -m "feat: add validated inquiry form with honeypot"
git add inquiries/views.py inquiries/emails.py config/urls.py && git commit -m "feat: submit, thank-you, tracking and rate limiting"
git add templates static && git commit -m "feat: multi-step brief UI in the Cynbit teal theme"
git add inquiries/admin.py && git commit -m "feat: staff dashboard, filters, CSV export and admin registration"
git add inquiries/tests.py && git commit -m "test: cover validation, abuse protection and staff access"
git add build.sh render.yaml .env.example README.md docs && git commit -m "docs: add deployment files, README and technical report"
```
