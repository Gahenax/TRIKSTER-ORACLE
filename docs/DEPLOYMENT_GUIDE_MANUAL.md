# 🚀 DEPLOYMENT GUIDE - STEP BY STEP (Manual)

**Project**: TRICKSTER-ORACLE  
**Date**: 2026-02-06  
**Status**: ✅ All Validations Passed - Ready to Deploy

---

## ✅ Pre-Deployment Validation Complete

```
✅ Runtime Tests: 5/5 PASSED
✅ Protocolo Semáforo: 🟢 GO (18/20 green)
✅ Git Status: Clean, pushed to master
✅ Commit: dbd0de0
```

---

## 📋 STEP-BY-STEP DEPLOYMENT INSTRUCTIONS

### PHASE 1: Create Render Service (15 minutes)

#### Step 1.1: Login to Render
1. Open browser: **https://dashboard.render.com**
2. Login with your Render account
   - If you don't have an account, create one (free)
   - Connect your GitHub account

#### Step 1.2: Create New Web Service (Option A - Recommended: Blueprint)

**Using Blueprint (Easiest - One Click)**:

1. In Render Dashboard, click **"New +"** → **"Blueprint"**
2. Connect GitHub repository:
   - Search for: `Gahenax/TRIKSTER-ORACLE`
   - Click **"Connect"**
3. Render will detect `render.yaml` automatically
4. Click **"Apply"** to create the service
5. ✅ Service will be created with all settings from `render.yaml`

**Blueprint Contents** (already in repo):
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

#### Step 1.3: OR Create Manually (Option B - if Blueprint fails)

1. Click **"New +"** → **"Web Service"**
2. Connect GitHub:
   - Repository: `Gahenax/TRIKSTER-ORACLE`
   - Branch: `master`
3. Configure Build Settings:
   - **Name**: `trickster-oracle-api`
   - **Region**: Choose closest to you (e.g., Oregon)
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -e .`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Instance Type**: Free
5. Click **"Create Web Service"**

#### Step 1.4: Configure Environment Variables

In the Render service page, go to **"Environment"** tab:

Add these variables:

| Key | Value |
|-----|-------|
| `ENV` | `prod` |
| `BUILD_COMMIT` | `dbd0de0` (or current commit) |
| `DATA_DIR` | `/var/data` |
| `CORS_ORIGINS` | `https://tricksteranalytics.gahenaxaisolutions.com` |

Click **"Save Changes"**

#### Step 1.5: Wait for Initial Deploy

- Render will start building and deploying
- This takes **5-10 minutes** for first deploy
- Monitor the **"Logs"** tab to see progress
- Look for: `Application startup complete` in logs

**Expected Log Output**:
```
2026-02-06 XX:XX:XX - app.main - INFO - Trickster Oracle API starting
INFO:     Uvicorn running on http://0.0.0.0:XXXXX
INFO:     Application startup complete.
```

✅ **Checkpoint**: Service should show "Live" status with green indicator

---

### PHASE 2: Add Custom Domain (10 minutes)

#### Step 2.1: Get Render CNAME Target

1. In your service page, click **"Settings"** tab
2. Scroll to **"Custom Domain"** section
3. Click **"Add Custom Domain"**
4. Enter: `trickster-api.gahenaxaisolutions.com`
5. Click **"Save"**
6. **IMPORTANT**: Copy the CNAME target shown (format: `servicename.onrender.com`)

Example CNAME target:
```
trickster-oracle-api.onrender.com
```

#### Step 2.2: Configure Hostinger DNS

1. Login to **Hostinger hPanel**: https://hpanel.hostinger.com
2. Go to **Domains** → Select `gahenaxaisolutions.com`
3. Click **"DNS Zone"**
4. Click **"Add Record"** or **"Manage"**
5. Add new **CNAME** record:

| Field | Value |
|-------|-------|
| **Type** | CNAME |
| **Name/Host** | `trickster-api` |
| **Points to/Target** | `trickster-oracle-api.onrender.com` (from Step 2.1) |
| **TTL** | 14400 (or Auto) |

6. Click **"Add Record"** or **"Save"**

#### Step 2.3: Wait for DNS Propagation

