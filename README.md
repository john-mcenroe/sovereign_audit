# Sovereign Scan MVP

A web application that analyzes SaaS sub-processor pages for data sovereignty risks using AI.

## Project Structure

```
sovereign_audit/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Hero.jsx
    │   │   ├── Loading.jsx
    │   │   └── Dashboard.jsx
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── index.css
    ├── package.json
    ├── vite.config.js
    └── tailwind.config.js
```

## Setup

### Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

5. Add your Gemini API key to `.env`:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

6. Run the backend server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173` (or the port Vite assigns).

## Usage

1. Start both the backend and frontend servers.
2. Open the frontend URL in your browser.
3. Enter a SaaS sub-processor page URL (e.g., `https://www.intercom.com/legal/subprocessors`).
4. Click "Run Audit" to analyze the page.
5. View the sovereignty score and vendor analysis in the dashboard.

## API Endpoint

### POST /analyze

Analyzes a URL for data sovereignty risks.

**Request:**
```json
{
  "url": "https://example.com/subprocessors"
}
```

**Response:**
```json
{
  "score": 65,
  "risk_level": "High",
  "summary": "This company relies heavily on US infrastructure...",
  "vendors": [
    {
      "name": "OpenAI",
      "purpose": "AI Inference",
      "location": "United States",
      "risk": "Critical"
    }
  ]
}
```

## Scoring Algorithm

- Starts at 100 points
- -10 points for every US-based vendor
- -20 points for high-risk AI vendors (OpenAI, Anthropic)
- -5 points for "Global" location
- Risk levels:
  - High: < 70
  - Medium: 70-89
  - Low: 90+

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

**Quick deploy**: Railway (Backend) + Vercel (Frontend)

1. Deploy backend to Railway, set `GEMINI_API_KEY` environment variable
2. Deploy frontend to Vercel, set `VITE_API_URL` to your Railway backend URL
3. Update backend `FRONTEND_URLS` to include your Vercel domain

Full instructions and alternative platforms available in [DEPLOYMENT.md](./DEPLOYMENT.md).
