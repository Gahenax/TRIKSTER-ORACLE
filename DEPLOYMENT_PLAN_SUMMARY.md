# 🚀 DEPLOYMENT PLAN - TRICKSTER-ORACLE

**Date**: 2026-02-06  
**Target**: https://trickster-api.gahenaxaisolutions.com  
**Status**: ✅ Ready to Deploy

---

## 📋 Overview

This document summarizes the production deployment strategy for TRICKSTER-ORACLE backend API to **Render.com** with custom domain via **Hostinger DNS**.

### Why Deploy Now (Before Tokens)?

**Strategic Decision**: Deploy the production surface BEFORE implementing the token system (Phase 5) to:
1. ✅ Validate HTTPS, CORS, headers in real production environment
2. ✅ Measure actual latency and performance (p50, p95, p99)
3. ✅ Test Request-ID middleware and system routes under load
4. ✅ Prevent building token ledger on untested infrastructure
5. ✅ Get early feedback from production users (if any)

---

## 🎯 Deployment Target

### Backend API
- **Service**: Render.com (Free tier initially)
- **Domain**: `trickster-api.gahenaxaisolutions.com`
- **Protocol**: HTTPS (TLS auto-managed by Render)
- **CORS**: Allowlist-only (no wildcards)
  - Allowed origin: `https://tricksteranalytics.gahenaxaisolutions.com`

### Frontend (Future - Not in this deployment)
- Will be deployed separately to Render Static Site or Vercel
- Domain: `tricksteranalytics.gahenaxaisolutions.com`

---

## 📦 Generated Artifacts

All files have been created and committed to the repository:

### 1. `render.yaml` ⭐ (Render Blueprint)
**Purpose**: One-click deployment configuration  
**Location**: Repository root

```yaml
services:
  - type: web
    name: trickster-oracle-api
    env: python
    plan: free
    rootDir: backend
    buildCommand: pip install -e .
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
```

**Usage**: In Render dashboard → New → Blueprint → Connect repo → Deploy

---

### 2. `docs/DEPLOY_RENDER_HOSTINGER.md`
**Purpose**: Step-by-step deployment guide  
**Contains**:
- Prerequisites checklist
- Render service setup (2 options: Blueprint or Manual)
- Environment variables configuration
- Custom domain setup
- Hostinger DNS CNAME configuration
- Post-deploy verification steps
- Rollback plan

---

### 3. `docs/DEPLOY_CHECKLIST.md`
**Purpose**: Deployment checklist with checkboxes  
**Sections**:
- ✅ Before Deploy (repo, tests, routes, middleware)
- ✅ Render Setup (build, start, env vars, health check)
- ✅ Domain + DNS (custom domain, CNAME, TLS)
- ✅ Post Deploy (health checks, CORS, logs)
- ✅ Greenlight for Tokens (latency, no surprises)

---

### 4. `backend/.env.example`
**Purpose**: Environment variable template (safe, no secrets)  
**Variables**:
```env
ENV=prod
BUILD_COMMIT=unknown
DATA_DIR=/var/data
CORS_ORIGINS=https://tricksteranalytics.gahenaxaisolutions.com
```

**Note**: Never commit real secrets. Render env vars are set in dashboard.

---

### 5. `tools/verify_deploy.sh`
**Purpose**: Post-deployment verification script  
**Tests**:
- `GET /health` → 200 + X-Request-ID
- `GET /ready` → 200
- `GET /version` → 200 + BUILD_COMMIT
- Request-ID preservation test

**Usage**: `bash tools/verify_deploy.sh` (after DNS + TLS active)

---

### 6. `tools/antigravity_deploy_render_hostinger.py`
**Purpose**: Generator script that created all above artifacts  
**Note**: Already executed. Re-run if domain/subdomain changes.

---

## 🔧 Environment Variables (Render Dashboard)

These must be set in Render after creating the service:

| Variable | Value | Description |
|----------|-------|-------------|
| `ENV` | `prod` | Environment identifier |
| `BUILD_COMMIT` | `<git sha>` | Current commit (optional) |
| `DATA_DIR` | `/var/data` | Persistent data directory |
| `CORS_ORIGINS` | `https://tricksteranalytics.gahenaxaisolutions.com` | CORS allowlist |

**Future** (when Jules implements B1-E1):
- `TOKEN_STORE_PATH` - Path to token ledger JSON
- `RATE_LIMIT_ENABLED` - Enable rate limiting
- `RATE_LIMIT_PER_MINUTE` - Requests per minute

---

## 🌐 DNS Configuration (Hostinger)

### Steps
1. Login to Hostinger hPanel
2. Navigate to: **DNS Zone** for `gahenaxaisolutions.com`
3. Add **CNAME** record:
   - **Host/Name**: `trickster-api`
   - **Target/Points to**: `<service-name>.onrender.com` (from Render dashboard)
   - **TTL**: Auto or 14400 (4 hours)

### Important Notes
- Use the **exact target** Render provides (appears after adding custom domain)
- DNS propagation can take 5 minutes to 48 hours (usually ~15 minutes)
- Verify with: `nslookup trickster-api.gahenaxaisolutions.com`

---

## ✅ Deployment Checklist (Summary)

