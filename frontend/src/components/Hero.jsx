import { useState, useEffect } from 'react'
import { AlertCircle, X } from 'lucide-react'

/**
 * Normalizes a URL by adding protocol if missing and handling common patterns
 * Only called on submit, not while typing
 */
function normalizeUrl(input) {
  if (!input || !input.trim()) {
    return input
  }

  let url = input.trim()

  // If already has protocol (http:// or https://), return as-is
  if (/^https?:\/\//i.test(url)) {
    return url
  }

  // If starts with //, add https:
  if (url.startsWith('//')) {
    return `https:${url}`
  }

  // If it's a valid domain pattern (contains at least one dot and valid TLD-like ending)
  // Add https:// prefix
  if (/^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}/.test(url)) {
    return `https://${url}`
  }

  // If it looks like a domain without TLD (e.g., "localhost", "local"), add https://
  if (/^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$/.test(url)) {
    return `https://${url}`
  }

  // If it starts with a path-like pattern (e.g., "/about"), assume it's relative
  // Don't modify it - let the backend handle it or return as-is
  if (url.startsWith('/')) {
    return url
  }

  // Default: try adding https://
  return `https://${url}`
}

function Hero({ onAnalyze, error }) {
  const [url, setUrl] = useState('')
  const [showError, setShowError] = useState(!!error)

  // Update showError when error prop changes
  useEffect(() => {
    setShowError(!!error)
  }, [error])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (url.trim()) {
      // Normalize the URL only on submit, not while typing
      const normalized = normalizeUrl(url.trim())
      console.log(`🔗 URL normalization: "${url.trim()}" -> "${normalized}"`)
      onAnalyze(normalized)
    }
  }

  return (
    <div className="min-h-screen relative flex items-center justify-center px-4 overflow-hidden">
      {/* Background — faded so content stays readable */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: 'url(/chatgpt-background.png)' }}
        aria-hidden="true"
      />
      <div className="absolute inset-0 bg-white/75" aria-hidden="true" />
      <div className="relative z-10 w-full max-w-2xl lg:max-w-3xl">
        <div className="text-center mb-12">
          <h1 className="text-5xl md:text-6xl font-black text-black mb-4 tracking-tight [text-shadow:0_2px_4px_rgba(255,255,255,0.9)]">
            Test any website for sovereignty in the EU
          </h1>
          <p className="text-lg md:text-xl font-extrabold text-gray-900 max-w-xl lg:max-w-2xl mx-auto [text-shadow:0_1px_2px_rgba(255,255,255,0.9)]">
            Enter any website and we analyze infrastructure, data flows, and compliance to let you know how well it meets EU data sovereignty requirements.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="text"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value)
                setShowError(false) // Clear error when user types
              }}
              placeholder="easyoffer.ie"
              className="w-full px-6 py-4 text-lg border-2 border-black focus:outline-none focus:ring-0 bg-white text-black placeholder-gray-500"
            />
          </div>
          {error && showError && (
            <div className="bg-red-50 border-2 border-red-500 px-6 py-4 text-red-900 relative">
              <button
                onClick={() => setShowError(false)}
                className="absolute top-2 right-2 text-red-600 hover:text-red-800"
                aria-label="Dismiss error"
              >
                <X className="w-5 h-5" />
              </button>
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <div className="font-semibold mb-1">Error</div>
                  <div className="text-sm leading-relaxed">{error}</div>
                  {error.includes('backend') && (
                    <div className="mt-3 text-xs text-red-700 bg-red-100 p-2 rounded">
                      <strong>Tip:</strong> Make sure the backend server is running. Check the terminal where you started the backend.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          <button
            type="submit"
            className="w-full bg-black text-white px-6 py-4 text-lg font-bold hover:bg-gray-800 hover:scale-[1.02] active:scale-[0.99] transition-all shadow-lg hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2 border-2 border-black"
          >
            Test sovereignty
          </button>
        </form>
      </div>
    </div>
  )
}

export default Hero
