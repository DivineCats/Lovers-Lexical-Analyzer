# Deployment

This project is deployed as two services:

- Netlify hosts the React frontend from `Frontend/`
- Railway hosts the Flask backend from the repository root

## Railway backend

Railway uses `railway.toml` + `Dockerfile` in the repository root.

### Backend start command

`gunicorn Backend.Lexical.main:app --bind 0.0.0.0:$PORT`

### Backend health check

`/health`

### Railway setup

1. Create a new Railway project from this repository.
2. Keep the service root at the repository root.
3. Railway reads `railway.toml`, builds with `Dockerfile`, and starts Gunicorn.
4. After deploy, copy the public Railway URL.

## Netlify frontend

Netlify uses `netlify.toml` in the repository root.

### Netlify build settings

- Base directory: `Frontend`
- Build command: `npm ci && npm run build`
- Publish directory: `dist`

### Netlify environment variables

Set these in the Netlify site settings:

- `VITE_LEX_ENDPOINT=https://lovers-lexical-analyzer-production.up.railway.app/lex`
- `VITE_VALIDATE_ENDPOINT=https://lovers-lexical-analyzer-production.up.railway.app/validate`

You can copy the template from `Frontend/.env.example`.

## Local production-style check

Frontend development still uses the Vite proxy in `Frontend/vite.config.ts`.

For deployed builds, the frontend uses the `VITE_*` variables above and calls Railway directly.