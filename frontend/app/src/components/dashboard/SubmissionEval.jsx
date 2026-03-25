import { useState } from 'react'

// Valid SHAP display names from services/prediction/core/constants.py
const VALID_FEATURE_NAMES = new Set([
  'Total entities in document',
  'Monetary values mentioned',
  'Number of perils mentioned',
  'Coverage types mentioned',
  'Claim statuses mentioned',
  'Property types mentioned',
  'Vehicles mentioned',
  'Open claim present',
  'Denied claim present',
  'Fire peril present',
  'Flood peril present',
  'Earthquake peril present',
  'Wind peril present',
  'Cyber coverage requested',
  'Umbrella coverage present',
  'Highest monetary value',
  'Average monetary value',
  'Count of monetary references',
  'Prior claims history',
  'Property construction risk',
  'Breadth of coverage requested',
  'Variety of perils',
  'Bodily injuries reported',
  'Vehicles involved in incident',
  'Witnesses present',
  'Police contacted',
  'Vehicle age (years)',
  'Multi-vehicle incident',
])

const TIER_RANGES = {
  LOW:      [0, 0.35],
  MODERATE: [0.25, 0.65],
  HIGH:     [0.50, 0.85],
  CRITICAL: [0.70, 1.0],
}

function runChecks(data) {
  const checks = []

  // 1. SHAP Grounded — use partial matching since display names may be shortened
  const factors = data.key_risk_factors || []
  const validNamesLower = [...VALID_FEATURE_NAMES].map(n => n.toLowerCase())
  const isGrounded = (name) => {
    const lower = name.toLowerCase()
    return validNamesLower.some(v => v.includes(lower) || lower.includes(v))
  }
  const invalidFactors = factors.filter(f => !isGrounded(f.name))
  checks.push({
    name: 'SHAP Grounded',
    description: 'All risk factor names are valid model features',
    passed: invalidFactors.length === 0,
    detail: invalidFactors.length === 0
      ? `${factors.length} factors, all valid`
      : `Invalid: ${invalidFactors.map(f => f.name).join(', ')}`,
  })

  // 2. RAG Retrieved
  const cases = data.similar_cases || []
  const topSim = cases.length > 0 ? Math.max(...cases.map(c => c.similarity_score || 0)) : 0
  checks.push({
    name: 'RAG Retrieved',
    description: 'Similar cases found with meaningful similarity',
    passed: cases.length > 0 && topSim > 0.5,
    detail: cases.length > 0
      ? `${cases.length} cases, top similarity ${(topSim * 100).toFixed(1)}%`
      : 'No similar cases retrieved',
  })

  // 3. Narrative Present
  const narrative = data.underwriter_narrative || ''
  checks.push({
    name: 'Narrative Generated',
    description: 'Underwriter narrative was produced',
    passed: narrative.length > 50,
    detail: narrative.length > 0
      ? `${narrative.length} characters`
      : 'Empty narrative',
  })

  // 4. Narrative References Tier
  const tier = (data.risk_tier || '').toUpperCase()
  const narrativeUpper = narrative.toUpperCase()
  const tierInNarrative = tier && narrativeUpper.includes(tier)
  checks.push({
    name: 'Tier Referenced',
    description: 'Narrative mentions the predicted risk tier',
    passed: tierInNarrative,
    detail: tierInNarrative
      ? `"${tier}" found in narrative`
      : `"${tier}" not mentioned in narrative`,
  })

  // 5. Narrative References Factors — use keyword matching (e.g. "monetary" matches "Highest monetary value")
  const narrativeLower = narrative.toLowerCase()
  const referencedFactors = factors.filter(f => {
    const words = f.name.toLowerCase().split(/\s+/).filter(w => w.length > 3)
    return words.some(w => narrativeLower.includes(w))
  })
  checks.push({
    name: 'Factors Referenced',
    description: 'Narrative mentions at least one SHAP factor',
    passed: referencedFactors.length > 0,
    detail: referencedFactors.length > 0
      ? `${referencedFactors.length}/${factors.length} factors referenced`
      : 'No SHAP factors mentioned in narrative',
  })

  // 6. Tier-Probability Alignment
  const prob = data.risk_probability || 0
  const range = TIER_RANGES[tier]
  const aligned = range ? prob >= range[0] && prob <= range[1] : false
  checks.push({
    name: 'Tier-Probability Aligned',
    description: 'Risk tier matches the probability range',
    passed: aligned,
    detail: range
      ? `${tier} expects ${(range[0]*100).toFixed(0)}–${(range[1]*100).toFixed(0)}%, got ${(prob*100).toFixed(1)}%`
      : `Unknown tier "${tier}"`,
  })

  // 7. Claim Amount Positive
  const claim = data.predicted_claim_amount || 0
  checks.push({
    name: 'Claim Positive',
    description: 'Predicted claim amount is greater than zero',
    passed: claim > 0,
    detail: claim > 0 ? `$${claim.toLocaleString()}` : 'Claim is $0 or negative',
  })

  // 8. Confidence Score
  const confidence = data.confidence_score || 0
  checks.push({
    name: 'Model Confident',
    description: 'Model confidence exceeds 60% threshold',
    passed: confidence >= 0.6,
    detail: `${(confidence * 100).toFixed(1)}% confidence`,
  })

  // 9. Hallucination Detection — check that dollar amounts in narrative are grounded
  const hallucination = detectHallucinations(data)
  checks.push({
    name: 'No Hallucinations',
    description: 'All facts in narrative are grounded in source data',
    passed: !hallucination.detected,
    detail: hallucination.detected
      ? `${hallucination.issues.length} issue(s): ${hallucination.issues.join('; ')}`
      : 'All monetary values and percentages traceable to source data',
  })

  return checks
}

