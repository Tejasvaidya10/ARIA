export default function Architecture() {
  return (
    <section className="py-24 bg-dark-950">
      <div className="max-w-4xl mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Architecture</h2>
          <p className="text-white/40">4 microservices on an internal Docker network</p>
        </div>

        <div className="bg-dark-800 rounded-2xl border border-white/5 p-8 font-mono text-sm overflow-x-auto">
          <pre className="text-white/50 leading-loose">
{`$ `}<span className="text-brand-cyan">docker compose up --build</span>{`

  `}<span className="text-white/30">+-----------------+     +-----------------+</span>{`
  `}<span className="text-white/30">|</span> <span className="text-cyan-400">ingestion</span>       <span className="text-white/30">|     |</span> <span className="text-blue-400">prediction</span>      <span className="text-white/30">|</span>{`
  `}<span className="text-white/30">|</span>{` PySpark + spaCy  `}<span className="text-white/30">|     |</span>{` XGBoost + SHAP  `}<span className="text-white/30">|</span>{`
  `}<span className="text-white/30">|</span> <span className="text-white/20">:8000</span>{`            `}<span className="text-white/30">|     |</span> <span className="text-white/20">:8001</span>{`           `}<span className="text-white/30">|</span>{`
  `}<span className="text-white/30">+-----------------+     +---------+-------+</span>{`
                                    `}<span className="text-white/20">|</span>{`
  `}<span className="text-white/30">+-----------------+     +---------+-------+</span>{`
  `}<span className="text-white/30">|</span> <span className="text-indigo-400">rag</span>{`             `}<span className="text-white/30">|     |</span> <span className="text-purple-400">llm</span>{`             `}<span className="text-white/30">|</span>{`
  `}<span className="text-white/30">|</span>{` FAISS + MiniLM   `}<span className="text-white/30">|     |</span>{` Claude / Ollama `}<span className="text-white/30">|</span>{`
  `}<span className="text-white/30">|</span> <span className="text-white/20">:8002</span>{`            `}<span className="text-white/30">|-----+</span> <span className="text-white/20">:8003</span>{`           `}<span className="text-white/30">|</span>{`
  `}<span className="text-white/30">+-----------------+     +-----------------+</span>
          </pre>
        </div>
      </div>
    </section>
  )
}
