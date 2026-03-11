from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator


def setup_metrics(app: FastAPI) -> None:
    """Instrument a FastAPI app with Prometheus metrics.

    Exposes /metrics endpoint that Prometheus can scrape.
    Automatically tracks request count, latency, and response size
    for all endpoints except health checks and the metrics endpoint itself.
    """
    Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/health", "/ready", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics")
