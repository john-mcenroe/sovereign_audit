# Comprehensive Sovereignty Analysis Improvements

## Executive Summary
To achieve truly comprehensive sovereignty checks, you need to analyze not just what companies *say* they use, but what they *actually* use in production. This requires multi-layered detection across infrastructure, frontend resources, APIs, and recursive dependency chains.

---

## 🎯 Level 1: Frontend Resource Analysis (Currently Missing!)

### **Problem**: You're only analyzing HTML text, missing all the services the page actually uses

### **Solution: Analyze All Client-Side Resources**

```python
# New function: analyze_frontend_resources()
def analyze_frontend_resources(url: str) -> dict:
    """
    Load the page in a real browser and capture:
    - All network requests (XHR, fetch, scripts, images, fonts)
    - Third-party domains accessed
    - Cookies set (and their domains)
    - LocalStorage/SessionStorage usage
    - WebSocket connections
    - Analytics trackers
    """
```

**What to detect:**
1. **Analytics & Tracking**:
   - Google Analytics (US)
   - Mixpanel (US)
   - Segment (US)
   - Hotjar (EU - Malta)
   - Plausible (EU - friendly option)
   - Matomo (EU - friendly option)

2. **Customer Support/Chat**:
   - Intercom (US)
   - Zendesk (US)
   - Drift (US)
   - Crisp (France - EU)
   - LiveChat (Poland - EU)

3. **CDNs & Assets**:
   - Google Fonts (US - data collection concern)
   - Font Awesome CDN
   - Bootstrap CDN
   - JSDelivr
   - Cloudflare (US company, EU PoPs)

4. **External Scripts**:
   - Tag managers (Google Tag Manager)
   - A/B testing (Optimizely, VWO)
   - Session replay (FullStory, LogRocket)

**Implementation Approach**:

```python
# Option 1: Browser automation (most accurate)
from playwright.async_api import async_playwright

async def capture_network_requests(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        requests_log = []

        # Capture all network requests
        page.on("request", lambda request: requests_log.append({
            "url": request.url,
            "resource_type": request.resource_type,
            "method": request.method
        }))

        await page.goto(url, wait_until="networkidle")

        # Analyze all third-party domains
        third_party_domains = extract_domains(requests_log)

        await browser.close()
        return third_party_domains
```

```python
# Option 2: Regex analysis of HTML (lighter weight)
def analyze_embedded_resources(html_content: str) -> dict:
    """
    Parse HTML for:
    - <script src="..."> tags
    - <link href="..."> (stylesheets, fonts)
    - <img src="...">
    - <iframe src="...">
    - Inline scripts calling external APIs
    """
    import re
    from urllib.parse import urlparse

    # Find all external scripts
    script_pattern = r'<script[^>]+src=["\']([^"\']+)["\']'
    scripts = re.findall(script_pattern, html_content, re.IGNORECASE)

    # Find all external stylesheets
    css_pattern = r'<link[^>]+href=["\']([^"\']+\.css[^"\']*)["\']'
    stylesheets = re.findall(css_pattern, html_content, re.IGNORECASE)

    # Find all external images
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    images = re.findall(img_pattern, html_content, re.IGNORECASE)

    # Find iframes (often used for chat widgets, analytics)
    iframe_pattern = r'<iframe[^>]+src=["\']([^"\']+)["\']'
    iframes = re.findall(iframe_pattern, html_content, re.IGNORECASE)

    # Find inline script API calls
    api_call_patterns = [
        r'fetch\(["\']([^"\']+)["\']',
        r'axios\.(get|post)\(["\']([^"\']+)["\']',
        r'\.ajax\(\s*["\']([^"\']+)["\']',
    ]

    all_external_resources = scripts + stylesheets + images + iframes

    # Extract domains and geolocate
    external_domains = {}
    for url in all_external_resources:
        domain = urlparse(url).netloc
        if domain:
            external_domains[domain] = geolocate_domain(domain)

    return external_domains
```

---

## 🎯 Level 2: DNS & IP Geolocation (Currently Partial)

### **Enhance Your Infrastructure Detection**

