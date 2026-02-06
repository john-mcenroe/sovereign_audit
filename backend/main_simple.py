"""
Simplified version for testing - removes complex logic to verify basic FastAPI setup works
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Sovereign Scan API - Simple Test")

# CORS middleware
FRONTEND_URLS = os.getenv("FRONTEND_URLS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_URLS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    url: str


class Vendor(BaseModel):
    name: str
    purpose: str
    location: str
    risk: str


class AnalyzeResponse(BaseModel):
    score: int
    risk_level: str
    summary: str
    vendors: list[Vendor]


@app.get("/")
async def root():
    return {"message": "Sovereign Scan API - Simple Test", "status": "running"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "message": "Backend is running",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_url(request: AnalyzeRequest):
    """Simplified analyze endpoint - returns mock data for testing"""
    import asyncio
    
    # Simulate processing time
    await asyncio.sleep(2)
    
    # Return mock data to test the flow
    return AnalyzeResponse(
        score=75,
        risk_level="Medium",
        summary="This is a test response. The backend is working correctly. URL received: " + request.url,
        vendors=[
            Vendor(
                name="Test Vendor 1",
                purpose="Hosting",
                location="United States",
                risk="High"
            ),
            Vendor(
                name="Test Vendor 2",
                purpose="Analytics",
                location="EEA",
                risk="Low"
            )
        ]
    )
