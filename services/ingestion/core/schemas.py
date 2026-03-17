from pydantic import BaseModel, Field


class InsuranceEntity(BaseModel):
    text: str
    label: str
    start_char: int
    end_char: int
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class PageExtraction(BaseModel):
    page_number: int
    text: str
    entities: list[InsuranceEntity]


class ExtractedDocument(BaseModel):
    submission_id: str
    filename: str
    page_count: int
    full_text: str
    pages: list[PageExtraction]
    entities: list[InsuranceEntity]
    entity_summary: dict[str, list[str]]
    processing_time_ms: float
