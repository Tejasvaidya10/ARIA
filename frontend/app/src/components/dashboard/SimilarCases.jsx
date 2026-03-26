export default function SimilarCases({ cases }) {
  return (
    <div className="card p-5 flex flex-col">
      <div className="flex items-center justify-between mb-1 shrink-0">
        <h3 className="text-sm font-semibold text-ink-900">Similar Cases</h3>
        <span className="text-[10px] text-ink-400 font-mono">2,126 vectors</span>
      </div>
      <p className="text-[11px] text-ink-400 mb-4 shrink-0">FAISS nearest-neighbor retrieval</p>

      <div className="space-y-2.5 overflow-y-auto max-h-[450px] pr-1">
        {cases.map((c) => {
          const isEdgar = c.policy_id.startsWith('EDGAR-')
          const simPct = Math.round(c.similarity_score * 100)

          return (
            <div
              key={c.policy_id}
              className={`border rounded-lg p-3 transition cursor-pointer ${
                isEdgar
                  ? 'border-purple-100 bg-purple-50/20 hover:border-brand-purple/30'
                  : 'border-surface-200 hover:border-brand-cyan/40'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-mono text-ink-400">{c.policy_id}</span>
                {isEdgar ? (
                  <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-purple-50 text-brand-purple">10-K</span>
                ) : null}
              </div>
              <p className="text-sm text-ink-700 mb-2">{c.summary}</p>
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-ink-400">{c.outcome}</span>
                <div className="flex items-center gap-1.5">
                  <div className="w-14 bg-surface-100 rounded-full h-1">
                    <div
                      className="h-1 rounded-full"
                      style={{
                        width: `${simPct}%`,
                        background: 'linear-gradient(90deg, #00d4ff, #8b5cf6)',
                      }}
                    />
                  </div>
                  <span className="text-[11px] font-semibold brand-gradient-text">{simPct}%</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
