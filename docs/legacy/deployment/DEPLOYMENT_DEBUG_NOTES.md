# Deployment Debug Notes - Phase 1 substrate-API
**Date:** 2025-11-13
**Status:** ✅ **RESOLVED - LIVE ON RENDER**

## Resolution Summary

**Service:** yarnnn-enterprise-api (substrate-API)
**Dashboard:** https://dashboard.render.com/web/srv-d43utn2dbo4c73b2hjjg
**Live Version:** Commit `91314c3f` (11/13) - **Phase 1 endpoints LIVE** ✅
**Final Fix:** Corrected relative import path in storage_service.py

**Failed Deployments (before fix):**
1. `ad28b8d2` - Phase 1 verification
2. `5b400f7c` - Added python-multipart
3. `97009acb` - Removed sys.path manipulation

**Successful Deployment:**
4. `91314c3f` - Fixed import path from `....utils` to `...utils`

## What Changed in Phase 1

### New Files Created
```
substrate-api/api/src/app/reference_assets/
├── __init__.py
├── routes.py
├── schemas.py
└── services/
    ├── __init__.py
    └── storage_service.py
```

### Modified Files
```
substrate-api/api/src/app/agent_server.py  # Added reference_assets_router import + registration
substrate-api/api/requirements.txt         # Added python-multipart>=0.0.6
```

### Key Dependencies Added
- `python-multipart>=0.0.6` - Required for FastAPI File/UploadFile

## Potential Issues to Check in Render Logs

### 1. Import Errors
**Check for:**
```
ModuleNotFoundError: No module named 'reference_assets'
ImportError: cannot import name 'router' from 'app.reference_assets'
```

**Cause:** Python import path issues in production environment

**Fix Options:**
- Verify `__init__.py` files exist in all directories
- Check relative import syntax (we use `from ..utils.jwt`)
- Ensure no circular imports

### 2. Dependency Installation Issues
**Check for:**
```
ERROR: Could not find a version that satisfies the requirement python-multipart
Failed to install requirements.txt
```

**Cause:** pip installation failure

**Fix Options:**
- Pin specific version: `python-multipart==0.0.9`
- Check if package name is correct (it is)

### 3. Supabase Storage Issues
**Check for:**
```
AttributeError: 'Client' object has no attribute 'storage'
supabase.storage module not found
```

**Cause:** Supabase client missing storage functionality

**Fix Options:**
- Verify supabase-py includes storage module
- May need to add explicit dependency

### 4. FastAPI Router Registration
**Check for:**
```
TypeError: app.include_router() missing required positional argument
AttributeError: 'APIRouter' object has no attribute 'prefix'
```

**Cause:** Router not properly configured

**Fix Options:**
- Verify router creation in routes.py:
  ```python
  router = APIRouter(prefix="/substrate/baskets", tags=["reference-assets"])
  ```

### 5. Startup Import Verification
**Check for:**
```
Error loading ASGI app. Could not import module "src.app.agent_server"
```

**Cause:** Module import fails at startup

**Fix Options:**
- Check agent_server.py line where reference_assets is imported:
  ```python
  from .reference_assets import router as reference_assets_router
  ```

## Files to Review in Render Dashboard

### Build Command
```bash
pip install --upgrade pip && pip install -r requirements.txt
```

### Start Command
```bash
uvicorn src.app.agent_server:app --host 0.0.0.0 --port 10000 --log-level debug
```

### Environment Variables
Ensure these are set:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`

## Local Verification Tests

### Test 1: Import Chain
```bash
cd substrate-api/api
python3 -c "from src.app.reference_assets import router; print(router.prefix)"
# Expected: /substrate/baskets
```

### Test 2: Router Registration
```python
from src.app.agent_server import app
routes = [route.path for route in app.routes]
print([r for r in routes if 'assets' in r])
# Expected: ['/api/substrate/baskets/{basket_id}/assets', ...]
```

### Test 3: Dependencies
```bash
cd substrate-api/api
pip install -r requirements.txt
# Should complete without errors
```

## Quick Fixes to Try

### Fix 1: Explicit __init__.py exports
Edit `substrate-api/api/src/app/reference_assets/__init__.py`:
```python
from .routes import router

__all__ = ["router"]
```

### Fix 2: Pin python-multipart version
Edit `requirements.txt`:
```
python-multipart==0.0.9  # Instead of >=0.0.6
```

### Fix 3: Check Supabase version
May need to upgrade supabase client:
```
supabase>=2.9.0,<3.0.0  # Ensure storage module included
```

## Working Deployment Checklist

Once deployment succeeds, verify:
- [ ] Service starts without errors
- [ ] Health endpoint responds: `GET https://yarnnn-enterprise-api.onrender.com/health`
- [ ] New routes exist:
  - `GET /api/substrate/baskets/{basketId}/asset-types`
  - `POST /api/substrate/baskets/{basketId}/assets`
  - `GET /api/substrate/baskets/{basketId}/assets`
  - `DELETE /api/substrate/baskets/{basketId}/assets/{assetId}`
  - `POST /api/substrate/baskets/{basketId}/assets/{assetId}/signed-url`

## Next Steps After Deployment Success

1. Test endpoints directly via curl/Postman
2. Verify Supabase Storage bucket is accessible
3. Test file upload flow end-to-end
4. Check RLS policies are enforced correctly
5. Deploy work-platform frontend to Vercel
6. Test full integration (UI → BFF → substrate-API → Storage)

---

## Manual Debugging Steps

1. **Check Render Build Logs:**
   - Go to https://dashboard.render.com/web/srv-d43utn2dbo4c73b2hjjg
   - Click on the failed deployment
   - Look for exact error message
   - Search this document for matching error pattern

2. **Test Locally:**
   - Run all verification tests above
   - If they pass locally, issue is environment-specific

3. **Simplify to Isolate:**
   - Temporarily comment out reference_assets import in agent_server.py
   - Push and see if deployment succeeds
   - If yes, issue is in reference_assets module
   - If no, issue is elsewhere (dependency, etc.)

4. **Compare with Working Service:**
   - Check work-platform API configuration (it deploys successfully)
   - Look for differences in build/start commands
   - Verify environment variables match

---

## Root Cause Analysis

**The Problem:**
- File: `substrate-api/api/src/app/reference_assets/services/storage_service.py`
- Line 12: `from ....utils.supabase_client import supabase_admin_client`
- Error: `ImportError: cannot import name 'supabase_admin_client' from 'src.utils.supabase_client'`

**Why It Failed:**
Directory structure:
```
substrate-api/api/src/
├── app/
│   ├── reference_assets/
│   │   └── services/
│   │       └── storage_service.py  <-- WE ARE HERE
└── utils/
    └── supabase_client.py  <-- TARGET (sibling of app/, not parent)
```

Using `....utils` (4 dots) from `services/` directory:
1. services/ → reference_assets/ (1 up)
2. reference_assets/ → app/ (2 up)
3. app/ → src/ (3 up)
4. src/ → api/ (4 up) ❌ **TOO FAR - utils is at src/utils/**

**The Fix:**
Changed to `...utils` (3 dots):
1. services/ → reference_assets/ (1 up)
2. reference_assets/ → app/ (2 up)
3. app/ → src/ (3 up) ✅ **CORRECT - utils is at src/utils/**

**Commit:** 91314c3f
**Deployed:** 2025-11-13 11:55 UTC
**Status:** ✅ LIVE

---

**Last Updated:** 2025-11-13 11:55 UTC
**Status:** ✅ RESOLVED - Deployment successful, all Phase 1 endpoints live
