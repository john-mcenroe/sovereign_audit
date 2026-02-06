# 🧪 Testing Guide: Verify Your New Features

## Quick Test Checklist

Use this guide to verify all new features are working correctly.

---

## ✅ **Pre-Test Setup**

### 1. Start Backend
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Open Browser
Navigate to: http://localhost:5173

---

## 🧪 **Test Case 1: Known Service Detection**

### **Test URL:** `https://www.intercom.com`

**Expected Results:**
- ✅ Detects **Intercom** from sub-processors page
- ✅ Detects **Google Fonts** from embedded `<link>` tags
- ✅ Detects **Google Analytics** from `<script>` tags
- ✅ Detects **Stripe** if they use it for payments
- ✅ Shows "Detected Services" section in purple box
- ✅ Each service shows:
  - Risk level (Critical/High/Medium/Low)
  - Jurisdiction (e.g., "United States")
  - Category (e.g., "Customer Support", "CDN/Fonts")
  - EU Alternatives (e.g., "Crisp (France)")

**How to Verify:**
1. Enter: `https://www.intercom.com/legal/subprocessors`
2. Click "Run Audit"
3. Scroll to "Detected Services from Resources" section
4. Should see multiple services listed

---

## 🧪 **Test Case 2: Category Weighting**

### **Test URL:** `https://openai.com` or any site using OpenAI

**Expected Results:**
- ✅ **OpenAI** vendor gets **Critical** risk (not just High)
- ✅ Score penalty is **weighted** (AI/ML = 1.5x multiplier)
- ✅ Deduction shows weight: `-18: OpenAI is US-based (AI/ML, weight=1.5)`
- ✅ Risk factors list: "US-based critical service: OpenAI (AI/ML)"

**How to Verify:**
1. Check the scoring logs in backend terminal
2. Look for lines like: `-18: OpenAI is US-based (AI/ML, weight=1.5)`
3. Compare to non-critical services (should be -8 to -12)

---

## 🧪 **Test Case 3: Resource Detection**

### **Test URL:** `https://www.stripe.com`

**Expected Results:**
- ✅ Detects external scripts loaded
- ✅ Detects fonts (if using Google Fonts)
- ✅ Detects analytics services
- ✅ Backend logs show:
  ```
  📊 Resource Analysis Complete:
     External Scripts: X
     External Fonts: Y
     Iframes (widgets): Z
     Unique External Domains: N
     Detected Services: M
  ```

**How to Verify:**
1. Check backend terminal during analysis
2. Look for "🔍 Analyzing embedded resources..."
3. Should see detected services logged: "🎯 Detected: Google Analytics..."

---

## 🧪 **Test Case 4: Enhanced Gemini Inference**

### **Test URL:** `https://www.notion.so` or similar

**Expected Results:**
- ✅ Infers services even if not explicitly listed
- ✅ If they mention "payment processing" → infers Stripe
- ✅ If they mention "analytics" → infers Google Analytics
- ✅ If they mention "chat" or "support" → infers Intercom/Zendesk
- ✅ More vendors detected than before

**How to Verify:**
1. Compare vendor count before/after implementation
2. Check if inferred vendors appear in results
3. Look for vendors not explicitly on sub-processors page

---

## 🧪 **Test Case 5: Service Merging**

### **Test URL:** Any URL with both sub-processors page AND embedded services

**Expected Results:**
- ✅ AI-detected vendors appear in "Sub-Processors" table
- ✅ Resource-detected services appear in "Detected Services" section
- ✅ No duplicates (same service not listed twice)
- ✅ Backend logs show:
  ```
  📊 Merging detected services: AI found X vendors, resource analysis found Y services
  ➕ Added detected service to vendors: Google Fonts (CDN/Fonts)
  📊 Total vendors after merging: Z
  ```

**How to Verify:**
1. Count vendors in "Sub-Processors" table
2. Count services in "Detected Services" section
3. Check for duplicates (e.g., Google Analytics in both)
4. Total should be AI + Resource - Duplicates

---

## 🧪 **Test Case 6: UI Display**

### **Test URL:** Any URL

**Expected Results:**
- ✅ New purple section: "Detected Services from Resources"
- ✅ Each service card has:
  - Color-coded border (Red/Orange/Yellow/Green)
  - Service name in bold
  - Domain shown
  - Risk level badge in top-right
  - Category and Jurisdiction in grid
  - Notes (if applicable)
  - EU Alternatives (if applicable)
- ✅ Explanation text: "These services were automatically detected..."

**How to Verify:**
1. Run any analysis
2. Scroll to detected services section
3. Verify visual styling matches description

---

