import { Link } from 'react-router-dom'

export default function CallToAction() {
  return (
    <section className="py-24 bg-dark-900 hero-gradient">
      <div className="max-w-3xl mx-auto px-6 text-center">
        <h2 className="text-3xl font-bold mb-4">See ARIA in Action</h2>
        <p className="text-white/40 mb-8 max-w-md mx-auto">
          Upload a document and watch the full pipeline run — from entity extraction to the final underwriter narrative.
        </p>
        <Link to="/app" className="inline-block px-8 py-3.5 text-sm font-semibold brand-gradient rounded-xl hover:opacity-90 transition brand-glow cursor-pointer">
          Launch Dashboard
        </Link>
      </div>
    </section>
  )
}
