# Finesse Research & Management Consulting Services Website

A multilingual, responsive company website with a Django backend and staff dashboard.

## Technology

- Frontend: HTML5, CSS3, JavaScript, Bootstrap 4, jQuery
- Backend: Python, Django
- Database: SQLite for local development; optional PostgreSQL for production
- Media: Pillow image processing
- Deployment: Gunicorn + WhiteNoise (hosting configuration required)

## Main functionality

- Responsive corporate website and multilingual content (English, Dari/Persian, Pashto and Arabic)
- Dynamic projects listing loaded from the backend database
- Contact form API with server-side validation, spam controls and email notification
- Staff dashboard for managing project entries and contact inquiries
- Project photo upload and publish/unpublish controls
- Admin statistics and inquiry status workflow

## Start locally

See [`backend/BACKEND.md`](backend/BACKEND.md) for setup and deployment instructions.

## Technical review

See [`TECHNICAL_REVIEW_AND_HANDOFF.md`](TECHNICAL_REVIEW_AND_HANDOFF.md) for the source review, backend improvements, production checklist and known limitations.

## Important

No runtime AI feature is currently included in the source reviewed. Do not market the delivered website as AI-powered unless a separately scoped AI feature is implemented and tested. Keep production secrets in environment variables; never commit `.env`.
