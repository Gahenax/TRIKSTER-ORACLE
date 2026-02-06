# DEPLOY CHECKLIST — TRICKSTER-ORACLE (Render + Hostinger)

## Before Deploy
- [ ] Repo identity verified: `git remote -v`
- [ ] Backend tests pass: `pytest -q`
- [ ] System routes exist: `/health`, `/ready`, `/version`
- [ ] `X-Request-ID` middleware returns header on responses
- [ ] `.env.example` exists (no secrets committed)
- [ ] CORS allowlist decided (no `*`)

## Render Setup
- [ ] Web Service created (rootDir backend)
- [ ] Build command correct (`pip install -e .`)
- [ ] Start command correct (uvicorn host 0.0.0.0 port $PORT)
- [ ] Env vars set: ENV, BUILD_COMMIT, DATA_DIR, CORS_ORIGINS
- [ ] Health check path set: `/health`

## Domain + DNS
- [ ] Custom domain added in Render: `trickster-api.gahenaxaisolutions.com`
- [ ] Hostinger DNS CNAME created for `trickster-api` pointing to Render-provided target
- [ ] TLS active (Render indicates certificate issued)

## Post Deploy
- [ ] `curl -i https://trickster-api.gahenaxaisolutions.com/health` returns 200 and `X-Request-ID`
- [ ] `curl -i https://trickster-api.gahenaxaisolutions.com/version` returns build metadata
- [ ] Frontend can call API (CORS ok)
- [ ] Logs show request_id and duration_ms (no secrets)

## Greenlight for Tokens
- [ ] Latency observed (p95 acceptable)
- [ ] No CORS/HTTPS surprises
- [ ] Ready to merge B1–E1 then implement Phase 5 tokens
