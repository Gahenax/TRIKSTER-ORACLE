# TRICKSTER-ORACLE v2 — Launch Checklist

## Backend (PROD)
- [ ] Backend deployed (Render or equivalent)
- [ ] Redis ONLINE (not only in-memory fallback)
- [ ] /health returns 200
- [ ] /ready returns 200
- [ ] /version returns v2.0.x
- [ ] /api/v2/simulate works (free tier)
- [ ] Token-gated endpoint denies without balance
- [ ] Token-gated endpoint allows with balance
- [ ] Idempotency prevents double charge
- [ ] Audit trail records transaction

## Frontend (PROD)
- [ ] Production build successful
- [ ] VITE_API_URL points to PROD API
- [ ] UI Pick v2 renders with partial data
- [ ] Uncertainty badges visible

## DNS
- [ ] api.tricksteroracle.com → backend
- [ ] tricksteroracle.com → frontend

## Closure Criterion
You can share the URL with an external user without warnings or manual steps.