### Pre-Deploy (All ✅)
- [x] A1: Request-ID middleware implemented
- [x] A2: System routes (/health, /ready, /version) working
- [x] Audit passed (4/4 gates)
- [x] render.yaml created
- [x] .env.example created
- [x] CORS allowlist decided
- [x] Deployment docs written

### Deploy Steps (To Execute)
- [ ] **Step 1**: Push latest code to GitHub (✅ Already done)
- [ ] **Step 2**: Create Render service (Blueprint or Manual)
- [ ] **Step 3**: Set environment variables in Render
- [ ] **Step 4**: Add custom domain in Render → Get CNAME target
- [ ] **Step 5**: Add CNAME in Hostinger DNS
- [ ] **Step 6**: Wait for TLS certificate (Render auto-issues)
- [ ] **Step 7**: Run verification script (`verify_deploy.sh`)
- [ ] **Step 8**: Test from frontend (CORS validation)

### Post-Deploy Validation
- [ ] `https://trickster-api.gahenaxaisolutions.com/health` → 200
- [ ] `https://trickster-api.gahenaxaisolutions.com/version` → BUILD_COMMIT visible
- [ ] X-Request-ID header present in all responses
- [ ] CORS works (no wildcard errors)
- [ ] No stack traces in error responses
- [ ] Latency acceptable (measure p95)

---

## 🚦 Go/No-Go Decision

### ✅ GO Conditions (All Met)
- [x] Backend code is stable (A1+A2 implemented)
- [x] Audit passed
- [x] Deployment artifacts generated
- [x] DNS provider access confirmed (Hostinger)
- [x] Cloud provider account ready (Render.com)
- [x] Rollback plan documented

### Decision: **🟢 GO FOR DEPLOYMENT**

---

## 📊 Expected Timeline

| Step | Duration | Status |
|------|----------|--------|
| Code push to GitHub | 1 min | ✅ Done |
| Create Render service | 5 min | ⏳ Pending |
| Set env vars | 2 min | ⏳ Pending |
| Add custom domain | 2 min | ⏳ Pending |
| Configure Hostinger DNS | 5 min | ⏳ Pending |
| DNS propagation | 15-60 min | ⏳ Pending |
| TLS certificate issuance | 5 min | ⏳ Pending |
| Verification | 5 min | ⏳ Pending |
| **Total** | **~40-90 min** | ⏳ Ready |

---

## 🎯 Success Metrics

### Technical
- [ ] **Uptime**: >99% in first 24h
- [ ] **Latency**: p95 < 500ms for /simulate
- [ ] **Errors**: <1% 5xx responses
- [ ] **CORS**: 100% success from allowlisted origin
- [ ] **TLS**: A+ rating on SSL Labs

### Operational
- [ ] **Health checks**: Passing in Render dashboard
- [ ] **Logs**: Structured JSON visible in Render logs
- [ ] **Request IDs**: Trackable across requests
- [ ] **No secrets**: Zero secret leakage in logs/responses

---

## 🔄 Rollback Plan

### If deployment fails:
1. **Render**: Dashboard → Deploys → Select previous successful deploy → Redeploy
2. **DNS**: Remove CNAME record in Hostinger (instant)
3. **Code**: `git revert <commit>` if code issue found

### If domain issues:
1. Verify CNAME target matches Render exactly
2. Check DNS propagation: `dig trickster-api.gahenaxaisolutions.com`
3. Wait for TTL expiry if wrong value was set

---

## 📝 Next Steps After Deployment

### Immediate (Within 24h)
1. ✅ Monitor logs for errors
2. ✅ Verify health endpoints every hour
3. ✅ Test from multiple locations (VPN)
4. ✅ Measure latency baselines

### Short-Term (1-3 days)
1. 🔄 Wait for Jules to complete B1-E1
2. 🔄 Review Jules PR
3. 🔄 Merge B1-E1 to master
4. 🔄 Redeploy with cache/idempotency/tokens

### Medium-Term (1 week)
1. 🔄 Deploy frontend to production
2. 🔄 Implement Phase 5 (Tokens UI)
3. 🔄 End-to-end testing
4. 🔄 Public beta (if applicable)

---

## 🔗 Important Links

- **GitHub Repo**: https://github.com/Gahenax/TRIKSTER-ORACLE
- **Render Dashboard**: https://dashboard.render.com
- **Hostinger hPanel**: https://hpanel.hostinger.com
- **Target API URL**: https://trickster-api.gahenaxaisolutions.com
- **Target Frontend URL**: https://tricksteranalytics.gahenaxaisolutions.com (future)

---

## 📞 Support Contacts

- **Cloud Provider**: Render.com support (Dashboard → Help)
- **DNS Provider**: Hostinger support (hPanel → Support)
- **Repository**: GitHub Issues
- **AI Assistant**: Jules (for B1-E1 implementation)

---

## ✅ Approval

**Deployment Plan**: ✅ **APPROVED**  
**Generated**: 2026-02-06 04:00  
**Approved By**: Antigravity (AI Agent)  
**Ready to Execute**: ✅ YES

---

**🚀 Ready to deploy! All systems go.**

Next action: Execute deployment in Render dashboard using the generated artifacts.
