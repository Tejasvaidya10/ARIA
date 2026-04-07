import { formatMs } from '@/lib/formatters'

const STAGES = [
  { key: 'ingestion_ms', label: 'Ingestion + NER' },
  { key: 'prediction_ms', label: 'XGBoost + SHAP' },
  { key: 'rag_ms', label: 'RAG retrieval' },
  { key: 'llm_ms', label: 'LLM synthesis' },
]

export default function PipelineTrace({ trace }) {
  const hasNull = Object.values(trace).some((v) => v == null)
  const total = Object.values(trace).reduce((sum, v) => sum + (v ?? 0), 0)

  return (
    <div className="card p-5">
      <h3 className="text-sm font-semibold text-ink-900 mb-4">Pipeline Trace</h3>
      <div className="space-y-3">
        {STAGES.map((stage) => (
          <div key={stage.key} className="pipeline-step flex items-center justify-between text-sm">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 rounded-full bg-emerald-50 flex items-center justify-center">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              </div>
              <span className="text-ink-700">{stage.label}</span>
            </div>
            <span className="text-ink-400 font-mono text-xs">
              {trace[stage.key] != null ? formatMs(trace[stage.key]) : '—'}
            </span>
          </div>
        ))}
        <div className="border-t border-surface-200 pt-3 mt-1 flex items-center justify-between text-sm">
          <span className="text-ink-900 font-semibold">
            Total{hasNull ? '*' : ''}
          </span>
          <span className="text-ink-900 font-mono text-xs font-bold">{formatMs(total)}</span>
        </div>
      </div>
    </div>
  )
}
