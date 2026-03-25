const stages = [
  {
    number: '1',
    title: 'Ingestion + NER',
    description: 'PySpark ingests documents. spaCy NER with custom insurance patterns extracts risk entities.',
    color: 'from-cyan-500/20 to-cyan-500/5 border-cyan-500/20',
    numColor: 'text-brand-cyan',
    tags: ['PySpark', 'spaCy', 'FastAPI'],
  },
  {
    number: '2',
    title: 'Prediction',
    description: 'XGBoost scores claim probability and severity. SHAP explains feature contributions.',
    color: 'from-blue-500/20 to-blue-500/5 border-blue-500/20',
    numColor: 'text-blue-400',
    tags: ['XGBoost', 'SHAP'],
  },
  {
    number: '3',
    title: 'RAG Retrieval',
    description: 'Sentence-transformers embed entities. FAISS retrieves top-k similar cases from claims + SEC EDGAR filings.',
    color: 'from-indigo-500/20 to-indigo-500/5 border-indigo-500/20',
    numColor: 'text-indigo-400',
    tags: ['FAISS', 'MiniLM', 'EDGAR'],
  },
  {
    number: '4',
    title: 'LLM Synthesis',
    description: 'Claude orchestrates via tool-use — calls prediction and RAG, then generates the underwriter narrative.',
    color: 'from-purple-500/20 to-purple-500/5 border-purple-500/20',
    numColor: 'text-brand-purple',
    tags: ['Claude', 'Ollama', 'Tool-use'],
  },
]

export default function Pipeline() {
  return (
    <section id="pipeline" className="py-24 bg-dark-900">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold mb-4">The 4-Stage Pipeline</h2>
          <p className="text-white/40 max-w-lg mx-auto">
            Each stage runs as an independent microservice, orchestrated by Docker Compose.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stages.map((stage) => (
            <div key={stage.number} className="pipeline-line text-center">
              <div className={`w-14 h-14 mx-auto rounded-2xl bg-gradient-to-br ${stage.color} border flex items-center justify-center mb-4`}>
                <span className={`${stage.numColor} font-bold text-lg`}>{stage.number}</span>
              </div>
              <h3 className="text-sm font-semibold mb-2">{stage.title}</h3>
              <p className="text-xs text-white/40 leading-relaxed">{stage.description}</p>
              <div className="mt-3 flex flex-wrap justify-center gap-1">
                {stage.tags.map((tag) => (
                  <span key={tag} className="px-2 py-0.5 text-[10px] bg-white/5 rounded text-white/30">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