## 🧪 **Test Case 7: Known Services Database**

### **Verify Database Loading:**

```bash
cd backend
python3 << 'EOF'
import json
with open('known_services.json', 'r') as f:
    db = json.load(f)
total = sum(len(services) for services in db.values())
print(f"✅ Loaded {total} services from database")
print(f"Categories: {', '.join(db.keys())}")
for category, services in db.items():
    print(f"  - {category}: {len(services)} services")
EOF
```

**Expected Output:**
```
✅ Loaded 90+ services from database
Categories: analytics, fonts, customer_support, payment, email, monitoring, cdn, ai_services, tag_management, social_auth, communication, storage, marketing, ab_testing
  - analytics: 7 services
  - fonts: 4 services
  - customer_support: 6 services
  ...
```

---

## 🐛 **Common Issues & Fixes**

### **Issue 1: "known_services.json not found"**

**Fix:**
```bash
# Verify file exists
ls backend/known_services.json

# If missing, it was created in this session - restart backend
cd backend
# Kill and restart uvicorn
```

### **Issue 2: No detected services shown**

**Possible causes:**
1. Website uses inline scripts (no external `<script src=...>`)
2. Website blocks scraping
3. Resource analysis failed silently

**Fix:**
- Check backend logs for "🔍 Analyzing embedded resources..."
- Try a different URL (e.g., intercom.com, stripe.com)
- Verify scraping succeeded (check for "✅ Successfully scraped")

### **Issue 3: Duplicate services**

**This is normal!**
- Some services appear in both sections intentionally
- Shows: what they SAY (sub-processors) vs what they USE (detected)

### **Issue 4: Wrong jurisdiction**

**Fix:**
- Edit `backend/known_services.json`
- Find the service and update jurisdiction
- Restart backend

---

## 📊 **Performance Benchmarks**

### **Expected Analysis Times:**

- **Simple site (1-2 pages):** 5-10 seconds
- **Medium site (5-7 pages):** 15-25 seconds
- **Complex site (10+ pages):** 30-45 seconds

### **Detection Rates:**

- **Before implementation:** 5-10 vendors
- **After implementation:** 20-50+ services
- **Improvement:** 3-5x more comprehensive

---

## ✅ **Success Criteria**

Your implementation is successful if:

1. ✅ Backend starts without errors
2. ✅ known_services.json loads (check logs for "✅ Loaded X services")
3. ✅ Resource analysis runs (logs show "🔍 Analyzing embedded resources...")
4. ✅ Services are detected (logs show "🎯 Detected: Service Name...")
5. ✅ Services appear in purple "Detected Services" section
6. ✅ Weighted scoring applies (logs show "weight=X.X")
7. ✅ More vendors detected than before (3-5x increase)
8. ✅ EU alternatives shown for US services
9. ✅ No errors in browser console
10. ✅ UI renders correctly with new section

---

## 🎯 **Recommended Test Sequence**

**Phase 1: Basic Functionality**
1. Test with `intercom.com` (known to use many services)
2. Verify detected services appear
3. Check for Google Fonts, Analytics detection

**Phase 2: Edge Cases**
1. Test with a simple site (minimal services)
2. Test with a complex SaaS (many services)
3. Test with non-English site

**Phase 3: Scoring Verification**
1. Compare scores before/after for same URL
2. Verify category weighting applies
3. Check critical services get higher penalties

**Phase 4: UI Verification**
1. Check all visual elements render
2. Verify color coding is correct
3. Test on different screen sizes

---

## 📝 **Test Results Template**

```markdown
## Test Results

**Date:** 2026-02-06
**Tester:** [Your Name]

### Test 1: Known Service Detection
- URL Tested: https://www.intercom.com/legal/subprocessors
- Services Detected: 12
- Expected Services Found: ✅ Google Fonts, ✅ Google Analytics, ✅ Stripe
- Status: ✅ PASS / ❌ FAIL

### Test 2: Category Weighting
- Weighted Penalties Applied: ✅ Yes / ❌ No
- Logs Show Weights: ✅ Yes / ❌ No
- Status: ✅ PASS / ❌ FAIL

### Test 3: Resource Detection
- Resources Analyzed: ✅ Yes / ❌ No
- External Domains Found: X
- Status: ✅ PASS / ❌ FAIL

### Overall Status: ✅ ALL TESTS PASSED
```

---

## 🚀 **Ready to Deploy?**

Once all tests pass:

1. ✅ Commit changes to git
2. ✅ Update documentation
3. ✅ Deploy to production
4. ✅ Monitor initial results
5. ✅ Gather user feedback

**Congratulations! Your comprehensive sovereignty scanner is ready! 🎉**
