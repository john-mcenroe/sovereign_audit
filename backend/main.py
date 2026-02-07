from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import re
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Also log uvicorn access logs
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.setLevel(logging.INFO)

load_dotenv()

app = FastAPI(title="Sovereign Scan API")

# Add global exception handler to catch all exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    error_msg = f"❌ GLOBAL EXCEPTION HANDLER CAUGHT: {type(exc).__name__}: {str(exc)}"
    print(error_msg, flush=True)
    print("Full traceback:", flush=True)
    traceback.print_exc()
    logger.error(error_msg, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {type(exc).__name__}: {str(exc)}",
            "error_type": type(exc).__name__
        }
    )

from fastapi.responses import JSONResponse

# Add request logging middleware - MUST be before other middleware
@app.middleware("http")
async def log_requests(request, call_next):
    # Force print to ensure visibility
    print(f"\n🌐 INCOMING: {request.method} {request.url.path}", flush=True)
    import time
    start_time = time.time()
    request_id = id(request)
    logger.info(f"🌐 [{request_id}] INCOMING REQUEST: {request.method} {request.url.path}")
    logger.debug(f"   [{request_id}] Headers: {dict(request.headers)}")
    logger.debug(f"   [{request_id}] Query params: {dict(request.query_params)}")
    
    # Log request body for POST requests
    if request.method == "POST":
        try:
            body = await request.body()
            body_str = body.decode('utf-8')[:500]
            logger.debug(f"   [{request_id}] Body: {body_str}")
            # Create a new request with the body (since we consumed it)
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive
        except Exception as e:
            logger.warning(f"   [{request_id}] Could not read request body: {e}")
    
    try:
        logger.debug(f"   [{request_id}] Calling next middleware/handler...")
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"✅ [{request_id}] RESPONSE: {request.method} {request.url.path} - Status {response.status_code} - {process_time:.3f}s")
        logger.debug(f"   [{request_id}] Response headers: {dict(response.headers)}")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"❌ [{request_id}] EXCEPTION in {request.method} {request.url.path} after {process_time:.3f}s")
        logger.error(f"   [{request_id}] Exception type: {type(e).__name__}")
        logger.error(f"   [{request_id}] Exception message: {str(e)}")
        logger.error(f"   [{request_id}] Full traceback:", exc_info=True)
        raise

# Thread pool for blocking operations
executor = ThreadPoolExecutor(max_workers=4)
logger.info("🚀 FastAPI application initialized")
logger.info(f"📦 Thread pool executor created with {executor._max_workers} workers")

# CORS middleware to allow frontend to connect
# Allow origins from environment variable or default to localhost
# On Render, set FRONTEND_URLS to your Vercel URL, e.g. https://your-app.vercel.app
FRONTEND_URLS = [o.strip() for o in os.getenv("FRONTEND_URLS", "http://localhost:5173,http://localhost:3000").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_URLS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
logger.info(f"🔑 GEMINI_API_KEY check: {'✅ Found' if GEMINI_API_KEY else '❌ Not found'}")
if GEMINI_API_KEY:
    logger.info("🤖 Initializing Gemini API...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Find available model - list models first
        logger.info("🔍 Checking available Gemini models...")
        available_models = []
        model_to_use = None
        
        try:
            models_list = list(genai.list_models())
            logger.info(f"📋 Found {len(models_list)} total models")
            for m in models_list:
                if 'generateContent' in m.supported_generation_methods:
                    model_name = m.name.replace('models/', '')
                    available_models.append(model_name)
                    logger.info(f"   ✅ Available: {model_name}")
            
            # Prefer Gemini 2.5 Flash-Lite (cost-effective, built for scale), then newer models
            preferred_order = ['gemini-2.5-flash-lite', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro', 'gemini-1.0-pro']
            for preferred in preferred_order:
                if preferred in available_models:
                    model_to_use = preferred
                    break
            
            if not model_to_use and available_models:
                model_to_use = available_models[0]
                logger.warning(f"⚠️ Using first available model: {model_to_use}")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not list models: {e}")
            # Fallback to common model names
            model_to_use = 'gemini-pro'
        
        if not model_to_use:
            raise Exception(f"No Gemini models available. Check your API key and quota.")
        
        logger.info(f"🤖 Initializing model: {model_to_use}")
        # Enable Google Search grounding for enhanced analysis
        # Note: Google Search is available in gemini-2.5-flash-lite, gemini-1.5 models, and newer
        try:
            # Try to enable Google Search (available in gemini-2.5-flash-lite, gemini-1.5+ models, and newer)
            if '2.5' in model_to_use or '1.5' in model_to_use or '3' in model_to_use:
                model = genai.GenerativeModel(
                    model_to_use,
                    tools=[{"google_search_retrieval": {}}]
                )
                logger.info("✅ Google Search grounding enabled for enhanced analysis")
            else:
                logger.info(f"ℹ️ Model {model_to_use} may not support Google Search, using standard model")
                model = genai.GenerativeModel(model_to_use)
        except Exception as e:
            logger.warning(f"⚠️ Could not enable Google Search: {e}. Using model without search.")
            model = genai.GenerativeModel(model_to_use)
        logger.info(f"✅ Successfully initialized Gemini model: {model_to_use}")
        logger.info("✅ Gemini API initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini API: {e}", exc_info=True)
        model = None
else:
    logger.warning("⚠️ GEMINI_API_KEY not set - Gemini features will be disabled")
    model = None

# Load known services database
KNOWN_SERVICES = {}
try:
    import os
    known_services_path = os.path.join(os.path.dirname(__file__), "known_services.json")
    with open(known_services_path, "r") as f:
        KNOWN_SERVICES = json.load(f)
    total_services = sum(len(services) for services in KNOWN_SERVICES.values())
    logger.info(f"✅ Loaded {total_services} known services from database")
except FileNotFoundError:
    logger.warning("⚠️ known_services.json not found - service detection will be limited")
except Exception as e:
    logger.error(f"❌ Error loading known_services.json: {e}")

# Service category weights for scoring
CATEGORY_WEIGHTS = {
    "AI/ML": 1.5,
    "Payment Processing": 1.4,
    "Database/Storage": 1.4,
    "Cloud Storage": 1.4,
    "Cloud Infrastructure": 1.4,
    "Authentication": 1.3,
    "Email Service": 1.2,
    "Email Marketing": 1.2,
    "Customer Support": 1.2,
    "SMS/Communications": 1.2,
    "Analytics": 1.0,
    "Monitoring": 1.0,
    "Error Tracking": 1.0,
    "Session Replay": 1.1,
    "CDN": 0.8,
    "CDN/Fonts": 0.7,
    "Tag Management": 1.1,
    "Marketing": 0.9,
    "A/B Testing": 0.8,
    "Social/Advertising": 0.9,
}


class AnalyzeRequest(BaseModel):
    url: str


class Vendor(BaseModel):
    name: str
    purpose: str
    location: str
    risk: str


class CompanyInfo(BaseModel):
    registration_country: str = "Unknown"
    legal_entity: str = "Unknown"
    office_locations: list[str] = []
    employee_locations: list[str] = []


class InfrastructureInfo(BaseModel):
    cloud_provider: str = "Unknown"
    hosting_platform: str = "Unknown"  # Fly.io, Heroku, Vercel, etc.
    data_centers: list[str] = []
    server_locations: list[str] = []
    cdn_providers: list[str] = []


class DataFlowInfo(BaseModel):
    storage_locations: list[str] = []
    processing_locations: list[str] = []
    data_residency: str = "Unknown"  # "EU", "US", "Global", "Unknown"


class ComplianceInfo(BaseModel):
    gdpr_status: str = "Unknown"
    certifications: list[str] = []
    data_residency_guarantees: str = "Unknown"
    recent_incidents: list[str] = []


class AdditionalFindings(BaseModel):
    recent_changes: list[str] = []
    additional_categories: list[str] = []
    search_summary: str = ""


class CompanyResearchQuestion(BaseModel):
    question: str
    answer: str = "No information found"
    confidence: str = "Low"  # "High", "Medium", "Low"
    source_urls: list[str] = []
    sentiment: str = "neutral"  # "positive", "negative", "neutral"


class CompanyResearch(BaseModel):
    score: int = 0
    research_summary: str = ""
    questions_answers: list[CompanyResearchQuestion] = []
    key_findings: list[str] = []
    sovereignty_flags: list[str] = []
    research_categories_covered: list[str] = []


class DetectedService(BaseModel):
    name: str
    domain: str = "Unknown"
    jurisdiction: str = "Unknown"
    category: str = "Other"
    risk_level: str = "Medium"
    alternatives_eu: list[str] = []
    notes: str = ""


class AnalyzeResponse(BaseModel):
    score: int
    risk_level: str
    summary: str
    vendors: list[Vendor]
    company_info: CompanyInfo = CompanyInfo()
    infrastructure: InfrastructureInfo = InfrastructureInfo()
    data_flows: DataFlowInfo = DataFlowInfo()
    compliance: ComplianceInfo = ComplianceInfo()
    additional_findings: AdditionalFindings = AdditionalFindings()
    company_research: CompanyResearch = CompanyResearch()
    risk_factors: list[str] = []
    positive_factors: list[str] = []
    detected_services: list[DetectedService] = []


# =============================================================================
# DATABASE MODULE - SQLite (local) + PostgreSQL (Render) support
# =============================================================================

DATABASE_URL = os.getenv("DATABASE_URL")  # Render sets this automatically
CACHE_MAX_AGE_HOURS = int(os.getenv("CACHE_MAX_AGE_HOURS", "1"))

# Detect which database backend to use
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    # PostgreSQL mode (Render production)
    import psycopg2
    import psycopg2.extras

    SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS analyses (
        id SERIAL PRIMARY KEY,
        url TEXT NOT NULL,
        normalized_url TEXT NOT NULL,
        score INTEGER NOT NULL,
        risk_level TEXT NOT NULL,
        summary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        duration_seconds REAL,
        success BOOLEAN DEFAULT TRUE,
        error_message TEXT,
        response_json TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_analyses_normalized_url ON analyses(normalized_url);
    CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC);

    CREATE TABLE IF NOT EXISTS vendors (
        id SERIAL PRIMARY KEY,
        analysis_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        purpose TEXT,
        location TEXT,
        risk TEXT,
        FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_vendors_analysis_id ON vendors(analysis_id);
    CREATE INDEX IF NOT EXISTS idx_vendors_name ON vendors(name);
    """

    def get_db_connection():
        """Get PostgreSQL connection."""
        conn = psycopg2.connect(DATABASE_URL)
        return conn

    def init_db():
        """Initialize PostgreSQL database."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Split schema into individual statements
            for statement in SCHEMA_SQL.split(';'):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("PostgreSQL database initialized")
        except psycopg2.Error as e:
            logger.warning(f"PostgreSQL init warning (may already exist): {e}")

    @contextmanager
    def get_db():
        """Context manager for PostgreSQL connections."""
        conn = get_db_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_analysis(url: str, normalized_url: str, response: AnalyzeResponse,
                      duration_seconds: float, success: bool = True,
                      error_message: str = None) -> int:
        """Save analysis to PostgreSQL database. Returns analysis ID."""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO analyses
                    (url, normalized_url, score, risk_level, summary,
                     duration_seconds, success, error_message, response_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    url,
                    normalized_url,
                    response.score if success else 0,
                    response.risk_level if success else "Error",
                    response.summary if success else error_message,
                    duration_seconds,
                    success,
                    error_message,
                    response.model_dump_json() if success else "{}"
                ))
                analysis_id = cursor.fetchone()[0]

                # Insert vendors
                if success and response.vendors:
                    for vendor in response.vendors:
                        cursor.execute("""
                            INSERT INTO vendors (analysis_id, name, purpose, location, risk)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (analysis_id, vendor.name, vendor.purpose,
                              vendor.location, vendor.risk))

                cursor.close()
                logger.info(f"Saved analysis #{analysis_id} for {normalized_url}")
                return analysis_id
        except Exception as e:
            logger.warning(f"Failed to save analysis to DB (non-fatal): {e}")
            return -1

    def get_cached_analysis(normalized_url: str) -> AnalyzeResponse | None:
        """Get cached analysis if exists and fresh enough."""
        try:
            with get_db() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute("""
                    SELECT response_json FROM analyses
                    WHERE normalized_url = %s
                      AND success = TRUE
                      AND created_at > NOW() - INTERVAL '%s hours'
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (normalized_url, CACHE_MAX_AGE_HOURS))
                row = cursor.fetchone()
                cursor.close()

                if row:
                    logger.info(f"Cache hit for {normalized_url}")
                    return AnalyzeResponse.model_validate_json(row['response_json'])
                return None
        except Exception as e:
            logger.warning(f"Cache lookup failed (non-fatal): {e}")
            return None

else:
    # SQLite mode (local development)
    DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).parent / "sovereign_audit.db"))

    SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        normalized_url TEXT NOT NULL,
        score INTEGER NOT NULL,
        risk_level TEXT NOT NULL,
        summary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        duration_seconds REAL,
        success BOOLEAN DEFAULT TRUE,
        error_message TEXT,
        response_json TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_analyses_normalized_url ON analyses(normalized_url);
    CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC);

    CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        analysis_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        purpose TEXT,
        location TEXT,
        risk TEXT,
        FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_vendors_analysis_id ON vendors(analysis_id);
    CREATE INDEX IF NOT EXISTS idx_vendors_name ON vendors(name);
    """

    def init_db():
        """Initialize SQLite database."""
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()
        logger.info(f"SQLite database initialized at {DB_PATH}")

    @contextmanager
    def get_db():
        """Context manager for SQLite connections."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_analysis(url: str, normalized_url: str, response: AnalyzeResponse,
                      duration_seconds: float, success: bool = True,
                      error_message: str = None) -> int:
        """Save analysis to SQLite database. Returns analysis ID."""
        try:
            with get_db() as db:
                cursor = db.execute("""
                    INSERT INTO analyses
                    (url, normalized_url, score, risk_level, summary,
                     duration_seconds, success, error_message, response_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    url,
                    normalized_url,
                    response.score if success else 0,
                    response.risk_level if success else "Error",
                    response.summary if success else error_message,
                    duration_seconds,
                    success,
                    error_message,
                    response.model_dump_json() if success else "{}"
                ))
                analysis_id = cursor.lastrowid

                # Insert vendors
                if success and response.vendors:
                    for vendor in response.vendors:
                        db.execute("""
                            INSERT INTO vendors (analysis_id, name, purpose, location, risk)
                            VALUES (?, ?, ?, ?, ?)
                        """, (analysis_id, vendor.name, vendor.purpose,
                              vendor.location, vendor.risk))

                logger.info(f"Saved analysis #{analysis_id} for {normalized_url}")
                return analysis_id
        except Exception as e:
            logger.warning(f"Failed to save analysis to DB (non-fatal): {e}")
            return -1

    def get_cached_analysis(normalized_url: str) -> AnalyzeResponse | None:
        """Get cached analysis if exists and fresh enough."""
        try:
            with get_db() as db:
                row = db.execute("""
                    SELECT response_json FROM analyses
                    WHERE normalized_url = ?
                      AND success = TRUE
                      AND datetime(created_at) > datetime('now', ?)
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (normalized_url, f"-{CACHE_MAX_AGE_HOURS} hours")).fetchone()

                if row:
                    logger.info(f"Cache hit for {normalized_url}")
                    return AnalyzeResponse.model_validate_json(row['response_json'])
                return None
        except Exception as e:
            logger.warning(f"Cache lookup failed (non-fatal): {e}")
            return None