```python
def deep_infrastructure_analysis(url: str) -> dict:
    """
    Go beyond HTTP headers:
    1. DNS lookups for all discovered domains
    2. IP geolocation for every IP
    3. ASN (Autonomous System Number) lookup to identify hosting provider
    4. Reverse DNS to find hosting patterns
    5. SSL certificate analysis
    """
    import socket
    import ssl
    import requests

    parsed = urlparse(url)
    domain = parsed.netloc

    # 1. DNS Resolution
    ips = socket.getaddrinfo(domain, None)

    # 2. IP Geolocation (use ipapi.co or similar)
    geolocations = []
    for ip_info in ips:
        ip = ip_info[4][0]
        geo = requests.get(f"https://ipapi.co/{ip}/json/").json()
        geolocations.append({
            "ip": ip,
            "country": geo.get("country_name"),
            "region": geo.get("region"),
            "org": geo.get("org"),  # Hosting provider
            "asn": geo.get("asn"),
        })

    # 3. SSL Certificate Analysis
    cert = ssl.get_server_certificate((domain, 443))
    # Parse cert for issuer location, SANs (additional domains)

    # 4. Check for known hosting patterns
    hosting_providers = {
        "AS16509": "Amazon AWS",
        "AS15169": "Google Cloud",
        "AS8075": "Microsoft Azure",
        "AS13335": "Cloudflare",
    }

    return {
        "ips": geolocations,
        "hosting_provider": identify_from_asn(geolocations),
        "ssl_info": parse_ssl_cert(cert)
    }
```

**Service to integrate**:
- ipapi.co (free tier: 1000 requests/day)
- ip-api.com (free, no auth required)
- MaxMind GeoIP2 (paid, more accurate)

---

## 🎯 Level 3: Recursive Sub-Processor Chain Analysis

### **Problem**: You find Vendor A, but miss that Vendor A uses Vendor B (US)

### **Solution: Multi-Level Dependency Tracking**

```python
async def recursive_vendor_analysis(vendor_name: str, depth: int = 2) -> dict:
    """
    For each discovered vendor:
    1. Search for their sub-processor page
    2. Analyze THEIR vendors
    3. Continue up to `depth` levels
    4. Build a dependency tree
    """
    if depth == 0:
        return {}

    # Search for vendor's sub-processor page
    vendor_subprocessor_urls = [
        f"https://{vendor_name.lower()}.com/legal/subprocessors",
        f"https://{vendor_name.lower()}.com/legal/sub-processors",
        f"https://{vendor_name.lower()}.com/privacy/subprocessors",
        f"https://{vendor_name.lower()}.com/security/subprocessors",
    ]

    for url in vendor_subprocessor_urls:
        try:
            # Scrape and analyze
            vendor_data = await analyze_url(url)

            # Recursively analyze their vendors
            for sub_vendor in vendor_data["vendors"]:
                sub_vendor["children"] = await recursive_vendor_analysis(
                    sub_vendor["name"],
                    depth - 1
                )

            return vendor_data
        except:
            continue

    return {}
```

**Dependency Tree Visualization**:
```
Your Company
├── Vendor A (US) - Critical Risk
│   ├── Vendor A's Cloud (AWS US) - Critical
│   └── Vendor A's Analytics (Mixpanel US) - High
├── Vendor B (EU)
│   └── Vendor B's Payment (Stripe US) - Critical
└── Vendor C (Global)
    └── Hidden US dependency!
```

---

## 🎯 Level 4: Service Pattern Detection with AI

### **Use Gemini to INFER services even when not explicitly listed**

```python
def infer_services_from_behavior(page_content: str, network_requests: list) -> dict:
    """
    Use Gemini to analyze patterns and infer services:
    - "Uses Stripe for payments" (even if not on subprocessor page)
    - "Likely uses AWS" (from infrastructure patterns)
    - "Uses Google Fonts" (privacy concern - shares IP with Google)
    """

    prompt = f"""You are a forensic data sovereignty analyst.

    Based on this website content and network requests, INFER what third-party
    services they are using, even if not explicitly stated:

    WEBPAGE CONTENT:
    {page_content[:5000]}

    NETWORK REQUESTS DETECTED:
    {json.dumps(network_requests, indent=2)}

    INFER AND CATEGORIZE:
    1. Payment Processing: (Stripe, PayPal, etc.)
    2. Email Services: (SendGrid, Mailgun, AWS SES, etc.)
    3. Authentication: (Auth0, Okta, Firebase Auth, etc.)
    4. Analytics: (Google Analytics, Mixpanel, Amplitude, etc.)
    5. Monitoring: (Datadog, New Relic, Sentry, etc.)
    6. Customer Support: (Intercom, Zendesk, Help Scout, etc.)
    7. SMS/Communications: (Twilio, Vonage, etc.)
    8. CDN/Edge: (Cloudflare, Fastly, Akamai, etc.)
    9. Cloud Storage: (AWS S3, Google Cloud Storage, etc.)
    10. AI/ML Services: (OpenAI, Anthropic, Google AI, etc.)
    11. Marketing: (Mailchimp, HubSpot, etc.)
    12. A/B Testing: (Optimizely, VWO, etc.)

    For EACH service detected, include:
    - Service name
    - Category
    - Jurisdiction (where company is based)
    - Confidence level (High/Medium/Low)
    - Evidence (why you think they use this)

    Return as JSON.
    """

    response = model.generate_content(prompt)
    return parse_inferred_services(response.text)
```

