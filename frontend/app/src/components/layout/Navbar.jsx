import { Link } from 'react-router-dom'
import Logo from '@/components/shared/Logo'

export default function Navbar() {
  return (
    <nav className="fixed top-0 w-full z-50 bg-dark-900/80 backdrop-blur-xl border-b border-white/5">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3">
          <Logo className="h-7 w-auto" />
        </Link>
        <div className="flex items-center gap-8">
          <a href="#features" className="text-sm text-white/50 hover:text-white/90 transition">Features</a>
          <a href="#pipeline" className="text-sm text-white/50 hover:text-white/90 transition">Pipeline</a>
          <a href="#tech" className="text-sm text-white/50 hover:text-white/90 transition">Tech Stack</a>
          <Link to="/app" className="px-4 py-2 text-sm font-medium brand-gradient rounded-lg hover:opacity-90 transition brand-glow cursor-pointer">
            Launch App
          </Link>
        </div>
      </div>
    </nav>
  )
}
