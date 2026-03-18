import pytest


@pytest.fixture()
def sample_entity_summary() -> dict[str, list[str]]:
    return {
        "PERIL": ["fire", "flood"],
        "COVERAGE_TYPE": ["general liability", "property"],
        "PROPERTY_TYPE": ["warehouse"],
        "MONEY": ["$1,000,000", "$500,000"],
        "CLAIM_STATUS": ["open"],
    }


@pytest.fixture()
def empty_entity_summary() -> dict[str, list[str]]:
    return {}
