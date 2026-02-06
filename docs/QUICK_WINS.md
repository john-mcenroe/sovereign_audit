# Quick Wins: Immediate Improvements You Can Implement Today

These are high-impact, low-effort improvements you can add to your existing codebase right now.

---

## 🎯 Quick Win #1: Known Services Database (30 minutes)

### Create `backend/known_services.json`

```json
{
  "analytics": {
    "google-analytics.com": {
      "name": "Google Analytics",
      "jurisdiction": "United States",
      "category": "Analytics",
      "risk_level": "High",
      "data_access": "IP addresses, browsing behavior, device info",
      "alternatives_eu": ["Plausible (Estonia)", "Matomo (self-hosted)"]
    },
    "mixpanel.com": {
      "name": "Mixpanel",
      "jurisdiction": "United States",
      "category": "Analytics",
      "risk_level": "High",
      "data_access": "User behavior, PII if configured",
      "alternatives_eu": ["Pirsch (Germany)"]
    },
    "plausible.io": {
      "name": "Plausible Analytics",
      "jurisdiction": "Estonia (EU)",
      "category": "Analytics",
      "risk_level": "Low",
      "data_access": "Minimal, no cookies",
      "gdpr_compliant": true
    }
  },
  "fonts": {
    "fonts.googleapis.com": {
      "name": "Google Fonts",
      "jurisdiction": "United States",
      "category": "CDN/Fonts",
      "risk_level": "Medium",
      "data_access": "IP address shared with Google",
      "alternatives_eu": ["Self-hosted fonts", "Bunny Fonts (Slovenia)"],
      "notes": "German courts ruled this violates GDPR (2022)"
    },
    "fonts.gstatic.com": {
      "name": "Google Fonts CDN",
      "jurisdiction": "United States",
      "category": "CDN/Fonts",
      "risk_level": "Medium",
      "data_access": "IP address",
      "alternatives_eu": ["Bunny Fonts"]
    }
  },
  "customer_support": {
    "intercom.io": {
      "name": "Intercom",
      "jurisdiction": "United States",
      "category": "Customer Support",
      "risk_level": "Critical",
      "data_access": "Customer PII, conversation history, metadata",
      "alternatives_eu": ["Crisp (France)", "Chatwoot (self-hosted)"]
    },
    "widget.intercom.io": {
      "name": "Intercom Widget",
      "jurisdiction": "United States",
      "category": "Customer Support",
      "risk_level": "Critical",
      "data_access": "Real-time user behavior, PII",
      "alternatives_eu": ["Crisp"]
    },
    "crisp.chat": {
      "name": "Crisp",
      "jurisdiction": "France (EU)",
      "category": "Customer Support",
      "risk_level": "Low",
      "data_access": "Customer conversations",
      "gdpr_compliant": true
    }
  },
  "payment": {
    "stripe.com": {
      "name": "Stripe",
      "jurisdiction": "United States",
      "category": "Payment Processing",
      "risk_level": "Critical",
      "data_access": "Payment data, PII, financial information",
      "alternatives_eu": ["Mollie (Netherlands)", "GoCardless (UK)"],
      "notes": "Has EU data centers but US company"
    },
    "js.stripe.com": {
      "name": "Stripe.js",
      "jurisdiction": "United States",
      "category": "Payment Processing",
      "risk_level": "Critical",
      "data_access": "Card details, checkout behavior",
      "alternatives_eu": ["Mollie"]
    }
  },
  "email": {
    "sendgrid.com": {
      "name": "SendGrid (Twilio)",
      "jurisdiction": "United States",
      "category": "Email Service",
      "risk_level": "High",
      "data_access": "Email content, recipient data",
      "alternatives_eu": ["Postmark (has EU region)", "Mailgun (EU region available)"]
    },
    "api.mailgun.net": {
      "name": "Mailgun",
      "jurisdiction": "United States",
      "category": "Email Service",
      "risk_level": "High",
      "data_access": "Email content, metadata",
      "alternatives_eu": ["Mailgun EU region", "Brevo/Sendinblue (France)"]
    }
  },
  "monitoring": {
    "sentry.io": {
      "name": "Sentry",
      "jurisdiction": "United States",
      "category": "Error Tracking",
      "risk_level": "High",
      "data_access": "Error logs, stack traces, user context",
      "alternatives_eu": ["Self-hosted Sentry", "Highlight.io (has EU region)"],
      "notes": "Errors may contain PII"
    },
    "datadoghq.com": {
      "name": "Datadog",
      "jurisdiction": "United States",
      "category": "Monitoring",
      "risk_level": "High",
      "data_access": "Logs, metrics, traces, user data",
      "alternatives_eu": ["Grafana Cloud (EU region)"]
    }
  },
  "cdn": {
    "cloudflare.com": {
      "name": "Cloudflare",
      "jurisdiction": "United States",
      "category": "CDN/DDoS Protection",
      "risk_level": "Medium",
      "data_access": "IP addresses, traffic patterns",
      "alternatives_eu": ["BunnyCDN (Slovenia)", "KeyCDN (Switzerland)"],
      "notes": "Has EU POPs but US-based company"
    },
    "cdnjs.cloudflare.com": {
      "name": "Cloudflare CDN (cdnjs)",
      "jurisdiction": "United States",
      "category": "CDN",
      "risk_level": "Medium",
      "data_access": "IP addresses",
      "alternatives_eu": ["jsDelivr (Poland)", "Self-hosted"]
    }
  },
  "ai_services": {
    "api.openai.com": {
      "name": "OpenAI",
      "jurisdiction": "United States",
      "category": "AI/ML",
      "risk_level": "Critical",
      "data_access": "Input prompts, output data, potential PII in queries",
      "alternatives_eu": ["Mistral AI (France)", "Aleph Alpha (Germany)"],
      "notes": "Data retention policies unclear for API usage"
    },
    "api.anthropic.com": {
      "name": "Anthropic",
      "jurisdiction": "United States",
      "category": "AI/ML",
      "risk_level": "Critical",
      "data_access": "Conversation data, PII in prompts",
      "alternatives_eu": ["Mistral AI"]
    }
  },
  "tag_management": {
    "googletagmanager.com": {
      "name": "Google Tag Manager",
      "jurisdiction": "United States",
      "category": "Tag Management",
      "risk_level": "High",
      "data_access": "All page data, user behavior",
      "alternatives_eu": ["Matomo Tag Manager (self-hosted)"],
      "notes": "Often loads other US trackers"
    }
  },
  "social_auth": {
    "accounts.google.com": {
      "name": "Google OAuth",
      "jurisdiction": "United States",
      "category": "Authentication",
      "risk_level": "High",
      "data_access": "Email, profile data, authentication events",
      "alternatives_eu": ["European identity providers", "Self-hosted OAuth"]
    }
  }
}
```

