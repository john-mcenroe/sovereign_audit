import { useState } from 'react'
import Hero from './components/Hero'
import Loading from './components/Loading'
import Dashboard from './components/Dashboard'
import { API_URL } from './config'
import { normalizeUrl } from './utils/urlNormalizer'

function App() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [currentUrl, setCurrentUrl] = useState(null)
  const [currentStep, setCurrentStep] = useState(0)

  const handleAnalyze = async (url) => {
    console.log('='.repeat(80))
    console.log('🚀 FRONTEND: Starting analysis request')
    
    // Normalize URL as a safety check (should already be normalized from Hero component)
    const normalizedUrl = normalizeUrl(url)
    if (normalizedUrl !== url) {
      console.log(`🔗 URL normalized: "${url}" -> "${normalizedUrl}"`)
    }
    
    console.log(`📋 URL to analyze: ${normalizedUrl}`)
    console.log(`🌐 API URL: ${API_URL}`)
    console.log(`⏰ Timestamp: ${new Date().toISOString()}`)
    
    setLoading(true)
    setError(null)
    setResult(null)
    setCurrentUrl(normalizedUrl)
    setCurrentStep(0)

    try {
      console.log(`📤 Step 1: Preparing request...`)
      const requestBody = { url: normalizedUrl }
      console.log(`📦 Request body:`, JSON.stringify(requestBody, null, 2))
      
      // Step 0: Connecting
      setCurrentStep(0)
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // Step 1: Scraping
      setCurrentStep(1)
      console.log(`🔄 Step 1: Scraping URL...`)
      
      // Add timeout to prevent hanging forever
      const controller = new AbortController()
      const timeoutId = setTimeout(() => {
        console.error(`⏱️ TIMEOUT: Request exceeded 60 seconds, aborting...`)
        controller.abort()
      }, 60000) // 60 second timeout
      
      const baseUrl = API_URL.replace(/\/+$/, '')
      const analyzeUrl = `${baseUrl}/analyze`
      const fetchStartTime = Date.now()
      console.log(`📡 Sending POST request to ${analyzeUrl}...`)
      
      const response = await fetch(analyzeUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal,
      })
      
      const fetchDuration = Date.now() - fetchStartTime
      clearTimeout(timeoutId)
      
      console.log(`📥 Response received after ${fetchDuration}ms`)
      console.log(`📊 Response status: ${response.status} ${response.statusText}`)
      console.log(`📋 Response headers:`, Object.fromEntries(response.headers.entries()))

      if (!response.ok) {
        console.error(`❌ Response not OK: ${response.status}`)
        let errorMessage = 'Failed to analyze URL'
        let errorDetails = null
        
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorMessage
          errorDetails = errorData
          console.error(`❌ API Error Response:`, JSON.stringify(errorData, null, 2))
        } catch (parseError) {
          console.error(`❌ Failed to parse error response as JSON:`, parseError)
          const text = await response.text()
          errorMessage = `HTTP ${response.status}: ${text || 'Unknown error'}`
          console.error(`❌ Error response text:`, text)
        }
        throw new Error(errorMessage)
      }

      // Step 2: AI Analysis (backend is doing this, but we show it here)
      console.log(`✅ Response OK, parsing JSON...`)
      setCurrentStep(2)
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // Step 3: Web Search (backend is doing this)
      setCurrentStep(3)
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const data = await response.json()
      console.log(`✅ Analysis complete!`)
      console.log(`📊 Result data:`, JSON.stringify(data, null, 2))
      console.log(`📈 Score: ${data.score}, Risk: ${data.risk_level}`)
      console.log(`📋 Vendors found: ${data.vendors?.length || 0}`)
      console.log(`🔍 Additional findings: ${data.additional_findings ? 'Yes' : 'No'}`)
      
      // Step 4: Calculating score (already done, but show completion)
      setCurrentStep(4)
      await new Promise(resolve => setTimeout(resolve, 800))
      
      console.log(`🎉 Setting result state...`)
      setResult(data)
      console.log('='.repeat(80))
    } catch (err) {
      console.error('='.repeat(80))
      console.error(`❌ FRONTEND ERROR CAUGHT`)
      console.error(`   Error name: ${err.name}`)
      console.error(`   Error message: ${err.message}`)
      console.error(`   Error stack:`, err.stack)
      console.error(`   Full error object:`, err)
      console.error('='.repeat(80))
      
      // Provide more helpful error messages
      let errorMessage = err.message
      
      if (err.name === 'AbortError' || err.message.includes('aborted')) {
        errorMessage = 'Request timed out after 60 seconds. The page may be too large or the server is taking too long. Please try a different URL or check the backend logs.'
      } else if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
        const isProduction = API_URL && !API_URL.includes('localhost')
        errorMessage = isProduction
          ? `Cannot reach the backend at ${API_URL}. Check that the service is running on Render (dashboard → Logs), that the deploy succeeded, and that FRONTEND_URLS includes this site. First request on free tier can take 30–60s (cold start).`
          : `Cannot connect to backend API at ${API_URL}. Make sure the backend server is running (e.g. uvicorn on port 8000).`
      } else if (err.message.includes('timeout')) {
        errorMessage = 'Request timed out. The page may be too large or the server is slow. Please try again.'
      } else if (err.message.includes('404')) {
        errorMessage = 'Page not found (404). Please check the URL is correct.'
      } else if (err.message.includes('403')) {
        errorMessage = 'Access forbidden (403). The page may require authentication or block automated access.'
      } else if (err.message.includes('Connection error')) {
        errorMessage = 'Could not reach the target URL. Check your internet connection and verify the URL is correct.'
      }
      
      console.error(`📝 Setting error state: ${errorMessage}`)
      setError(errorMessage)
    } finally {
      console.log(`🏁 Finally block: Cleaning up...`)
      setLoading(false)
      setCurrentStep(0)
      console.log('='.repeat(80))
    }
  }

  const handleReset = () => {
    setResult(null)
    setError(null)
    setCurrentUrl(null)
    setCurrentStep(0)
  }

  return (
    <div className="min-h-screen bg-white">
      {!result && !loading && (
        <Hero onAnalyze={handleAnalyze} error={error} />
      )}
      {loading && <Loading currentStep={currentStep} url={currentUrl} />}
      {result && <Dashboard result={result} onReset={handleReset} analyzedUrl={currentUrl} />}
    </div>
  )
}

export default App
