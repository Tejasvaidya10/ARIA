const stack = [
  ['Data Engineering', 'PySpark'],
  ['ML Model', 'XGBoost + SHAP'],
  ['NLP', 'spaCy (custom NER)'],
  ['Embeddings', 'all-MiniLM-L6-v2'],
  ['Vector Store', 'FAISS'],
  ['LLM', 'Claude / Ollama'],
  ['API', 'FastAPI'],
  ['Orchestration', 'Docker Compose'],
  ['Frontend', 'React + Tailwind'],
  ['CI/CD', 'GitHub Actions'],
  ['Data Sources', 'Kaggle + SEC EDGAR'],
  ['Explainability', 'SHAP values'],
]

export default function TechStack() {
  return (
    <section id="tech" className="py-24 bg-dark-900">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold mb-4">Built With</h2>
          <p className="text-white/40 max-w-lg mx-auto">Production-grade tooling. No shortcuts.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-16 gap-y-4 max-w-3xl mx-auto">
          {stack.map(([category, tool]) => (
            <div key={category} className="flex items-center justify-between py-3 border-b border-white/5">
              <span className="text-sm text-white/60">{category}</span>
              <span className="text-sm font-medium text-white/90">{tool}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