# Initialize DB on startup
try:
    init_db()
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

# =============================================================================
# NEW: Enhanced Service Detection Functions
# =============================================================================

def identify_service_from_domain(domain: str) -> dict:
    """
    Identify known services from domain names.
    Returns service info or None if unknown.
    """
    if not domain:
        return None

    domain_lower = domain.lower()

    # Search through known services database
    for category, services in KNOWN_SERVICES.items():
        for known_domain, service_info in services.items():
            if known_domain in domain_lower:
                return {
                    'name': service_info['name'],
                    'domain': domain,
                    'jurisdiction': service_info['jurisdiction'],
                    'category': service_info['category'],
                    'risk_level': service_info['risk_level'],
                    'detected_from': 'known_services_db',
                    'alternatives_eu': service_info.get('alternatives_eu', []),
                    'notes': service_info.get('notes', '')
                }

    # If not a known service, return basic info
    return {
        'name': f'Unknown Service ({domain})',
        'domain': domain,
        'jurisdiction': 'Unknown',
        'category': 'Other',
        'risk_level': 'Medium',
        'detected_from': 'resource_analysis',
        'alternatives_eu': [],
        'notes': 'Unidentified third-party service'
    }


def analyze_embedded_resources(html_content: str, base_url: str) -> dict:
    """
    Extract all external resources from HTML to detect third-party services.
    This detects services by analyzing what resources the page actually loads.
    """
    from urllib.parse import urljoin, urlparse
    from collections import defaultdict

    logger.info("🔍 Analyzing embedded resources...")

    resources = defaultdict(list)

    # 1. External Scripts (JavaScript) - often include analytics, chat widgets, payment processors
    script_pattern = r'<script[^>]*src=["\']([^"\']+)["\']'
    scripts = re.findall(script_pattern, html_content, re.IGNORECASE)

    for script in scripts:
        full_url = urljoin(base_url, script)
        domain = urlparse(full_url).netloc

        # Only track external domains (not the company's own domain)
        if domain and domain not in urlparse(base_url).netloc:
            service = identify_service_from_domain(domain)
            resources['external_scripts'].append({
                'url': full_url,
                'domain': domain,
                'detected_service': service
            })

    # 2. External Stylesheets and Fonts
    css_pattern = r'<link[^>]*href=["\']([^"\']+)["\']'
    links = re.findall(css_pattern, html_content, re.IGNORECASE)

    for link in links:
        full_url = urljoin(base_url, link)
        domain = urlparse(full_url).netloc

        if domain and domain not in urlparse(base_url).netloc:
            if 'font' in link.lower() or 'fonts' in domain:
                service = identify_service_from_domain(domain)
                resources['external_fonts'].append({
                    'url': full_url,
                    'domain': domain,
                    'detected_service': service
                })
            elif '.css' in link:
                resources['external_stylesheets'].append({
                    'url': full_url,
                    'domain': domain
                })

    # 3. Iframes (often chat widgets, payment forms, embedded content)
    iframe_pattern = r'<iframe[^>]*src=["\']([^"\']+)["\']'
    iframes = re.findall(iframe_pattern, html_content, re.IGNORECASE)

    for iframe in iframes:
        full_url = urljoin(base_url, iframe)
        domain = urlparse(full_url).netloc

        if domain and domain not in urlparse(base_url).netloc:
            service = identify_service_from_domain(domain)
            resources['iframes'].append({
                'url': full_url,
                'domain': domain,
                'detected_service': service,
                'note': f'Likely {service["category"]} widget' if service else 'Embedded widget'
            })

    # 4. External Images (can reveal analytics trackers, pixels)
    img_pattern = r'<img[^>]*src=["\']([^"\']+)["\']'
    images = re.findall(img_pattern, html_content, re.IGNORECASE)

    # Track unique image domains (often tracking pixels)
    image_domains = set()
    for img in images:
        full_url = urljoin(base_url, img)
        domain = urlparse(full_url).netloc

        if domain and domain not in urlparse(base_url).netloc:
            image_domains.add(domain)

    for domain in image_domains:
        service = identify_service_from_domain(domain)
        if service and service.get('category') in ['Analytics', 'Tag Management', 'Social/Advertising']:
            # Likely tracking pixel
            resources['tracking_pixels'].append({
                'domain': domain,
                'detected_service': service,
                'note': 'Likely tracking pixel'
            })

    # 5. Detect inline API calls (fetch, axios, jQuery AJAX)
    api_patterns = [
        (r'fetch\(["\']([^"\']+)["\']', 'fetch'),
        (r'axios\.(get|post|put|delete)\(["\']([^"\']+)["\']', 'axios'),
        (r'\$\.ajax\([^)]*url:\s*["\']([^"\']+)["\']', 'jQuery'),
    ]

    for pattern, method in api_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            url = match if isinstance(match, str) else match[-1]
            if url.startswith('http'):
                domain = urlparse(url).netloc
                service = identify_service_from_domain(domain)
                resources['api_calls'].append({
                    'url': url,
                    'domain': domain,
                    'method': method,
                    'detected_service': service
                })

    # Summarize findings
    all_domains = set()
    detected_services = []

    for category, items in resources.items():
        for item in items:
            domain = item.get('domain')
            if domain:
                all_domains.add(domain)

                # Collect detected services (avoid duplicates)
                service = item.get('detected_service')
                if service:
                    # Check if we already have this service
                    if not any(s.get('domain') == service.get('domain') for s in detected_services):
                        detected_services.append(service)

    logger.info(f"📊 Resource Analysis Complete:")
    logger.info(f"   External Scripts: {len(resources['external_scripts'])}")
    logger.info(f"   External Fonts: {len(resources['external_fonts'])}")
    logger.info(f"   Iframes (widgets): {len(resources['iframes'])}")
    logger.info(f"   Tracking Pixels: {len(resources.get('tracking_pixels', []))}")
    logger.info(f"   Unique External Domains: {len(all_domains)}")
    logger.info(f"   Detected Services: {len(detected_services)}")

    return {
        'resources_by_type': dict(resources),
        'unique_domains': list(all_domains),
        'detected_services': detected_services,
        'total_external_resources': sum(len(items) for items in resources.values())
    }


def find_privacy_policy_url(base_url: str) -> str:
    """
    Try to find privacy policy URL by checking common paths.
    """
    from urllib.parse import urljoin

    common_paths = [
        "/privacy",
        "/privacy-policy",
        "/legal/privacy",
        "/privacy.html",
        "/en/privacy",
        "/legal/privacy-policy",
        "/privacypolicy",
    ]

    for path in common_paths:
        try:
            url = urljoin(base_url, path)
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                logger.info(f"✅ Found privacy policy: {url}")
                return url
        except:
            continue

    logger.warning(f"⚠️ Could not find privacy policy for {base_url}")
    return None


def extract_data_transfer_info(privacy_text: str) -> dict:
    """
    Extract data transfer information from privacy policy using Gemini.
    """
    if not model or not privacy_text or len(privacy_text.strip()) < 100:
        return {}

    prompt = f"""Analyze this privacy policy for data sovereignty information:

{privacy_text[:10000]}

Extract:
1. Countries/regions where data is transferred (list ALL mentions)
2. Legal mechanisms used (Standard Contractual Clauses, Binding Corporate Rules, etc.)
3. Any mention of US data transfers or FISA/government access
4. Data retention periods
5. International transfer safeguards
6. Any adequacy decisions mentioned

Return ONLY JSON:
{{
  "transfer_countries": ["...", "..."],
  "legal_mechanisms": ["...", "..."],
  "us_transfers": true/false,
  "government_access_mentioned": true/false,
  "retention_period": "...",
  "safeguards": ["...", "..."]
}}"""

    try:
        response = model.generate_content(prompt)
        if not hasattr(response, 'text') or response.text is None:
            return {}

        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        logger.warning(f"⚠️ Privacy policy analysis failed: {e}")

    return {}


def get_category_weight(purpose: str) -> float:
    """
    Return weight multiplier based on vendor category.
    Higher weights = more critical services.
    """
    if not purpose:
        return 1.0

    purpose_upper = purpose.upper()

    for category, weight in CATEGORY_WEIGHTS.items():
        if category.upper() in purpose_upper:
            return weight

    return 1.0  # Default weight


def scrape_multiple_pages(base_url: str) -> dict[str, str]:
    """Scrape multiple pages from a website to get comprehensive information."""
    from urllib.parse import urljoin, urlparse
    
    logger.info(f"🌐 Starting multi-page scrape for: {base_url}")
    
    parsed = urlparse(base_url)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"
    
    # Common pages to check
    pages_to_check = [
        "",  # Homepage
        "/about",
        "/company",
        "/legal/subprocessors",
        "/legal/sub-processors",
        "/privacy",
        "/privacy-policy",
        "/security",
        "/compliance",
        "/careers",
        "/jobs",
    ]
    
    scraped_pages = {}
    all_infrastructure_hints = []
    all_detected_services = []

    for page_path in pages_to_check:
        try:
            full_url = urljoin(base_domain, page_path)
            logger.info(f"🔍 Attempting to scrape: {full_url}")
            text, hints = scrape_url(full_url)
            if text and len(text.strip()) > 100:  # Only save if we got meaningful content
                scraped_pages[page_path or "homepage"] = text
                if hints.get("cloud_provider") != "Unknown" or hints.get("hosting_platform") != "Unknown":
                    all_infrastructure_hints.append(hints)

                # NEW: Analyze resources on this page
                try:
                    resource_analysis = analyze_embedded_resources(text, full_url)

                    # Collect all detected services (avoid duplicates)
                    for service in resource_analysis['detected_services']:
                        # Check if we already have this service (by domain)
                        if not any(s.get('domain') == service.get('domain') for s in all_detected_services):
                            all_detected_services.append(service)
                            logger.info(f"   🎯 Detected: {service['name']} ({service['category']}) - {service['jurisdiction']}")
                except Exception as e:
                    logger.warning(f"⚠️ Resource analysis failed for {page_path}: {e}")

                logger.info(f"✅ Successfully scraped {page_path or 'homepage'}: {len(text)} chars")
            else:
                logger.debug(f"⚠️ Skipping {page_path}: insufficient content")
        except Exception as e:
            logger.debug(f"⚠️ Could not scrape {page_path}: {str(e)[:100]}")
            continue
    
    # Combine infrastructure hints (take first non-Unknown value)
    detected_infrastructure = {
        "cloud_provider": "Unknown",
        "hosting_platform": "Unknown",
        "cdn_providers": []
    }
    for hints in all_infrastructure_hints:
        if hints.get("cloud_provider") != "Unknown" and detected_infrastructure["cloud_provider"] == "Unknown":
            detected_infrastructure["cloud_provider"] = hints["cloud_provider"]
        if hints.get("hosting_platform") != "Unknown" and detected_infrastructure["hosting_platform"] == "Unknown":
            detected_infrastructure["hosting_platform"] = hints["hosting_platform"]
        detected_infrastructure["cdn_providers"].extend(hints.get("cdn_providers", []))
    
    # Add infrastructure hints to combined text for AI analysis
    infrastructure_note = ""
    if detected_infrastructure["cloud_provider"] != "Unknown":
        infrastructure_note += f"\n\n[INFRASTRUCTURE DETECTED FROM HEADERS]\nCloud Provider: {detected_infrastructure['cloud_provider']}\n"
    if detected_infrastructure["hosting_platform"] != "Unknown":
        infrastructure_note += f"Hosting Platform: {detected_infrastructure['hosting_platform']}\n"
    if detected_infrastructure["cdn_providers"]:
        infrastructure_note += f"CDN Providers: {', '.join(detected_infrastructure['cdn_providers'])}\n"
    
    # Combine all text
    combined_text = "\n\n--- PAGE BREAK ---\n\n".join([
        f"=== {page_name.upper()} ===\n{content[:5000]}"  # Limit each page to 5000 chars
        for page_name, content in scraped_pages.items()
    ])
    
    if infrastructure_note:
        combined_text = infrastructure_note + "\n\n" + combined_text
    
    # Total limit of 20,000 characters
    if len(combined_text) > 20000:
        combined_text = combined_text[:20000]
    
    logger.info(f"📚 Scraped {len(scraped_pages)} pages, total text: {len(combined_text)} characters")
    if detected_infrastructure["cloud_provider"] != "Unknown" or detected_infrastructure["hosting_platform"] != "Unknown":
        logger.info(f"🔍 Infrastructure detected: {detected_infrastructure}")
    logger.info(f"🎯 Total detected services from resources: {len(all_detected_services)}")

    return {
        "combined": combined_text,
        "pages": scraped_pages,
        "infrastructure_hints": detected_infrastructure,
        "detected_services": all_detected_services
    }


