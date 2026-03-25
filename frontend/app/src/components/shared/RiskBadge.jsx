import { RISK_COLORS } from '@/lib/constants'

export default function RiskBadge({ tier, size = 'md' }) {
  const colors = RISK_COLORS[tier] || RISK_COLORS.MODERATE
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm'

  return (
    <span className={`${colors.bg} ${colors.text} ${sizeClasses} font-semibold rounded-full inline-block`}>
      {tier}
    </span>
  )
}
