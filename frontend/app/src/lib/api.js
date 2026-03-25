const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost'

const INGESTION_URL = `${API_BASE}:8000`
const LLM_URL = `${API_BASE}:8003`

/**
 * Upload a PDF to the ingestion service and get extracted entities.
 * POST /extract (multipart/form-data)
 */
export async function extractDocument(file) {
  const form = new FormData()
  form.append('file', file)

  const res = await fetch(`${INGESTION_URL}/extract`, {
    method: 'POST',
    body: form,
  })

  if (!res.ok) {
    const err = await res.text()
    throw new Error(`Ingestion failed: ${err}`)
  }

  return res.json()
}

/**
 * Send extracted data to the LLM orchestrator for full analysis.
 * POST /synthesize (JSON)
 */
export async function synthesizeAnalysis({ submission_id, entity_summary, full_text }) {
  const res = await fetch(`${LLM_URL}/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ submission_id, entity_summary, full_text }),
  })

  if (!res.ok) {
    const err = await res.text()
    throw new Error(`Synthesis failed: ${err}`)
  }

  return res.json()
}

/**
 * Run the full pipeline: extract → synthesize, and merge into the shape
 * that AnalysisView expects.
 */
export async function runPipeline(file, onStageChange) {
  // Stage 0: Extracting entities
  onStageChange(0)
  const extraction = await extractDocument(file)

  // Stage 1: Running prediction model
  onStageChange(1)
  // Stage 2: Searching similar cases (prediction + RAG happen inside /synthesize)
  const synthesisPromise = synthesizeAnalysis({
    submission_id: extraction.submission_id,
    entity_summary: extraction.entity_summary,
    full_text: extraction.full_text,
  })

  // Simulate stage progression while waiting for synthesis
  const stageTimer = setTimeout(() => onStageChange(2), 1500)
  const synthesis = await synthesisPromise
  clearTimeout(stageTimer)

  // Stage 3: Generating narrative (already done)
  onStageChange(3)

  // Merge extraction + synthesis into the shape AnalysisView expects
  return {
    submission_id: synthesis.submission_id,
    filename: extraction.filename,
    risk_tier: synthesis.risk_tier,
    risk_probability: synthesis.risk_probability,
    predicted_claim_amount: synthesis.predicted_claim_amount,
    key_risk_factors: synthesis.key_risk_factors,
    underwriter_narrative: synthesis.underwriter_narrative,
    similar_cases: synthesis.similar_cases,
    confidence_score: synthesis.confidence_score,
    processing_time_ms: synthesis.processing_time_ms,
    entities: extraction.entity_summary,
    pipeline_trace: {
      ingestion_ms: extraction.processing_time_ms,
      prediction_ms: null,
      rag_ms: null,
      llm_ms: synthesis.processing_time_ms,
    },
  }
}
