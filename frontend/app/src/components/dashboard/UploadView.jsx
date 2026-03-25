import { useState, useRef } from 'react'
import { getAllDemos } from '@/hooks/useDemoData'
import { runPipeline } from '@/lib/api'
import RiskBadge from '@/components/shared/RiskBadge'

const STAGE_LABELS = ['Extracting entities...', 'Running prediction model...', 'Searching similar cases...', 'Generating narrative...']

export default function UploadView({ onSelectDemo, onLiveResult }) {
  const [processing, setProcessing] = useState(false)
  const [stage, setStage] = useState(0)
  const [error, setError] = useState(null)
  const fileRef = useRef(null)
  const demos = getAllDemos()

  async function handleFile(file) {
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
      setError('Please upload a PDF file.')
      return
    }
    setError(null)
    setProcessing(true)
    setStage(0)

    try {
      const result = await runPipeline(file, setStage)
      setProcessing(false)
      onLiveResult(result)
    } catch (err) {
      console.error(err)
      setProcessing(false)
      setError(err.message || 'Pipeline failed. Make sure Docker services are running.')
    }
  }

  function handleUploadClick() {
    fileRef.current?.click()
  }

  function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = ''
  }

  function handleDrop(e) {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  function handleDragOver(e) {
    e.preventDefault()
  }

  if (processing) {
    return (
      <div className="max-w-2xl mx-auto fade-in">
        <div className="bg-white rounded-xl border border-surface-200 p-14 text-center">
          <div className="w-16 h-16 mx-auto mb-5 rounded-2xl brand-gradient flex items-center justify-center pulse-glow">
            <svg className="w-7 h-7 text-white animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>
          <p className="text-ink-800 font-medium mb-2">Processing document...</p>
          <p className="text-ink-400 text-sm mb-6">{STAGE_LABELS[stage]}</p>
          <div className="flex justify-center gap-1.5">
            {STAGE_LABELS.map((_, i) => (
              <div key={i} className={`w-2 h-2 rounded-full transition-colors ${i <= stage ? 'bg-brand-cyan' : 'bg-surface-200'}`} />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto fade-in">
      <input
        ref={fileRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* Upload Zone */}
      <div
        onClick={handleUploadClick}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className="upload-zone rounded-xl p-14 text-center cursor-pointer bg-white"
      >
        <div className="w-16 h-16 mx-auto mb-5 rounded-2xl brand-gradient flex items-center justify-center brand-glow">
          <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <p className="text-ink-800 font-medium mb-1">Drag and drop your PDF here</p>
        <p className="text-ink-400 text-sm mb-5">or click to browse files</p>
        <span className="inline-block px-5 py-2.5 brand-gradient text-white text-sm font-medium rounded-lg cursor-pointer hover:opacity-90 transition brand-glow">
          Select File
        </span>
        <p className="text-ink-300 text-xs mt-5">PDF only, max 25MB, up to 200 pages</p>
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Recent Submissions (Demo) */}
      <div className="mt-10">
        <h3 className="text-xs font-semibold text-ink-400 uppercase tracking-wider mb-4">Demo Submissions</h3>
        <div className="space-y-2">
          {demos.map((demo) => (
            <div
              key={demo.id}
              onClick={() => onSelectDemo(demo.id)}
              className="card flex items-center justify-between px-4 py-3.5 cursor-pointer hover:border-brand-cyan/30"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-surface-100 flex items-center justify-center">
                  <svg className="w-4 h-4 text-ink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-ink-800">{demo.filename}</p>
                  <p className="text-xs text-ink-400">{demo.submission_id}</p>
                </div>
              </div>
              <RiskBadge tier={demo.risk_tier} size="sm" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
