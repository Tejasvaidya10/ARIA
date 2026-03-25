import { Link, useLocation } from 'react-router-dom'
import Logo from '@/components/shared/Logo'

const PIPELINE_SERVICES = [
  { name: 'Ingestion', port: ':8000' },
  { name: 'Prediction', port: ':8001' },
  { name: 'RAG', port: ':8002' },
  { name: 'LLM', port: ':8003' },
]

export default function Sidebar({ view, onViewChange }) {
  const location = useLocation()
  const isEval = location.pathname === '/eval'

  return (
    <aside className="w-64 bg-dark-800 min-h-screen flex flex-col fixed left-0 top-0 bottom-0 z-10">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/5">
        <Link to="/" className="flex items-center gap-3">
          <Logo className="h-8 w-auto" />
        </Link>
        <p className="text-white/30 text-xs mt-2">Automated Risk Intelligence</p>
      </div>

      {/* Nav items */}
      <nav className="flex-1 py-4 px-3">
        <p className="text-white/25 text-[10px] font-semibold uppercase tracking-widest px-3 mb-2">Analysis</p>

        <button
          onClick={() => onViewChange('upload')}
          className={`sidebar-item w-full flex items-center gap-3 px-3 py-2.5 rounded-r-lg text-sm mb-0.5 ${
            !isEval && view === 'upload' ? 'sidebar-active text-white/90' : 'text-white/50'
          }`}
        >
          <svg className={`w-4 h-4 ${!isEval && view === 'upload' ? 'text-brand-cyan' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          Upload
        </button>

        <button
          onClick={() => onViewChange('analysis')}
          className={`sidebar-item w-full flex items-center gap-3 px-3 py-2.5 rounded-r-lg text-sm mb-0.5 ${
            !isEval && view === 'analysis' ? 'sidebar-active text-white/90' : 'text-white/50'
          }`}
        >
          <svg className={`w-4 h-4 ${!isEval && view === 'analysis' ? 'text-brand-cyan' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Dashboard
        </button>

        <p className="text-white/25 text-[10px] font-semibold uppercase tracking-widest px-3 mt-6 mb-2">Validation</p>

        <Link
          to="/eval"
          className={`sidebar-item w-full flex items-center gap-3 px-3 py-2.5 rounded-r-lg text-sm mb-0.5 ${
            isEval ? 'sidebar-active text-white/90' : 'text-white/50'
          }`}
        >
          <svg className={`w-4 h-4 ${isEval ? 'text-brand-cyan' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Evaluation
        </Link>
      </nav>

      {/* Pipeline status */}
      <div className="px-5 py-4 border-t border-white/5">
        <div className="flex items-center justify-between mb-3">
          <p className="text-white/25 text-[10px] font-semibold uppercase tracking-widest">Pipeline</p>
          <span className="text-[10px] text-white/20 font-mono">Demo Mode</span>
        </div>
        <div className="space-y-2">
          {PIPELINE_SERVICES.map((svc) => (
            <div key={svc.name} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span className="text-white/50 text-xs">{svc.name}</span>
              </div>
              <span className="text-white/20 text-[10px] font-mono">{svc.port}</span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  )
}
