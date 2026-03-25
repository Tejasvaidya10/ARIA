const features = [
  {
    title: 'Document Intelligence',
    description: 'Upload PDFs of policies, claims, or underwriting submissions. spaCy NER extracts risk entities — perils, coverage types, monetary values, and claim history.',
    iconColor: 'bg-cyan-500/10 text-brand-cyan',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    title: 'Explainable Predictions',
    description: 'XGBoost predicts claim probability and severity. SHAP values explain exactly which factors drive the risk score — not a black box.',
    iconColor: 'bg-blue-500/10 text-blue-400',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    title: 'AI Narratives',
    description: 'Claude synthesizes predictions, SHAP factors, and similar historical cases into a structured underwriter narrative — ready for review.',
    iconColor: 'bg-purple-500/10 text-brand-purple',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
      </svg>
    ),
  },
]

export default function Features() {
  return (
    <section id="features" className="py-24 bg-dark-950">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold mb-4 fade-up">What ARIA Does</h2>
          <p className="text-white/40 max-w-lg mx-auto fade-up fade-up-delay-1">
            An end-to-end system that replaces manual underwriting review with a GenAI-powered pipeline.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <div key={feature.title} className={`gradient-border p-6 card-glow transition fade-up fade-up-delay-${i + 1}`}>
              <div className={`w-10 h-10 rounded-xl ${feature.iconColor} flex items-center justify-center mb-4`}>
                {feature.icon}
              </div>
              <h3 className="text-base font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-sm text-white/40 leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
