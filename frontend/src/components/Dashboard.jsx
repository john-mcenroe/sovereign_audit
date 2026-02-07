import { ArrowLeft, AlertTriangle, CheckCircle2, AlertCircle, Building2, Server, Database, MapPin, Users, Globe, Search, ExternalLink, ShieldAlert, ChevronDown, ChevronUp, Shield, FileText, Layers } from 'lucide-react'
import { useState, useRef } from 'react'

// ─── Shared Helpers ────────────────────────────────────────────────────────────

const RISK_COLORS = {
  Critical: { text: 'text-red-700', bg: 'bg-red-50', border: 'border-red-500', badge: 'bg-red-100 text-red-900 border-red-500' },
  High:     { text: 'text-orange-700', bg: 'bg-orange-50', border: 'border-orange-500', badge: 'bg-orange-100 text-orange-900 border-orange-500' },
  Medium:   { text: 'text-yellow-700', bg: 'bg-yellow-50', border: 'border-yellow-500', badge: 'bg-yellow-100 text-yellow-900 border-yellow-500' },
  Low:      { text: 'text-green-700', bg: 'bg-green-50', border: 'border-green-500', badge: 'bg-green-100 text-green-900 border-green-500' },
}

function riskOf(level) {
  return RISK_COLORS[level] || RISK_COLORS.Medium
}

function locationColor(loc) {
  const u = (loc || '').toUpperCase()
  if (u.includes('US') || u.includes('USA') || u.includes('UNITED STATES')) return 'bg-red-50 border-red-400 text-red-900'
  if (u.includes('EU') || u.includes('EUROPE') || u.includes('IRELAND') || u.includes('GERMANY') || u.includes('FRANCE') || u.includes('NETHERLANDS') || u.includes('ESTONIA')) return 'bg-green-50 border-green-400 text-green-900'
  return 'bg-gray-50 border-gray-300 text-gray-900'
}

// ─── Section Wrapper (consistent card frame for every section) ──────────────

function Section({ id, icon: Icon, title, accent = 'gray', badge, children }) {
  const accentMap = {
    gray:   'border-l-gray-400',
    red:    'border-l-red-500',
    orange: 'border-l-orange-500',
    purple: 'border-l-purple-500',
    blue:   'border-l-blue-500',
    green:  'border-l-green-500',
  }
  return (
    <div id={id} className={`mb-6 border border-gray-200 bg-white border-l-4 ${accentMap[accent] || accentMap.gray}`}>
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
        <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
          {Icon && <Icon className="w-5 h-5 text-gray-600" />}
          {title}
        </h2>
        {badge}
      </div>
      <div className="p-6">
        {children}
      </div>
    </div>
  )
}

// ─── Tag component ──────────────────────────────────────────────────────────

function Tag({ children, className = '' }) {
  return <span className={`inline-block px-3 py-1 text-sm font-medium border ${className}`}>{children}</span>
}

// ─── Field label ────────────────────────────────────────────────────────────

function FieldLabel({ children, icon: Icon }) {
  return (
    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 flex items-center gap-1.5">
      {Icon && <Icon className="w-3.5 h-3.5" />}
      {children}
    </div>
  )
}

// ─── Category Index ─────────────────────────────────────────────────────────