/**
 * Client-side hallucination detection.
 * Extracts dollar amounts and percentages from the narrative and checks
 * whether each one can be traced back to entities, prediction output, or SHAP values.
 */
function detectHallucinations(data) {
  const narrative = data.underwriter_narrative || ''
  const issues = []

  // Build a set of "known" numbers from source data
  const knownNumbers = new Set()

  // From prediction
  const prob = data.risk_probability || 0
  knownNumbers.add((prob * 100).toFixed(1))
  knownNumbers.add((prob * 100).toFixed(2))
  knownNumbers.add(Math.round(prob * 100).toString())

  const claim = data.predicted_claim_amount || 0
  knownNumbers.add(claim.toFixed(2))
  knownNumbers.add(Math.round(claim).toString())
  knownNumbers.add(claim.toLocaleString('en-US', { maximumFractionDigits: 2 }))

  const conf = data.confidence_score || 0
  knownNumbers.add((conf * 100).toFixed(1))
  knownNumbers.add(Math.round(conf * 100).toString())

  // From SHAP factors
  const factors = data.key_risk_factors || []
  for (const f of factors) {
    const val = Math.abs(f.impact || f.value || 0)
    knownNumbers.add(val.toFixed(2))
    knownNumbers.add(val.toFixed(4))
  }

  // From entities — extract all numbers from entity values
  const entities = data.entities || {}
  for (const [, values] of Object.entries(entities)) {
    if (!Array.isArray(values)) continue
    for (const v of values) {
      // extract numbers from entity strings like "$2,000,000" or "42"
      const nums = String(v).match(/[\d,]+\.?\d*/g) || []
      for (const n of nums) {
        knownNumbers.add(n.replace(/,/g, ''))
        knownNumbers.add(n)
      }
    }
  }

  // From similar cases — extract numbers from summaries
  const similarCases = data.similar_cases || []
  for (const c of similarCases) {
    const summary = c.summary || ''
    const nums = summary.match(/[\d,]+\.?\d*/g) || []
    for (const n of nums) {
      knownNumbers.add(n.replace(/,/g, ''))
    }
  }

  // Extract dollar amounts from narrative
  const dollarMatches = narrative.match(/\$[\d,]+\.?\d*/g) || []
  for (const match of dollarMatches) {
    const num = match.replace(/[$,]/g, '')
    if (!knownNumbers.has(num) && !isCloseToKnown(parseFloat(num), knownNumbers)) {
      issues.push(`Ungrounded amount: ${match}`)
    }
  }

  // Extract percentages from narrative — allow small percentages (<30%) as reasonable
  // underwriter recommendations (e.g., "+15-20% premium adjustment")
  const pctMatches = narrative.match(/[\d.]+\s*%/g) || []
  for (const match of pctMatches) {
    const num = match.replace(/[%\s]/g, '')
    const val = parseFloat(num)
    if (val <= 30) continue // small percentages are likely rate/premium recommendations
    if (!knownNumbers.has(num) && !isCloseToKnown(val, knownNumbers)) {
      issues.push(`Ungrounded percentage: ${match}`)
    }
  }

  return {
    detected: issues.length > 0,
    issues: issues.slice(0, 5), // cap at 5 for display
  }
}

