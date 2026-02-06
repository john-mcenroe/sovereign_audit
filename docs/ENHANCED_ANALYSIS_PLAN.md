# Enhanced Sovereignty Analysis - Implementation Plan

## Current Scope
Currently analyzing: **Sub-processor lists only**

## Proposed Enhanced Scope

### 1. Company Registration & Legal Entity
**What to check:**
- Company registration country/jurisdiction
- Legal entity structure (incorporated in US, EU, etc.)
- Parent company location
- Subsidiary locations

**Where to find:**
- `/about` page
- `/legal` or `/terms` pages
- Footer of website (often shows "Company Inc. registered in...")
- Privacy policy (legal entity info)
- Investor relations pages

**Scoring impact:**
- US-registered company = higher risk
- EU-registered company = lower risk
- Multi-jurisdictional = medium risk

### 2. Cloud Infrastructure & Hosting
**What to check:**
- Primary cloud provider (AWS, GCP, Azure, etc.)
- Data center regions/locations
- Server locations
- CDN providers and locations
- Database hosting locations

**Where to find:**
- Infrastructure/technology pages
- Security/compliance pages
- Job postings (often mention tech stack)
- Status pages (often show infrastructure)
- Privacy policy (data storage locations)

**Scoring impact:**
- US data centers = high risk
- EU data centers = low risk
- Global/multi-region = medium risk

### 3. Employee Locations & Operations
**What to check:**
- Office locations
- Employee distribution by country
- Where engineering/data teams are located
- Support team locations

**Where to find:**
- `/about` or `/company` pages
- `/careers` or `/jobs` pages
- Office location pages
- Team pages
- LinkedIn company page (if accessible)

**Scoring impact:**
- US-based engineering teams = higher risk (data access)
- EU-based teams = lower risk
- Mixed locations = medium risk

### 4. Data Processing & Storage Locations
**What to check:**
- Where customer data is stored
- Where data is processed
- Data residency guarantees
- Data transfer mechanisms (SCCs, etc.)
- Backup locations

**Where to find:**
- Privacy policy (most detailed)
- Data processing agreements (DPAs)
- Security/compliance pages
- GDPR compliance pages
- Terms of service

**Scoring impact:**
- Data stored in US = critical risk
- Data stored in EU = low risk
- Data transfer to US = high risk

### 5. Third-Party Services & Integrations
**What to check:**
- Analytics providers (Google Analytics, etc.)
- Customer support tools (Intercom, Zendesk)
- Payment processors (Stripe, PayPal)
- Marketing tools (Mailchimp, HubSpot)
- Authentication providers (Auth0, Okta)

**Where to find:**
- Sub-processor lists (current focus)
- Privacy policy
- Cookie policies
- Integration pages

**Scoring impact:**
- US-based services = risk points
- EU-based services = no penalty

## Implementation Strategy

### Phase 1: Multi-Page Scraping
Instead of just scraping sub-processor page, scrape multiple pages:
1. Main domain (homepage)
2. `/about` or `/company`
3. `/legal/subprocessors` (current)
4. `/privacy` or `/privacy-policy`
5. `/security` or `/compliance` (if exists)
6. `/careers` (for office locations)

### Phase 2: Enhanced AI Prompt
Update Gemini prompt to extract:
- Company registration info
- Infrastructure details
- Office/employee locations
- Data storage locations
- All sub-processors (current)

### Phase 3: Additional Data Sources
- DNS/WHOIS lookup (company registration)
- IP geolocation (server locations)
- Public APIs (if available)

### Phase 4: Enhanced Scoring
Update scoring algorithm to consider:
- Company jurisdiction
- Infrastructure locations
- Employee locations
- Data storage locations
- Sub-processors (current)

## Technical Implementation

### New Data Model
```python
class CompanyInfo(BaseModel):
    registration_country: str
    legal_entity: str
    office_locations: list[str]
    employee_locations: list[str]

class InfrastructureInfo(BaseModel):
    cloud_provider: str
    data_centers: list[str]
    server_locations: list[str]
    cdn_providers: list[str]

class DataFlowInfo(BaseModel):
    storage_locations: list[str]
    processing_locations: list[str]
    backup_locations: list[str]
    data_residency: str  # "EU", "US", "Global", "Unknown"
```

### Enhanced Response
```python
class EnhancedAnalyzeResponse(BaseModel):
    score: int
    risk_level: str
    summary: str
    vendors: list[Vendor]
    company_info: CompanyInfo
    infrastructure: InfrastructureInfo
    data_flows: DataFlowInfo
    risk_factors: list[str]  # List of specific risks found
```

## Quick Wins (Easy to Implement)

1. **Scrape multiple pages** - Already have scraping infrastructure
2. **Enhanced AI prompt** - Just update the prompt text
3. **Extract company info** - Add to AI extraction
4. **Better scoring** - Add penalties for company location, infrastructure

## Future Enhancements

1. **WHOIS lookup** - Get domain registration info
2. **IP geolocation** - Check where servers actually are
3. **Certificate transparency** - See what domains they use
4. **Public compliance reports** - SOC2, ISO27001 locations
5. **API integrations** - Company data APIs, DNS APIs