function CategoryIndex({ items }) {
  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="mb-8 border border-gray-200 bg-white">
      <div className="px-6 py-3 bg-gray-900 text-white text-sm font-bold uppercase tracking-wider flex items-center gap-2">
        <Layers className="w-4 h-4" />
        Audit Overview
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-px bg-gray-200">
        {items.map((item) => (
          <button
            key={item.id}
            onClick={() => scrollTo(item.id)}
            className="bg-white px-4 py-4 text-left hover:bg-gray-50 transition-colors group"
          >
            <div className="flex items-center gap-2 mb-1.5">
              <item.icon className={`w-4 h-4 ${item.iconColor || 'text-gray-500'}`} />
              <span className="text-xs font-bold text-gray-900 uppercase tracking-wide group-hover:underline">{item.label}</span>
            </div>
            <div className="flex items-center gap-2">
              {item.status && (
                <span className={`text-sm font-bold ${item.statusColor || 'text-gray-700'}`}>{item.status}</span>
              )}
              {item.detail && (
                <span className="text-xs text-gray-500">{item.detail}</span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

// ─── Company Research Section ───────────────────────────────────────────────

function CompanyResearchSection({ research }) {
  const [expandedQuestions, setExpandedQuestions] = useState({})

  const toggleQuestion = (idx) => {
    setExpandedQuestions(prev => ({ ...prev, [idx]: !prev[idx] }))
  }

  const confidenceStyle = {
    High: 'bg-green-50 border-green-400 text-green-800',
    Medium: 'bg-yellow-50 border-yellow-400 text-yellow-800',
    Low: 'bg-gray-50 border-gray-300 text-gray-600',
  }

  const sentimentIcon = (s) => {
    if (s === 'positive') return <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0" />
    if (s === 'negative') return <AlertTriangle className="w-4 h-4 text-red-600 flex-shrink-0" />
    return <AlertCircle className="w-4 h-4 text-gray-400 flex-shrink-0" />
  }

  const scoreColor = research.score >= 70
    ? 'text-green-700 bg-green-50 border-green-500'
    : research.score >= 40
    ? 'text-orange-700 bg-orange-50 border-orange-500'
    : 'text-red-700 bg-red-50 border-red-500'

  return (
    <Section
      id="company-research"
      icon={Search}
      title="Company Research"
      accent="orange"
      badge={<span className={`px-3 py-1 border-2 font-bold text-sm ${scoreColor}`}>{research.score}/100</span>}
    >
      <div className="space-y-6">
        <p className="text-gray-700 leading-relaxed">{research.research_summary}</p>

        {/* Key Findings */}
        {research.key_findings?.length > 0 && (
          <div>
            <FieldLabel icon={CheckCircle2}>Key Findings</FieldLabel>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
              {research.key_findings.map((f, i) => (
                <div key={i} className="flex items-start gap-2 p-2.5 bg-green-50 border border-green-200 text-sm text-gray-800">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  {f}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Sovereignty Flags */}
        {research.sovereignty_flags?.length > 0 && (
          <div>
            <FieldLabel icon={ShieldAlert}>Sovereignty Flags</FieldLabel>
            <div className="space-y-2 mt-2">
              {research.sovereignty_flags.map((flag, i) => (
                <div key={i} className="flex items-start gap-2 p-2.5 bg-red-50 border border-red-200 text-sm text-red-900">
                  <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                  {flag}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Q&A Accordion */}
        {research.questions_answers?.length > 0 && (
          <div>
            <FieldLabel>Research Questions ({research.questions_answers.length})</FieldLabel>
            <div className="space-y-1 mt-2">
              {research.questions_answers.map((qa, idx) => (
                <div key={idx} className="border border-gray-200">
                  <button
                    onClick={() => toggleQuestion(idx)}
                    className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-2.5 flex-1 min-w-0">
                      {sentimentIcon(qa.sentiment)}
                      <span className="text-sm font-medium text-gray-900 truncate">{qa.question}</span>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                      <Tag className={confidenceStyle[qa.confidence] || confidenceStyle.Low}>
                        {qa.confidence}
                      </Tag>
                      {expandedQuestions[idx]
                        ? <ChevronUp className="w-4 h-4 text-gray-400" />
                        : <ChevronDown className="w-4 h-4 text-gray-400" />
                      }
                    </div>
                  </button>
                  {expandedQuestions[idx] && (
                    <div className="px-4 pb-4 border-t border-gray-100">
                      <p className="text-sm text-gray-700 mt-3 leading-relaxed">{qa.answer}</p>
                      {qa.source_urls?.length > 0 && (
                        <div className="mt-3 flex flex-wrap items-center gap-2">
                          <span className="text-xs font-semibold text-gray-400">Sources:</span>
                          {qa.source_urls.map((url, ui) => (
                            <a key={ui} href={url} target="_blank" rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-xs text-orange-700 hover:text-orange-900 underline">
                              <ExternalLink className="w-3 h-3" />
                              {(() => { try { return new URL(url).hostname } catch { return url } })()}
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Category Tags */}
        {research.research_categories_covered?.length > 0 && (
          <div>
            <FieldLabel>Categories Covered</FieldLabel>
            <div className="flex flex-wrap gap-1.5 mt-2">
              {research.research_categories_covered.map((cat, i) => (
                <Tag key={i} className="bg-orange-50 border-orange-300 text-orange-800 text-xs">{cat}</Tag>
              ))}
            </div>
          </div>
        )}
      </div>
    </Section>
  )
}

// ─── Main Dashboard ─────────────────────────────────────────────────────────

function Dashboard({ result, onReset, analyzedUrl }) {

  // Build index items based on what's present
  const indexItems = []

  indexItems.push({
    id: 'executive-summary', label: 'Summary', icon: FileText,
    iconColor: 'text-gray-600', status: result.risk_level,
    statusColor: result.risk_level === 'High' ? 'text-red-600' : result.risk_level === 'Medium' ? 'text-yellow-600' : 'text-green-600',
  })

  if (result.risk_factors?.length > 6) {
    indexItems.push({
      id: 'risk-factors', label: 'Risk Factors', icon: AlertTriangle,
      iconColor: 'text-red-500', status: `${result.risk_factors.length}`, detail: 'identified',
      statusColor: 'text-red-600',
    })
  }

  if (result.company_info && (result.company_info.registration_country !== 'Unknown' || result.company_info.office_locations?.length > 0)) {
    indexItems.push({
      id: 'company-info', label: 'Company', icon: Building2,
      iconColor: 'text-gray-600', status: result.company_info.registration_country !== 'Unknown' ? result.company_info.registration_country : '—',
      statusColor: 'text-gray-700',
    })
  }

  if (result.infrastructure && (result.infrastructure.cloud_provider !== 'Unknown' || result.infrastructure.data_centers?.length > 0)) {
    indexItems.push({
      id: 'infrastructure', label: 'Infrastructure', icon: Server,
      iconColor: 'text-gray-600', status: result.infrastructure.cloud_provider !== 'Unknown' ? result.infrastructure.cloud_provider.split(' ')[0] : '—',
      statusColor: 'text-gray-700',
    })
  }

  if (result.data_flows && (result.data_flows.storage_locations?.length > 0 || result.data_flows.data_residency !== 'Unknown')) {
    indexItems.push({
      id: 'data-flows', label: 'Data Flows', icon: Database,
      iconColor: 'text-gray-600',
      status: result.data_flows.data_residency !== 'Unknown' ? result.data_flows.data_residency : '—',
      statusColor: result.data_flows.data_residency === 'EU' ? 'text-green-600' : result.data_flows.data_residency === 'US' ? 'text-red-600' : 'text-yellow-600',
    })
  }

  if (result.compliance && (result.compliance.gdpr_status !== 'Unknown' || result.compliance.certifications?.length > 0)) {
    indexItems.push({
      id: 'compliance', label: 'Compliance', icon: Shield,
      iconColor: 'text-gray-600',
      status: result.compliance.gdpr_status?.toLowerCase().includes('compliant') ? 'GDPR OK' : result.compliance.gdpr_status !== 'Unknown' ? 'Review' : '—',
      statusColor: result.compliance.gdpr_status?.toLowerCase().includes('compliant') ? 'text-green-600' : 'text-yellow-600',
    })
  }

  if (result.detected_services?.length > 0) {
    indexItems.push({
      id: 'detected-services', label: 'Services', icon: Globe,
      iconColor: 'text-purple-500', status: `${result.detected_services.length}`, detail: 'detected',
      statusColor: 'text-purple-700',
    })
  }

  if (result.company_research?.research_summary) {
    indexItems.push({
      id: 'company-research', label: 'Research', icon: Search,
      iconColor: 'text-orange-500', status: `${result.company_research.score}/100`,
      statusColor: result.company_research.score >= 70 ? 'text-green-600' : result.company_research.score >= 40 ? 'text-orange-600' : 'text-red-600',
    })
  }

  if (result.vendors?.length > 0) {
    indexItems.push({
      id: 'sub-processors', label: 'Sub-Processors', icon: Layers,
      iconColor: 'text-gray-600', status: `${result.vendors.length}`, detail: 'vendors',
      statusColor: 'text-gray-700',
    })
  }

  // Score helpers
  const scoreColor = result.score < 50 ? 'text-red-600' : result.score < 75 ? 'text-yellow-600' : 'text-green-600'
  const scoreBg = result.score < 50 ? 'border-red-500 bg-red-50' : result.score < 75 ? 'border-yellow-500 bg-yellow-50' : 'border-green-500 bg-green-50'

  const riskBadge = () => {
    if (result.risk_level === 'High') return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-100 text-red-900 border border-red-500 text-sm font-bold">
        <AlertTriangle className="w-4 h-4" /> High Risk
      </span>
    )
    if (result.risk_level === 'Medium') return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-yellow-100 text-yellow-900 border border-yellow-500 text-sm font-bold">
        <AlertCircle className="w-4 h-4" /> Medium Risk
      </span>
    )
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-green-100 text-green-900 border border-green-500 text-sm font-bold">
        <CheckCircle2 className="w-4 h-4" /> Sovereign Compliant
      </span>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 py-8 px-4">
      <div className="max-w-5xl mx-auto">

        {/* Top Bar */}
        <div className="flex items-center justify-between mb-6">
          <button onClick={onReset} className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-black transition-colors font-medium">
            <ArrowLeft className="w-4 h-4" />
            New Audit
          </button>
          {analyzedUrl && (
            <div className="text-sm text-gray-500 font-mono truncate max-w-md">{analyzedUrl}</div>
          )}
        </div>

        {/* Score Card */}
        <div className={`border-2 ${scoreBg} mb-6 p-6 flex items-center justify-between`}>
          <div>
            <div className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Sovereignty Score</div>
            <div className={`text-6xl font-black ${scoreColor}`}>{result.score}</div>
          </div>
          <div className="text-right">
            {riskBadge()}
            {result.company_research?.research_summary && (
              <div className="mt-3 text-xs text-gray-500">
                Research Score: <span className="font-bold text-gray-700">{result.company_research.score}/100</span>
              </div>
            )}
          </div>
        </div>

        {/* Category Index */}
        <CategoryIndex items={indexItems} />

        {/* Executive Summary */}
        <Section id="executive-summary" icon={FileText} title="Executive Summary">
          <p className="text-gray-700 leading-relaxed mb-5">{result.summary}</p>

          {/* Positive & Negative Factors Side-by-Side */}
          {(result.positive_factors?.length > 0 || result.risk_factors?.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Positive Signals */}
              {result.positive_factors?.length > 0 && (
                <div className="border border-green-200 bg-green-50/50 p-4">
                  <h3 className="text-sm font-bold text-green-800 flex items-center gap-1.5 mb-3">
                    <CheckCircle2 className="w-4 h-4" />
                    Positive Signals ({result.positive_factors.length})
                  </h3>
                  <ul className="space-y-1.5">
                    {result.positive_factors.map((factor, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-green-900">
                        <CheckCircle2 className="w-3.5 h-3.5 text-green-600 mt-0.5 flex-shrink-0" />
                        {factor}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Key Concerns */}
              {result.risk_factors?.length > 0 && (
                <div className="border border-red-200 bg-red-50/50 p-4">
                  <h3 className="text-sm font-bold text-red-800 flex items-center gap-1.5 mb-3">
                    <AlertTriangle className="w-4 h-4" />
                    Key Concerns ({result.risk_factors.length})
                  </h3>
                  <ul className="space-y-1.5">
                    {result.risk_factors.slice(0, 6).map((factor, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-red-900">
                        <AlertTriangle className="w-3.5 h-3.5 text-red-500 mt-0.5 flex-shrink-0" />
                        {factor}
                      </li>
                    ))}
                    {result.risk_factors.length > 6 && (
                      <li className="text-xs text-red-600 font-medium pt-1">
                        + {result.risk_factors.length - 6} more concern{result.risk_factors.length - 6 > 1 ? 's' : ''} below
                      </li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          )}
        </Section>

        {/* Full Risk Factors (expanded list if more than 6) */}
        {result.risk_factors?.length > 6 && (
          <Section id="risk-factors" icon={AlertTriangle} title={`All Risk Factors (${result.risk_factors.length})`} accent="red">
            <ul className="space-y-2">
              {result.risk_factors.map((factor, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-800">
                  <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                  {factor}
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Company Information */}
        {result.company_info && (result.company_info.registration_country !== 'Unknown' || result.company_info.office_locations?.length > 0) && (
          <Section id="company-info" icon={Building2} title="Company Information">
            <div className="space-y-4">
              {result.company_info.registration_country !== 'Unknown' && (
                <div>
                  <FieldLabel>Registration Country</FieldLabel>
                  <div className="text-lg font-bold text-gray-900">{result.company_info.registration_country}</div>
                </div>
              )}
              {result.company_info.legal_entity !== 'Unknown' && (
                <div>
                  <FieldLabel>Legal Entity</FieldLabel>
                  <div className="text-base text-gray-900">{result.company_info.legal_entity}</div>
                </div>
              )}
              {result.company_info.office_locations?.length > 0 && (
                <div>
                  <FieldLabel icon={MapPin}>Office Locations</FieldLabel>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {result.company_info.office_locations.map((loc, i) => (
                      <Tag key={i} className={locationColor(loc)}>{loc}</Tag>
                    ))}
                  </div>
                </div>
              )}
              {result.company_info.employee_locations?.length > 0 && (
                <div>
                  <FieldLabel icon={Users}>Employee Locations</FieldLabel>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {result.company_info.employee_locations.map((loc, i) => (
                      <Tag key={i} className={locationColor(loc)}>{loc}</Tag>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Section>
        )}

        {/* Infrastructure */}
        {result.infrastructure && (result.infrastructure.cloud_provider !== 'Unknown' || result.infrastructure.hosting_platform !== 'Unknown' || result.infrastructure.data_centers?.length > 0) && (
          <Section id="infrastructure" icon={Server} title="Infrastructure & Hosting">
            <div className="space-y-4">
              {result.infrastructure.cloud_provider !== 'Unknown' && (
                <div>
                  <FieldLabel>Cloud Provider</FieldLabel>
                  <div className="text-lg font-bold text-gray-900">{result.infrastructure.cloud_provider}</div>
                </div>
              )}
              {result.infrastructure.hosting_platform && result.infrastructure.hosting_platform !== 'Unknown' && (
                <div>
                  <FieldLabel>Hosting Platform</FieldLabel>
                  <div className="text-base font-bold text-gray-900">{result.infrastructure.hosting_platform}</div>
                </div>
              )}
              {result.infrastructure.data_centers?.length > 0 && (
                <div>
                  <FieldLabel>Data Centers</FieldLabel>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {result.infrastructure.data_centers.map((dc, i) => (
                      <Tag key={i} className={locationColor(dc)}>{dc}</Tag>
                    ))}
                  </div>
                </div>
              )}
              {result.infrastructure.server_locations?.length > 0 && (
                <div>
                  <FieldLabel>Server Locations</FieldLabel>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {result.infrastructure.server_locations.map((loc, i) => (
                      <Tag key={i} className={locationColor(loc)}>{loc}</Tag>
                    ))}
                  </div>
                </div>
              )}
              {result.infrastructure.cdn_providers?.length > 0 && (
                <div>
                  <FieldLabel>CDN Providers</FieldLabel>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {result.infrastructure.cdn_providers.map((cdn, i) => (
                      <Tag key={i} className="bg-gray-50 border-gray-300 text-gray-900">{cdn}</Tag>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Section>
        )}

        {/* Data Flows */}
        {result.data_flows && (result.data_flows.storage_locations?.length > 0 || result.data_flows.data_residency !== 'Unknown') && (
          <Section id="data-flows" icon={Database} title="Data Storage & Processing">
            <div className="space-y-4">
              {result.data_flows.data_residency !== 'Unknown' && (
                <div>
                  <FieldLabel>Data Residency</FieldLabel>
                  <div className={`text-lg font-bold ${
                    result.data_flows.data_residency === 'EU' ? 'text-green-600' :
                    result.data_flows.data_residency === 'US' ? 'text-red-600' : 'text-yellow-600'
                  }`}>{result.data_flows.data_residency}</div>
                </div>
              )}
              {result.data_flows.storage_locations?.length > 0 && (
                <div>
                  <FieldLabel icon={Database}>Storage Locations</FieldLabel>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {result.data_flows.storage_locations.map((loc, i) => (
                      <Tag key={i} className={`font-semibold ${locationColor(loc)}`}>{loc}</Tag>
                    ))}
                  </div>
                </div>
              )}
              {result.data_flows.processing_locations?.length > 0 && (
                <div>
                  <FieldLabel>Processing Locations</FieldLabel>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {result.data_flows.processing_locations.map((loc, i) => (
                      <Tag key={i} className={locationColor(loc)}>{loc}</Tag>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Section>
        )}

        {/* Compliance */}
        {result.compliance && (result.compliance.gdpr_status !== 'Unknown' || result.compliance.certifications?.length > 0) && (
          <Section id="compliance" icon={Shield} title="Compliance & Certifications" accent="green">
            <div className="space-y-4">
              {result.compliance.gdpr_status !== 'Unknown' && (
                <div>
                  <FieldLabel>GDPR Status</FieldLabel>
                  <div className={`text-lg font-bold ${
                    result.compliance.gdpr_status.toLowerCase().includes('compliant') ? 'text-green-600' : 'text-red-600'
                  }`}>{result.compliance.gdpr_status}</div>
                </div>
              )}
              {result.compliance.certifications?.length > 0 && (
                <div>
                  <FieldLabel>Certifications</FieldLabel>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {result.compliance.certifications.map((cert, i) => (
                      <Tag key={i} className="bg-green-50 border-green-400 text-green-900 font-semibold">{cert}</Tag>
                    ))}
                  </div>
                </div>
              )}
              {result.compliance.data_residency_guarantees !== 'Unknown' && (
                <div>
                  <FieldLabel>Data Residency Guarantees</FieldLabel>
                  <div className="text-sm text-gray-800">{result.compliance.data_residency_guarantees}</div>
                </div>
              )}
              {result.compliance.recent_incidents?.length > 0 && (
                <div>
                  <FieldLabel icon={AlertTriangle}>Recent Security Incidents</FieldLabel>
                  <div className="space-y-1.5 mt-1">
                    {result.compliance.recent_incidents.map((inc, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-red-900 bg-red-50 border border-red-200 p-2.5">
                        <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                        {inc}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Section>
        )}

        {/* Detected Services */}
        {result.detected_services?.length > 0 && (
          <Section id="detected-services" icon={Globe} title={`Detected Services (${result.detected_services.length})`} accent="purple">
            <div className="text-sm text-gray-500 mb-4">
              Services detected by analyzing external resources (scripts, fonts, iframes) loaded by the website.
            </div>
            <div className="space-y-2">
              {result.detected_services.map((svc, i) => {
                const r = riskOf(svc.risk_level)
                return (
                  <div key={i} className={`p-4 border ${r.border} ${r.bg}`}>
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-bold text-gray-900">{svc.name}</div>
                        <div className="text-xs text-gray-500 font-mono">{svc.domain}</div>
                      </div>
                      <Tag className={`${r.badge} text-xs font-bold`}>{svc.risk_level}</Tag>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm mb-2">
                      <div><span className="text-gray-500">Category:</span> {svc.category}</div>
                      <div>
                        <span className="text-gray-500">Jurisdiction:</span>{' '}
                        <span className={`font-semibold ${
                          svc.jurisdiction.includes('United States') || svc.jurisdiction.includes('US') ? 'text-red-600'
                          : svc.jurisdiction.includes('EU') || svc.jurisdiction.includes('Europe') ? 'text-green-600'
                          : 'text-gray-900'
                        }`}>{svc.jurisdiction}</span>
                      </div>
                    </div>
                    {svc.notes && <div className="text-xs text-gray-600 mb-1">{svc.notes}</div>}
                    {svc.alternatives_eu?.length > 0 && (
                      <div className="text-xs"><span className="font-semibold text-green-700">EU Alternatives:</span> {svc.alternatives_eu.join(', ')}</div>
                    )}
                  </div>
                )
              })}
            </div>
          </Section>
        )}

        {/* Additional Findings */}
        {result.additional_findings?.search_summary && (
          <Section id="additional-findings" icon={Globe} title="Additional Findings" accent="blue">
            <p className="text-gray-700 leading-relaxed mb-4">{result.additional_findings.search_summary}</p>
            {result.additional_findings.additional_categories?.length > 0 && (
              <div>
                <FieldLabel>Categories Analyzed</FieldLabel>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {result.additional_findings.additional_categories.map((cat, i) => (
                    <Tag key={i} className="bg-blue-50 border-blue-300 text-blue-800 text-xs">{cat}</Tag>
                  ))}
                </div>
              </div>
            )}
          </Section>
        )}

        {/* Company Research */}
        {result.company_research?.research_summary && (
          <CompanyResearchSection research={result.company_research} />
        )}

        {/* Sub-Processors Table */}
        {result.vendors?.length > 0 && (
          <div id="sub-processors" className="mb-6 border border-gray-200 bg-white border-l-4 border-l-gray-400">
            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Layers className="w-5 h-5 text-gray-600" />
                Sub-Processors ({result.vendors.length})
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Vendor</th>
                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Purpose</th>
                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Location</th>
                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {result.vendors.map((v, i) => {
                    const r = riskOf(v.risk)
                    return (
                      <tr key={i} className={`border-b border-gray-100 ${v.risk === 'Critical' || v.risk === 'High' ? r.bg : ''}`}>
                        <td className="px-6 py-3 text-sm font-semibold text-gray-900">{v.name}</td>
                        <td className="px-6 py-3 text-sm text-gray-600">{v.purpose}</td>
                        <td className="px-6 py-3 text-sm">
                          <Tag className={`text-xs ${locationColor(v.location)}`}>{v.location}</Tag>
                        </td>
                        <td className="px-6 py-3 text-sm">
                          <span className={`font-bold ${r.text}`}>{v.risk}</span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}

export default Dashboard
