# Web Search Enhancement with Gemini

## Overview

The Sovereign Audit application now uses **Gemini's Google Search grounding** capability to discover additional information about companies beyond what's available on their websites. This significantly enhances the analysis by finding:

- Recent infrastructure announcements
- Compliance certifications and audit reports
- Security incidents and data breaches
- Office locations and expansions
- Corporate structure changes
- Additional risk factors

## How It Works

### 1. **Multi-Page Scraping** (Step 1)
The application scrapes multiple pages from the company's website:
- Homepage
- `/about`
- `/privacy`
- `/legal/subprocessors`
- `/security`
- `/careers`

### 2. **AI Analysis of Website Content** (Step 2)
Gemini analyzes the scraped content to extract:
- Company registration and legal info
- Infrastructure details
- Data flows and storage locations
- Sub-processors
- Compliance information

### 3. **Web Search Discovery** (Step 3) ⭐ NEW
Gemini with Google Search grounding searches the web for:
- **Company Registration & Legal Info:**
  - Legal entity name and registration country
  - Parent company or subsidiary information
  - Recent corporate structure changes

- **Infrastructure & Technology:**
  - Cloud provider usage (AWS, GCP, Azure)
  - Data center locations and regions
  - Recent infrastructure announcements or migrations
  - CDN and edge network providers

- **Data Processing & Compliance:**
  - GDPR compliance status
  - SOC 2, ISO 27001 certifications
  - Data residency guarantees
  - Recent data breaches or security incidents
  - Compliance certifications and audit reports

- **Operations & Employees:**
  - Office locations worldwide
  - Engineering team locations
  - Data team locations
  - Recent office openings/closings

- **Additional Risk Factors:**
  - Recent regulatory actions
  - Privacy policy changes
  - Data sovereignty commitments
  - EU-specific offerings or data centers

### 4. **Data Merging** (Step 3)
The web search findings are intelligently merged with website-scraped data:
- Search results take precedence for accuracy (more up-to-date)
- Website data fills gaps where search didn't find information
- Both sources contribute to a comprehensive analysis

### 5. **Score Calculation** (Step 4)
The enhanced scoring algorithm considers:
- Company jurisdiction (registration country)
- Infrastructure locations (cloud providers, data centers)
- Data storage and processing locations
- Employee/office locations
- Sub-processors and their risks
- Compliance status
- Recent security incidents

### 6. **Results Display** (Step 5)
The dashboard now shows:
- **Compliance & Certifications** section with GDPR status, certifications, and recent incidents
- **Additional Findings (Web Search)** section with search summary and discovered categories
- Enhanced risk factors that include compliance-related issues

## Technical Implementation

### Gemini Model Configuration

The application automatically enables Google Search grounding when using Gemini 1.5 models:

```python
if '1.5' in model_to_use:
    model = genai.GenerativeModel(
        model_to_use,
        tools=[{"google_search_retrieval": {}}]
    )
```

### Search Function

The `search_company_info_with_gemini()` function:
1. Extracts company name from URL
2. Constructs a comprehensive search prompt
3. Uses Gemini with Google Search to find information
4. Parses JSON response with additional findings
5. Returns structured data for merging

### Error Handling

- If Google Search is unavailable, the application continues with website data only
- Search failures are logged but don't block the analysis
- The application gracefully degrades to website-only analysis

## Benefits

1. **More Accurate Information**: Web search finds recent announcements and changes not yet reflected on company websites
2. **Comprehensive Coverage**: Discovers information from multiple sources (news, press releases, compliance reports)
3. **Real-Time Data**: Google Search provides current information beyond the model's training cutoff
4. **Risk Discovery**: Identifies recent security incidents, regulatory actions, and compliance issues
5. **Expanded Categories**: Automatically discovers additional analysis categories relevant to data sovereignty

## Frontend Updates

The loading component now shows 5 steps instead of 4:
1. Scraping multiple pages
2. Extracting information
3. **AI Analysis** (website content)
4. **Web Search Discovery** ⭐ NEW
5. Calculating sovereignty score

The dashboard displays:
- Compliance section with certifications and GDPR status
- Additional Findings section with web search summary
- Enhanced risk factors including compliance issues

## Future Enhancements

Potential improvements:
- Caching search results to reduce API calls
- Configurable search depth (shallow vs. deep analysis)
- Citation links from search results
- Search result confidence scores
- Multi-language search support
