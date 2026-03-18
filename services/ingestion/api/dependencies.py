from fastapi import Request
from pyspark.sql import SparkSession
from spacy.language import Language

from services.ingestion.config import IngestionSettings


def get_settings(request: Request) -> IngestionSettings:
    return request.app.state.settings  # type: ignore[no-any-return]


def get_spark(request: Request) -> SparkSession:
    return request.app.state.spark  # type: ignore[no-any-return]


def get_nlp(request: Request) -> Language:
    return request.app.state.nlp  # type: ignore[no-any-return]
