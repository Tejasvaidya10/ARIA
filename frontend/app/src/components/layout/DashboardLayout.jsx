import Sidebar from './Sidebar'

export default function DashboardLayout({ children, title, subtitle, view, onViewChange, headerRight }) {
  return (
    <div className="bg-surface-100 min-h-screen flex">
      <Sidebar view={view} onViewChange={onViewChange} />
      <main className="ml-64 flex-1 min-h-screen">
        <header className="bg-white border-b border-surface-200 px-8 py-4 flex items-center justify-between sticky top-0 z-[5]">
          <div>
            <h2 className="text-lg font-semibold text-ink-900">{title}</h2>
            <p className="text-xs text-ink-500 mt-0.5">{subtitle}</p>
          </div>
          <div className="flex items-center gap-3">
            {headerRight || (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-50 rounded-lg border border-surface-200">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span className="text-xs text-ink-500">Demo Mode</span>
              </div>
            )}
          </div>
        </header>
        <div className="px-8 py-8">
          {children}
        </div>
      </main>
    </div>
  )
}
