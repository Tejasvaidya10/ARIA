const stats = [
  { value: '2,126', label: 'Indexed vectors in FAISS' },
  { value: '28ms', label: 'RAG retrieval latency' },
  { value: '8', label: 'SEC EDGAR insurers indexed' },
  { value: '2.6s', label: 'End-to-end pipeline' },
]

export default function Stats() {
  return (
    <section className="py-20 bg-dark-950 border-y border-white/5">
      <div className="max-w-6xl mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {stats.map((stat) => (
            <div key={stat.label}>
              <p className="text-3xl font-bold brand-gradient-text">{stat.value}</p>
              <p className="text-xs text-white/30 mt-1">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
