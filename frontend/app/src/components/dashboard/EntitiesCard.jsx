const ENTITY_STYLES = {
  PERIL: 'bg-red-50 text-red-600',
  COVERAGE_TYPE: 'bg-blue-50 text-blue-600',
  MONEY: 'bg-emerald-50 text-emerald-600',
  PROPERTY_TYPE: 'bg-amber-50 text-amber-600',
  VEHICLE: 'bg-indigo-50 text-indigo-600',
  INJURY: 'bg-pink-50 text-pink-600',
}

const ENTITY_LABELS = {
  PERIL: 'Peril',
  COVERAGE_TYPE: 'Coverage',
  MONEY: 'Money',
  PROPERTY_TYPE: 'Property',
  VEHICLE: 'Vehicle',
  INJURY: 'Injury',
}

export default function EntitiesCard({ entities }) {
  const displayEntities = Object.entries(entities).filter(([, values]) => values.length > 0)

  return (
    <div className="card p-5 flex flex-col">
      <h3 className="text-sm font-semibold text-ink-900 mb-3 shrink-0">Extracted Entities</h3>
      <div className="space-y-2.5 overflow-y-auto max-h-[300px] pr-1">
        {displayEntities.map(([type, values]) => (
          <div key={type}>
            <span className={`inline-block px-2 py-0.5 text-[10px] font-semibold rounded mb-1 uppercase tracking-wide ${ENTITY_STYLES[type] || 'bg-gray-50 text-gray-600'}`}>
              {ENTITY_LABELS[type] || type}
            </span>
            <p className="text-sm text-ink-700">{values.join(', ')}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
