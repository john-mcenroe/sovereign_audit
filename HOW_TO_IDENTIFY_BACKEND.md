# How to Identify the Backend Terminal

## Quick Check

The **backend terminal** is the one where you ran:
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

## What You Should See

### ✅ Backend Terminal Signs:
1. **Command prompt shows**: `(venv)` at the start
2. **Last command**: `uvicorn main:app --reload --port 8000`
3. **Output shows**:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   INFO:     Started reloader process [XXXXX] using WatchFiles
   INFO:     Started server process [XXXXX]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   ```

4. **When you make requests**, you'll see logs like:
   ```
   🌐 INCOMING: POST /analyze
   🚀 STARTING /analyze endpoint
   ```

### ❌ NOT Backend Terminal:
- Shows `npm run dev` or `vite` (that's the frontend)
- Shows `(venv)` but running `python` scripts
- No server output

## How to Check

Run this in the terminal:
```bash
# Check if port 8000 is in use
lsof -ti:8000

# If it returns a number, something is running on port 8000
# That's likely your backend
```

## If You Can't Find It

1. **Look for terminal tabs/windows** with:
   - `uvicorn` in the title or content
   - Python/venv related output
   - Port 8000 mentioned

2. **Check all terminal windows** - the backend might be in a different tab

3. **Start fresh**:
   ```bash
   # Kill any existing backend
   lsof -ti:8000 | xargs kill -9
   
   # Start new backend
   cd /Users/johnmcenroe/Documents/programming_misc/sovereign_audit/backend
   source venv/bin/activate
   uvicorn main:app --reload --port 8000
   ```

## Frontend vs Backend

- **Backend Terminal**: Port 8000, shows `uvicorn`, Python logs
- **Frontend Terminal**: Port 5173, shows `vite`, npm/node logs
