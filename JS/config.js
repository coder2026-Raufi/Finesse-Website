/* Where is the Finesse backend (API)?
   - Same server as the website (e.g. local test with "python manage.py runserver"): leave "".
   - Website and API on different domains: put the API address, e.g. "https://api.finesse-af.com"
     (no slash at the end). That domain must also be listed in CORS_ALLOWED_ORIGINS in backend/.env */
window.FINESSE_API_BASE = "https://finesse-eta-blond.vercel.app";
