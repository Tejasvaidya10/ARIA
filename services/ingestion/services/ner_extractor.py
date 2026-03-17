from typing import Any

import spacy
from spacy.language import Language

from services.ingestion.core.schemas import InsuranceEntity

# Module-level reference so PySpark UDFs can access the loaded model
# without serialization. Only works in local mode (same process).
_nlp: Language | None = None


def load_nlp_pipeline(model_path: str, entity_patterns: list[dict[str, Any]]) -> Language:
    """Load spaCy with an EntityRuler for insurance-specific entities."""
    global _nlp
    nlp = spacy.load(model_path)

    ruler = nlp.add_pipe("entity_ruler", before="ner")
    ruler.add_patterns(entity_patterns)  # type: ignore[attr-defined]

    _nlp = nlp
    return nlp


def extract_entities(text: str, nlp: Language | None = None) -> list[InsuranceEntity]:
    """Run NER on text and return structured entities."""
    pipeline = nlp or _nlp
    if pipeline is None:
        raise RuntimeError("NLP pipeline not loaded — call load_nlp_pipeline first")

    doc = pipeline(text)
    return [
        InsuranceEntity(
            text=ent.text,
            label=ent.label_,
            start_char=ent.start_char,
            end_char=ent.end_char,
            confidence=1.0 if ent._.has("pattern") else 0.85,
        )
        for ent in doc.ents
    ]


def deduplicate_entities(entities: list[InsuranceEntity]) -> list[InsuranceEntity]:
    """Remove duplicate entities, keeping the highest confidence one."""
    seen: dict[tuple[str, str], InsuranceEntity] = {}
    for ent in entities:
        key = (ent.text.lower(), ent.label)
        if key not in seen or ent.confidence > seen[key].confidence:
            seen[key] = ent
    return list(seen.values())


def summarize_entities(entities: list[InsuranceEntity]) -> dict[str, list[str]]:
    """Group unique entity texts by label."""
    summary: dict[str, list[str]] = {}
    for ent in entities:
        if ent.label not in summary:
            summary[ent.label] = []
        if ent.text not in summary[ent.label]:
            summary[ent.label].append(ent.text)
    return summary