def detect_infrastructure_from_headers(url: str, response: requests.Response) -> dict:
    """Detect infrastructure hints from HTTP headers and DNS."""
    infrastructure_hints = {
        "cloud_provider": "Unknown",
        "hosting_platform": "Unknown",
        "server_locations": [],
        "cdn_providers": []
    }
    
    # Check HTTP headers for infrastructure hints
    headers_lower = {k.lower(): v.lower() for k, v in response.headers.items()}
    
    # Server header
    server = headers_lower.get('server', '')
    x_powered_by = headers_lower.get('x-powered-by', '')
    cf_ray = headers_lower.get('cf-ray', '')  # Cloudflare
    fly_request_id = headers_lower.get('fly-request-id', '')  # Fly.io
    
    # Detect hosting platforms
    if 'fly.io' in server or 'fly.io' in x_powered_by or fly_request_id:
        infrastructure_hints["hosting_platform"] = "Fly.io"
        logger.info("🔍 Detected Fly.io from headers")
    
    if 'cloudflare' in server or 'cloudflare' in x_powered_by or cf_ray:
        infrastructure_hints["cdn_providers"].append("Cloudflare")
        logger.info("🔍 Detected Cloudflare CDN from headers")
    
    # Detect cloud providers from headers
    if 'google' in server or 'gce' in server or 'gfe' in server:
        infrastructure_hints["cloud_provider"] = "Google Cloud Platform (GCP)"
        logger.info("🔍 Detected Google Cloud from headers")
    
    if 'amazon' in server or 'aws' in server or 'ec2' in server:
        infrastructure_hints["cloud_provider"] = "Amazon Web Services (AWS)"
        logger.info("🔍 Detected AWS from headers")
    
    if 'azure' in server or 'microsoft' in server:
        infrastructure_hints["cloud_provider"] = "Microsoft Azure"
        logger.info("🔍 Detected Azure from headers")
    
    # Try DNS/IP geolocation (basic)
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '')
        ip = socket.gethostbyname(domain)
        logger.info(f"🌐 Resolved {domain} to IP: {ip}")
        # Note: Full geolocation would require a service like ipapi.co or similar
        # For now, we'll rely on the AI to detect from content
    except Exception as e:
        logger.debug(f"⚠️ Could not resolve DNS: {e}")
    
    return infrastructure_hints


