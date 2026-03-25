import highRisk from '@/data/demo-high-risk.json'
import lowRisk from '@/data/demo-low-risk.json'
import criticalRisk from '@/data/demo-critical-risk.json'

const DEMOS = {
  high: highRisk,
  low: lowRisk,
  critical: criticalRisk,
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
