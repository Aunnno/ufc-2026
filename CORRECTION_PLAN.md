# CORRECTION PLAN: Fix CORS and Mixed Content Issues

## Current Problem Analysis

Frontend (HTTPS port 9000) → Nginx (port 9000) → Frontend Dev Server (port 5173)
Frontend (HTTPS port 9000) → **Direct HTTP to Backend (port 9001)** ❌

**Should be:**
Frontend (HTTPS port 9000) → Nginx (port 9000) → **Backend (port 9001)** ✅

## Root Causes
1. Frontend API store using old `serverAddress` from localStorage
2. Nginx configured correctly but frontend bypassing it
3. Backend CORS configuration issue (`allow_credentials=True` with wildcard origin)

## Step-by-Step Correction

### Step 1: Clear Frontend LocalStorage
Open browser DevTools (F12) and run:
```javascript
localStorage.removeItem('serverAddress')
localStorage.clear()  // Optional: clear all
```

Or use browser UI:
1. F12 → Application → Local Storage
2. Find `serverAddress` key
3. Delete it
4. Refresh page (Ctrl+F5)

### Step 2: Verify Environment Variables
Check `frontend/.env.development`:
```
VITE_API_BASE_URL=https://192.168.43.105:9000/api
```

Check `frontend/.env`:
```
VITE_API_BASE_URL=https://192.168.43.105:9000/api
```

### Step 3: Check What Backend Port is Running
```bash
sudo netstat -tlnp | grep -E ':9001|:8000'
```

### Step 4: Start/Restart Services in Correct Order

#### Option A: Backend on Port 9001
```bash
# 1. Stop all services
sudo nginx -s stop 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true

# 2. Start backend on port 9001
cd /home/n1ghts4kura/Desktop/ufc-2026/backend
source venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 9001 --reload &

# 3. Start frontend dev server
cd /home/n1ghts4kura/Desktop/ufc-2026/frontend
npm run dev &

# 4. Start nginx with updated config
sudo nginx -c /home/n1ghts4kura/Desktop/ufc-2026/nginx.conf

# 5. Verify services
sudo netstat -tlnp | grep -E ':5173|:9000|:9001'
```

#### Option B: Backend on Port 8000 (Update nginx)
If backend must run on port 8000:
```bash
# Update nginx.conf line 109:
# proxy_pass http://localhost:9001; → proxy_pass http://localhost:8000;

# Then start backend on port 8000
cd /home/n1ghts4kura/Desktop/ufc-2026/backend
source venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
```

### Step 5: Test Configuration

#### Test 1: Direct Backend Access (should work)
```bash
curl http://192.168.43.105:9001/api/map/
```

#### Test 2: Nginx Proxy Access (should work via HTTPS)
```bash
curl -k https://192.168.43.105:9000/api/map/
```

#### Test 3: Frontend Access
1. Open browser to `https://192.168.43.105:9000`
2. Accept SSL warning (self-signed certificate)
3. Open DevTools → Network tab
4. Check API requests go to `https://192.168.43.105:9000/api/...`

### Step 6: Verify Backend CORS Configuration
Check `backend/src/main.py` has:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False with wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)
```

## Alternative: Simplify Setup (Recommended)

Since both frontend and backend are on same machine, use **Vite Proxy** instead of nginx for API:

### Step 1: Update Vite Configuration
Edit `frontend/vite.config.js`:
```javascript
export default defineConfig({
  plugins: [...],
  resolve: {...},
  server: {
    allowedHosts: ["*"],
    proxy: {
      '/api': {
        target: 'http://localhost:9001',  // or 8000
        changeOrigin: true,
        secure: false,  // For self-signed certs
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

### Step 2: Update Environment Variables
Change `frontend/.env.development`:
```
VITE_API_BASE_URL=/api  # Use relative path
```

### Step 3: Restart Services
```bash
# Stop nginx (not needed anymore)
sudo nginx -s stop

# Start backend
cd backend && source venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 9001 --reload &

# Start frontend
cd frontend && npm run dev
```

### Step 4: Access Frontend
Visit `https://localhost:5173` (Vite dev server with HTTPS)

## Debug Checklist

### If Still Getting Mixed Content:
1. Check browser console for actual request URL
2. Verify `baseUrl.value` in API store:
   ```javascript
   // In browser console
   const apiStore = useApiStore()
   console.log(apiStore.baseUrl)
   ```

### If CORS Errors Persist:
1. Check backend logs for CORS middleware errors
2. Test with curl to see if CORS headers present:
   ```bash
   curl -I http://192.168.43.105:9001/api/map/
   # Look for: Access-Control-Allow-Origin: *
   ```

### If 500 Internal Server Error:
1. Check backend logs:
   ```bash
   cd /home/n1ghts4kura/Desktop/ufc-2026/backend
   tail -f nohup.out  # or check terminal output
   ```
2. Common causes:
   - Missing API key in `.env`
   - Model files not found
   - Python import errors

## Final Verification

After fixes, API requests should show:
- URL: `https://192.168.43.105:9000/api/...`
- No Mixed Content warnings
- CORS headers present in response
- Status 200 for successful requests

## Files to Check/Update
1. `frontend/.env.development` - HTTPS URL with port 9000
2. `frontend/.env` - HTTPS URL with port 9000
3. `backend/src/main.py` - CORS configuration
4. `nginx.conf` - Correct proxy_pass port
5. Browser localStorage - Clear `serverAddress`
6. `frontend/vite.config.js` - If using Vite proxy