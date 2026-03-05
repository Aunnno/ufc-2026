# Fixes for CORS and Mixed Content Errors

## Changes Made

### 1. Frontend Environment Configuration
- Updated `frontend/.env.development`: Changed `VITE_API_BASE_URL` from `http://192.168.43.105:9001/api` to `https://192.168.43.105:9000/api`
- Updated `frontend/.env`: Changed `VITE_API_BASE_URL` from `http://192.168.43.105:9000/api` to `https://192.168.43.105:9000/api`

### 2. Backend CORS Configuration
- Updated `backend/src/main.py`: Changed `allow_credentials=True` to `allow_credentials=False` to fix CORS preflight issues when using wildcard origins (`allow_origins=["*"]`)

### 3. Nginx Configuration
- Updated `nginx.example.conf`: Changed API proxy from port `8000` to `9001` (line 109)
- Created `nginx.conf` copy with same configuration

## Root Cause Analysis

### Mixed Content Error
- Frontend served via HTTPS on port 9000 (nginx proxy to Vite dev server)
- Frontend was configured to connect directly to backend via HTTP on port 9001
- Browser blocks HTTP requests from HTTPS pages for security

### CORS Error
- Backend CORS middleware had `allow_origins=["*"]` with `allow_credentials=True`
- This combination is not allowed per CORS specification
- Browser rejects preflight requests when credentials are required with wildcard origin

### 500 Internal Server Error
- Backend returned 500 error for `/api/triager/collect_conditions/`
- May be due to internal exception in workflow or model loading issue
- CORS headers may not be added if error occurs before middleware (but map request succeeded)

## Next Steps Required

### 1. Restart Services

#### Restart Frontend Dev Server (to pick up new environment variables):
```bash
cd /home/n1ghts4kura/Desktop/ufc-2026/frontend
npm run dev
```

#### Restart Nginx with updated configuration:
```bash
sudo nginx -s stop
sudo nginx -c /home/n1ghts4kura/Desktop/ufc-2026/nginx.conf
```

#### Restart Backend (with CORS fix):
```bash
cd /home/n1ghts4kura/Desktop/ufc-2026/backend
source venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 9001 --reload
```

**Note**: If backend is already running on port 9001, you may need to kill the existing process first.

### 2. Verify Backend Port
Check which port the backend is actually running on:
```bash
sudo netstat -tlnp | grep :9001
sudo netstat -tlnp | grep :8000
```

If backend is running on port 8000, update `nginx.conf` line 109 to `proxy_pass http://localhost:8000;`

### 3. Clear Frontend LocalStorage (Optional)
If frontend still uses old server address from localStorage:
1. Open browser Developer Tools
2. Go to Application → Local Storage
3. Remove `serverAddress` key
4. Refresh page

### 4. Test Configuration

#### Test Nginx Proxy:
```bash
curl -k https://192.168.43.105:9000/api/map/
```
Should return map data.

#### Test Backend Directly:
```bash
curl http://192.168.43.105:9001/api/map/
```
Should also return map data.

### 5. Investigate 500 Error
Check backend logs for detailed error:
```bash
cd /home/n1ghts4kura/Desktop/ufc-2026/backend
tail -f nohup.out  # or wherever backend logs are written
```

Common causes:
- Missing API key for online model (check `.env` file)
- Offline model not loaded (check model files exist)
- Python exception in workflow

## Alternative Solution
If nginx proxy setup is too complex, you can:
1. Run backend on HTTPS (requires SSL certificates)
2. Run frontend on HTTP (but microphone won't work)
3. Use Vite proxy instead of nginx (add proxy config to `vite.config.js`)

## Files Modified
- `frontend/.env.development`
- `frontend/.env`
- `backend/src/main.py`
- `nginx.example.conf`
- Created `nginx.conf`

## Verification
After applying fixes:
1. Mixed Content warnings should disappear
2. CORS errors should be resolved
3. API requests should go through HTTPS port 9000
4. Map data should load successfully
5. Voice-to-text may still fail with 500 error (separate issue)