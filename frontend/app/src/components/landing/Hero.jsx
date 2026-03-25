import { Link } from 'react-router-dom'

export default function Hero() {
  return (
    <section className="hero-gradient min-h-screen flex items-center pt-20">
      <div className="max-w-6xl mx-auto px-6 py-20">
        <div className="max-w-3xl">
          <div className="fade-up">
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-white/60 mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              4-Stage GenAI Pipeline
            </span>
          </div>

          <h1 className="text-5xl font-bold leading-tight mb-6 fade-up fade-up-delay-1">
            Automated Risk<br />
            <span className="brand-gradient-text">Intelligence Assistant</span>
          </h1>

          <p className="text-lg text-white/50 leading-relaxed max-w-xl mb-10 fade-up fade-up-delay-2">
            ARIA transforms insurance underwriting with AI. Upload a document, extract risk entities, predict claim probability, and generate explainable underwriter narratives — in seconds, not hours.
          </p>

          <div className="flex items-center gap-4 fade-up fade-up-delay-3">
            <Link to="/app" className="px-6 py-3 text-sm font-semibold brand-gradient rounded-xl hover:opacity-90 transition brand-glow cursor-pointer">
              Try the Demo
            </Link>
            <a href="#pipeline" className="px-6 py-3 text-sm font-medium text-white/60 border border-white/10 rounded-xl hover:border-white/25 hover:text-white/80 transition cursor-pointer">
              See How It Works
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}
