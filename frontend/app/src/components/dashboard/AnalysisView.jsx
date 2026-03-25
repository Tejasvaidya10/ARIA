import KpiCards from './KpiCards'
import ShapFactors from './ShapFactors'
import EntitiesCard from './EntitiesCard'
import NarrativeCard from './NarrativeCard'
import SimilarCases from './SimilarCases'
import PipelineTrace from './PipelineTrace'

export default function AnalysisView({ data }) {
  return (
    <div className="fade-in">
      <KpiCards data={data} />

      <div className="grid grid-cols-3 gap-5">
        {/* Left column: SHAP + Entities */}
        <div className="col-span-1 space-y-5">
          <ShapFactors factors={data.key_risk_factors} />
          <EntitiesCard entities={data.entities} />
        </div>

        {/* Center column: Narrative */}
        <div className="col-span-1">
          <NarrativeCard narrative={data.underwriter_narrative} />
        </div>

        {/* Right column: Similar Cases + Pipeline */}
        <div className="col-span-1 space-y-5">
          <SimilarCases cases={data.similar_cases} />
          <PipelineTrace trace={data.pipeline_trace} />
        </div>
      </div>
    </div>
  )
}
