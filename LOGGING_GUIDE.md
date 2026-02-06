# Logging Guide

## Backend Logging

The backend now has comprehensive logging at multiple levels:

### Log Levels
- **DEBUG**: Very detailed information (function calls, variable values)
- **INFO**: General information (requests, responses, steps)
- **WARNING**: Warnings (missing config, non-critical issues)
- **ERROR**: Errors (exceptions, failures)

### What You'll See

#### On Startup:
```
🚀 FastAPI application initialized
📦 Thread pool executor created with 4 workers
🔑 GEMINI_API_KEY check: ✅ Found
🤖 Initializing Gemini API...
✅ Gemini API initialized successfully
```

#### On Each Request:
```
🌐 [12345] INCOMING REQUEST: POST /analyze
   [12345] Headers: {...}
   [12345] Body: {"url": "https://example.com"}
   [12345] Calling next middleware/handler...
🚀 STARTING /analyze endpoint
📥 Request received: url='https://example.com'
🔗 URL to analyze: https://example.com
...
✅ [12345] RESPONSE: POST /analyze - Status 200 - 2.345s
```

#### On Errors:
```
❌ [12345] EXCEPTION in POST /analyze after 1.234s
   [12345] Exception type: HTTPException
   [12345] Exception message: Could not access page
   [12345] Full traceback: ...
```

### Where to See Logs

**Backend Terminal**: All logs appear in the terminal where you ran `uvicorn main:app --reload`

**Look for:**
- `🌐` = Incoming request
- `🚀` = Starting operation
- `📥` = Receiving data
- `📤` = Sending data
- `✅` = Success
- `❌` = Error
- `⚠️` = Warning

## Frontend Logging

The frontend logs to the browser console:

### How to View
1. Open browser DevTools (F12 or Cmd+Option+I)
2. Go to "Console" tab
3. You'll see all the logs

### What You'll See

#### On Request Start:
```
================================================================================
🚀 FRONTEND: Starting analysis request
📋 URL to analyze: https://example.com
🌐 API URL: http://localhost:8000
⏰ Timestamp: 2026-02-06T10:30:15.123Z
📤 Step 1: Preparing request...
📦 Request body: {
  "url": "https://example.com"
}
```

#### On Response:
```
📥 Response received after 2345ms
📊 Response status: 200 OK
✅ Response OK, parsing JSON...
✅ Analysis complete!
📊 Result data: {...}
```

#### On Error:
```
================================================================================
❌ FRONTEND ERROR CAUGHT
   Error name: TypeError
   Error message: Failed to fetch
   Error stack: ...
   Full error object: {...}
================================================================================
```

## Debugging Tips

1. **Backend not responding?**
   - Check backend terminal for `🌐 INCOMING REQUEST` logs
   - If you don't see this, the request isn't reaching the backend

2. **500 Internal Server Error?**
   - Look for `❌ EXCEPTION` or `❌ UNEXPECTED EXCEPTION` in backend logs
   - Check the full traceback to see where it failed

3. **Request hanging?**
   - Check which step it's stuck on in backend logs
   - Look for `🔄 About to run...` messages to see what's executing

4. **Frontend errors?**
   - Open browser console (F12)
   - Look for `❌ FRONTEND ERROR` messages
   - Check the error stack trace

5. **No logs at all?**
   - Make sure the server is running
   - Check if auto-reload picked up changes (look for "Reloading..." message)
   - Try restarting the server manually

## Enabling More Logs

To see even more detail, change the log level in `backend/main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG for more detail
    ...
)
```

This will show:
- Function entry/exit
- Variable values
- Internal function calls
- More detailed request/response info
