import RiskBadge from '@/components/shared/RiskBadge'
import { formatCurrency, formatPercent, formatMs } from '@/lib/formatters'

const RISK_BAR_COLORS = {
  LOW: 'from-emerald-400 to-emerald-500',
  MODERATE: 'from-amber-400 to-amber-500',
  HIGH: 'from-orange-400 to-red-500',
  CRITICAL: 'from-red-500 to-red-700',
}

const RISK_ICON_BG = {
  LOW: 'bg-emerald-50',
  MODERATE: 'bg-amber-50',
  HIGH: 'bg-orange-50',
  CRITICAL: 'bg-red-50',
}

export default function KpiCards({ data }) {
  const probPct = (data.risk_probability * 100).toFixed(1)

  return (
    <div className="grid grid-cols-4 gap-4 mb-6 fade-in">
      {/* Risk Tier */}
      <div className="card p-5">
        <p className="text-[10px] font-semibold text-ink-400 uppercase tracking-wider mb-3">Risk Tier</p>
        <div className="flex items-center gap-3">
          <div className={`w-11 h-11 rounded-xl ${RISK_ICON_BG[data.risk_tier]} flex items-center justify-center`}>
            <svg className={`w-5 h-5 text-risk-${data.risk_tier.toLowerCase()}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div>
            <RiskBadge tier={data.risk_tier} />
          </div>
        </div>
      </div>

      {/* Claim Probability */}
      <div className="card p-5">
        <p className="text-[10px] font-semibold text-ink-400 uppercase tracking-wider mb-3">Claim Probability</p>
        <p className="text-3xl font-bold text-ink-900">{probPct}<span className="text-lg text-ink-400">%</span></p>
        <div className="mt-2.5 w-full bg-surface-100 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full bg-gradient-to-r ${RISK_BAR_COLORS[data.risk_tier]}`}
            style={{ width: `${probPct}%` }}
          />
        </div>
      </div>

      {/* Predicted Amount */}
      <div className="card p-5">
        <p className="text-[10px] font-semibold text-ink-400 uppercase tracking-wider mb-3">Predicted Claim</p>
        <p className="text-3xl font-bold text-ink-900">
          <span className="text-lg text-ink-400">$</span>
          {data.predicted_claim_amount.toLocaleString()}
        </p>
        <p className="text-[11px] text-ink-400 mt-2">XGBoost severity model</p>
      </div>

      {/* Confidence */}
      <div className="card p-5">
        <p className="text-[10px] font-semibold text-ink-400 uppercase tracking-wider mb-3">Model Confidence</p>
        <p className="text-3xl font-bold text-ink-900">
          {(data.confidence_score * 100).toFixed(1)}<span className="text-lg text-ink-400">%</span>
        </p>
        <p className="text-[11px] text-ink-400 mt-2">
          Latency: {formatMs(data.pipeline_trace.prediction_ms)}
        </p>
      </div>
    </div>
  )
}