---

## 🎯 Level 5: Privacy Policy Deep Analysis

### **Mine privacy policies for hidden data transfers**

```python
def analyze_privacy_policy_transfers(privacy_policy_text: str) -> dict:
    """
    Privacy policies often reveal:
    - Countries where data is transferred
    - Legal bases for transfers (SCCs, BCRs, etc.)
    - Data retention periods
    - Third-party recipients
    """

    prompt = f"""Analyze this privacy policy for data sovereignty risks:

    {privacy_policy_text}

    Extract:
    1. ALL countries/regions where data may be transferred
    2. Legal mechanisms used (Standard Contractual Clauses, Binding Corporate Rules, etc.)
    3. ANY mention of US data transfers or US-based processors
    4. Data retention periods
    5. Rights of data subjects (deletion, portability, etc.)
    6. Any mentions of government access or law enforcement
    7. International transfer safeguards

    CRITICAL: Flag ANY transfers to countries without adequacy decisions from the EU.

    Return structured JSON.
    """

    return model.generate_content(prompt)
```

---

## 🎯 Level 6: Categorization & Weighting System

### **Not all vendors are equal - weight by criticality**

```python
# New scoring system with weighted categories
VENDOR_CATEGORY_WEIGHTS = {
    # Critical - handles actual customer data
    "Database/Storage": 1.5,
    "Cloud Infrastructure": 1.4,
    "Authentication": 1.4,
    "Payment Processing": 1.4,
    "AI/ML Processing": 1.5,  # Especially critical

    # High - processes customer data
    "Email Service": 1.2,
    "Customer Support": 1.2,
    "SMS/Communications": 1.2,
    "Backup/DR": 1.3,

    # Medium - analytics/monitoring
    "Analytics": 1.0,
    "Monitoring/APM": 1.0,
    "Error Tracking": 1.0,

    # Lower - limited data access
    "CDN": 0.8,
    "DNS": 0.6,
    "Marketing/Email": 0.9,
    "A/B Testing": 0.8,
}

def calculate_weighted_score(vendors: list) -> int:
    """
    Apply weights based on vendor category and data access level
    """
    score = 100

    for vendor in vendors:
        category = vendor.get("category", "Unknown")
        weight = VENDOR_CATEGORY_WEIGHTS.get(category, 1.0)

        # Base penalty
        if "US" in vendor["location"]:
            penalty = 12 * weight
        elif "GLOBAL" in vendor["location"]:
            penalty = 8 * weight
        else:
            penalty = 0

        score -= penalty

    return max(0, min(100, score))
```

---

## 🎯 Level 7: Known Services Database

### **Build a database of common services and their locations**

```python
# Add to backend: known_services.json
KNOWN_SERVICES = {
    # Analytics
    "google-analytics.com": {"name": "Google Analytics", "location": "United States", "category": "Analytics", "risk": "High"},
    "mixpanel.com": {"name": "Mixpanel", "location": "United States", "category": "Analytics", "risk": "High"},
    "segment.com": {"name": "Segment", "location": "United States", "category": "Analytics", "risk": "High"},
    "plausible.io": {"name": "Plausible", "location": "EU (Estonia)", "category": "Analytics", "risk": "Low"},

    # Support/Chat
    "intercom.io": {"name": "Intercom", "location": "United States", "category": "Customer Support", "risk": "Critical"},
    "zendesk.com": {"name": "Zendesk", "location": "United States", "category": "Customer Support", "risk": "High"},
    "crisp.chat": {"name": "Crisp", "location": "France", "category": "Customer Support", "risk": "Low"},

    # Payment
    "stripe.com": {"name": "Stripe", "location": "United States", "category": "Payment Processing", "risk": "Critical"},
    "paypal.com": {"name": "PayPal", "location": "United States", "category": "Payment Processing", "risk": "Critical"},

    # Email
    "sendgrid.com": {"name": "SendGrid", "location": "United States", "category": "Email Service", "risk": "High"},
    "mailgun.com": {"name": "Mailgun", "location": "United States", "category": "Email Service", "risk": "High"},

    # Cloud Storage
    "s3.amazonaws.com": {"name": "AWS S3", "location": "United States", "category": "Cloud Storage", "risk": "Critical"},
    "googleapis.com": {"name": "Google Cloud Storage", "location": "United States", "category": "Cloud Storage", "risk": "Critical"},

    # Fonts (often overlooked!)
    "fonts.googleapis.com": {"name": "Google Fonts", "location": "United States", "category": "CDN", "risk": "Medium", "note": "Shares IP address with Google"},
    "fonts.gstatic.com": {"name": "Google Fonts CDN", "location": "United States", "category": "CDN", "risk": "Medium"},

    # AI Services
    "api.openai.com": {"name": "OpenAI", "location": "United States", "category": "AI/ML", "risk": "Critical"},
    "api.anthropic.com": {"name": "Anthropic", "location": "United States", "category": "AI/ML", "risk": "Critical"},

    # Monitoring
    "sentry.io": {"name": "Sentry", "location": "United States", "category": "Error Tracking", "risk": "High"},
    "datadoghq.com": {"name": "Datadog", "location": "United States", "category": "Monitoring", "risk": "High"},
}

def match_known_services(domains: list) -> list:
    """
    Match discovered domains against known services database
    """
    detected_services = []

    for domain in domains:
        for known_domain, service_info in KNOWN_SERVICES.items():
            if known_domain in domain:
                detected_services.append(service_info)

    return detected_services
```