### Add to `main.py` (after line 450):

```python
import json

# Load known services database
KNOWN_SERVICES = {}
try:
    with open("known_services.json", "r") as f:
        KNOWN_SERVICES = json.load(f)
    logger.info(f"✅ Loaded {sum(len(v) for v in KNOWN_SERVICES.values())} known services")
except FileNotFoundError:
    logger.warning("⚠️ known_services.json not found")

def detect_known_services(html_content: str) -> list:
    """
    Scan HTML for known third-party service domains
    """
    detected = []
    html_lower = html_content.lower()

    for category, services in KNOWN_SERVICES.items():
        for domain, info in services.items():
            if domain in html_lower:
                detected.append({
                    **info,
                    "domain": domain,
                    "category_group": category
                })
                logger.info(f"🔍 Detected known service: {info['name']} ({domain})")

    return detected
```

### Update `scrape_url` function (after line 448):

```python
# Add after getting text (line 448)
detected_services = detect_known_services(text)
return text, infrastructure_hints, detected_services  # Return 3 values now
```

### Update `analyze_url` endpoint to include detected services in response

---

## 🎯 Quick Win #2: Enhanced Resource Detection (1 hour)

### Add regex-based resource analysis to `main.py`:

```python
import re
from urllib.parse import urlparse, urljoin
from collections import defaultdict

def analyze_embedded_resources(html_content: str, base_url: str) -> dict:
    """
    Extract all external resources from HTML without browser automation
    """
    logger.info("🔍 Analyzing embedded resources...")

    resources = defaultdict(list)

    # 1. External Scripts
    script_pattern = r'<script[^>]*src=["\']([^"\']+)["\']'
    scripts = re.findall(script_pattern, html_content, re.IGNORECASE)
    for script in scripts:
        full_url = urljoin(base_url, script)
        domain = urlparse(full_url).netloc
        if domain and domain not in urlparse(base_url).netloc:
            resources['external_scripts'].append({
                'url': full_url,
                'domain': domain
            })

    # 2. External Stylesheets
    css_pattern = r'<link[^>]*href=["\']([^"\']+\.css[^"\']*)["\']'
    stylesheets = re.findall(css_pattern, html_content, re.IGNORECASE)
    for css in stylesheets:
        full_url = urljoin(base_url, css)
        domain = urlparse(full_url).netloc
        if domain and domain not in urlparse(base_url).netloc:
            resources['external_stylesheets'].append({
                'url': full_url,
                'domain': domain
            })

    # 3. External Images
    img_pattern = r'<img[^>]*src=["\']([^"\']+)["\']'
    images = re.findall(img_pattern, html_content, re.IGNORECASE)
    for img in images:
        full_url = urljoin(base_url, img)
        domain = urlparse(full_url).netloc
        if domain and domain not in urlparse(base_url).netloc:
            resources['external_images'].append({
                'url': full_url,
                'domain': domain
            })

    # 4. Iframes (often chat widgets, payment forms)
    iframe_pattern = r'<iframe[^>]*src=["\']([^"\']+)["\']'
    iframes = re.findall(iframe_pattern, html_content, re.IGNORECASE)
    for iframe in iframes:
        full_url = urljoin(base_url, iframe)
        domain = urlparse(full_url).netloc
        if domain and domain not in urlparse(base_url).netloc:
            resources['iframes'].append({
                'url': full_url,
                'domain': domain,
                'note': 'Likely widget (chat, payment, etc.)'
            })

    # 5. Web Fonts
    font_pattern = r'@font-face[^}]*url\(["\']?([^"\')\s]+)["\']?\)'
    fonts = re.findall(font_pattern, html_content, re.IGNORECASE)
    font_links = re.findall(r'<link[^>]*href=["\']([^"\']*fonts[^"\']*)["\']', html_content, re.IGNORECASE)
    for font in fonts + font_links:
        full_url = urljoin(base_url, font)
        domain = urlparse(full_url).netloc
        if domain and domain not in urlparse(base_url).netloc:
            resources['external_fonts'].append({
                'url': full_url,
                'domain': domain
            })

    # 6. API calls in inline scripts
    api_patterns = [
        r'fetch\(["\']([^"\']+)["\']',
        r'axios\.(get|post)\(["\']([^"\']+)["\']',
        r'\$\.ajax\(["\']([^"\']+)["\']',
    ]
    for pattern in api_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            url = match if isinstance(match, str) else match[-1]  # Handle groups
            if url.startswith('http'):
                domain = urlparse(url).netloc
                resources['api_calls'].append({
                    'url': url,
                    'domain': domain
                })

    # Summarize unique external domains
    all_domains = set()
    for category, items in resources.items():
        for item in items:
            all_domains.add(item['domain'])

    logger.info(f"📊 Found {len(all_domains)} unique external domains:")
    logger.info(f"   Scripts: {len(resources['external_scripts'])}")
    logger.info(f"   Stylesheets: {len(resources['external_stylesheets'])}")
    logger.info(f"   Images: {len(resources['external_images'])}")
    logger.info(f"   Iframes: {len(resources['iframes'])}")
    logger.info(f"   Fonts: {len(resources['external_fonts'])}")

    return {
        'resources_by_type': dict(resources),
        'unique_domains': list(all_domains),
        'total_external_resources': sum(len(items) for items in resources.values())
    }
```

