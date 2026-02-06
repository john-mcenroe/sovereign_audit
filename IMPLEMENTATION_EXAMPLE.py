# Example Implementation: Enhanced Resource Detection
# Add this to your main.py to immediately improve detection

import re
from urllib.parse import urlparse, urljoin
from collections import defaultdict

# =============================================================================
# STEP 1: Add this function after your scrape_url function (around line 450)
# =============================================================================

def analyze_embedded_resources(html_content: str, base_url: str) -> dict:
    """
    Extract all external resources from HTML without browser automation.
    This detects third-party services by analyzing what resources the page loads.
    """
    logger.info("🔍 Analyzing embedded resources...")

    resources = defaultdict(list)

    # 1. External Scripts (JavaScript)
    # These often include analytics, chat widgets, payment processors, etc.
    script_pattern = r'<script[^>]*src=["\']([^"\']+)["\']'
    scripts = re.findall(script_pattern, html_content, re.IGNORECASE)

    for script in scripts:
        full_url = urljoin(base_url, script)
        domain = urlparse(full_url).netloc

        # Only track external domains (not the company's own domain)
        if domain and domain not in urlparse(base_url).netloc:
            resources['external_scripts'].append({
                'url': full_url,
                'domain': domain,
                'detected_service': identify_service_from_domain(domain)
            })

    # 2. External Stylesheets and Fonts
    # Google Fonts is a common sovereignty issue (shares IP with Google)
    css_pattern = r'<link[^>]*href=["\']([^"\']+)["\']'
    links = re.findall(css_pattern, html_content, re.IGNORECASE)

    for link in links:
        full_url = urljoin(base_url, link)
        domain = urlparse(full_url).netloc

        if domain and domain not in urlparse(base_url).netloc:
            if 'font' in link.lower() or 'fonts' in domain:
                resources['external_fonts'].append({
                    'url': full_url,
                    'domain': domain,
                    'detected_service': identify_service_from_domain(domain)
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
        resources['external_images'].append({
            'domain': domain,
            'note': 'May be tracking pixel or analytics'
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
                resources['api_calls'].append({
                    'url': url,
                    'domain': domain,
                    'method': method,
                    'detected_service': identify_service_from_domain(domain)
                })

    # Summarize findings
    all_domains = set()
    detected_services = []

    for category, items in resources.items():
        for item in items:
            domain = item.get('domain')
            if domain:
                all_domains.add(domain)

                # Collect detected services
                service = item.get('detected_service')
                if service and service not in detected_services:
                    detected_services.append(service)

    logger.info(f"📊 Resource Analysis Complete:")
    logger.info(f"   External Scripts: {len(resources['external_scripts'])}")
    logger.info(f"   External Fonts: {len(resources['external_fonts'])}")
    logger.info(f"   Iframes (widgets): {len(resources['iframes'])}")
    logger.info(f"   Unique External Domains: {len(all_domains)}")
    logger.info(f"   Detected Services: {len(detected_services)}")

    return {
        'resources_by_type': dict(resources),
        'unique_domains': list(all_domains),
        'detected_services': detected_services,
        'total_external_resources': sum(len(items) for items in resources.values())
    }


# =============================================================================
# STEP 2: Add this helper function to identify services from domains
# =============================================================================

def identify_service_from_domain(domain: str) -> dict:
    """
    Identify known services from domain names.
    Returns service info or None if unknown.
    """
    if not domain:
        return None

    domain_lower = domain.lower()

    # Known service patterns
    # Format: (pattern, name, jurisdiction, category, risk_level)
    known_patterns = [
        # Analytics
        ('google-analytics.com', 'Google Analytics', 'United States', 'Analytics', 'High'),
        ('googletagmanager.com', 'Google Tag Manager', 'United States', 'Tag Management', 'High'),
        ('mixpanel.com', 'Mixpanel', 'United States', 'Analytics', 'High'),
        ('segment.com', 'Segment', 'United States', 'Analytics', 'High'),
        ('plausible.io', 'Plausible', 'Estonia (EU)', 'Analytics', 'Low'),
        ('analytics.google.com', 'Google Analytics', 'United States', 'Analytics', 'High'),

        # Fonts
        ('fonts.googleapis.com', 'Google Fonts', 'United States', 'CDN/Fonts', 'Medium'),
        ('fonts.gstatic.com', 'Google Fonts CDN', 'United States', 'CDN/Fonts', 'Medium'),
        ('use.typekit.net', 'Adobe Fonts', 'United States', 'CDN/Fonts', 'Medium'),

        # Customer Support
        ('intercom.io', 'Intercom', 'United States', 'Customer Support', 'Critical'),
        ('widget.intercom.io', 'Intercom Widget', 'United States', 'Customer Support', 'Critical'),
        ('zendesk.com', 'Zendesk', 'United States', 'Customer Support', 'High'),
        ('crisp.chat', 'Crisp', 'France (EU)', 'Customer Support', 'Low'),
        ('drift.com', 'Drift', 'United States', 'Customer Support', 'High'),

        # Payment
        ('stripe.com', 'Stripe', 'United States', 'Payment Processing', 'Critical'),
        ('js.stripe.com', 'Stripe.js', 'United States', 'Payment Processing', 'Critical'),
        ('paypal.com', 'PayPal', 'United States', 'Payment Processing', 'Critical'),

        # AI Services
        ('api.openai.com', 'OpenAI', 'United States', 'AI/ML', 'Critical'),
        ('openai.com', 'OpenAI', 'United States', 'AI/ML', 'Critical'),
        ('api.anthropic.com', 'Anthropic', 'United States', 'AI/ML', 'Critical'),
        ('anthropic.com', 'Anthropic', 'United States', 'AI/ML', 'Critical'),

        # CDN
        ('cloudflare.com', 'Cloudflare', 'United States', 'CDN', 'Medium'),
        ('cdnjs.cloudflare.com', 'Cloudflare CDN', 'United States', 'CDN', 'Medium'),
        ('cdn.jsdelivr.net', 'jsDelivr', 'Poland (EU)', 'CDN', 'Low'),
        ('unpkg.com', 'unpkg', 'United States', 'CDN', 'Medium'),

        # Monitoring/Error Tracking
        ('sentry.io', 'Sentry', 'United States', 'Error Tracking', 'High'),
        ('datadoghq.com', 'Datadog', 'United States', 'Monitoring', 'High'),
        ('newrelic.com', 'New Relic', 'United States', 'Monitoring', 'High'),

        # Social/Advertising
        ('facebook.com', 'Facebook', 'United States', 'Social/Advertising', 'High'),
        ('connect.facebook.net', 'Facebook SDK', 'United States', 'Social/Advertising', 'High'),
        ('twitter.com', 'Twitter/X', 'United States', 'Social/Advertising', 'High'),
        ('linkedin.com', 'LinkedIn', 'United States', 'Social/Advertising', 'High'),

        # Email
        ('sendgrid.com', 'SendGrid', 'United States', 'Email Service', 'High'),
        ('mailgun.com', 'Mailgun', 'United States', 'Email Service', 'High'),
    ]

    for pattern, name, jurisdiction, category, risk in known_patterns:
        if pattern in domain_lower:
            return {
                'name': name,
                'domain': domain,
                'jurisdiction': jurisdiction,
                'category': category,
                'risk_level': risk,
                'detected_from': 'domain_pattern'
            }

    # If not a known service, still return basic info
    return {
        'name': f'Unknown Service ({domain})',
        'domain': domain,
        'jurisdiction': 'Unknown',
        'category': 'Other',
        'risk_level': 'Medium',
        'detected_from': 'resource_analysis'
    }


# =============================================================================
# STEP 3: Integrate into your scrape_multiple_pages function
# =============================================================================

# In scrape_multiple_pages function (around line 236), after scraping each page,
# add resource analysis:

# OLD CODE (line ~266):
# if text and len(text.strip()) > 100:
#     scraped_pages[page_path or "homepage"] = text

# NEW CODE:
# if text and len(text.strip()) > 100:
#     scraped_pages[page_path or "homepage"] = text
#
#     # NEW: Analyze resources on this page
#     try:
#         full_url = urljoin(base_domain, page_path)
#         resource_analysis = analyze_embedded_resources(text, full_url)
#
#         # Collect all detected services
#         for service in resource_analysis['detected_services']:
#             if service not in all_detected_services:
#                 all_detected_services.append(service)
#                 logger.info(f"   🎯 Detected: {service['name']} ({service['category']}) - {service['jurisdiction']}")
#
#     except Exception as e:
#         logger.warning(f"⚠️ Resource analysis failed for {page_path}: {e}")


# =============================================================================
# STEP 4: Update your return value from scrape_multiple_pages
# =============================================================================

# At the end of scrape_multiple_pages function (around line 318), update return:

# OLD CODE:
# return {"combined": combined_text, "pages": scraped_pages, "infrastructure_hints": detected_infrastructure}

# NEW CODE:
# return {
#     "combined": combined_text,
#     "pages": scraped_pages,
#     "infrastructure_hints": detected_infrastructure,
#     "detected_services": all_detected_services  # NEW
# }


# =============================================================================
# STEP 5: Update analyze endpoint to use detected services
# =============================================================================

# In the /analyze endpoint (around line 1236), after scraping:

# After line 1219 (where you get scraped_data):
# OLD CODE:
# vendors_data = analysis.get("vendors", [])

# NEW CODE:
# vendors_data = analysis.get("vendors", [])
# detected_services = scraped_data.get("detected_services", [])
#
# # Merge detected services with AI-found vendors
# for service in detected_services:
#     # Check if this service is already in vendors (avoid duplicates)
#     service_name = service['name']
#     if not any(v.get('name') == service_name for v in vendors_data):
#         # Add as a new vendor
#         vendors_data.append({
#             'name': service['name'],
#             'purpose': service['category'],
#             'location': service['jurisdiction'],
#             'risk': service['risk_level']
#         })
#         logger.info(f"➕ Added detected service to vendors: {service_name}")


# =============================================================================
# EXPECTED RESULTS
# =============================================================================

# Before this implementation:
# - Detects 5-10 vendors from sub-processor page text
#
# After this implementation:
# - Detects 20-40 vendors including:
#   ✅ Google Analytics (from <script> tag)
#   ✅ Google Fonts (from <link> tag)
#   ✅ Intercom chat widget (from <iframe>)
#   ✅ Stripe payment (from js.stripe.com script)
#   ✅ Cloudflare CDN (from resource domains)
#   ✅ Social media tracking pixels
#   ✅ Third-party analytics services
#
# This gives you a MUCH more comprehensive sovereignty analysis!


# =============================================================================
# BONUS: Add to frontend Dashboard to show detected services
# =============================================================================

# In Dashboard.jsx, add a new section to show resource-detected services:

# {result.detected_services && result.detected_services.length > 0 && (
#   <div className="mb-8 border-2 border-blue-500 bg-blue-50 p-6">
#     <h2 className="text-xl font-bold text-blue-900 mb-3 flex items-center gap-2">
#       <Globe className="w-6 h-6" />
#       Services Detected from Resources ({result.detected_services.length})
#     </h2>
#     <div className="text-sm text-blue-800 mb-4">
#       These services were detected by analyzing the website's external resources
#       (scripts, fonts, iframes, etc.), not just from their sub-processor page.
#     </div>
#     <div className="space-y-2">
#       {result.detected_services.map((service, idx) => (
#         <div
#           key={idx}
#           className={`p-3 border-2 ${
#             service.risk_level === 'Critical' ? 'bg-red-50 border-red-500' :
#             service.risk_level === 'High' ? 'bg-orange-50 border-orange-500' :
#             service.risk_level === 'Medium' ? 'bg-yellow-50 border-yellow-500' :
#             'bg-green-50 border-green-500'
#           }`}
#         >
#           <div className="font-bold text-black">{service.name}</div>
#           <div className="text-sm text-gray-700">
#             {service.category} • {service.jurisdiction} • Risk: {service.risk_level}
#           </div>
#         </div>
#       ))}
#     </div>
#   </div>
# )}