---

## 🎯 Level 8: Cookie & Tracking Analysis

### **Analyze cookies for hidden third-party services**

```python
def analyze_cookies(url: str) -> dict:
    """
    Capture and analyze all cookies set by the page:
    - First-party vs third-party
    - Cookie domains
    - Tracking purposes
    """

    # Using Playwright to capture cookies
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url)
        cookies = await context.cookies()

        third_party_cookies = []
        for cookie in cookies:
            domain = cookie["domain"]
            if domain not in url:
                # Third-party cookie
                third_party_cookies.append({
                    "domain": domain,
                    "name": cookie["name"],
                    "purpose": infer_cookie_purpose(cookie["name"])
                })

        return third_party_cookies

def infer_cookie_purpose(cookie_name: str) -> str:
    """
    Infer cookie purpose from name
    """
    analytics_patterns = ["_ga", "_gid", "utm_", "_fbp", "mp_"]
    support_patterns = ["intercom", "zendesk", "drift"]

    if any(pattern in cookie_name.lower() for pattern in analytics_patterns):
        return "Analytics/Tracking"
    elif any(pattern in cookie_name.lower() for pattern in support_patterns):
        return "Customer Support"

    return "Unknown"
```

---

## 🎯 Level 9: GitHub/Public Repository Analysis (Bonus)

### **If the app is open-source, analyze dependencies directly**

```python
def analyze_dependencies(repo_url: str) -> dict:
    """
    For open-source apps:
    1. Clone the repository
    2. Analyze package.json, requirements.txt, Gemfile, etc.
    3. Map each dependency to its maintainer location
    4. Check for telemetry/analytics in dependencies
    """

    # Example: Node.js app
    package_json = fetch_from_github(f"{repo_url}/package.json")
    dependencies = package_json["dependencies"]

    sovereignty_map = {}
    for dep_name, version in dependencies.items():
        # Look up dependency maintainer location
        npm_info = requests.get(f"https://registry.npmjs.org/{dep_name}").json()
        maintainer = npm_info.get("maintainers", [{}])[0]

        # Check if dependency has known telemetry
        has_telemetry = check_telemetry(dep_name)

        sovereignty_map[dep_name] = {
            "version": version,
            "maintainer_location": geolocate_maintainer(maintainer),
            "has_telemetry": has_telemetry
        }

    return sovereignty_map
```

---

## 📊 Implementation Priority Roadmap

### **Phase 1 (Quick Wins - 1-2 weeks)**
✅ **Level 7**: Build known services database (JSON file)
✅ **Level 5**: Add privacy policy deep analysis
✅ **Level 2**: Enhance DNS/IP geolocation
✅ **Level 6**: Implement category weighting system

### **Phase 2 (Medium Effort - 2-4 weeks)**
✅ **Level 1 (Lite)**: Regex-based resource analysis (scripts, images, iframes)
✅ **Level 4**: Service inference with enhanced Gemini prompts
✅ **Level 3**: Basic recursive vendor analysis (1 level deep)

### **Phase 3 (Advanced - 4-8 weeks)**
✅ **Level 1 (Full)**: Browser automation with Playwright
✅ **Level 8**: Cookie and tracking analysis
✅ **Level 3 (Deep)**: Multi-level recursive vendor analysis (2-3 levels)

