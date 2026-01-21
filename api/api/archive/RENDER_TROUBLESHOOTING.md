# 🔧 Render Deployment Troubleshooting Guide

## ❌ **Issue: `ModuleNotFoundError: No module named 'databases'`**

This error indicates that Render isn't successfully installing the `databases` package. Here's how to diagnose and fix it:

---

## 🔍 **Diagnostic Steps**

### 1. Check Render Build Logs
Look for these patterns in your Render build logs:

```bash
# Good signs:
✓ pip install --upgrade pip && pip install -r requirements.txt
✓ Successfully installed databases-0.7.0 asyncpg-0.29.0

# Bad signs:
✗ ERROR: Could not find a version that satisfies the requirement databases[postgresql]
✗ ERROR: Failed building wheel for databases
✗ WARNING: pip is being invoked by an old script wrapper
```

### 2. Verify Requirements Structure
Run locally to test:
```bash
cd api/
python test_requirements.py
```

### 3. Test Database Imports
The system now has automatic fallback:
- **Primary**: Uses `databases` library if available
- **Fallback**: Uses `asyncpg` directly if databases fails
- **Error**: Only fails if neither package is available

---

## 🔧 **Fixes Applied**

### ✅ **1. Flattened requirements.txt**
**Before**: Used `-r src/requirements.codex.txt` with git dependencies  
**After**: All dependencies listed directly in requirements.txt

```txt
# CRITICAL: databases package for Manager Agent system
databases[postgresql]>=0.7.0
asyncpg>=0.29.0

# Core FastAPI runtime
fastapi>=0.110.0
uvicorn>=0.34.0
...
```

### ✅ **2. Fixed render.yaml Configuration**
**Before**: 
```yaml
buildCommand: pip install -r api/requirements.txt  # Wrong path!
root: api/
```

**After**:
```yaml
buildCommand: pip install --upgrade pip && pip install -r requirements.txt
root: api/  # Now requirements.txt is relative to this root
```

### ✅ **3. Automatic Fallback System**
The system now automatically falls back to asyncpg if databases fails:

```python
try:
    from databases import Database
    print("✅ Using 'databases' library")
except ImportError:
    print("🔄 Falling back to asyncpg...")
    from .deps_fallback import get_db  # Uses asyncpg directly
```

### ✅ **4. Better Error Messages**
Added clear diagnostic messages that show exactly what's missing and how to fix it.

---

## 🚀 **Deployment Process**

### 1. **Deploy to Render**
The system should now deploy successfully with either:
- `databases[postgresql]` package (preferred)
- `asyncpg` package (fallback)

### 2. **Check Startup Logs** 
Look for these messages:
```bash
✅ Using 'databases' library for database connections
# OR
⚠️  'databases' package not available
🔄 Falling back to asyncpg direct connection...
✅ Using asyncpg fallback for database connections
```

### 3. **Verify Database Connection**
Test the health endpoint:
```bash
curl https://your-app.onrender.com/health/db
```

Expected response:
```json
{
  "status": "healthy",
  "database_connected": true,
  "current_time": "2024-01-15T10:30:00"
}
```

### 4. **Run Migrations**
Once deployed successfully:
```bash
# Via Render shell or locally with DATABASE_URL
python run_migrations.py
```

---

## 🔍 **If Still Failing**

### Render-Specific Issues

1. **Build Environment Problems**
   - Render might be using old pip version
   - Python version mismatch
   - Insufficient build resources

2. **Dependency Resolution Issues**
   - Complex dependency trees
   - Version conflicts
   - Build tools missing (gcc, postgresql-dev)

### Database Connection Errors
- **`asyncpg.exceptions.InternalServerError: Tenant or user not found`**
  - Indicates an invalid `DATABASE_URL`
  - Verify the connection string includes the correct Supabase project reference and credentials
  - The server will now start without a database, but features that depend on it will be disabled

### Emergency Fallback
If all else fails, you can temporarily simplify:

```python
# Minimal deps.py for emergency deployment
import os
import asyncio

async def get_db():
    # Return a mock database for basic functionality
    return MockDatabase()

class MockDatabase:
    async def fetch_one(self, query, values=None):
        return None
    async def execute(self, query, values=None):
        return 0
```

---

## ✅ **Success Indicators**

You'll know the fix worked when you see:

1. **Build Logs**: No import errors during startup
2. **Health Check**: `/health/db` returns `{"database_connected": true}`
3. **Manager API**: `POST /api/baskets/{id}/work` returns real BasketDelta
4. **No Fake Data**: Real worker agent analysis in responses

---

## 📞 **Get Help**

If you're still seeing issues:

1. **Check build logs** for specific error messages
2. **Test requirements locally**: `python test_requirements.py`
3. **Verify environment variables**: `DATABASE_URL`, `SUPABASE_*`
4. **Test individual packages**: `pip install databases[postgresql]==0.7.0`

The system is designed to be robust - it should work with either the `databases` library OR plain `asyncpg`. If both fail, there's likely a deeper Render environment issue.