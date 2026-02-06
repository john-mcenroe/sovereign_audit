"""
Simple test version of the API to verify FastAPI is working
Run this with: uvicorn test_simple:app --reload --port 8001
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sovereign Scan API - Test")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Sovereign Scan API - Simple Test", "status": "working"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "message": "Simple test endpoint is working"
    }

@app.get("/test")
async def test():
    return {
        "message": "Test endpoint works!",
        "data": {
            "test": True,
            "fastapi": "working"
        }
    }

@app.post("/test-post")
async def test_post(data: dict):
    return {
        "message": "POST request received",
        "received_data": data,
        "echo": "This is a simple echo endpoint"
    }
