# Technical Report: Cynbit Project Discovery

**Candidate:** Vidhi Kashyap  |  **Role:** Full Stack Developer Intern  |  **Task:** Improve Cynbit's Website
**Repository:** `<paste GitHub URL>`  |  **Live demo:** `<paste live URL>`

## 1. Problem statement

Cynbit sells services (software engineering, AI automation, cloud infrastructure, digital marketing) whose scope varies a
lot from one project to the next. I reviewed the public contact page as a visitor and as a developer:

* **User view.** The form asks for name, email, company (optional), industry (optional) and a single message. The visitor is
  not asked which service they need, their budget or timeline, and they receive no reference number or visible next step.
  A blank message box is also hard to fill in well, so briefs are likely to arrive vague.
* **Developer view.** A one-box message means the team must ask follow-up questions before a first useful call. There is
  no structured data to filter, prioritise or track.

**Hypothesis:** a short guided brief that adapts to the chosen service will give the team better-qualified leads and
give visitors more confidence, which supports conversion.

## 2. Proposed improvement

A three-step project brief with:
1. service-aware prompts and structured fields (service, project, requirements, budget, timeline);
2. instant inline validation, a reference number, a confirmation email and a status tracker for the visitor;
3. a staff dashboard to search, filter, update and export briefs.

## 3. Technical stack and rationale

| Choice | Reason |
|---|---|
| Django 5 | Built-in forms, validation, auth, ORM and admin; fast to build securely |
| SQLite (local) / PostgreSQL (live) via `dj-database-url` | Zero setup locally, durable storage in production |
| Server-rendered templates + vanilla JS | Works without a build step; progressive enhancement; server re-validates everything |
| WhiteNoise + Gunicorn on Render | Simple, low-cost deployment |
| Environment variables | No secrets in the repository |

## 4. Implementation

* **Data model.** `Inquiry` stores contact data, service, project details, budget, timeline, status, internal notes and a
  unique random reference (`CY-` plus 8 hex characters).
* **Form.** `InquiryForm` validates name, email, phone pattern and a 20 to 2000 character overview; consent is required;
  a hidden honeypot rejects bots. The same rules run in JavaScript for instant feedback.
* **Views.** `home` (create), `thank_you` (visible only to the submitting session), `track` (reference plus matching
  email), staff-only `dashboard`, `inquiry_detail` and `export_csv`.
* **Abuse protection.** Honeypot, a per-visitor limit of 5 briefs per hour, CSRF protection and a CSV export that neutralises
  spreadsheet formulas.
* **Email.** A confirmation to the visitor and an optional notification to the team, sent in a background thread so the
  visitor never waits; failures are logged and never block the submission.
* **UI.** A theme matched to the live site: primary teal `#006067`, light surfaces, tracked uppercase navigation, pill
  buttons, very rounded inputs and numbered step badges.
* **Accessibility.** Labels, `aria-live` errors, keyboard-operable steps, a skip link and reduced-motion support.

## 5. Results

What I measured (see the test output and screenshots in `docs/screenshots`):

| Measure | Existing contact form | This prototype |
|---|---|---|
| Fields collected | 5 (2 optional) | 11, grouped in 3 steps (service-specific prompts) |
| Service captured | No | Yes (5 options) |
| Budget and timeline captured | No | Yes |
| Visitor receives a reference and email | No visible reference | Yes |
| Visitor can check status | No | Yes (`/track/`) |
| Team can filter, update and export | Not visible to the visitor | Yes (`/manage/`) |
| Automated tests | n/a | 16 passing (`python manage.py test`) |

I also ran the app with `DEBUG=False` under Gunicorn: static files are served, CSRF is enforced, a real submission is
stored, and another visitor cannot open someone else's thank-you page.

**Not measured.** I have not run an A/B test, so I make no claim about conversion uplift. The expected benefit is
better-qualified briefs and fewer follow-up emails; measuring it would need real traffic.

## 6. Limitations and next steps

* Standalone prototype; production use would call a JSON endpoint from the existing site (or embed the form).
* Free-tier hosting sleeps when idle; use hosted Postgres for durable data.
* Add file attachments, a CRM or Slack webhook, spam scoring (for example Turnstile) and analytics on drop-off per step.
* Use Redis for rate limiting across several servers.

## 7. How to run

See `README.md` for setup, tests and deployment.