### **Phase 4 (Expert - 8+ weeks)**
✅ **Level 9**: GitHub/public repository analysis
✅ **Machine Learning**: Train model to recognize services from patterns
✅ **Real-time Monitoring**: Track changes in vendor sovereignty over time

---

## 🎨 Enhanced Category System

```python
# Suggested categories with clear definitions
VENDOR_CATEGORIES = {
    "critical_data_processing": [
        "Database/Storage",
        "Cloud Infrastructure",
        "AI/ML Processing",
        "Authentication",
        "Payment Processing",
        "Backup/Disaster Recovery"
    ],
    "high_data_access": [
        "Email Service",
        "Customer Support/Chat",
        "SMS/Communications",
        "Document Storage",
        "CRM/Sales Tools"
    ],
    "medium_data_access": [
        "Analytics",
        "Monitoring/APM",
        "Error Tracking",
        "Session Replay",
        "A/B Testing"
    ],
    "low_data_access": [
        "CDN",
        "DNS",
        "Load Balancer",
        "DDoS Protection"
    ],
    "indirect_access": [
        "Marketing Automation",
        "Social Media Integration",
        "Advertising Platforms",
        "Tag Management"
    ]
}
```

---

## 🔍 Example: Complete Analysis Flow

```python
async def comprehensive_sovereignty_audit(url: str) -> dict:
    """
    The complete sovereignty audit combining all levels
    """
    results = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "layers": {}
    }

    # Layer 1: Static content analysis (current)
    results["layers"]["static_content"] = await scrape_and_analyze(url)

    # Layer 2: Frontend resources
    results["layers"]["frontend_resources"] = await analyze_frontend_resources(url)

    # Layer 3: Infrastructure deep dive
    results["layers"]["infrastructure"] = await deep_infrastructure_analysis(url)

    # Layer 4: Service inference
    results["layers"]["inferred_services"] = await infer_services_from_behavior(
        results["layers"]["static_content"]["text"],
        results["layers"]["frontend_resources"]["network_requests"]
    )

    # Layer 5: Privacy policy analysis
    privacy_url = find_privacy_policy_url(url)
    results["layers"]["privacy_analysis"] = await analyze_privacy_policy_transfers(privacy_url)

    # Layer 6: Recursive vendor analysis
    vendors = results["layers"]["static_content"]["vendors"]
    for vendor in vendors:
        vendor["sub_vendors"] = await recursive_vendor_analysis(vendor["name"], depth=2)

    # Layer 7: Known services matching
    all_domains = extract_all_domains(results)
    results["layers"]["known_services"] = match_known_services(all_domains)

    # Layer 8: Cookie analysis
    results["layers"]["cookies"] = await analyze_cookies(url)

    # Final comprehensive score
    results["final_score"] = calculate_comprehensive_score(results)
    results["dependency_tree"] = build_dependency_tree(results)
    results["risk_heatmap"] = generate_risk_heatmap(results)

    return results
```

---

## 📈 Enhanced Output Format

```json
{
  "sovereignty_score": 45,
  "risk_level": "Critical",
  "analysis_depth": "Comprehensive (8 layers)",
  "total_services_detected": 47,
  "breakdown": {
    "us_based_services": 32,
    "eu_based_services": 8,
    "global_services": 7,
    "unknown_jurisdiction": 0
  },
  "critical_findings": [
    "OpenAI API detected (US, Critical data access)",
    "AWS hosting with no EU region guarantee",
    "Google Analytics tracking (IP sharing with US)",
    "Hidden Stripe dependency via primary vendor"
  ],
  "service_map": {
    "critical_data_processing": 8,
    "high_data_access": 12,
    "medium_data_access": 15,
    "low_data_access": 9,
    "indirect_access": 3
  },
  "dependency_chains": [
    "Your App → Vendor A (US) → AWS (US) → [CRITICAL PATH]",
    "Your App → Intercom (US) → Zendesk (US) → [SUPPORT CHAIN]"
  ],
  "recommendations": [
    "Replace Google Fonts with self-hosted fonts (easy fix, -5 points)",
    "Migrate to EU-based analytics (Plausible, Matomo)",
    "Request AWS eu-west-1 region lock from vendor",
    "Consider replacing Intercom with Crisp (EU-based)"
  ]
}
```

---

## 🚀 Next Steps

1. **Start with Phase 1** (known services DB + privacy policy analysis)
2. **Add lightweight resource detection** (regex-based)
3. **Enhance Gemini prompts** for service inference
4. **Gradually add browser automation** for production-quality analysis

This multi-layered approach will give you the most comprehensive sovereignty analysis available on the market. Let me know which level you'd like to implement first!
