import pytest


@pytest.fixture
def sample_entity_summary() -> dict[str, list[str]]:
    return {
        "PERSON": ["John Smith"],
        "MONEY": ["$50,000", "$500,000"],
        "PERIL": ["fire", "water damage"],
        "COVERAGE_TYPE": ["commercial general liability", "umbrella coverage"],
        "CLAIM_STATUS": ["pending review"],
        "PROPERTY_TYPE": ["wood-frame residential"],
        "POLICY_NUMBER": ["PLY-2024-00892"],
    }


@pytest.fixture
def empty_entity_summary() -> dict[str, list[str]]:
    return {}
