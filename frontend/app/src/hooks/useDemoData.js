import highRisk from '@/data/demo-high-risk.json'
import lowRisk from '@/data/demo-low-risk.json'
import criticalRisk from '@/data/demo-critical-risk.json'
import moderateRisk from '@/data/demo-moderate-risk.json'

const DEMOS = {
  critical: criticalRisk,
  high: highRisk,
  moderate: moderateRisk,
  low: lowRisk,
}

export function useDemoData(id) {
  return DEMOS[id] || null
}

export function getAllDemos() {
  return Object.entries(DEMOS).map(([id, data]) => ({
    id,
    ...data,
  }))
}