- DNS changes take **5-60 minutes** (usually ~15 minutes)
- Check propagation: https://dnschecker.org
  - Enter: `trickster-api.gahenaxaisolutions.com`
  - Look for CNAME record pointing to Render

#### Step 2.4: Wait for TLS Certificate

- Render will automatically issue Let's Encrypt certificate
- This happens after DNS propagates
- Check in Render: Settings → Custom Domain
- Look for **"Certificate Status: Active"** with green 🔒

✅ **Checkpoint**: Domain should show green lock icon in Render dashboard

---

### PHASE 3: Verification (5 minutes)

#### Step 3.1: Test System Endpoints

Open these URLs in browser or use curl:

1. **Health Check**:
```bash
curl -i https://trickster-api.gahenaxaisolutions.com/health
```

Expected response:
```json
HTTP/2 200
x-request-id: <UUID>
x-process-time: <N>ms

{
  "status": "healthy",
  "service": "trickster-oracle-api",
  "version": "0.1.0",
  "timestamp": "2026-02-06T..."
}
```

2. **Ready Check**:
```bash
curl https://trickster-api.gahenaxaisolutions.com/ready
```

Expected:
```json
{
  "ready": true,
  "checks": {
    "app_booted": true
  }
}
```

3. **Version Info**:
```bash
curl https://trickster-api.gahenaxaisolutions.com/version
```

Expected:
```json
{
  "version": "0.1.0",
  "build_commit": "dbd0de0",
  "api_name": "Trickster Oracle",
  "environment": "production"
}
```

#### Step 3.2: Run Verification Script

From local terminal:

```bash
cd c:/Users/USUARIO/.gemini/antigravity/playground/TRIKSTER-ORACLE
# Edit tools/verify_deploy.sh to use production URL
bash tools/verify_deploy.sh
```

Or manually test each:
```bash
curl -i https://trickster-api.gahenaxaisolutions.com/health
curl -i https://trickster-api.gahenaxaisolutions.com/ready
curl -i https://trickster-api.gahenaxaisolutions.com/version
```

#### Step 3.3: Verify Request-ID Preservation

```bash
curl -i https://trickster-api.gahenaxaisolutions.com/health \
  -H "X-Request-ID: my-custom-id-123"
```

Check response headers contain:
```
X-Request-ID: my-custom-id-123
X-Process-Time: <N>ms
```

✅ **Checkpoint**: All endpoints return 200 with correct headers

---

### PHASE 4: CORS Validation (if frontend exists)

If you have a frontend deployed:

1. Open frontend in browser
2. Make API call from frontend
3. Check browser console for CORS errors
4. If CORS errors appear:
   - Update `CORS_ORIGINS` env var in Render
   - Add frontend domain to allowlist
   - Redeploy

---

## ✅ Deployment Checklist

Mark each as you complete:

### Pre-Deploy
- [x] Tests passed locally (5/5)
- [x] Protocolo Semáforo approved (🟢 GO)
- [x] Code pushed to GitHub (commit: dbd0de0)
- [x] render.yaml in repo
- [x] .env.example in repo

### Render Setup
- [ ] Render account created/logged in
- [ ] GitHub connected to Render
- [ ] Web Service created (Blueprint or Manual)
- [ ] Environment variables set (ENV, BUILD_COMMIT, DATA_DIR, CORS_ORIGINS)
- [ ] Health check path set to `/health`
- [ ] Initial deploy completed (status: Live)

### Custom Domain
- [ ] Custom domain added in Render
- [ ] CNAME target copied
- [ ] Hostinger DNS configured (CNAME record)
- [ ] DNS propagated (dnschecker.org)
- [ ] TLS certificate active (green lock)

### Verification
- [ ] `/health` returns 200 + X-Request-ID
- [ ] `/ready` returns 200 + ready: true
- [ ] `/version` returns 200 + build_commit
- [ ] Request-ID preservation works
- [ ] No CORS errors (if frontend deployed)
- [ ] HTTPS works (green lock in browser)

### Post-Deploy
- [ ] Monitor logs for errors (first 24h)
- [ ] Check response times (acceptable?)
- [ ] Test from different locations
- [ ] Document deployment date/time

