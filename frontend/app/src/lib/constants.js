export const RISK_COLORS = {
  LOW: { bg: 'bg-emerald-50', text: 'text-risk-low', border: 'border-risk-low' },
  MODERATE: { bg: 'bg-amber-50', text: 'text-risk-moderate', border: 'border-risk-moderate' },
  HIGH: { bg: 'bg-orange-50', text: 'text-risk-high', border: 'border-risk-high' },
  CRITICAL: { bg: 'bg-red-50', text: 'text-risk-critical', border: 'border-risk-critical' },
}

export const RISK_ORDER = ['LOW', 'MODERATE', 'HIGH', 'CRITICAL']

export const PIPELINE_STAGES = [
  { name: 'Ingestion', description: 'PySpark + spaCy NER', port: 8000 },
  { name: 'Prediction', description: 'XGBoost + SHAP', port: 8001 },
  { name: 'RAG', description: 'FAISS + MiniLM', port: 8002 },
  { name: 'LLM', description: 'Claude / Ollama', port: 8003 },
]

export const DEMO_SUBMISSIONS = [
  { id: 'high', label: 'Commercial Property Fire', tier: 'HIGH' },
  { id: 'low', label: 'Minor Vehicle Theft', tier: 'LOW' },
  { id: 'critical', label: 'Multi-Vehicle Collision', tier: 'CRITICAL' },
]
