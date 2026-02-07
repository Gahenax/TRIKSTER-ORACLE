# 🚀 RENDER QUICK START - Form Values

**URL**: https://dashboard.render.com/web/new  
**Task**: Create new Web Service for TRICKSTER-ORACLE

---

## 📋 STEP 1: Connect GitHub Repository

### 1.1 If Repository Not Connected Yet:
- Click **"Connect account"** or **"Connect GitHub"**
- Authorize Render to access your GitHub
- Search for: `Gahenax/TRIKSTER-ORACLE`
- Click **"Connect"** on the repository

### 1.2 If Already Connected:
- Look for `Gahenax/TRIKSTER-ORACLE` in the list
- Click **"Connect"** button next to it

---

## 📋 STEP 2: Fill Out the Form

Copy these EXACT values into the Render form:

### Basic Information

**Name** (Service name):
```
trickster-oracle-api
```

**Region**:
```
Oregon (US West) or closest to you
```

**Branch**:
```
master
```

**Root Directory**:
```
backend
```

---

### Build & Deploy Settings

**Runtime**:
```
Python 3
```
(Select from dropdown)

**Build Command**:
```
pip install -e .
```

**Start Command**:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

### Advanced Settings (Click "Advanced" button)

**Health Check Path**:
```
/health
```

---

### Environment Variables (Click "Add Environment Variable" for each)

| Key | Value |
|-----|-------|
| `ENV` | `prod` |
| `BUILD_COMMIT` | `6b98823` |
| `DATA_DIR` | `/var/data` |
| `CORS_ORIGINS` | `https://tricksteranalytics.gahenaxaisolutions.com` |

**How to add**:
1. Click **"Add Environment Variable"** button (or similar)
2. Enter **Key** (left box)
3. Enter **Value** (right box)
4. Repeat for all 4 variables

---

### Instance Type

**Plan**:
```
Free
```
(Select the free tier option)

---

## 📋 STEP 3: Review & Create

### Before clicking "Create Web Service", verify:

- [x] Name: `trickster-oracle-api`
- [x] Branch: `master`
- [x] Root Directory: `backend`
- [x] Build Command: `pip install -e .`
- [x] Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [x] Health Check Path: `/health`
- [x] Environment variables: 4 total (ENV, BUILD_COMMIT, DATA_DIR, CORS_ORIGINS)
- [x] Plan: Free

### Click "Create Web Service" Button

---

## 📋 STEP 4: Wait for Deployment

### What Happens Next:

1. **Build starts** (~3-5 minutes)
   - You'll see logs scrolling
   - Look for: `Building...`

2. **Deploy starts** (~2-3 minutes)
   - After build succeeds
   - Look for: `Deploying...`

3. **Service goes live** 
   - Status changes to **"Live"** with 🟢 green indicator
   - Look for in logs: `Application startup complete`

### Expected Build Log Output:
```
==> Building...
Collecting dependencies...
Installing backend...
Successfully built

==> Deploying...
Starting service...
2026-02-06 XX:XX:XX - app.main - INFO - Trickster Oracle API starting
INFO:     Uvicorn running on http://0.0.0.0:XXXXX
INFO:     Application startup complete.

==> Deploy successful!
```

**Total time**: ~5-10 minutes

---

## 📋 STEP 5: Get Service URL

After deploy completes:

1. Look at the top of the page
2. You'll see a URL like: `https://trickster-oracle-api.onrender.com`
3. **COPY THIS URL** (you'll need it for DNS later)
4. **TEST IT**:
   ```
   Open in browser or curl:
   https://trickster-oracle-api.onrender.com/health
   ```

Expected response:
```json
{
  "status": "healthy",
  "service": "trickster-oracle-api",
  "version": "0.1.0"
}
```

---

## ✅ Success Indicators

You know it worked when:

- ✅ Status shows: **"Live"** with green dot 🟢
- ✅ Logs show: `Application startup complete`
- ✅ URL works: `https://<your-service>.onrender.com/health` returns 200
- ✅ No "Deploy failed" errors
- ✅ No crash loops

---

## 🚨 Common Issues

### Issue: "Build Failed"
**Check**:
- Is `backend` directory spelled correctly?
- Is branch `master` correct?
- Check build logs for specific error

### Issue: "Deploy Failed" or "Crashed"
**Check**:
- Start command exact: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- All 4 environment variables added
- Check application logs tab

### Issue: Can't Find Repository
**Solution**:
- Click "Connect account" to link GitHub
- Give Render permission to read repos
- Refresh the page

---

## 📝 What to Copy/Save

While deploying, save these for next steps:

1. **Service Name**: `trickster-oracle-api`
2. **Service URL**: `https://trickster-oracle-api.onrender.com` (example)
3. **Deploy Time**: Note when it finishes
4. **Logs**: Check for any warnings

---

## ⏭️ NEXT STEP (After Deploy Succeeds)

Once you see **"Live"** status:

**→ Go to**: [docs/DEPLOYMENT_GUIDE_MANUAL.md - Phase 2](DEPLOYMENT_GUIDE_MANUAL.md)

**→ Task**: Add Custom Domain

You'll need:
- Service URL from this step
- Access to Hostinger DNS

---

## 📞 Need Help?

- **Render Docs**: https://render.com/docs/deploy-fastapi
- **Render Status**: Check if Render has any outages
- **Our Repo**: https://github.com/Gahenax/TRIKSTER-ORACLE

---

## 🎯 Quick Reference

**Repository**: `Gahenax/TRIKSTER-ORACLE`  
**Branch**: `master`  
**Root Dir**: `backend`  
**Build**: `pip install -e .`  
**Start**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`  
**Health**: `/health`  
**Env Vars**: 4 (ENV, BUILD_COMMIT, DATA_DIR, CORS_ORIGINS)  

---

**Good luck! 🚀 Report back when you see "Live" status!**