---

## 🚨 Troubleshooting

### Issue: Build Fails

**Symptom**: Render shows "Build failed" in logs

**Solutions**:
1. Check build logs for specific error
2. Common issues:
   - Missing dependencies → Check `backend/pyproject.toml`
   - Python version mismatch → Specify in `render.yaml`
   - Import errors → Check `backend/app/main.py`

### Issue: Application Crash on Startup

**Symptom**: Deploy succeeds but service shows "Crashed"

**Solutions**:
1. Check application logs in Render
2. Look for:
   - Port binding issues → Should use `$PORT` from Render
   - Missing env vars → Check Environment tab
   - Import errors → Check all modules load

### Issue: DNS Not Resolving

**Symptom**: `nslookup trickster-api.gahenaxaisolutions.com` returns nothing

**Solutions**:
1. Wait 30 more minutes (DNS can be slow)
2. Check CNAME record in Hostinger:
   - Name: exactly `trickster-api` (no dots)
   - Target: exactly as shown in Render (with `.onrender.com`)
3. Clear local DNS cache:
   ```bash
   ipconfig /flushdns
   ```

### Issue: TLS Certificate Won't Issue

**Symptom**: Render shows "Certificate: Pending" for > 30 minutes

**Solutions**:
1. Ensure DNS is fully propagated first
2. Check domain ownership in Render
3. Try removing and re-adding custom domain
4. Wait another 30 minutes (Let's Encrypt can be slow)

### Issue: 503 Service Unavailable

**Symptom**: Domain resolves but returns 503

**Solutions**:
1. Check service status in Render (should be "Live")
2. Check health endpoint logs
3. Ensure `/health` endpoint works
4. Check if service is sleeping (Free tier sleeps after inactivity)

---

## 📊 Expected Timeline

| Phase | Duration | Can Overlap |
|-------|----------|-------------|
| Create Render Service | 5 min | No |
| Initial Build/Deploy | 5-10 min | No |
| Add Custom Domain | 2 min | After deploy |
| DNS Propagation | 15-60 min | Yes (wait) |
| TLS Certificate | 5-15 min | After DNS |
| Verification | 5 min | After TLS |
| **TOTAL** | **40-95 min** | |

---

## 🎯 Success Criteria

Deployment is **SUCCESSFUL** when:

✅ Render service shows "Live" status  
✅ Custom domain accessible via HTTPS  
✅ Green lock icon in browser  
✅ `/health` returns 200 with X-Request-ID  
✅ `/ready` returns 200  
✅ `/version` shows correct build_commit  
✅ No CORS errors from frontend  
✅ Response times acceptable (< 500ms p95)  

---

## 📞 Support

- **Render Docs**: https://render.com/docs
- **Render Support**: Dashboard → Help → Chat
- **Hostinger Support**: hPanel → Support
- **Project Docs**: `docs/DEPLOY_RENDER_HOSTINGER.md`

---

## 🔄 Rollback Procedure

If deployment fails or has issues:

### In Render:
1. Go to service → **"Deploys"** tab
2. Find previous successful deploy
3. Click **"Redeploy"** on the old deploy

### In Hostinger:
1. Go to DNS Zone
2. Delete the CNAME record for `trickster-api`
3. DNS will propagate removal in 5-60 minutes

---

## ✅ Next Steps After Successful Deploy

1. **Monitor for 24 hours**:
   - Check Render logs hourly
   - Watch for errors or crashes
   - Test endpoints periodically

2. **Document deployment**:
   - Record actual domain: `https://trickster-api.gahenaxaisolutions.com`
   - Record deploy date/time
   - Record any issues encountered

3. **Create GitHub Issue for Jules**:
   - Use `GITHUB_ISSUE_FOR_JULES.md`
   - Jules will implement B1-E1 features

4. **Continue Phase 5 (Tokens)**:
   - After Jules completes B1-E1
   - Deploy frontend (Phase 6)

---

## 🎉 Ready to Deploy!

**Current Status**: All validations passed, ready to execute

**Start with**: Phase 1, Step 1.1 (Login to Render)

**Good luck! 🚀**
