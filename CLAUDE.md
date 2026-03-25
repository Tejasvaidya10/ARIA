# ARIA — Project Instructions

## What is ARIA?
ARIA (Automated Risk Intelligence Assistant) is a 4-stage GenAI pipeline for insurance underwriting. Upload a document, extract risk entities via NER, predict claim probability with XGBoost, retrieve similar cases via RAG, and generate an explainable underwriter narrative with Claude.

## Architecture

4 FastAPI microservices orchestrated by Docker Compose:

| Service    | Port | Stack                        |
|------------|------|------------------------------|
| ingestion  | 8000 | PySpark + spaCy (custom NER) |
| prediction | 8001 | XGBoost + SHAP (28 features) |
| rag        | 8002 | FAISS + all-MiniLM-L6-v2     |
| llm        | 8003 | Claude (tool-use) / Ollama   |

## Project Structure

```
services/
  ingestion/    # PDF upload → text extraction → spaCy NER → entity_summary
  prediction/   # entity_summary → XGBoost risk tier + SHAP explanations
  rag/          # entity_summary → FAISS similarity search → similar cases
  llm/          # orchestrates prediction + RAG via tool-use → narrative
scripts/
  train_xgboost.py    # Train model on Kaggle data
  build_case_index.py # Build FAISS index from Kaggle claims
  download_edgar.py   # Download SEC EDGAR 10-K filings
  index_edgar.py      # Chunk + index EDGAR filings into FAISS
  eval_pipeline.py    # 20-case stratified evaluation
frontend/
  app/          # React + Vite scaffold (Tailwind, React Router)
  mockup/       # HTML/Tailwind mockups (landing.html, index.html)
  assets/       # aria-logo.png
data/
  raw/          # insurance_claims.csv (Kaggle)
  edgar/        # SEC EDGAR 10-K text files
  faiss/        # FAISS index files (gitignored)
  eval/         # eval_report.json
```

## Development

```bash
# Activate venv
source .venv/bin/activate

# Run all tests (55 tests)
python -m pytest services/ -x -q

# Lint
ruff check .

# Docker (all 4 services)
docker compose up --build

# Train model
python scripts/train_xgboost.py

# Run evaluation
python scripts/eval_pipeline.py
```

## Coding Conventions

- **Python:** Ruff for linting + formatting. Follow existing patterns in each service.
- **FastAPI tests:** Use `TestClient`, NOT `httpx.AsyncClient`. AsyncClient does not trigger FastAPI lifespan events.
- **PySpark:** Set `os.environ["PYSPARK_PYTHON"] = sys.executable` before creating SparkSession.
- **Entity summaries:** All data flows through `entity_summary` dicts (e.g., `{"PERIL": ["fire", "flood"], "MONEY": ["$50000"]}`). Training and inference use the same `extract_features()` function.
- **Pre-commit hooks:** May auto-fix files without completing the commit. Re-stage with `git add .` and commit again.

## Key Design Decisions

- **ML target is severity-based** (incident_severity mapped to risk tiers), not dollar-based
- **No CLAIM_STATUS in entity summaries** — it leaked the target variable
- **Provider protocol pattern** for LLM service — AnthropicProvider + OllamaProvider behind a common interface
- **FAISS IndexFlatIP** for vector search — 2,126 vectors, sub-50ms latency
- **EDGAR case IDs offset by 10000** to avoid collisions with Kaggle case IDs

## Frontend Design

- **Font:** Poppins + Fira Code (mono)
- **Brand colors:** cyan `#00d4ff`, blue `#1e3a8a`, purple `#8b5cf6`
- **Risk colors:** LOW `#10b981`, MODERATE `#f59e0b`, HIGH `#f97316`, CRITICAL `#ef4444`
- **Logo:** `frontend/assets/aria-logo.png`
- **Mockups:** `frontend/mockup/landing.html` (dark theme landing) and `frontend/mockup/index.html` (light theme dashboard)

## Evaluation Framework

The eval pipeline (`scripts/eval_pipeline.py`) runs 20 stratified cases (5 per severity tier, seed=42) through prediction + RAG and validates outputs.

### Checks per case
| Check | What it validates |
|-------|-------------------|
| tier_match | Predicted risk tier == expected tier (from incident_severity) |
| tier_adjacent | Predicted tier within 1 ordinal step of expected |
| claim_reasonable | Predicted claim > 0 and ratio to actual between 0.05x–20x |
| shap_grounded | All SHAP factor names exist in FEATURE_DISPLAY_NAMES (no hallucinated features) |
| rag_has_results | At least 1 FAISS result with similarity > 0 |
| rag_type_match | Retrieved case contains same incident type keyword |
| consistency | Re-running same case produces identical risk_probability |

### Current results (seed=42, 20 cases)
- Tier exact match: 55% (11/20)
- Tier adjacent match: 100% (20/20) — zero FAIL cases
- SHAP grounding: 100%
- Consistency: 100%
- Mean RAG similarity: 0.88
- Mean processing time: 22ms
- Report: `data/eval/eval_report.json`

### CLI usage
```bash
python scripts/eval_pipeline.py                    # Direct mode (no Docker)
python scripts/eval_pipeline.py --live             # Against running Docker services
python scripts/eval_pipeline.py --include-llm      # Include LLM synthesis + hallucination detection
```

## Frontend Evaluation Page

The dashboard sidebar includes an **Evaluation** button that loads `data/eval/eval_report.json` and displays:
- Metric cards: Tier Exact Match, Adjacent Match, SHAP Grounding, Consistency (each with percentage + count)
- Table of all 20 cases: index, incident type, severity, expected vs predicted tier, pass/fail, risk probability, RAG similarity
- Mean RAG similarity and processing time stats
- This page shows users/reviewers how confident the model is and that results have been validated

## Data Sources

- **Kaggle:** Auto Insurance Claims dataset at `data/raw/insurance_claims.csv`
- **SEC EDGAR:** 10-K filings from 8 insurers (AIG, Travelers, Allstate, Progressive, Chubb, MetLife, Hartford, Markel)