---

## 🎯 Quick Win #3: Privacy Policy Mining (30 minutes)

### Add to `main.py`:

```python
def find_privacy_policy_url(base_url: str) -> str:
    """
    Try to find privacy policy URL
    """
    from urllib.parse import urljoin

    common_paths = [
        "/privacy",
        "/privacy-policy",
        "/legal/privacy",
        "/privacy.html",
        "/en/privacy",
    ]

    for path in common_paths:
        try:
            url = urljoin(base_url, path)
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Found privacy policy: {url}")
                return url
        except:
            continue

    return None

def extract_data_transfer_info(privacy_text: str) -> dict:
    """
    Extract data transfer information from privacy policy
    """
    if not model:
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
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        logger.warning(f"⚠️ Privacy policy analysis failed: {e}")

    return {}
```

---

## 🎯 Quick Win #4: Category-Based Weighting (15 minutes)

### Add to `calculate_score` function (before line 827):

```python
# Service category weights
CATEGORY_WEIGHTS = {
    "AI/ML": 1.5,
    "Payment Processing": 1.4,
    "Database/Storage": 1.4,
    "Cloud Infrastructure": 1.4,
    "Authentication": 1.3,
    "Email Service": 1.2,
    "Customer Support": 1.2,
    "Analytics": 1.0,
    "Monitoring": 1.0,
    "CDN": 0.8,
    "Fonts": 0.7,
    "Tag Management": 1.1,
}

def get_category_weight(purpose: str) -> float:
    """
    Return weight multiplier based on vendor category
    """
    purpose_upper = purpose.upper()

    for category, weight in CATEGORY_WEIGHTS.items():
        if category.upper() in purpose_upper:
            return weight

    return 1.0  # Default weight
```