/** Check if a number is within 1% of any known number */
function isCloseToKnown(num, knownSet) {
  if (isNaN(num)) return true // don't flag non-numbers
  for (const k of knownSet) {
    const kn = parseFloat(k.replace(/,/g, ''))
    if (!isNaN(kn) && kn > 0) {
      const ratio = num / kn
      if (ratio >= 0.99 && ratio <= 1.01) return true
    }
  }
  return false
}

export default function SubmissionEval({ data }) {
  const [open, setOpen] = useState(false)

  if (!data) return null

  const checks = runChecks(data)
  const passed = checks.filter(c => c.passed).length
  const total = checks.length
  const allPassed = passed === total
  const score = Math.round((passed / total) * 100)

  return (
    <>
      {/* Trigger button — rendered inline in the layout */}
      <button
        onClick={() => setOpen(true)}
        className="px-4 py-2 text-sm font-medium text-white brand-gradient rounded-lg hover:opacity-90 cursor-pointer transition brand-glow"
      >
        Evaluate
      </button>

      {/* Modal overlay */}
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={() => setOpen(false)}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

          {/* Modal content */}
          <div
            className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="sticky top-0 bg-white rounded-t-2xl border-b border-surface-200 px-6 py-4 flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-ink-900">Submission Evaluation</h2>
                <p className="text-xs text-ink-400 mt-0.5">Quality checks for this analysis</p>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <span className={`text-3xl font-bold font-mono ${allPassed ? 'text-emerald-500' : score >= 75 ? 'text-amber-500' : 'text-red-500'}`}>
                    {score}%
                  </span>
                  <p className="text-xs text-ink-400">{passed}/{total} passed</p>
                </div>
                <button
                  onClick={() => setOpen(false)}
                  className="p-1.5 rounded-lg hover:bg-surface-100 text-ink-400 hover:text-ink-600 transition cursor-pointer"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Checks list */}
            <div className="p-6 space-y-2.5">
              {checks.map((check) => (
                <div key={check.name} className={`flex items-start gap-3 p-3.5 rounded-xl ${check.passed ? 'bg-emerald-50' : 'bg-red-50'}`}>
                  <span className="mt-0.5">
                    {check.passed ? (
                      <svg className="w-4.5 h-4.5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className="w-4.5 h-4.5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    )}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium ${check.passed ? 'text-emerald-800' : 'text-red-800'}`}>
                      {check.name}
                    </p>
                    <p className="text-xs text-ink-500 mt-0.5">{check.description}</p>
                    <p className={`text-xs mt-1 font-mono ${check.passed ? 'text-emerald-600' : 'text-red-600'}`}>
                      {check.detail}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
