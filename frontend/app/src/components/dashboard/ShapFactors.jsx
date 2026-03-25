export default function ShapFactors({ factors }) {
  const maxAbs = Math.max(...factors.map((f) => Math.abs(f.shap_value)))

  return (
    <div className="card p-5">
      <h3 className="text-sm font-semibold text-ink-900 mb-0.5">Key Risk Factors</h3>
      <p className="text-[11px] text-ink-400 mb-4">SHAP feature importance</p>

      <div className="space-y-2">
        {factors.map((factor) => {
          const isPositive = factor.direction === 'increases_risk'
          const barWidth = (Math.abs(factor.shap_value) / maxAbs) * 100

          return (
            <div key={factor.name} className={`${isPositive ? 'shap-positive' : 'shap-negative'} rounded-lg p-3`}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-ink-800">{factor.name}</span>
                <span className={`text-xs font-semibold font-mono ${isPositive ? 'text-red-500' : 'text-emerald-600'}`}>
                  {isPositive ? '+' : ''}{factor.shap_value.toFixed(2)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-surface-100 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full ${isPositive ? 'bg-red-400' : 'bg-emerald-400'}`}
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
                <span className={`text-[10px] font-medium w-20 text-right ${isPositive ? 'text-red-500' : 'text-emerald-600'}`}>
                  {isPositive ? 'increases risk' : 'decreases risk'}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
