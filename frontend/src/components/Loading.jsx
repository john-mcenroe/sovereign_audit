import { Loader2, Globe, FileText, Brain, Calculator, CheckCircle2, AlertCircle } from 'lucide-react'
import { useState, useEffect } from 'react'

function Loading({ currentStep = 0, url = '' }) {
  const [thinkingSteps, setThinkingSteps] = useState([])
  const [currentThinking, setCurrentThinking] = useState('')

  const steps = [
    { 
      id: 0,
      icon: Globe, 
      title: 'Scraping multiple pages', 
      thinking: [
        'Connecting to homepage...',
        'Scraping /about page...',
        'Scraping /privacy policy...',
        'Scraping /legal/subprocessors...',
        'Scraping /security page...',
        'Scraping /careers page...',
        'Combining all page content...'
      ]
    },
    { 
      id: 1,
      icon: FileText, 
      title: 'Extracting information', 
      thinking: [
        'Parsing HTML from all pages...',
        'Removing scripts and styles...',
        'Extracting visible text...',
        'Cleaning and formatting content...',
        'Preparing for AI analysis...'
      ]
    },
    { 
      id: 2,
      icon: Brain, 
      title: 'AI Analysis', 
      thinking: [
        'Analyzing company registration...',
        'Identifying cloud infrastructure...',
        'Extracting data storage locations...',
        'Finding office/employee locations...',
        'Identifying sub-processors...',
        'Assessing vendor risks...',
        'Analyzing data flows...',
        'Generating comprehensive summary...'
      ]
    },
    { 
      id: 3,
      icon: Globe, 
      title: 'Web Search Discovery', 
      thinking: [
        'Searching for company registration details...',
        'Finding infrastructure announcements...',
        'Discovering compliance certifications...',
        'Locating recent security incidents...',
        'Finding office expansions...',
        'Discovering additional risk factors...',
        'Merging search findings...'
      ]
    },
    { 
      id: 4,
      icon: Calculator, 
      title: 'Calculating sovereignty score', 
      thinking: [
        'Evaluating company jurisdiction...',
        'Assessing infrastructure risks...',
        'Analyzing data storage locations...',
        'Checking employee locations...',
        'Evaluating compliance status...',
        'Scoring sub-processors...',
        'Calculating final score...',
        'Determining risk level...'
      ]
    },
  ]

  useEffect(() => {
    // Reset thinking steps when step changes
    if (currentStep === 0) {
      setThinkingSteps([])
      setCurrentThinking('')
    }
  }, [currentStep])

  useEffect(() => {
    if (currentStep >= 0 && currentStep < steps.length) {
      const step = steps[currentStep]
      let thinkingIndex = 0
      
      // Reset thinking for this step
      setThinkingSteps(prev => {
        const newSteps = [...prev]
        newSteps[currentStep] = []
        return newSteps
      })
      setCurrentThinking('')
      
      // Show thinking steps for current step
      const interval = setInterval(() => {
        if (thinkingIndex < step.thinking.length) {
          const thought = step.thinking[thinkingIndex]
          setCurrentThinking(thought)
          setThinkingSteps(prev => {
            const newSteps = [...prev]
            if (!newSteps[currentStep]) {
              newSteps[currentStep] = []
            }
            if (!newSteps[currentStep].includes(thought)) {
              newSteps[currentStep] = [...newSteps[currentStep], thought]
            }
            return newSteps
          })
          thinkingIndex++
        } else {
          setCurrentThinking('')
          clearInterval(interval)
        }
      }, 1000) // Show new thinking step every 1 second
      
      return () => clearInterval(interval)
    }
  }, [currentStep])

  return (
    <div className="min-h-screen bg-white py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Loader2 className="w-12 h-12 text-black animate-spin" />
          </div>
          <h2 className="text-2xl font-bold text-black mb-2">Analyzing Sovereignty Risk</h2>
          {url && (
            <p className="text-sm text-gray-600 font-mono break-all">{url}</p>
          )}
        </div>

        {/* Progress Steps */}
        <div className="space-y-4 mb-8">
          {steps.map((step, index) => {
            const Icon = step.icon
            const isActive = index === currentStep
            const isComplete = index < currentStep
            const thinkingForStep = thinkingSteps[index] || []

            return (
              <div
                key={step.id}
                className={`border-2 rounded p-4 transition-all ${
                  isActive
                    ? 'border-black bg-gray-50'
                    : isComplete
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-300 bg-white'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 mt-1">
                    {isComplete ? (
                      <CheckCircle2 className="w-6 h-6 text-green-600" />
                    ) : isActive ? (
                      <Icon className="w-6 h-6 text-black animate-pulse" />
                    ) : (
                      <Icon className="w-6 h-6 text-gray-400" />
                    )}
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3
                        className={`font-bold text-lg ${
                          isActive ? 'text-black' : isComplete ? 'text-green-700' : 'text-gray-500'
                        }`}
                      >
                        {step.title}
                      </h3>
                      {isActive && (
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-black rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                          <div className="w-2 h-2 bg-black rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                          <div className="w-2 h-2 bg-black rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                      )}
                    </div>

                    {/* Thinking steps */}
                    {isActive && (
                      <div className="mt-3 space-y-2">
                        {thinkingForStep.map((thought, thoughtIndex) => (
                          <div
                            key={thoughtIndex}
                            className="flex items-center gap-2 text-sm text-gray-700 animate-fade-in"
                            style={{
                              animation: 'fadeIn 0.3s ease-in',
                              animationDelay: `${thoughtIndex * 0.1}s`
                            }}
                          >
                            <div className="w-1.5 h-1.5 bg-black rounded-full" />
                            <span className="font-mono">{thought}</span>
                          </div>
                        ))}
                        {currentThinking && thinkingForStep.includes(currentThinking) && (
                          <div className="flex items-center gap-2 text-sm text-gray-600 mt-2">
                            <Loader2 className="w-3 h-3 animate-spin" />
                            <span className="font-mono italic">{currentThinking}</span>
                          </div>
                        )}
                      </div>
                    )}

                    {isComplete && (
                      <div className="mt-2 text-sm text-green-700 font-semibold">
                        ✓ Complete
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Status Footer */}
        <div className="text-center border-t-2 border-gray-200 pt-6">
          <div className="flex items-center justify-center gap-2 text-gray-600 mb-2">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">This process typically takes 15-45 seconds</span>
          </div>
          <div className="text-xs text-gray-500">
            The AI is analyzing the page content and extracting vendor information...
          </div>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-5px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fadeIn 0.3s ease-in;
        }
      `}</style>
    </div>
  )
}

export default Loading
