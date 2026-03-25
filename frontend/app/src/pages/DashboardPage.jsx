import { useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import UploadView from '@/components/dashboard/UploadView'
import AnalysisView from '@/components/dashboard/AnalysisView'
import RiskBadge from '@/components/shared/RiskBadge'
import SubmissionEval from '@/components/dashboard/SubmissionEval'
import { useDemoData } from '@/hooks/useDemoData'

export default function DashboardPage() {
  const [view, setView] = useState('upload')
  const [selectedId, setSelectedId] = useState(null)
  const [liveData, setLiveData] = useState(null)
  const demoData = useDemoData(selectedId)

  const data = liveData || demoData

  function handleSelectDemo(id) {
    setLiveData(null)
    setSelectedId(id)
    setView('analysis')
  }

  function handleLiveResult(result) {
    setSelectedId(null)
    setLiveData(result)
    setView('analysis')
  }

  function handleViewChange(v) {
    setView(v)
    if (v === 'upload') {
      setSelectedId(null)
      setLiveData(null)
    }
  }

  const title = view === 'upload' ? 'Submit Document' : 'Risk Analysis'
  const subtitle = view === 'upload'
    ? 'Upload a policy, claim, or underwriting submission'
    : data
      ? `${data.filename} — #${data.submission_id}`
      : ''

  const headerRight = view === 'analysis' && data ? (
    <div className="flex items-center gap-3">
      <RiskBadge tier={data.risk_tier} />
      <SubmissionEval data={data} />
      <button
        onClick={() => handleViewChange('upload')}
        className="px-4 py-2 text-sm font-medium text-white brand-gradient rounded-lg hover:opacity-90 cursor-pointer transition brand-glow"
      >
        New Submission
      </button>
    </div>
  ) : undefined

  return (
    <DashboardLayout
      title={title}
      subtitle={subtitle}
      view={view}
      onViewChange={handleViewChange}
      headerRight={headerRight}
    >
      {view === 'upload' ? (
        <UploadView
          onSelectDemo={handleSelectDemo}
          onLiveResult={handleLiveResult}
        />
      ) : data ? (
        <AnalysisView data={data} />
      ) : null}
    </DashboardLayout>
  )
}