def scrape_url(url: str) -> tuple[str, dict]:
    """Scrape text content from a URL and return text + infrastructure hints."""
    logger.info(f"🔍 Starting scrape for URL: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    infrastructure_hints = {}
    
    try:
        logger.info(f"📡 Making HTTP GET request to: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"✅ Received response: Status {response.status_code}, Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        
        # Detect infrastructure from headers
        infrastructure_hints = detect_infrastructure_from_headers(url, response)
        
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error(f"⏱️ Request timeout for URL: {url}")
        raise HTTPException(status_code=400, detail=f"Request timeout: The page took too long to respond")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"🔌 Connection error for URL: {url} - {str(e)}")
        raise HTTPException(status_code=400, detail=f"Connection error: Could not reach {url}. Check if the URL is correct.")
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP error for URL: {url} - Status {response.status_code}")
        if response.status_code == 404:
            raise HTTPException(
                status_code=400, 
                detail=f"The page at {url} returned 404 Not Found. The page may not exist, require authentication, or block automated access. Try a different URL or check if the page is publicly accessible."
            )
        elif response.status_code == 403:
            raise HTTPException(
                status_code=400,
                detail=f"The page at {url} returned 403 Forbidden. The server is blocking automated access. This page may require authentication or have anti-scraping protection."
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"HTTP {response.status_code}: Could not access page. The server returned an error. URL: {url}"
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request error for URL: {url} - {str(e)}")
        raise HTTPException(status_code=400, detail=f"Could not access page: {str(e)}")
    
    logger.info(f"📄 Parsing HTML content (size: {len(response.content)} bytes)")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove script and style elements
    scripts_removed = len(soup.find_all(['script', 'style']))
    for script in soup(["script", "style"]):
        script.decompose()
    logger.info(f"🧹 Removed {scripts_removed} script/style elements")
    
    # Get text and clean it
    text = soup.get_text()
    original_length = len(text)
    logger.info(f"📝 Extracted text: {original_length} characters")
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    cleaned_length = len(text)
    logger.info(f"✨ Cleaned text: {cleaned_length} characters (removed {original_length - cleaned_length} chars)")
    
    # Limit to 20,000 characters
    if len(text) > 20000:
        logger.warning(f"⚠️ Text truncated from {len(text)} to 20000 characters")
        text = text[:20000]
    
    logger.info(f"✅ Scraping complete. Final text length: {len(text)} characters")
    logger.info(f"📋 Text preview (first 200 chars): {text[:200]}...")
    
    return text, infrastructure_hints


def _scrape_multiple_pages_safe(base_url: str):
    """Wrapper for scrape_multiple_pages that handles exceptions properly in thread pool.
    Returns tuple: (success: bool, result: dict | None, error: dict | None)
    """
    logger.debug(f"🔧 _scrape_multiple_pages_safe called with url: {base_url}")
    try:
        logger.debug(f"🔄 Calling scrape_multiple_pages({base_url})...")
        result = scrape_multiple_pages(base_url)
        total_chars = len(result.get("combined", ""))
        logger.debug(f"✅ scrape_multiple_pages succeeded, returning {total_chars} chars from {len(result.get('pages', {}))} pages")
        return (True, result, None)
    except HTTPException as e:
        logger.error(f"❌ HTTPException in _scrape_multiple_pages_safe: {e.status_code} - {e.detail}")
        return (False, None, {"status_code": e.status_code, "detail": e.detail})
    except Exception as e:
        logger.error(f"❌ Unexpected error in _scrape_multiple_pages_safe: {type(e).__name__}: {str(e)}", exc_info=True)
        return (False, None, {"status_code": 500, "detail": f"Scraping error: {type(e).__name__}: {str(e)}"})


def _search_company_info_safe(url: str, text: str):
    """Wrapper for search_company_info_with_gemini that handles exceptions properly in thread pool."""
    logger.debug(f"🔧 _search_company_info_safe called")
    try:
        result = search_company_info_with_gemini(url, text)
        return result
    except Exception as e:
        logger.warning(f"⚠️ Search failed: {type(e).__name__}: {str(e)}")
        return {}


def _analyze_with_gemini_safe(text: str):
    """Wrapper for analyze_with_gemini that handles exceptions properly in thread pool.
    Returns tuple: (success: bool, result: dict | None, error: dict | None)
    """
    logger.debug(f"🔧 _analyze_with_gemini_safe called with text length: {len(text)}")
    try:
        logger.debug(f"🔄 Calling analyze_with_gemini...")
        result = analyze_with_gemini(text)
        logger.debug(f"✅ analyze_with_gemini succeeded, returning {len(result.get('vendors', []))} vendors")
        return (True, result, None)
    except HTTPException as e:
        logger.error(f"❌ HTTPException in _analyze_with_gemini_safe: {e.status_code} - {e.detail}")
        # HTTPException can't be pickled, so return error info
        return (False, None, {"status_code": e.status_code, "detail": e.detail})
    except Exception as e:
        logger.error(f"❌ Unexpected error in _analyze_with_gemini_safe: {type(e).__name__}: {str(e)}", exc_info=True)
        return (False, None, {"status_code": 500, "detail": f"Gemini analysis error: {type(e).__name__}: {str(e)}"})


def search_company_info_with_gemini(company_url: str, scraped_text: str) -> dict:
    """Use Gemini with Google Search to discover additional company information."""
    if not model:
        logger.error("❌ Gemini API key not configured")
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    logger.info("🔍 Using Gemini with Google Search to discover additional information...")
    
    # Extract company name from URL or text
    from urllib.parse import urlparse
    domain = urlparse(company_url).netloc.replace('www.', '')
    company_name = domain.split('.')[0].title()
    
    search_prompt = f"""You are a Data Sovereignty Research Assistant. I need you to search the web for comprehensive information about this company: {company_url} (domain: {domain})

Based on the website content I've scraped, search for and find:

1. **Company Registration & Legal Info:**
   - Where is the company legally registered/incorporated?
   - What is the legal entity name?
   - Parent company or subsidiary information
   - Recent corporate structure changes

2. **Infrastructure & Technology:**
   - What cloud providers do they use? (AWS, Google Cloud Platform/GCP, Azure, Fly.io, etc.)
   - Hosting platforms (Fly.io, Heroku, Vercel, Netlify, etc.)
   - Data center locations and regions (especially EU vs US)
   - Server infrastructure details
   - CDN and edge network providers
   - Recent infrastructure announcements or migrations
   - Look for mentions like "hosted on Google Cloud", "deployed on Fly.io", "servers in Europe"

3. **Data Processing & Compliance:**
   - GDPR compliance status
   - SOC 2, ISO 27001 certifications and locations
   - Data residency guarantees
   - Data processing agreements (DPA) details
   - Recent data breaches or security incidents
   - Compliance certifications and audit reports

4. **Operations & Employees:**
   - Office locations worldwide
   - Engineering team locations
   - Data team locations
   - Recent office openings/closings
   - Remote work policies

5. **Business Relationships:**
   - Partnerships with cloud providers
   - Vendor relationships
   - Recent acquisitions or mergers
   - Investor information (if relevant to data sovereignty)

6. **Additional Risk Factors:**
   - Recent regulatory actions
   - Privacy policy changes
   - Data sovereignty commitments
   - EU-specific offerings or data centers

IMPORTANT: You have access to Google Search through the google_search_retrieval tool. USE IT to search the web for current information about this company. Do not say you cannot access external websites - you can search the web using the search tool.

Search for recent, accurate information. Focus on data sovereignty, privacy, and infrastructure details. Specifically look for:
- Infrastructure announcements (e.g., "migrated to Google Cloud", "deployed on Fly.io", "using AWS")
- Data center locations and regions
- Compliance certifications
- Recent security incidents

Return ONLY valid JSON with this structure:
{{
  "additional_findings": {{
    "company_info": {{
      "registration_country": "...",
      "legal_entity": "...",
      "parent_company": "...",
      "recent_changes": "..."
    }},
    "infrastructure": {{
      "cloud_provider": "...",
      "data_centers": ["..."],
      "recent_announcements": ["..."],
      "certifications": ["..."]
    }},
    "compliance": {{
      "gdpr_status": "...",
      "certifications": ["..."],
      "data_residency_guarantees": "...",
      "recent_incidents": ["..."]
    }},
    "operations": {{
      "office_locations": ["..."],
      "engineering_locations": ["..."],
      "recent_expansions": ["..."]
    }},
    "risk_factors": ["...", "..."],
    "additional_categories": ["category1", "category2"]
  }},
  "search_summary": "Summary of what was found through web search"
}}"""

    try:
        logger.info(f"🌐 Searching web for: {company_name} ({domain})")
        logger.info("🔍 Using Gemini with Google Search to find additional information...")
        
        # Generate content with search enabled - explicitly request search
        logger.info("🔍 Requesting Google Search for company information...")
        try:
            response = model.generate_content(
                search_prompt,
                # Google Search should be automatically triggered by the model when needed
            )
        except Exception as e:
            logger.warning(f"⚠️ Error generating content with search: {e}")
            # Try without explicit search tool
            response = model.generate_content(search_prompt)
        
        # Check for function calls (Google Search results)
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                # Check if search was performed
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') or hasattr(part, 'grounding_metadata'):
                        logger.info("✅ Google Search was used (grounding metadata found)")
        
        if not hasattr(response, 'text') or response.text is None:
            logger.warning("⚠️ Google Search returned empty response, continuing without search data")
            return {}
        
        response_text = response.text.strip()
        logger.info(f"📥 Received search results ({len(response_text)} characters)")
        logger.info(f"📋 Search response preview: {response_text[:500]}...")
        
        # Check if the response indicates search wasn't used
        if "cannot access external websites" in response_text.lower() or "cannot perform live web searches" in response_text.lower():
            logger.warning("⚠️ Model indicates it cannot access web search. This may be a model limitation.")
            logger.info("💡 Attempting to extract any useful information from the response anyway...")
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                result = json.loads(json_str)
                logger.info("✅ Successfully parsed search results")
                findings = result.get("additional_findings", result)  # Handle both structures
                if isinstance(findings, dict):
                    return findings
                return {}
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Could not parse search results JSON: {e}")
                logger.debug(f"📄 JSON attempt: {json_str[:300]}")
                # Try to extract information from text even if not JSON
                return {"search_summary": response_text[:500]}
        else:
            logger.warning("⚠️ No JSON found in search results, using text summary")
            # Even if not JSON, try to extract useful info
            return {"search_summary": response_text[:1000]}
            
    except Exception as e:
        logger.warning(f"⚠️ Web search failed: {str(e)}. Continuing without search data.")
        logger.debug(f"Search error details:", exc_info=True)
        return {}


def analyze_with_gemini(text: str) -> dict:
    """Analyze text using Gemini API."""
    if not model:
        logger.error("❌ Gemini API key not configured")
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    logger.info("🤖 Initializing Gemini API analysis...")
    logger.info(f"📊 Text length being sent to Gemini: {len(text)} characters")
    
    system_prompt = """You are a Data Sovereignty Auditor for the EU. I will give you text from a SaaS company's website (multiple pages including homepage, about, privacy policy, sub-processors, etc.).

CRITICAL INSTRUCTIONS:
1. Look for EXPLICIT mentions of services, vendors, and infrastructure
2. INFER services from context clues (e.g., "we use industry-leading email delivery" → likely SendGrid/Mailgun)
3. Check for hidden third-party services in:
   - Payment processing (Stripe, PayPal, Mollie, etc.)
   - Analytics (Google Analytics, Mixpanel, Plausible, etc.)
   - Support chat (Intercom, Zendesk, Crisp, Drift, etc.)
   - Email (SendGrid, Mailgun, AWS SES, Brevo, etc.)
   - Monitoring (Datadog, Sentry, New Relic, etc.)
   - AI services (OpenAI, Anthropic, Mistral, Aleph Alpha, etc.)
   - Authentication (Auth0, Okta, Firebase, etc.)
   - CDN/Fonts (Cloudflare, Google Fonts, Bunny CDN, etc.)

WHAT TO EXTRACT:

1. COMPANY INFORMATION:
   - Registration country/jurisdiction (where company is legally registered)
   - Legal entity name
   - Office locations (where they have offices)
   - Employee locations (where teams are based, especially engineering/data teams)
   - Look for: "incorporated in", "registered in", "headquarters in"

2. INFRASTRUCTURE:
   - Cloud provider (AWS, GCP, Azure, Fly.io, etc.)
   - Hosting platform (Fly.io, Heroku, Vercel, Railway, etc.)
   - Data center locations/regions mentioned
   - Server locations
   - CDN providers and their locations
   - Look for: "hosted on", "powered by", "deployed on", "infrastructure"

3. DATA FLOWS:
   - Where customer data is stored (countries/regions)
   - Where data is processed (countries/regions)
   - Data residency guarantees (EU-only, US, Global, etc.)
   - Backup locations
   - Look for: "data is stored in", "servers located in", "EU data centers"

4. SUB-PROCESSORS (third-party vendors):
   For EACH vendor found, extract:
   - Name
   - Purpose/Category (choose from: Payment Processing, AI/ML, Customer Support, Email Service, Analytics, Monitoring, Cloud Infrastructure, Database/Storage, CDN, CDN/Fonts, Authentication, SMS/Communications, Marketing, Tag Management, Session Replay, Error Tracking, Other)
   - Processing Location (Country/Region where the vendor processes data)
   - Sovereignty Risk (Critical, High, Medium, Low)

Risk Assignment Rules (FOLLOW STRICTLY):
- IF Location is USA AND Purpose is (AI/ML OR Payment Processing OR Cloud Infrastructure OR Database/Storage OR Cloud Storage) → Risk is CRITICAL
- IF Location is USA AND Purpose is (Customer Support OR Email Service OR Authentication OR Email Marketing) → Risk is HIGH
- IF Location is USA AND Purpose is (Analytics OR Monitoring OR Error Tracking OR Session Replay OR Other) → Risk is HIGH
- IF Location is USA AND Purpose is (CDN OR CDN/Fonts OR Tag Management) → Risk is MEDIUM to HIGH
- IF Location is "Global" OR "Multiple regions" → Risk is MEDIUM (no EU guarantee)
- IF Location is EEA/EU country → Risk is LOW
- IF Location is Unknown → Risk is MEDIUM

5. COMPLIANCE:
   - GDPR compliance status
   - Certifications (SOC 2, ISO 27001, etc.)
   - Data residency guarantees
   - Recent security incidents or breaches
   - Look for: "GDPR compliant", "ISO 27001", "SOC 2", "data breach"

INFERENCE RULES (Important!):
- If they mention "payment processing" but no vendor → INFER likely Stripe (US, Critical) or PayPal (US, Critical)
- If they mention "analytics" but no vendor → INFER likely Google Analytics (US, High)
- If they mention "live chat" or "customer messaging" → INFER likely Intercom or Zendesk (US, High)
- If they mention "email delivery" or "transactional emails" → INFER likely SendGrid or Mailgun (US, High)
- If they mention "AI features" or "GPT" or "LLM" or "machine learning" → INFER likely OpenAI (US, Critical)
- If they have a chat widget → INFER Intercom/Zendesk/Crisp
- If they mention "monitoring" or "observability" → INFER Datadog/New Relic (US, High)
- If they mention "error tracking" → INFER Sentry (US, High)
- If you see references to fonts from external sources → INFER Google Fonts (US, Medium)

Return ONLY valid JSON matching this EXACT schema:
{
  "vendors": [{"name": "...", "purpose": "...", "location": "...", "risk": "..."}],
  "company_info": {
    "registration_country": "...",
    "legal_entity": "...",
    "office_locations": ["..."],
    "employee_locations": ["..."]
  },
  "infrastructure": {
    "cloud_provider": "...",
    "hosting_platform": "...",
    "data_centers": ["..."],
    "server_locations": ["..."],
    "cdn_providers": ["..."]
  },
  "data_flows": {
    "storage_locations": ["..."],
    "processing_locations": ["..."],
    "data_residency": "EU|US|Global|Unknown"
  },
  "compliance": {
    "gdpr_status": "...",
    "certifications": ["..."],
    "data_residency_guarantees": "...",
    "recent_incidents": ["..."]
  },
  "additional_categories": ["category1", "category2"],
  "summary": "3-5 sentence narrative executive summary. Start with who the company is and where they are registered/headquartered. Then describe their infrastructure choices and key third-party dependencies. Highlight both positive sovereignty signals (EU registration, EU hosting, EU vendors) and concerns (US dependencies, data flows outside EU). End with an overall sovereignty assessment. Be specific - name the country, the providers, the risks."
}"""

    try:
        prompt = f"{system_prompt}\n\nText to analyze:\n{text}"
        logger.info("📤 Sending request to Gemini API...")
        response = model.generate_content(prompt)
        
        # Check if response has text
        if not hasattr(response, 'text') or response.text is None:
            logger.error("❌ Gemini API returned empty response")
            raise HTTPException(status_code=500, detail="Gemini API returned an empty response. Please try again.")
        
        # Extract JSON from response
        response_text = response.text.strip()
        logger.info(f"📥 Received response from Gemini ({len(response_text)} characters)")
        logger.info(f"📋 Gemini response preview: {response_text[:500]}...")
        
        # Try to find JSON in the response (sometimes Gemini wraps it in markdown)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            logger.info("✅ Found JSON in response (extracted from markdown)")
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse JSON: {str(e)}")
                logger.error(f"📄 JSON string that failed: {json_str[:500]}")
                raise HTTPException(status_code=500, detail=f"Failed to parse JSON from Gemini response: {str(e)}")
        else:
            # Fallback: try parsing the whole response
            logger.info("⚠️ No JSON match found, attempting to parse entire response")
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse entire response as JSON: {str(e)}")
                logger.error(f"📄 Full response: {response_text}")
                raise HTTPException(status_code=500, detail=f"Gemini did not return valid JSON. Response: {response_text[:200]}")
        
        # Validate result structure
        if not isinstance(result, dict):
            logger.error(f"❌ Result is not a dictionary: {type(result)}")
            raise HTTPException(status_code=500, detail="Gemini returned invalid response format")
        
        if "vendors" not in result:
            logger.warning("⚠️ Response missing 'vendors' key, adding empty list")
            result["vendors"] = []
        
        if "summary" not in result:
            logger.warning("⚠️ Response missing 'summary' key, adding default")
            result["summary"] = "No summary provided by AI analysis"
        
        # Validate and add defaults for new fields
        if "company_info" not in result:
            logger.warning("⚠️ Response missing 'company_info' key, adding defaults")
            result["company_info"] = {}
        
        if "infrastructure" not in result:
            logger.warning("⚠️ Response missing 'infrastructure' key, adding defaults")
            result["infrastructure"] = {}
        
        if "data_flows" not in result:
            logger.warning("⚠️ Response missing 'data_flows' key, adding defaults")
            result["data_flows"] = {}
        
        if "compliance" not in result:
            logger.warning("⚠️ Response missing 'compliance' key, adding defaults")
            result["compliance"] = {}
        
        if "additional_categories" not in result:
            result["additional_categories"] = []
        
        logger.info(f"✅ Successfully parsed Gemini response:")
        logger.info(f"   Vendors: {len(result.get('vendors', []))}")
        logger.info(f"   Company info: {bool(result.get('company_info'))}")
        logger.info(f"   Infrastructure: {bool(result.get('infrastructure'))}")
        logger.info(f"   Data flows: {bool(result.get('data_flows'))}")
        logger.info(f"   Compliance: {bool(result.get('compliance'))}")
        logger.info(f"   Additional categories: {len(result.get('additional_categories', []))}")
        logger.info(f"📝 Summary: {result.get('summary', 'N/A')[:100]}...")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in Gemini analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error analyzing with Gemini: {str(e)}")


def calculate_score(vendors: list[dict], company_info: dict = None, infrastructure: dict = None, data_flows: dict = None, compliance: dict = None) -> tuple[int, str, list[str], list[str]]:
    """Calculate sovereignty score based on vendors, company info, infrastructure, data flows, and compliance.

    Returns: (score, risk_level, risk_factors, positive_factors)
    """
    logger.info(f"🧮 Calculating sovereignty score for {len(vendors)} vendors")
    score = 100
    deductions = []
    risk_factors = []
    positive_factors = []

    # Track if we have complete information (penalize unknowns lightly)
    has_complete_info = True

    # EU country list for matching
    EU_COUNTRIES = ["GERMANY", "FRANCE", "IRELAND", "NETHERLANDS", "ITALY", "SPAIN",
                    "BELGIUM", "AUSTRIA", "SWEDEN", "DENMARK", "FINLAND", "POLAND",
                    "PORTUGAL", "CZECH", "ROMANIA", "BULGARIA", "CROATIA", "SLOVENIA",
                    "SLOVAKIA", "ESTONIA", "LATVIA", "LITHUANIA", "LUXEMBOURG", "MALTA",
                    "CYPRUS", "GREECE", "HUNGARY"]

    def _is_eu(text: str) -> bool:
        t = text.upper()
        return "EU" in t or "EEA" in t or any(c in t for c in EU_COUNTRIES)

    def _is_us(text: str) -> bool:
        t = text.upper().strip()
        if "USA" in t or "UNITED STATES" in t:
            return True
        # Match "US" as standalone word (e.g., "US (Virginia)") but not inside words
        return bool(re.search(r'\bUS\b', t))

    # 1. Company Registration & Jurisdiction
    if company_info:
        reg_country = str(company_info.get("registration_country", "") or "").upper()
        if not reg_country or reg_country == "UNKNOWN":
            score -= 5
            deductions.append("-5: Company registration country unknown")
            risk_factors.append("Company registration country not disclosed")
            has_complete_info = False
        elif _is_us(reg_country):
            score -= 25
            deductions.append("-25: Company registered in US (high sovereignty risk)")
            risk_factors.append("Company is US-registered entity - subject to US jurisdiction")
        elif _is_eu(reg_country):
            score += 8  # Meaningful bonus for EU registration
            positive_factors.append(f"Company registered in EU ({reg_country.title()})")
            logger.info("+8: Company registered in EU")
        else:
            # Other non-EU countries
            score -= 5
            deductions.append("-5: Company registered outside EU")
            risk_factors.append(f"Company registered in {reg_country} (non-EU)")
    else:
        score -= 5
        deductions.append("-5: No company registration information available")
        has_complete_info = False
    
    # 2. Infrastructure & Cloud
    EU_CLOUD_PROVIDERS = ["HETZNER", "OVH", "SCALEWAY", "IONOS", "LEASEWEB",
                          "EXOSCALE", "UPCLOUD", "FUGA", "CITY CLOUD", "OPEN TELEKOM"]
    EU_HOSTING_PLATFORMS = ["HETZNER", "OVH", "SCALEWAY", "IONOS"]

    if infrastructure:
        cloud_provider = str(infrastructure.get("cloud_provider", "") or "").upper()
        hosting_platform = str(infrastructure.get("hosting_platform", "") or "").upper()
        data_centers = infrastructure.get("data_centers", [])
        server_locations = infrastructure.get("server_locations", [])
        cdn_providers = infrastructure.get("cdn_providers", [])

        # Penalize unknown infrastructure (light penalty)
        if cloud_provider == "UNKNOWN" or not cloud_provider:
            score -= 3
            deductions.append("-3: Cloud provider unknown")
            risk_factors.append("Cloud provider not disclosed")
            has_complete_info = False

        # Check for EU cloud providers (bonus)
        if any(eu_cp in cloud_provider for eu_cp in EU_CLOUD_PROVIDERS):
            score += 8
            positive_factors.append(f"EU-based cloud provider: {cloud_provider.title()}")
            logger.info(f"+8: EU cloud provider: {cloud_provider}")

        # Check hosting platform (Fly.io, etc.)
        if hosting_platform and hosting_platform != "UNKNOWN":
            # EU hosting platforms get a bonus
            if any(eu_hp in hosting_platform for eu_hp in EU_HOSTING_PLATFORMS):
                score += 5
                positive_factors.append(f"EU-based hosting platform: {hosting_platform.title()}")
                logger.info(f"+5: EU hosting platform: {hosting_platform}")

            # Fly.io is a US company - penalize, but less if EU regions
            if "FLY.IO" in hosting_platform or "FLYIO" in hosting_platform:
                all_locations = " ".join(str(l) for l in data_centers + server_locations if l).upper()
                if _is_eu(all_locations):
                    score -= 6
                    deductions.append("-6: Using Fly.io (US company) with EU server regions")
                    risk_factors.append(f"Hosting platform: {hosting_platform} (US company) - subject to US jurisdiction, but using EU regions")
                else:
                    score -= 15
                    deductions.append("-15: Using Fly.io (US company) without EU region specified")
                    risk_factors.append(f"Hosting platform: {hosting_platform} (US company), EU region not specified")

            # Check for other US hosting platforms
            if any(us_host in hosting_platform for us_host in ["HEROKU", "VERCEL", "NETLIFY", "RAILWAY"]):
                score -= 8
                deductions.append(f"-8: Using US hosting platform: {hosting_platform}")
                risk_factors.append(f"US hosting platform: {hosting_platform}")

        # Check for US cloud providers
        if any(us_provider in cloud_provider for us_provider in ["AWS", "AMAZON", "GOOGLE CLOUD", "GCP", "AZURE", "MICROSOFT"]):
            all_locations = " ".join(str(l) for l in data_centers + server_locations if l).upper()
            if _is_eu(all_locations):
                score -= 8
                deductions.append("-8: US cloud provider with EU regions (still subject to US jurisdiction)")
                risk_factors.append(f"Infrastructure uses US cloud provider: {cloud_provider} (subject to US jurisdiction even with EU regions)")
            else:
                score -= 20
                deductions.append("-20: Using US cloud provider without EU regions specified")
                risk_factors.append(f"Infrastructure uses US cloud provider: {cloud_provider}, no EU regions mentioned")

        # Check data center / server locations
        eu_dc_count = 0
        for dc in data_centers + server_locations:
            if dc:
                dc_str = str(dc)
                dc_upper = dc_str.upper()
                if _is_us(dc_upper):
                    score -= 10
                    deductions.append(f"-10: Data center in US: {dc}")
                    risk_factors.append(f"Data center located in US: {dc}")
                elif _is_eu(dc_upper):
                    eu_dc_count += 1

        # Bonus for EU data centers (up to +9)
        if eu_dc_count > 0:
            eu_dc_bonus = min(9, eu_dc_count * 3)
            score += eu_dc_bonus
            positive_factors.append(f"Data centers in EU ({eu_dc_count} location{'s' if eu_dc_count > 1 else ''})")
            logger.info(f"+{eu_dc_bonus}: EU data centers ({eu_dc_count})")

        # Check CDN providers
        for cdn in cdn_providers:
            if cdn:
                cdn_upper = str(cdn).upper()
                if "CLOUDFLARE" in cdn_upper:
                    score -= 3
                    deductions.append(f"-3: Cloudflare CDN (US company, but EU PoPs)")
                    risk_factors.append(f"CDN provider: {cdn} (US company with EU presence)")
                elif _is_us(cdn_upper):
                    score -= 5
                    deductions.append(f"-5: US-based CDN: {cdn}")
                    risk_factors.append(f"US-based CDN provider: {cdn}")
    else:
        score -= 5
        deductions.append("-5: No infrastructure information available")
        has_complete_info = False
    
    # 3. Data Flows & Storage
    if data_flows:
        storage_locs = data_flows.get("storage_locations", [])
        processing_locs = data_flows.get("processing_locations", [])
        data_residency = str(data_flows.get("data_residency", "") or "").upper()

        # Penalize unknown data residency (light)
        if not data_residency or data_residency == "UNKNOWN":
            score -= 5
            deductions.append("-5: Data residency unknown")
            risk_factors.append("Data residency not disclosed")
            has_complete_info = False

        # Check storage locations
        eu_storage_count = 0
        for loc in storage_locs:
            if loc:
                loc_upper = str(loc).upper()
                if _is_us(loc_upper):
                    score -= 12
                    deductions.append(f"-12: Data stored in US: {loc}")
                    risk_factors.append(f"Customer data stored in US: {loc}")
                elif _is_eu(loc_upper):
                    eu_storage_count += 1

        # Bonus for EU storage (up to +10)
        if eu_storage_count > 0:
            eu_storage_bonus = min(10, eu_storage_count * 5)
            score += eu_storage_bonus
            positive_factors.append(f"Data stored in EU ({eu_storage_count} location{'s' if eu_storage_count > 1 else ''})")
            logger.info(f"+{eu_storage_bonus}: EU storage locations ({eu_storage_count})")

        # Check processing locations
        eu_processing_count = 0
        for loc in processing_locs:
            if loc:
                loc_upper = str(loc).upper()
                if _is_us(loc_upper):
                    score -= 8
                    deductions.append(f"-8: Data processed in US: {loc}")
                    risk_factors.append(f"Data processing occurs in US: {loc}")
                elif _is_eu(loc_upper):
                    eu_processing_count += 1

        # Bonus for EU processing (up to +6)
        if eu_processing_count > 0:
            eu_proc_bonus = min(6, eu_processing_count * 3)
            score += eu_proc_bonus
            positive_factors.append(f"Data processed in EU ({eu_processing_count} location{'s' if eu_processing_count > 1 else ''})")

        # Data residency evaluation
        data_residency = (data_flows.get("data_residency") or "").upper()
        if data_residency == "US":
            score -= 25
            deductions.append("-25: Data residency explicitly in US")
            risk_factors.append("Data residency explicitly in US - high sovereignty risk")
        elif data_residency == "GLOBAL":
            score -= 10
            deductions.append("-10: Global data residency (no EU guarantee)")
            risk_factors.append("Data residency is global, no EU-only guarantee")
        elif data_residency == "EU":
            score += 10
            positive_factors.append("EU-only data residency guarantee")
            logger.info("+10: EU-only data residency")

        # No locations disclosed at all
        if not storage_locs and not processing_locs and (not data_residency or data_residency == "UNKNOWN"):
            score -= 3
            deductions.append("-3: No data storage/processing locations disclosed")
            risk_factors.append("Data storage and processing locations not disclosed")
    else:
        score -= 8
        deductions.append("-8: No data flow information available")
        has_complete_info = False
    
    # 4. Employee & Office Locations
    if company_info:
        emp_locations = company_info.get("employee_locations", [])
        office_locations = company_info.get("office_locations", [])
        all_emp_locs = " ".join([str(loc) for loc in (emp_locations + office_locations) if loc]).upper()

        # Count EU and US locations
        eu_office_count = sum(1 for loc in office_locations if loc and _is_eu(str(loc)))
        eu_emp_count = sum(1 for loc in emp_locations if loc and _is_eu(str(loc)))
        us_office_count = sum(1 for loc in office_locations if loc and _is_us(str(loc)))
        us_emp_count = sum(1 for loc in emp_locations if loc and _is_us(str(loc)))

        # Bonus for EU offices/employees (up to +6)
        total_eu_locs = eu_office_count + eu_emp_count
        if total_eu_locs > 0:
            eu_loc_bonus = min(6, total_eu_locs * 2)
            score += eu_loc_bonus
            positive_factors.append(f"EU office/employee presence ({total_eu_locs} location{'s' if total_eu_locs > 1 else ''})")
            logger.info(f"+{eu_loc_bonus}: EU employee/office locations ({total_eu_locs})")

        # US employees/offices = data access risk
        total_us_locs = us_office_count + us_emp_count
        if total_us_locs > 0:
            penalty = min(12, 6 + (total_us_locs * 2))
            score -= penalty
            deductions.append(f"-{penalty}: Employees/offices in US ({total_us_locs} location(s))")
            risk_factors.append(f"Company has {total_us_locs} US office/employee location(s) - US-based employees can access EU data")

        # No location info at all (light penalty)
        if not emp_locations and not office_locations:
            score -= 2
            deductions.append("-2: Employee/office locations not disclosed")
            risk_factors.append("Employee and office locations not disclosed")
            has_complete_info = False
    
    # 5. Sub-processors / Vendors
    us_vendor_count = 0
    eu_vendor_count = 0
    total_vendor_penalty = 0
    MAX_VENDOR_PENALTY = 45  # Cap total vendor deductions

    for vendor in vendors:
        location = str(vendor.get("location", "") or "").upper()
        purpose = str(vendor.get("purpose", "") or "").upper()
        vendor_name = str(vendor.get("name", "Unknown") or "Unknown")

        if _is_us(location):
            us_vendor_count += 1
            category_weight = get_category_weight(purpose)
            # Single weighted penalty per US vendor (no double-counting)
            penalty = int(8 * category_weight)
            actual_penalty = min(penalty, MAX_VENDOR_PENALTY - total_vendor_penalty)
            if actual_penalty > 0:
                score -= actual_penalty
                total_vendor_penalty += actual_penalty
                deductions.append(f"-{actual_penalty}: {vendor_name} is US-based ({purpose})")
            risk_factors.append(f"US-based sub-processor: {vendor_name} ({purpose})")

            # Extra penalty only for high-risk AI vendors (OpenAI, Anthropic)
            if vendor_name and any(ai_vendor in str(vendor_name).upper() for ai_vendor in ["OPENAI", "ANTHROPIC"]):
                ai_penalty = min(12, MAX_VENDOR_PENALTY - total_vendor_penalty)
                if ai_penalty > 0:
                    score -= ai_penalty
                    total_vendor_penalty += ai_penalty
                    deductions.append(f"-{ai_penalty}: {vendor_name} is high-risk AI vendor (US jurisdiction)")
                risk_factors.append(f"High-risk AI vendor: {vendor_name} (critical sovereignty risk)")

        elif _is_eu(location):
            eu_vendor_count += 1

        elif "GLOBAL" in location:
            penalty = min(5, MAX_VENDOR_PENALTY - total_vendor_penalty)
            if penalty > 0:
                score -= penalty
                total_vendor_penalty += penalty
                deductions.append(f"-{penalty}: {vendor_name} has Global location (uncertain jurisdiction)")
            risk_factors.append(f"Global sub-processor (uncertain jurisdiction): {vendor_name}")

        elif not location or location == "UNKNOWN":
            penalty = min(3, MAX_VENDOR_PENALTY - total_vendor_penalty)
            if penalty > 0:
                score -= penalty
                total_vendor_penalty += penalty
                deductions.append(f"-{penalty}: {vendor_name} location unknown")
            risk_factors.append(f"Sub-processor location unknown: {vendor_name}")

    # Bonus for EU-based vendors (up to +10)
    if eu_vendor_count > 0:
        eu_vendor_bonus = min(10, eu_vendor_count * 2)
        score += eu_vendor_bonus
        positive_factors.append(f"{eu_vendor_count} EU-based sub-processor{'s' if eu_vendor_count > 1 else ''}")
        logger.info(f"+{eu_vendor_bonus}: EU vendors ({eu_vendor_count})")

    # Cumulative US vendor warning (informational, light penalty)
    if us_vendor_count > 5:
        extra_penalty = min(5, (us_vendor_count - 5))
        score -= extra_penalty
        deductions.append(f"-{extra_penalty}: High US vendor concentration ({us_vendor_count} total)")
        risk_factors.append(f"High concentration of US sub-processors ({us_vendor_count}) increases cumulative sovereignty risk")
    
    # 6. Compliance & Certifications
    if compliance:
        gdpr_status = str(compliance.get("gdpr_status", "") or "").upper()
        certifications = compliance.get("certifications", []) or []
        recent_incidents = compliance.get("recent_incidents", []) or []
        data_residency_guarantees = str(compliance.get("data_residency_guarantees", "") or "").upper()

        # GDPR compliance status
        if not gdpr_status or gdpr_status == "UNKNOWN":
            score -= 5
            deductions.append("-5: GDPR compliance status unknown")
            risk_factors.append("GDPR compliance status not disclosed")
            has_complete_info = False
        elif "NON-COMPLIANT" in gdpr_status or "NOT COMPLIANT" in gdpr_status:
            score -= 20
            deductions.append("-20: GDPR non-compliant")
            risk_factors.append("GDPR non-compliance - critical risk")
        elif "COMPLIANT" in gdpr_status or "COMPLIANCE" in gdpr_status:
            score += 5
            positive_factors.append("GDPR compliance stated")
            logger.info("+5: GDPR compliance stated")

        # Certifications
        if certifications and len(certifications) > 0:
            cert_bonus = min(5, len(certifications) * 2)
            score += cert_bonus
            positive_factors.append(f"{len(certifications)} compliance certification{'s' if len(certifications) > 1 else ''} ({', '.join(str(c) for c in certifications[:3])})")
            logger.info(f"+{cert_bonus}: Certifications ({len(certifications)})")
        else:
            score -= 3
            deductions.append("-3: No compliance certifications disclosed")
            risk_factors.append("No compliance certifications (SOC 2, ISO 27001, etc.) disclosed")

        # Recent security incidents
        if recent_incidents and len(recent_incidents) > 0:
            incident_penalty = min(15, len(recent_incidents) * 6)
            score -= incident_penalty
            deductions.append(f"-{incident_penalty}: Recent security incidents ({len(recent_incidents)} reported)")
            risk_factors.append(f"Recent security incidents: {len(recent_incidents)} reported")

        # Data residency guarantees
        if data_residency_guarantees and data_residency_guarantees != "UNKNOWN" and "NONE" not in data_residency_guarantees:
            score += 3
            positive_factors.append("Data residency guarantees disclosed")
        elif not data_residency_guarantees or data_residency_guarantees == "UNKNOWN":
            score -= 3
            deductions.append("-3: Data residency guarantees not disclosed")
            risk_factors.append("Data residency guarantees not disclosed")
    else:
        score -= 5
        deductions.append("-5: No compliance information available")
        has_complete_info = False

    # 7. Transparency penalty (light)
    if not has_complete_info:
        score -= 2
        deductions.append("-2: Incomplete information disclosure")
        risk_factors.append("Some information not disclosed (transparency gap)")

    # Ensure score is between 0 and 100
    score = max(0, min(100, score))

    # Risk level thresholds
    if score < 50:
        risk_level = "High"
    elif score < 75:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    logger.info(f"📊 Sovereignty score calculation complete: {score}/100 ({risk_level} risk)")
    logger.info(f"📈 Positive factors: {len(positive_factors)}")
    if deductions:
        logger.info(f"📉 Deductions applied: {', '.join(deductions[:10])}")
    if risk_factors:
        logger.info(f"⚠️ Risk factors identified: {len(risk_factors)} total")

    return score, risk_level, risk_factors, positive_factors


# =============================================================================
# Company Web Research - Sovereignty Investigation
# =============================================================================

SOVEREIGNTY_RESEARCH_QUESTIONS = [
    {
        "id": "registration",
        "question": "Where is {company} legally incorporated or registered? What country and jurisdiction?",
        "category": "Registration",
        "weight": 20,
        "positive_signals": ["EU", "EEA", "Germany", "France", "Ireland", "Netherlands", "Sweden", "Finland", "Denmark", "Austria", "Belgium", "Spain", "Italy", "Portugal", "Poland", "Estonia"],
        "negative_signals": ["United States", "USA", "Delaware", "California", "Cayman Islands", "British Virgin Islands"],
    },
    {
        "id": "founders",
        "question": "Who founded {company}? What are the founders' nationalities and where are they based?",
        "category": "Team Background",
        "weight": 10,
        "positive_signals": ["European", "EU-based", "German", "French", "Irish", "Dutch", "Swedish", "Danish", "Finnish"],
        "negative_signals": ["American", "US-based", "Silicon Valley", "San Francisco", "New York"],
    },
    {
        "id": "funding",
        "question": "What is {company}'s funding history? Who are the major investors and venture capital firms, and where are they headquartered?",
        "category": "Funding Sources",
        "weight": 15,
        "positive_signals": ["European VC", "EU investors", "EIF", "EIB", "Earlybird", "Atomico", "Balderton", "Northzone", "Lakestar"],
        "negative_signals": ["Sequoia", "Andreessen", "a16z", "Y Combinator", "Accel US", "Tiger Global", "Softbank", "US venture"],
    },
    {
        "id": "ownership",
        "question": "Is {company} independent, or is it owned by or subsidiary of a larger corporation? If so, where is the parent company based?",
        "category": "Ownership Structure",
        "weight": 18,
        "positive_signals": ["independent", "EU parent", "European parent", "employee-owned", "founder-led"],
        "negative_signals": ["US parent", "American parent", "acquired by US", "subsidiary of US", "owned by US"],
    },
    {
        "id": "breaches",
        "question": "Has {company} had any significant data breaches, security incidents, or privacy violations in the past 5 years?",
        "category": "Security History",
        "weight": 15,
        "positive_signals": ["no known breaches", "no incidents", "clean record", "no violations"],
        "negative_signals": ["breach", "incident", "leak", "compromised", "fine", "penalty", "violation"],
    },
    {
        "id": "gdpr_fines",
        "question": "Has {company} received any GDPR fines, regulatory actions, or enforcement notices from EU data protection authorities?",
        "category": "Regulatory History",
        "weight": 20,
        "positive_signals": ["no fines", "compliant", "no regulatory action", "no enforcement"],
        "negative_signals": ["fined", "penalty", "enforcement", "DPA action", "regulatory action", "infringement"],
    },
    {
        "id": "data_residency_public",
        "question": "What is {company}'s publicly stated data residency policy? Do they offer EU-only data storage and processing for European customers?",
        "category": "Data Residency Policy",
        "weight": 15,
        "positive_signals": ["EU-only", "European data centers", "EU data residency", "data stays in EU", "EU region available"],
        "negative_signals": ["US data centers", "global storage", "no EU option", "data transferred to US", "US processing"],
    },
    {
        "id": "transparency",
        "question": "Does {company} publish transparency reports about government data requests or law enforcement access? What do they show?",
        "category": "Transparency",
        "weight": 8,
        "positive_signals": ["transparency report", "publishes reports", "discloses requests", "warrant canary"],
        "negative_signals": ["no transparency", "no reports published", "does not disclose"],
    },
    {
        "id": "cloud_act",
        "question": "Is {company} subject to the US CLOUD Act or similar US legislation that could compel disclosure of EU customer data?",
        "category": "Legal Jurisdiction",
        "weight": 18,
        "positive_signals": ["not subject to CLOUD Act", "EU jurisdiction only", "no US legal obligation"],
        "negative_signals": ["subject to CLOUD Act", "US jurisdiction", "compelled disclosure", "US legal obligations", "FISA"],
    },
    {
        "id": "eu_commitment",
        "question": "Has {company} made any recent public commitments, announcements, or investments specifically about EU data sovereignty or data localization?",
        "category": "EU Commitment",
        "weight": 10,
        "positive_signals": ["EU investment", "EU data center launch", "sovereignty commitment", "EU-first", "data localization"],
        "negative_signals": ["no commitment", "US-first", "no EU plans"],
    },
]


def research_company_with_gemini(company_name: str, company_url: str, company_info: dict = None) -> dict:
    """
    Perform web research about a company to assess sovereignty posture.
    Uses Gemini with Google Search grounding to answer sovereignty questions.
    """
    if not model:
        logger.warning("⚠️ Gemini API key not configured, skipping company research")
        return {}

    from urllib.parse import urlparse
    domain = urlparse(company_url).netloc.replace('www.', '')
    if company_name == "Unknown" or not company_name:
        company_name = domain.split('.')[0].title()

    logger.info(f"🔬 Starting sovereignty research for: {company_name} ({domain})")

    # Build a single comprehensive research prompt
    questions_text = ""
    for i, q in enumerate(SOVEREIGNTY_RESEARCH_QUESTIONS, 1):
        question = q["question"].format(company=company_name)
        questions_text += f"\n{i}. [{q['category']}] {question}"

    research_prompt = f"""You are an EU Data Sovereignty Research Analyst. Research the company "{company_name}" (website: {company_url}, domain: {domain}).

USE GOOGLE SEARCH to find real, current information about this company. Search for "{company_name}" along with relevant terms for each question.

Answer ALL of the following questions based on your web research:
{questions_text}

For EACH question, provide:
- A factual answer based on what you found
- Your confidence level: "High" (found on official sources), "Medium" (found on credible third-party sources), "Low" (limited information or inference)
- The sentiment regarding EU data sovereignty: "positive" (good for EU sovereignty), "negative" (risk to EU sovereignty), or "neutral"
- URLs of sources you found (real URLs from search results)

IMPORTANT RULES:
- Be factual and specific. Include names, dates, and locations when available.
- If you cannot find information, say "No information found" with confidence "Low"
- Do NOT make up URLs. Only include real source URLs from search results.
- Focus on facts relevant to EU data sovereignty risk assessment.

Return ONLY valid JSON matching this exact schema:
{{
  "company_name": "{company_name}",
  "research_summary": "2-3 sentence executive summary of sovereignty research findings",
  "questions_answers": [
    {{
      "id": "registration",
      "question": "Where is {company_name} legally incorporated...",
      "answer": "Factual answer here...",
      "confidence": "High|Medium|Low",
      "sentiment": "positive|negative|neutral",
      "source_urls": ["https://real-source-url.com"]
    }}
  ],
  "key_findings": ["Finding 1", "Finding 2", "Finding 3"],
  "sovereignty_flags": ["Warning 1 if any negative findings"]
}}

The questions_answers array MUST have exactly {len(SOVEREIGNTY_RESEARCH_QUESTIONS)} entries, one for each question above, in the same order.
"""

    try:
        logger.info(f"🌐 Sending research prompt to Gemini for {company_name}...")
        response = model.generate_content(research_prompt)

        if not hasattr(response, 'text') or response.text is None:
            logger.warning("⚠️ Gemini returned empty response for company research")
            return {}

        response_text = response.text.strip()
        logger.info(f"📥 Received research response ({len(response_text)} characters)")
        logger.info(f"📋 Research preview: {response_text[:300]}...")

        # Extract JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            logger.warning("⚠️ No JSON found in research response")
            return {"research_summary": response_text[:500]}

        result = json.loads(json_match.group(0))
        logger.info(f"✅ Research parsed: {len(result.get('questions_answers', []))} answers, {len(result.get('key_findings', []))} findings")
        return result

    except json.JSONDecodeError as e:
        logger.warning(f"⚠️ Could not parse research JSON: {e}")
        return {"research_summary": "Research completed but response could not be parsed"}
    except Exception as e:
        logger.warning(f"⚠️ Company research failed: {str(e)}")
        return {}


def _research_company_safe(company_name: str, company_url: str, company_info: dict = None):
    """Thread-safe wrapper for research_company_with_gemini."""
    logger.debug(f"🔧 _research_company_safe called for {company_name}")
    try:
        result = research_company_with_gemini(company_name, company_url, company_info)
        return (True, result, None)
    except Exception as e:
        logger.warning(f"⚠️ Research failed: {type(e).__name__}: {str(e)}")
        return (False, {}, {"detail": str(e)})


def calculate_research_score(research_data: dict) -> tuple[int, list[str]]:
    """
    Calculate a sovereignty research score (0-100) based on research findings.
    Returns (score, sovereignty_flags).
    """
    if not research_data or not research_data.get("questions_answers"):
        return 50, ["Insufficient research data to assess sovereignty posture"]

    score = 50  # Start neutral
    flags = list(research_data.get("sovereignty_flags", []))
    questions_answered = research_data.get("questions_answers", [])

    # Build a lookup from question config
    question_config = {q["id"]: q for q in SOVEREIGNTY_RESEARCH_QUESTIONS}

    for qa in questions_answered:
        qid = qa.get("id", "")
        answer = str(qa.get("answer", "")).upper()
        confidence = str(qa.get("confidence", "Low")).lower()
        sentiment = str(qa.get("sentiment", "neutral")).lower()
        config = question_config.get(qid, {})
        weight = config.get("weight", 10)

        # Skip if no real answer
        if "NO INFORMATION FOUND" in answer or not answer:
            score -= 2  # Small penalty for unknown
            continue

        # Confidence multiplier
        conf_multiplier = {"high": 1.0, "medium": 0.6, "low": 0.3}.get(confidence, 0.3)

        # Check positive signals
        positive_signals = config.get("positive_signals", [])
        positive_found = sum(1 for sig in positive_signals if sig.upper() in answer)

        # Check negative signals
        negative_signals = config.get("negative_signals", [])
        negative_found = sum(1 for sig in negative_signals if sig.upper() in answer)

        # Also use sentiment from LLM
        if sentiment == "positive":
            positive_found = max(positive_found, 1)
        elif sentiment == "negative":
            negative_found = max(negative_found, 1)

        # Calculate points for this question
        if positive_found > negative_found:
            points = int(weight * 0.5 * conf_multiplier)
            score += points
            logger.info(f"   +{points}: {qid} - positive signals ({positive_found} positive, {negative_found} negative, conf={confidence})")
        elif negative_found > positive_found:
            points = int(weight * 0.8 * conf_multiplier)  # Penalties weighted more heavily
            score -= points
            logger.info(f"   -{points}: {qid} - negative signals ({positive_found} positive, {negative_found} negative, conf={confidence})")

            # Add to flags for significant negative findings
            if points >= 5:
                question_text = config.get("question", "").format(company="the company")
                answer_short = qa.get("answer", "")[:150]
                flags.append(f"{config.get('category', 'Unknown')}: {answer_short}")
        else:
            # Mixed or neutral
            if negative_found > 0:
                score -= int(weight * 0.2 * conf_multiplier)

    # Clamp score
    score = max(0, min(100, score))

    logger.info(f"🔬 Research score: {score}/100, flags: {len(flags)}")
    return score, flags


def normalize_url(url: str) -> str:
    """Normalize URL to ensure it has a protocol."""
    if not url or not isinstance(url, str):
        return url
    
    url = url.strip()
    
    # If already has protocol, upgrade http to https
    if url.startswith(('http://', 'https://')):
        if url.startswith('http://'):
            url = url.replace('http://', 'https://', 1)
        return url
    
    # If starts with //, add https:
    if url.startswith('//'):
        return 'https:' + url
    
    # Add https:// if it looks like a domain
    # Basic check: contains a dot or is localhost
    if '.' in url or url.startswith('localhost') or url.replace('.', '').replace(':', '').replace('/', '').isdigit():
        return 'https://' + url
    
    return url


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_url(request: AnalyzeRequest):
    """Analyze a URL for data sovereignty risks."""
    # Force print to ensure we see this even if logging fails
    print("=" * 80, flush=True)
    print("🚀 STARTING /analyze endpoint", flush=True)
    
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info(f"🚀 STARTING /analyze endpoint")
    
    try:
        logger.info(f"📥 Request received: {request}")
        original_url = request.url
        
        # Normalize URL (add https:// if missing)
        normalized_url = normalize_url(original_url)
        if normalized_url != original_url:
            logger.info(f"🔗 URL normalized: '{original_url}' -> '{normalized_url}'")
            request.url = normalized_url
        
        logger.info(f"🔗 URL to analyze: {request.url}")
        logger.info(f"⏰ Start time: {start_time}")
        logger.debug(f"📋 Full request object: {request.dict()}")
        print(f"📥 Request URL: {request.url}", flush=True)
    except Exception as parse_err:
        logger.error(f"❌ Failed to parse request: {parse_err}", exc_info=True)
        print(f"❌ Failed to parse request: {parse_err}", flush=True)
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(parse_err)}")

    # --- CACHE CHECK: return cached result if fresh enough ---
    if request.url.strip().lower() not in ("dummy", "https://dummy", "http://dummy"):
        cached = get_cached_analysis(request.url)
        if cached:
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"📦 Returning cached result for {request.url} ({duration:.3f}s)")
            return cached

    # --- DUMMY MODE: return mock data without any LLM/scraping calls ---
    if request.url.strip().lower() in ("dummy", "https://dummy", "http://dummy"):
        logger.info("🧪 DUMMY MODE: Returning mock response (no LLM calls)")
        dummy_response = AnalyzeResponse(
            score=42,
            risk_level="High",
            summary=(
                "DummyCorp GmbH is an EU-registered SaaS company (Berlin, Germany) that provides project management tools. "
                "Despite EU registration, the company relies heavily on US-based infrastructure and sub-processors. "
                "Primary hosting is on AWS eu-west-1 (Ireland), but critical services including AI features (OpenAI, US), "
                "payment processing (Stripe, US), and customer support (Intercom, US) route data through US jurisdiction. "
                "The company claims GDPR compliance and holds SOC 2 Type II certification, but lacks EU-only data residency guarantees. "
                "A 2024 security incident involving unauthorized access to customer metadata raises additional concerns. "
                "Overall sovereignty risk is HIGH due to extensive US sub-processor dependency and global data residency."
            ),
            vendors=[
                Vendor(name="Amazon Web Services (AWS)", purpose="Cloud Infrastructure", location="United States (eu-west-1 region)", risk="Critical"),
                Vendor(name="OpenAI", purpose="AI/ML", location="United States", risk="Critical"),
                Vendor(name="Stripe", purpose="Payment Processing", location="United States", risk="Critical"),
                Vendor(name="Intercom", purpose="Customer Support", location="United States", risk="High"),
                Vendor(name="SendGrid", purpose="Email Service", location="United States", risk="High"),
                Vendor(name="Datadog", purpose="Monitoring", location="United States", risk="High"),
                Vendor(name="Sentry", purpose="Error Tracking", location="United States", risk="High"),
                Vendor(name="Google Analytics", purpose="Analytics", location="United States", risk="High"),
                Vendor(name="Cloudflare", purpose="CDN", location="United States (global PoPs)", risk="Medium"),
                Vendor(name="Google Fonts", purpose="CDN/Fonts", location="United States", risk="Medium"),
                Vendor(name="Hetzner", purpose="Database/Storage", location="Germany", risk="Low"),
                Vendor(name="Plausible Analytics", purpose="Analytics", location="Estonia (EU)", risk="Low"),
            ],
            company_info=CompanyInfo(
                registration_country="Germany (EU)",
                legal_entity="DummyCorp GmbH",
                office_locations=["Berlin, Germany", "Dublin, Ireland", "San Francisco, USA"],
                employee_locations=["Berlin, Germany", "Remote (EU)", "San Francisco, USA"],
            ),
            infrastructure=InfrastructureInfo(
                cloud_provider="Amazon Web Services (AWS)",
                hosting_platform="Fly.io",
                data_centers=["eu-west-1 (Ireland)", "us-east-1 (Virginia)"],
                server_locations=["Ireland", "United States"],
                cdn_providers=["Cloudflare", "Bunny CDN"],
            ),
            data_flows=DataFlowInfo(
                storage_locations=["EU (Ireland)", "United States (Virginia)"],
                processing_locations=["EU (Ireland)", "United States"],
                data_residency="Global",
            ),
            compliance=ComplianceInfo(
                gdpr_status="GDPR Compliant (self-certified)",
                certifications=["SOC 2 Type II", "ISO 27001", "GDPR Art. 28 DPA"],
                data_residency_guarantees="EU data processing available on Enterprise plan; standard plan uses global infrastructure",
                recent_incidents=["2024-03: Unauthorized access to customer metadata via misconfigured API endpoint (resolved within 48h)"],
            ),
            additional_findings=AdditionalFindings(
                recent_changes=[
                    "2024-Q4: Migrated primary database to Hetzner (Germany) from AWS US",
                    "2025-Q1: Added Plausible Analytics as EU alternative to Google Analytics",
                    "2025-Q2: Announced upcoming EU-only hosting tier",
                ],
                additional_categories=["Project Management", "SaaS", "B2B"],
                search_summary=(
                    "DummyCorp was founded in 2020 in Berlin and has grown to 150+ employees across 3 offices. "
                    "Recent blog posts indicate a strategic shift toward EU data sovereignty, with planned migration "
                    "of remaining US infrastructure to EU regions by Q4 2025. The company raised Series B funding "
                    "from EU-based investors in 2024. Engineering team is primarily EU-based (Berlin, Dublin) with "
                    "a small US presence in San Francisco for sales and partnerships."
                ),
            ),
            company_research=CompanyResearch(
                score=68,
                research_summary=(
                    "DummyCorp GmbH is a German-registered company founded in 2020 by EU-based entrepreneurs. "
                    "The company has raised Series B funding primarily from European VCs, though one US-based investor "
                    "(Accel) participated. While the founding team and majority of employees are EU-based, the company "
                    "maintains a San Francisco office and uses US cloud infrastructure (AWS), creating some sovereignty concerns. "
                    "No major data breaches or GDPR fines have been reported."
                ),
                questions_answers=[
                    CompanyResearchQuestion(
                        question="Where is DummyCorp legally incorporated or registered? What country and jurisdiction?",
                        answer="DummyCorp GmbH is registered in Berlin, Germany as a Gesellschaft mit beschränkter Haftung (GmbH). The company was incorporated in 2020 under German commercial law.",
                        confidence="High",
                        source_urls=["https://www.dummycorp.com/about", "https://www.handelsregister.de"],
                        sentiment="positive",
                    ),
                    CompanyResearchQuestion(
                        question="Who founded DummyCorp? What are the founders' nationalities and where are they based?",
                        answer="Founded by Maria Schmidt (German, based in Berlin) and Lars Eriksson (Swedish, based in Berlin). Both founders have backgrounds in enterprise software and data privacy.",
                        confidence="High",
                        source_urls=["https://www.dummycorp.com/about", "https://www.linkedin.com/company/dummycorp"],
                        sentiment="positive",
                    ),
                    CompanyResearchQuestion(
                        question="What is DummyCorp's funding history? Who are the major investors and where are they headquartered?",
                        answer="Seed round (2020): Earlybird Venture Capital (Berlin). Series A (2022): Northzone (Stockholm) led, with participation from Balderton Capital (London). Series B (2024): Led by Latitude Ventures (Paris), with Accel (US/London) participating. Total raised: ~€45M.",
                        confidence="High",
                        source_urls=["https://www.crunchbase.com/organization/dummycorp", "https://techcrunch.com/dummycorp-series-b"],
                        sentiment="neutral",
                    ),
                    CompanyResearchQuestion(
                        question="Is DummyCorp independent, or is it owned by or subsidiary of a larger corporation?",
                        answer="DummyCorp is an independent company. It is not a subsidiary of any larger corporation. The founders retain significant ownership alongside institutional investors.",
                        confidence="Medium",
                        source_urls=["https://www.crunchbase.com/organization/dummycorp"],
                        sentiment="positive",
                    ),
                    CompanyResearchQuestion(
                        question="Has DummyCorp had any significant data breaches or security incidents in the past 5 years?",
                        answer="One minor incident in March 2024: unauthorized access to customer metadata via a misconfigured API endpoint. The issue was resolved within 48 hours and affected metadata only (no PII exposed). The company disclosed the incident proactively.",
                        confidence="High",
                        source_urls=["https://www.dummycorp.com/security/incidents", "https://status.dummycorp.com"],
                        sentiment="neutral",
                    ),
                    CompanyResearchQuestion(
                        question="Has DummyCorp received any GDPR fines or regulatory actions from EU data protection authorities?",
                        answer="No GDPR fines or regulatory actions have been reported against DummyCorp. The company has not appeared in any DPA enforcement decisions.",
                        confidence="Medium",
                        source_urls=["https://www.enforcementtracker.com"],
                        sentiment="positive",
                    ),
                    CompanyResearchQuestion(
                        question="What is DummyCorp's publicly stated data residency policy?",
                        answer="DummyCorp offers EU data residency on Enterprise plans. Standard plans use global infrastructure (AWS eu-west-1 and us-east-1). The company announced an upcoming EU-only hosting tier for Q4 2025.",
                        confidence="High",
                        source_urls=["https://www.dummycorp.com/security", "https://www.dummycorp.com/blog/eu-data-residency"],
                        sentiment="neutral",
                    ),
                    CompanyResearchQuestion(
                        question="Does DummyCorp publish transparency reports about government data requests?",
                        answer="DummyCorp has published annual transparency reports since 2022. The most recent report (2024) disclosed 3 government data requests, all from EU authorities, and all requiring valid legal process.",
                        confidence="Medium",
                        source_urls=["https://www.dummycorp.com/transparency"],
                        sentiment="positive",
                    ),
                    CompanyResearchQuestion(
                        question="Is DummyCorp subject to the US CLOUD Act or similar US legislation?",
                        answer="As a German GmbH, DummyCorp is not directly subject to the US CLOUD Act. However, its use of AWS (US cloud provider) and presence of a US office could create indirect exposure to US jurisdiction in certain scenarios.",
                        confidence="Medium",
                        source_urls=["https://www.dummycorp.com/legal", "https://www.dummycorp.com/security"],
                        sentiment="neutral",
                    ),
                    CompanyResearchQuestion(
                        question="Has DummyCorp made recent commitments about EU data sovereignty or data localization?",
                        answer="In Q2 2025, DummyCorp announced a roadmap to migrate all standard-tier infrastructure to EU-only regions by end of 2025. They also partnered with Hetzner (German hosting provider) for database hosting and adopted Plausible Analytics (Estonia) as their analytics platform.",
                        confidence="High",
                        source_urls=["https://www.dummycorp.com/blog/sovereignty-roadmap", "https://techeu.com/dummycorp-eu-migration"],
                        sentiment="positive",
                    ),
                ],
                key_findings=[
                    "German-registered GmbH with EU-based founding team",
                    "Primarily EU-funded (Earlybird, Northzone, Latitude) with one US investor (Accel)",
                    "Independent company - not owned by US parent corporation",
                    "No GDPR fines or major regulatory actions",
                    "One minor security incident (2024) - proactively disclosed",
                    "EU data residency available on Enterprise; EU-only migration planned for 2025",
                    "Publishes annual transparency reports since 2022",
                    "Active roadmap to reduce US infrastructure dependencies",
                ],
                sovereignty_flags=[
                    "US investor participation (Accel) in Series B funding round",
                    "US office in San Francisco with employees who may access EU data",
                    "Currently uses AWS (US cloud provider) for primary infrastructure",
                    "Standard plan routes data through US regions (us-east-1)",
                ],
                research_categories_covered=[
                    "Registration", "Team Background", "Funding Sources", "Ownership Structure",
                    "Security History", "Regulatory History", "Data Residency Policy",
                    "Transparency", "Legal Jurisdiction", "EU Commitment",
                ],
            ),
            risk_factors=[
                "Company has US office location - US-based employees can access EU data",
                "Infrastructure uses US cloud provider: AWS (subject to US jurisdiction even with EU regions)",
                "Using Fly.io (US company) with EU server regions",
                "CDN provider: Cloudflare (US company with EU presence)",
                "US-based sub-processor: OpenAI (AI/ML)",
                "US-based sub-processor: Stripe (Payment Processing)",
                "US-based sub-processor: Intercom (Customer Support)",
                "US-based sub-processor: SendGrid (Email Service)",
                "US-based sub-processor: Datadog (Monitoring)",
                "US-based sub-processor: Sentry (Error Tracking)",
                "US-based sub-processor: Google Analytics (Analytics)",
                "Data residency is global, no EU-only guarantee",
                "Recent security incidents: 1 reported",
            ],
            positive_factors=[
                "Company registered in EU (Germany)",
                "EU office/employee presence (3 locations)",
                "Data centers in EU (1 location)",
                "Data stored in EU (1 location)",
                "GDPR compliance stated",
                "3 compliance certifications (SOC 2 Type II, ISO 27001, GDPR Art. 28 DPA)",
                "Data residency guarantees disclosed",
                "2 EU-based sub-processors",
            ],
            detected_services=[
                DetectedService(
                    name="Google Fonts", domain="fonts.googleapis.com", jurisdiction="United States",
                    category="CDN/Fonts", risk_level="Medium",
                    alternatives_eu=["Bunny Fonts (Slovenia)", "Self-hosted fonts"],
                    notes="Font files served from Google servers; may leak visitor IP addresses to US",
                ),
                DetectedService(
                    name="Intercom", domain="widget.intercom.io", jurisdiction="United States",
                    category="Customer Support", risk_level="High",
                    alternatives_eu=["Crisp (France)", "Userlike (Germany)"],
                    notes="Chat widget loads external scripts and transmits user session data",
                ),
                DetectedService(
                    name="Stripe", domain="js.stripe.com", jurisdiction="United States",
                    category="Payment Processing", risk_level="Critical",
                    alternatives_eu=["Mollie (Netherlands)", "Adyen (Netherlands)"],
                    notes="Payment processing scripts handle sensitive financial data",
                ),
                DetectedService(
                    name="Sentry", domain="browser.sentry-cdn.com", jurisdiction="United States",
                    category="Error Tracking", risk_level="High",
                    alternatives_eu=["Glitchtip (EU-hosted)", "Highlight.io (self-hosted)"],
                    notes="Error tracking may capture user data and session information",
                ),
                DetectedService(
                    name="Google Analytics", domain="www.googletagmanager.com", jurisdiction="United States",
                    category="Analytics", risk_level="High",
                    alternatives_eu=["Plausible (Estonia)", "Matomo (EU-hosted)", "Fathom (Canada, GDPR-compliant)"],
                    notes="Comprehensive user tracking and behavioral analytics sent to US servers",
                ),
            ],
        )
        duration = (datetime.now() - start_time).total_seconds()
        save_analysis(url="dummy", normalized_url="dummy", response=dummy_response, duration_seconds=duration)
        return dummy_response
    # --- END DUMMY MODE ---

    try:
        # Scrape multiple pages (run in thread pool to avoid blocking)
        logger.info("📥 Step 1/4: Scraping multiple pages from website...")
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        
        logger.info(f"🌐 Scraping multiple pages from: {request.url}")
        logger.info("   Checking: homepage, /about, /privacy, /legal/subprocessors, /security, /careers")
        success, scraped_data, error = await loop.run_in_executor(executor, _scrape_multiple_pages_safe, request.url)
        logger.debug(f"📊 Scrape result - success: {success}, pages_scraped: {len(scraped_data.get('pages', {})) if scraped_data else 0}, error: {error}")
        if not success:
            logger.error(f"❌ Scraping failed: {error}")
            raise HTTPException(status_code=error["status_code"], detail=error["detail"])
        
        combined_text = scraped_data.get("combined", "")
        pages_scraped = scraped_data.get("pages", {})
        logger.info(f"✅ Scraping successful: {len(pages_scraped)} pages scraped, {len(combined_text)} total characters")
        logger.info(f"📄 Pages found: {', '.join(pages_scraped.keys())}")
        
        if not combined_text or len(combined_text.strip()) < 50:
            logger.error(f"❌ Insufficient text extracted: {len(combined_text.strip())} characters")
            raise HTTPException(status_code=400, detail="Could not extract sufficient text from the website (need at least 50 characters)")
        
        # Analyze with Gemini (run in thread pool to avoid blocking)
        logger.info("📥 Step 2/5: Analyzing scraped content with Gemini AI...")
        logger.debug(f"🔄 About to run analyze_with_gemini in thread pool")
        success, analysis, error = await loop.run_in_executor(executor, _analyze_with_gemini_safe, combined_text)
        logger.debug(f"📊 Gemini result - success: {success}, vendors_count: {len(analysis.get('vendors', [])) if analysis else 0}, error: {error}")
        if not success:
            logger.error(f"❌ Gemini analysis failed: {error}")
            raise HTTPException(status_code=error["status_code"], detail=error["detail"])
        logger.info(f"✅ Website content analysis successful")
        
        vendors_data = analysis.get("vendors", [])
        company_info_data = analysis.get("company_info", {})
        infrastructure_data = analysis.get("infrastructure", {})
        data_flows_data = analysis.get("data_flows", {})
        compliance_data = analysis.get("compliance", {})
        summary = analysis.get("summary", "No summary available")

        # NEW: Merge detected services from resource analysis with AI-found vendors
        detected_services = scraped_data.get("detected_services", [])
        logger.info(f"📊 Merging detected services: AI found {len(vendors_data)} vendors, resource analysis found {len(detected_services)} services")

        for service in detected_services:
            # Check if this service is already in vendors (avoid duplicates by name)
            service_name = service.get('name', '')
            if not any(v.get('name', '').lower() == service_name.lower() for v in vendors_data):
                # Add as a new vendor
                vendors_data.append({
                    'name': service['name'],
                    'purpose': service.get('category', 'Other'),
                    'location': service.get('jurisdiction', 'Unknown'),
                    'risk': service.get('risk_level', 'Medium')
                })
                logger.info(f"➕ Added detected service to vendors: {service_name} ({service.get('category')})")
            else:
                logger.debug(f"⏭️ Skipping duplicate service: {service_name}")

        logger.info(f"📊 Total vendors after merging: {len(vendors_data)}")

        # Merge infrastructure hints from headers with AI-detected infrastructure
        infrastructure_hints = scraped_data.get("infrastructure_hints", {})
        if infrastructure_hints.get("cloud_provider") != "Unknown":
            if infrastructure_data.get("cloud_provider", "Unknown") == "Unknown":
                infrastructure_data["cloud_provider"] = infrastructure_hints["cloud_provider"]
                logger.info(f"✅ Using infrastructure detected from headers: {infrastructure_hints['cloud_provider']}")
            else:
                # Combine both (headers take precedence if different)
                logger.info(f"🔍 AI detected: {infrastructure_data.get('cloud_provider')}, Headers detected: {infrastructure_hints['cloud_provider']}")
                if infrastructure_hints["cloud_provider"] not in infrastructure_data.get("cloud_provider", ""):
                    infrastructure_data["cloud_provider"] = f"{infrastructure_data.get('cloud_provider', '')}, {infrastructure_hints['cloud_provider']}"
        
        if infrastructure_hints.get("hosting_platform") != "Unknown":
            if "hosting_platform" not in infrastructure_data or infrastructure_data.get("hosting_platform") == "Unknown":
                infrastructure_data["hosting_platform"] = infrastructure_hints["hosting_platform"]
                logger.info(f"✅ Using hosting platform detected from headers: {infrastructure_hints['hosting_platform']}")
        
        if infrastructure_hints.get("cdn_providers"):
            existing_cdns = infrastructure_data.get("cdn_providers", [])
            for cdn in infrastructure_hints["cdn_providers"]:
                if cdn not in existing_cdns:
                    existing_cdns.append(cdn)
            infrastructure_data["cdn_providers"] = existing_cdns
        
        logger.info(f"📊 Extracted from website: {len(vendors_data)} vendors, company info: {bool(company_info_data)}, infrastructure: {bool(infrastructure_data)}, data flows: {bool(data_flows_data)}")
        
        # Step 3: Company web research for sovereignty assessment
        logger.info("📥 Step 3/6: Researching company background for sovereignty assessment...")
        search_findings = {}
        search_summary = ""
        additional_categories = []
        research_data = {}

        company_name = company_info_data.get("legal_entity", "Unknown")
        if company_name == "Unknown" or not company_name:
            from urllib.parse import urlparse
            domain = urlparse(request.url).netloc.replace('www.', '')
            company_name = domain.split('.')[0].title()

        try:
            success, research_result, research_error = await loop.run_in_executor(
                executor,
                _research_company_safe,
                company_name,
                request.url,
                company_info_data
            )
            if success and research_result:
                research_data = research_result
                logger.info(f"✅ Company research complete: {len(research_data.get('questions_answers', []))} questions answered")
            else:
                logger.warning(f"⚠️ Company research returned no data: {research_error}")
                research_data = {}
        except Exception as e:
            logger.warning(f"⚠️ Company research failed: {str(e)}, continuing without research")
            research_data = {}

        # Calculate research score
        research_score, sovereignty_flags = calculate_research_score(research_data)
        logger.info(f"📊 Research score: {research_score}/100, sovereignty flags: {len(sovereignty_flags)}")

        # Calculate enhanced score (fast, can run synchronously)
        logger.info("📥 Step 4/6: Calculating strict sovereignty score...")
        logger.info(f"📊 Scoring inputs:")
        logger.info(f"   Vendors: {len(vendors_data)}")
        logger.info(f"   Infrastructure: cloud={infrastructure_data.get('cloud_provider')}, hosting={infrastructure_data.get('hosting_platform')}")
        logger.info(f"   Compliance: gdpr={compliance_data.get('gdpr_status')}, incidents={len(compliance_data.get('recent_incidents', []))}")
        score, risk_level, risk_factors, positive_factors = calculate_score(
            vendors_data,
            company_info_data,
            infrastructure_data,
            data_flows_data,
            compliance_data
        )
        logger.info(f"📊 Score result: {score}/100 ({risk_level} risk)")
        
        # Prepare additional findings (compliance is separate field in response)
        additional_findings = AdditionalFindings(
            recent_changes=search_findings.get("recent_changes", []),
            additional_categories=additional_categories + analysis.get("additional_categories", []),
            search_summary=search_summary
        )
        
        # Format vendors
        vendors = []
        for v in vendors_data:
            try:
                vendor = Vendor(
                    name=v.get("name", "Unknown"),
                    purpose=v.get("purpose", "Unknown"),
                    location=v.get("location", "Unknown"),
                    risk=v.get("risk", "Unknown")
                )
                vendors.append(vendor)
            except Exception as e:
                logger.warning(f"⚠️ Skipping invalid vendor data: {v} - Error: {str(e)}")
                continue
        
        # Format company info
        company_info = CompanyInfo(
            registration_country=company_info_data.get("registration_country", "Unknown"),
            legal_entity=company_info_data.get("legal_entity", "Unknown"),
            office_locations=company_info_data.get("office_locations", []),
            employee_locations=company_info_data.get("employee_locations", [])
        )
        
        # Format infrastructure
        infrastructure = InfrastructureInfo(
            cloud_provider=infrastructure_data.get("cloud_provider") or "Unknown",
            hosting_platform=infrastructure_data.get("hosting_platform") or "Unknown",
            data_centers=infrastructure_data.get("data_centers", []),
            server_locations=infrastructure_data.get("server_locations", []),
            cdn_providers=infrastructure_data.get("cdn_providers", [])
        )
        
        # Format data flows
        data_flows = DataFlowInfo(
            storage_locations=data_flows_data.get("storage_locations", []),
            processing_locations=data_flows_data.get("processing_locations", []),
            data_residency=data_flows_data.get("data_residency", "Unknown")
        )
        
        # Format compliance info (separate from additional findings)
        compliance = ComplianceInfo(
            gdpr_status=compliance_data.get("gdpr_status", "Unknown"),
            certifications=compliance_data.get("certifications", []),
            data_residency_guarantees=compliance_data.get("data_residency_guarantees", "Unknown"),
            recent_incidents=compliance_data.get("recent_incidents", [])
        )

        # Format detected services
        detected_services_formatted = []
        for service in detected_services:
            try:
                detected_service = DetectedService(
                    name=service.get("name", "Unknown"),
                    domain=service.get("domain", "Unknown"),
                    jurisdiction=service.get("jurisdiction", "Unknown"),
                    category=service.get("category", "Other"),
                    risk_level=service.get("risk_level", "Medium"),
                    alternatives_eu=service.get("alternatives_eu", []),
                    notes=service.get("notes", "")
                )
                detected_services_formatted.append(detected_service)
            except Exception as e:
                logger.warning(f"⚠️ Skipping invalid detected service: {service} - Error: {str(e)}")
                continue

        # Format company research
        company_research_qa = []
        for qa in research_data.get("questions_answers", []):
            try:
                company_research_qa.append(CompanyResearchQuestion(
                    question=qa.get("question", ""),
                    answer=qa.get("answer", "No information found"),
                    confidence=qa.get("confidence", "Low"),
                    source_urls=qa.get("source_urls", []),
                    sentiment=qa.get("sentiment", "neutral"),
                ))
            except Exception as e:
                logger.warning(f"⚠️ Skipping invalid research Q&A: {e}")
                continue

        company_research = CompanyResearch(
            score=research_score,
            research_summary=research_data.get("research_summary", ""),
            questions_answers=company_research_qa,
            key_findings=research_data.get("key_findings", []),
            sovereignty_flags=sovereignty_flags,
            research_categories_covered=[q["category"] for q in SOVEREIGNTY_RESEARCH_QUESTIONS],
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"✅ Analysis complete in {duration:.2f} seconds")
        logger.info(f"📊 Final result: Score {score}/100 ({risk_level} risk), Research: {research_score}/100")
        logger.info(f"   Vendors: {len(vendors)}, Risk factors: {len(risk_factors)}")
        logger.info(f"   Detected Services: {len(detected_services_formatted)}")
        logger.info(f"   Company: {company_info.registration_country}, Cloud: {infrastructure.cloud_provider}")
        logger.info(f"   Compliance: GDPR {compliance.gdpr_status}, Certifications: {len(compliance.certifications)}")
        logger.info(f"   Research: {len(company_research_qa)} questions answered, {len(sovereignty_flags)} flags")
        logger.info("=" * 80)

        response_obj = AnalyzeResponse(
            score=score,
            risk_level=risk_level,
            summary=summary,
            vendors=vendors,
            company_info=company_info,
            infrastructure=infrastructure,
            data_flows=data_flows,
            compliance=compliance,
            additional_findings=additional_findings,
            company_research=company_research,
            risk_factors=risk_factors[:20],
            positive_factors=positive_factors[:10],
            detected_services=detected_services_formatted
        )

        # Save to database
        save_analysis(
            url=original_url,
            normalized_url=request.url,
            response=response_obj,
            duration_seconds=duration,
        )

        return response_obj

    except HTTPException as http_err:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        error_msg = f"❌ HTTPException after {duration:.2f}s: {http_err.status_code} - {http_err.detail}"
        logger.error(error_msg)
        print(error_msg, flush=True)
        logger.info("=" * 80)
        raise
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        error_msg = f"❌ UNEXPECTED EXCEPTION after {duration:.2f}s: {type(e).__name__}: {str(e)}"
        logger.error(error_msg)
        logger.error(f"   Full traceback:", exc_info=True)
        print(error_msg, flush=True)
        print(f"   Exception type: {type(e).__name__}", flush=True)
        print(f"   Exception message: {str(e)}", flush=True)
        import traceback
        print("   Full traceback:", flush=True)
        traceback.print_exc()
        logger.info("=" * 80)
        # Save failure to DB for tracking
        try:
            save_analysis(
                url=original_url,
                normalized_url=request.url,
                response=AnalyzeResponse(score=0, risk_level="Error", summary=str(e), vendors=[]),
                duration_seconds=duration,
                success=False,
                error_message=str(e),
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Internal server error: {type(e).__name__}: {str(e)}")


@app.get("/")
async def root():
    logger.info("📥 GET / endpoint called")
    return {"message": "Sovereign Scan API", "status": "running"}

@app.get("/test")
async def test():
    """Simple test endpoint to verify API is working"""
    return {
        "message": "API is working!",
        "endpoints": {
            "root": "/",
            "health": "/health",
            "test": "/test",
            "analyze": "POST /analyze"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    logger.info("🏥 GET /health endpoint called")
    health_status = {
        "status": "healthy",
        "gemini_configured": model is not None,
        "timestamp": datetime.now().isoformat()
    }
    logger.debug(f"🏥 Health status: {health_status}")
    return health_status


@app.get("/stats")
async def get_stats():
    """Get usage statistics for the prototype."""
    try:
        with get_db() as db:
            # Overall counts
            total = db.execute("SELECT COUNT(*) as c FROM analyses").fetchone()['c']
            unique_urls = db.execute("SELECT COUNT(DISTINCT normalized_url) as c FROM analyses WHERE success = TRUE").fetchone()['c']
            failures = db.execute("SELECT COUNT(*) as c FROM analyses WHERE success = FALSE").fetchone()['c']

            # Recent analyses
            recent = db.execute("""
                SELECT url, score, risk_level, duration_seconds, created_at
                FROM analyses
                WHERE success = TRUE
                ORDER BY created_at DESC
                LIMIT 20
            """).fetchall()

            # Top vendors seen across all analyses
            top_vendors = db.execute("""
                SELECT name, location, risk, COUNT(*) as appearances
                FROM vendors
                GROUP BY name
                ORDER BY appearances DESC
                LIMIT 15
            """).fetchall()

            # Risk distribution
            risk_dist = db.execute("""
                SELECT risk_level, COUNT(*) as count
                FROM analyses
                WHERE success = TRUE
                GROUP BY risk_level
            """).fetchall()

            # Score stats
            score_stats = db.execute("""
                SELECT AVG(score) as avg_score, MIN(score) as min_score, MAX(score) as max_score
                FROM analyses
                WHERE success = TRUE
            """).fetchone()

            return {
                "total_analyses": total,
                "unique_urls": unique_urls,
                "failed_analyses": failures,
                "score_stats": {
                    "average": round(score_stats['avg_score'], 1) if score_stats['avg_score'] else 0,
                    "min": score_stats['min_score'] or 0,
                    "max": score_stats['max_score'] or 0,
                },
                "risk_distribution": {r['risk_level']: r['count'] for r in risk_dist},
                "recent_analyses": [
                    {
                        "url": r['url'],
                        "score": r['score'],
                        "risk_level": r['risk_level'],
                        "duration_seconds": round(r['duration_seconds'], 2) if r['duration_seconds'] else None,
                        "analyzed_at": r['created_at'],
                    }
                    for r in recent
                ],
                "top_vendors": [
                    {
                        "name": v['name'],
                        "location": v['location'],
                        "risk": v['risk'],
                        "appearances": v['appearances'],
                    }
                    for v in top_vendors
                ],
            }
    except Exception as e:
        logger.error(f"Stats query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Stats unavailable: {str(e)}")
