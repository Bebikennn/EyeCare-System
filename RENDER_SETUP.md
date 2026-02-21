# Render deployment (monorepo)

This repo is set up to deploy 3 things on Render via `render.yaml`:

- `eyecare-backend` (Flask API)
- `eyecare-admin` (Flask admin site)
- `eyecare-web` (Flutter Web static site)

## Required env vars (set in Render)

### Backend: `eyecare-backend`
- `SECRET_KEY` (random, long)
- `JWT_SECRET_KEY` (random, long)
- `CORS_ORIGINS` (comma-separated allowlist)
  - Example: `https://eyecare-web.onrender.com`

### Admin: `eyecare-admin`
- `SECRET_KEY` (random, long)
- `DEFAULT_ADMIN_PASSWORD` (strong password)
  - `AUTO_INIT_DB=1` will run `init_db()` and create tables.
  - In production, the app will *not* create a default admin unless `DEFAULT_ADMIN_PASSWORD` is set.

## Flutter Web
- Set `API_BASE_URL` on the `eyecare-web` static site
  - Example: `https://eyecare-backend.onrender.com`

## Notes on security
- Keep `CORS_ORIGINS` tight (no `*` in production).
- Rotate secrets if they ever leak.
- `AUTO_INIT_DB` is convenient for first deploy; after initial setup you can set it to `0`.
