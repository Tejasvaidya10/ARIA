import DashboardLayout from '@/components/layout/DashboardLayout'
import EvalMetricCards from '@/components/eval/EvalMetricCards'
import EvalCaseTable from '@/components/eval/EvalCaseTable'
import evalReport from '@/data/eval-report.json'
import { formatMs } from '@/lib/formatters'

export default function EvalPage() {
  const { metrics, cases, total_cases } = evalReport

  return (
    <DashboardLayout
      title="Pipeline Evaluation"
      subtitle={`${total_cases} test cases — seed=42`}
      view="eval"
      onViewChange={() => {}}
    >
      <div className="fade-in">
        <EvalMetricCards metrics={metrics} totalCases={total_cases} />

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="card p-4 flex items-center justify-between">
            <span className="text-sm text-ink-500">Mean RAG Similarity</span>
            <span className="text-sm font-semibold font-mono brand-gradient-text">
              {(metrics.mean_rag_similarity * 100).toFixed(1)}%
            </span>
          </div>
          <div className="card p-4 flex items-center justify-between">
            <span className="text-sm text-ink-500">Mean Processing Time</span>
            <span className="text-sm font-semibold font-mono brand-gradient-text">
              {formatMs(metrics.mean_processing_time_ms)}
            </span>
          </div>
          <div className="card p-4 flex items-center justify-between">
            <span className="text-sm text-ink-500">Git Hash</span>
            <span className="text-sm font-mono text-ink-400">
              {evalReport.git_hash?.slice(0, 7) || 'N/A'}
            </span>
          </div>
        </div>

        <EvalCaseTable cases={cases} />
      </div>
    </DashboardLayout>
  )
}
