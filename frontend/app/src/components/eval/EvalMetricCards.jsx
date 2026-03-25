const ICONS = {
  tier_exact_match: (
    <svg className="w-4 h-4 text-risk-moderate" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  tier_adjacent_match: (
    <svg className="w-4 h-4 text-risk-low" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
    </svg>
  ),
  shap_grounded: (
    <svg className="w-4 h-4 text-brand-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  consistency_passed: (
    <svg className="w-4 h-4 text-brand-purple" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
}

const CARDS = [
  { key: 'tier_exact_match', label: 'Tier Exact Match', desc: 'Predicted matches expected tier' },
  { key: 'tier_adjacent_match', label: 'Adjacent Match', desc: 'Within 1 ordinal step' },
  { key: 'shap_grounded', label: 'SHAP Grounding', desc: 'All factors map to real features' },
  { key: 'consistency_passed', label: 'Consistency', desc: 'Identical results on re-run' },
]

export default function EvalMetricCards({ metrics, totalCases }) {
  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      {CARDS.map(({ key, label, desc }) => {
        const count = metrics[key]
        const pct = (count / totalCases) * 100

        return (
          <div key={key} className="card p-5">
            <div className="flex items-center gap-2 mb-3">
              {ICONS[key]}
              <p className="text-[10px] font-semibold text-ink-400 uppercase tracking-wider">{label}</p>
            </div>
            <p className={`text-3xl font-bold ${pct === 100 ? 'text-risk-low' : pct >= 50 ? 'text-risk-moderate' : 'text-risk-critical'}`}>
              {pct.toFixed(0)}<span className="text-lg text-ink-400">%</span>
            </p>
            <p className="text-[11px] text-ink-400 mt-1">{count}/{totalCases} cases</p>
            <p className="text-[11px] text-ink-300 mt-0.5">{desc}</p>
          </div>
        )
      })}
    </div>
  )
}
