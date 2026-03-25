import RiskBadge from '@/components/shared/RiskBadge'

export default function EvalCaseTable({ cases }) {
  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-4 border-b border-surface-200">
        <h3 className="text-sm font-semibold text-ink-900">Test Cases</h3>
        <p className="text-[11px] text-ink-400">20 stratified cases (5 per severity tier, seed=42)</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-50 text-left">
              <th className="px-4 py-3 text-[10px] font-semibold text-ink-400 uppercase tracking-wider">Idx</th>
              <th className="px-4 py-3 text-[10px] font-semibold text-ink-400 uppercase tracking-wider">Incident Type</th>
              <th className="px-4 py-3 text-[10px] font-semibold text-ink-400 uppercase tracking-wider">Severity</th>
              <th className="px-4 py-3 text-[10px] font-semibold text-ink-400 uppercase tracking-wider">Expected</th>
              <th className="px-4 py-3 text-[10px] font-semibold text-ink-400 uppercase tracking-wider">Predicted</th>
              <th className="px-4 py-3 text-[10px] font-semibold text-ink-400 uppercase tracking-wider">Match</th>
              <th className="px-4 py-3 text-[10px] font-semibold text-ink-400 uppercase tracking-wider">Prob</th>
              <th className="px-4 py-3 text-[10px] font-semibold text-ink-400 uppercase tracking-wider">RAG Sim</th>
              <th className="px-4 py-3 text-[10px] font-semibold text-ink-400 uppercase tracking-wider">SHAP</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-200">
            {cases.map((c) => (
              <tr key={c.case_index} className={c.tier_match ? 'bg-white' : 'bg-amber-50/50'}>
                <td className="px-4 py-3 font-mono text-ink-500 text-xs">{c.case_index}</td>
                <td className="px-4 py-3 text-ink-700">{c.incident_type}</td>
                <td className="px-4 py-3 text-ink-500 text-xs">{c.incident_severity}</td>
                <td className="px-4 py-3"><RiskBadge tier={c.expected_tier} size="sm" /></td>
                <td className="px-4 py-3"><RiskBadge tier={c.predicted_tier} size="sm" /></td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-semibold ${c.tier_match ? 'text-risk-low' : 'text-risk-moderate'}`}>
                    {c.tier_match ? 'PASS' : 'ADJ'}
                  </span>
                </td>
                <td className="px-4 py-3 font-mono text-xs text-ink-600">{(c.risk_probability * 100).toFixed(1)}%</td>
                <td className="px-4 py-3 font-mono text-xs text-ink-600">{(c.rag_top_similarity * 100).toFixed(0)}%</td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-semibold ${c.shap_grounded ? 'text-risk-low' : 'text-risk-critical'}`}>
                    {c.shap_grounded ? 'PASS' : 'FAIL'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