### Update vendor penalty calculation (line 1036):

```python
# Old code:
# score -= 12

# New code:
category_weight = get_category_weight(purpose)
base_penalty = 12
weighted_penalty = int(base_penalty * category_weight)
score -= weighted_penalty
deductions.append(f"-{weighted_penalty}: {vendor_name} is US-based ({purpose}, weight={category_weight})")
```

---

## 🎯 Quick Win #5: Better Gemini Prompts (15 minutes)

### Update the Gemini analysis prompt (line 675) to be more explicit:

```python
system_prompt = """You are a Data Sovereignty Auditor for the EU. I will give you text from a SaaS company's website (multiple pages including homepage, about, privacy policy, sub-processors, etc.).

CRITICAL INSTRUCTIONS:
1. Look for EXPLICIT mentions of services, vendors, and infrastructure
2. INFER services from context clues (e.g., "we use industry-leading email delivery" → likely SendGrid/Mailgun)
3. Check for hidden third-party services in:
   - Payment processing (Stripe, PayPal, etc.)
   - Analytics (Google Analytics, Mixpanel, etc.)
   - Support chat (Intercom, Zendesk, Crisp, etc.)
   - Email (SendGrid, Mailgun, AWS SES, etc.)
   - Monitoring (Datadog, Sentry, etc.)
   - AI services (OpenAI, Anthropic, etc.)

WHAT TO EXTRACT:

1. COMPANY INFORMATION:
   - Registration country/jurisdiction (where company is legally registered)
   - Legal entity name
   - Office locations (where they have offices)
   - Employee locations (where teams are based, especially engineering/data teams)
   - Look for: "incorporated in", "registered in", "headquarters in"

2. INFRASTRUCTURE:
   - Cloud provider (AWS, GCP, Azure, etc.)
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
   - Purpose/Category (choose from: Payment Processing, AI/ML, Customer Support, Email Service, Analytics, Monitoring, Cloud Infrastructure, Database/Storage, CDN, Authentication, SMS/Communications, Marketing, Tag Management, Other)
   - Processing Location (Country/Region where the vendor processes data)
   - Sovereignty Risk (Critical, High, Medium, Low)

Risk Assignment Rules (FOLLOW STRICTLY):
- IF Location is USA AND Purpose is (AI/ML OR Payment Processing OR Cloud Infrastructure OR Database/Storage) → Risk is CRITICAL
- IF Location is USA AND Purpose is (Customer Support OR Email Service OR Authentication) → Risk is HIGH
- IF Location is USA AND Purpose is (Analytics OR Monitoring OR Other) → Risk is HIGH
- IF Location is "Global" OR "Multiple regions" → Risk is MEDIUM (no EU guarantee)
- IF Location is EEA/EU country → Risk is LOW
- IF Location is Unknown → Risk is MEDIUM

5. COMPLIANCE:
   - GDPR compliance status
   - Certifications (SOC 2, ISO 27001, etc.)
   - Data residency guarantees
   - Recent security incidents or breaches
   - Look for: "GDPR compliant", "ISO 27001", "SOC 2", "data breach"

INFERENCE RULES:
- If they mention "payment processing" but no vendor → INFER likely Stripe (US, Critical)
- If they mention "analytics" but no vendor → INFER likely Google Analytics (US, High)
- If they mention "live chat" or "customer messaging" → INFER likely Intercom or Zendesk (US, High)
- If they mention "email delivery" → INFER likely SendGrid or Mailgun (US, High)
- If they mention "AI features" or "GPT" or "LLM" → INFER likely OpenAI (US, Critical)
- If they have a chat widget → INFER Intercom/Zendesk/Crisp
- If they mention "monitoring" or "observability" → INFER Datadog/New Relic (US, High)

Return ONLY valid JSON matching this EXACT schema:
{
  "vendors": [
    {
      "name": "string",
      "purpose": "Payment Processing|AI/ML|Customer Support|Email Service|Analytics|Monitoring|Cloud Infrastructure|Database/Storage|CDN|Authentication|SMS/Communications|Marketing|Tag Management|Other",
      "location": "string (country/region)",
      "risk": "Critical|High|Medium|Low"
    }
  ],
  "company_info": {
    "registration_country": "string",
    "legal_entity": "string",
    "office_locations": ["string"],
    "employee_locations": ["string"]
  },
  "infrastructure": {
    "cloud_provider": "string",
    "hosting_platform": "string",
    "data_centers": ["string"],
    "server_locations": ["string"],
    "cdn_providers": ["string"]
  },
  "data_flows": {
    "storage_locations": ["string"],
    "processing_locations": ["string"],
    "data_residency": "EU|US|Global|Unknown"
  },
  "compliance": {
    "gdpr_status": "string",
    "certifications": ["string"],
    "data_residency_guarantees": "string",
    "recent_incidents": ["string"]
  },
  "additional_categories": ["string"],
  "summary": "Comprehensive executive summary of sovereignty risk covering company jurisdiction, infrastructure, data flows, compliance, and sub-processors. Highlight critical US dependencies and GDPR concerns."
}"""
```

---

## 🎯 Implementation Order

1. **Start here** (5 minutes): Add enhanced Gemini prompt (#5)
2. **Next** (30 minutes): Add known services database (#1)
3. **Then** (1 hour): Add resource detection (#2)
4. **Finally** (30 minutes): Add privacy policy analysis (#3) + weighting (#4)

**Total time: ~2-3 hours for significant improvement**

---

## 📊 Expected Impact

- **Before**: Detecting ~5-10 vendors from sub-processor page
- **After**: Detecting ~20-40 services including hidden dependencies
- **Before**: Generic US vs EU categorization
- **After**: Specific service identification with alternatives
- **Before**: Single sovereignty score
- **After**: Multi-layered analysis with actionable recommendations

Start with these quick wins, then gradually add the more advanced features from the comprehensive guide!
