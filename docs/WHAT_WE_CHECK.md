# What We Check - Enhanced Sovereignty Analysis

## Overview

The application now performs a **comprehensive multi-page analysis** of SaaS companies to assess data sovereignty risks. Instead of just checking sub-processor lists, we analyze the entire company's infrastructure, operations, and data handling.

## What Gets Checked

### 1. 🌐 Multi-Page Scraping

The app automatically scrapes multiple pages from the target website:

- **Homepage** (`/`) - General company info
- **About/Company** (`/about`, `/company`) - Company details, office locations
- **Privacy Policy** (`/privacy`, `/privacy-policy`) - Data handling, storage locations
- **Sub-processors** (`/legal/subprocessors`) - Third-party vendors
- **Security** (`/security`, `/compliance`) - Infrastructure details
- **Careers** (`/careers`, `/jobs`) - Office locations, employee distribution

**Why:** Different pages contain different types of information. Combining them gives a complete picture.

---

### 2. 🏢 Company Information

**What we extract:**
- **Registration Country**: Where the company is legally registered (US, EU, etc.)
- **Legal Entity**: Company name and structure
- **Office Locations**: Physical offices around the world
- **Employee Locations**: Where teams are based (especially engineering/data teams)

**Why it matters:**
- US-registered companies = Higher sovereignty risk
- EU-registered companies = Lower risk
- Employee locations matter because US-based engineers can access EU data

**Scoring:**
- US registration: **-15 points**
- US offices/employees: **-5 points**
- EU registration: **+5 points** (bonus)

---

### 3. ☁️ Infrastructure & Hosting

**What we extract:**
- **Cloud Provider**: AWS, Google Cloud, Azure, etc.
- **Data Center Locations**: Where servers are physically located
- **Server Locations**: Geographic regions
- **CDN Providers**: Content delivery networks and their locations

**Why it matters:**
- US cloud providers without EU regions = High risk
- Data centers in US = Data sovereignty risk
- EU data centers = Lower risk

**Scoring:**
- US cloud provider (no EU regions): **-20 points**
- US cloud provider (with EU regions): **-5 points**
- US data centers: **-10 points each**

---

### 4. 💾 Data Storage & Processing

**What we extract:**
- **Storage Locations**: Where customer data is stored (countries/regions)
- **Processing Locations**: Where data is processed
- **Data Residency**: Explicit guarantees (EU-only, US, Global, etc.)
- **Backup Locations**: Where backups are stored

**Why it matters:**
- Data stored in US = Critical sovereignty risk
- Data processed in US = High risk
- EU-only data residency = Best case

**Scoring:**
- Data stored in US: **-15 points per location**
- Data processed in US: **-10 points per location**
- US data residency: **-20 points**
- Global data residency: **-10 points**
- EU-only data residency: **+10 points** (bonus)

---

### 5. 🔗 Sub-Processors (Third-Party Vendors)

**What we extract:**
- **Vendor Name**: Company name
- **Purpose**: What they do (Hosting, AI, Support, Analytics, Payment, etc.)
- **Location**: Where they're based/operate
- **Risk Level**: Critical, High, Medium, Low

**Why it matters:**
- US-based vendors = Data sovereignty risk
- AI vendors in US = Critical risk
- Hosting vendors in US = Critical risk

**Scoring:**
- US-based vendor: **-10 points**
- US-based AI/Hosting vendor: **-20 points** (total)
- High-risk AI vendors (OpenAI, Anthropic): **-20 points**
- Global location: **-5 points**

---

## Enhanced Scoring Algorithm

**Starting Score:** 100 points (perfect compliance)

**Deductions:**
1. Company registration in US: -15
2. US cloud infrastructure: -5 to -20
3. US data storage: -15 per location
4. US data processing: -10 per location
5. US employees/offices: -5
6. US sub-processors: -10 each
7. US AI/Hosting vendors: -20 each
8. High-risk AI vendors: -20 each

**Bonuses:**
- EU registration: +5
- EU-only data residency: +10

**Final Risk Levels:**
- **High Risk**: < 70 points
- **Medium Risk**: 70-89 points
- **Low Risk**: 90+ points

---

## What You'll See in Results

### Dashboard Sections:

1. **Sovereignty Score** - Overall risk score (0-100)
2. **Risk Factors** - List of specific risks found
3. **Company Information** - Registration, offices, employees
4. **Infrastructure** - Cloud provider, data centers, servers
5. **Data Storage & Processing** - Where data goes
6. **Sub-Processors** - Third-party vendors table

### Color Coding:

- **Red**: US-based (high risk)
- **Green**: EU-based (low risk)
- **Yellow**: Global/Unknown (medium risk)

---

## Example Analysis Flow

For a company like "Example SaaS Inc":

1. **Scrapes**: homepage, /about, /privacy, /legal/subprocessors
2. **Finds**: 
   - Registered in Delaware, USA
   - Uses AWS (US cloud provider)
   - Data centers in US-East and EU-West
   - Offices in San Francisco and Berlin
   - 15 sub-processors (10 US-based, 5 EU-based)
3. **Calculates**:
   - -15 (US registration)
   - -5 (AWS with EU regions)
   - -100 (10 US vendors × 10 points)
   - = **Score: 80** (Medium Risk)
4. **Shows**: All this information in organized sections

---

## Limitations & Future Enhancements

**Current Limitations:**
- Relies on publicly available information
- Some companies don't publish all details
- JavaScript-heavy sites may not be fully scraped
- Can't verify claims (just reports what's stated)

**Future Enhancements:**
- WHOIS lookup for domain registration
- IP geolocation for actual server locations
- Certificate transparency logs
- Public compliance reports (SOC2, ISO27001)
- API integrations for company data

---

## How to Use

1. Enter any SaaS company's website URL
2. The app will automatically:
   - Scrape multiple pages
   - Extract comprehensive information
   - Analyze with AI
   - Calculate sovereignty score
3. Review the detailed dashboard showing:
   - What cloud they use
   - Where they're registered
   - Where data is stored
   - All sub-processors
   - Specific risk factors

This gives you a **complete picture** of a company's data sovereignty posture, not just their sub-processor list!
