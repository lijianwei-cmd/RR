"""Backend contract evidence; does not claim Android UI or CMS acceptance."""
import os

import pytest

from rr_ai_work import (
    FEED_PATH, VERSIONS, Blocked, compare_versions, feed_index,
    request_api, require_positive_negative, successful_data,
)

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def responses():
    if os.getenv("RR_AI_LIVE") != "1":
        raise Blocked("BLOCKED: use run_ai_work.py --suite feed to explicitly run Alpha tests")
    return {version: request_api(FEED_PATH, version) for version in VERSIONS}


@pytest.mark.parametrize("version", VERSIONS)
def test_http_and_business_success(responses, version):
    successful_data(responses[version])


@pytest.mark.parametrize("version", VERSIONS)
def test_nullable_boolean_contract(responses, version, record_property):
    index = feed_index(responses[version])
    for state in ("true", "false", "null", "missing"):
        record_property(state + "_count", sum(value == state for value in index.values()))


@pytest.mark.parametrize("version", VERSIONS)
def test_ai_and_non_ai_sample_coverage(responses, version):
    require_positive_negative(responses[version])


def test_shared_drama_has_no_observed_version_difference(responses, record_property):
    compare_versions(responses[VERSIONS[0]], responses[VERSIONS[1]])
    common = feed_index(responses[VERSIONS[0]]).keys() & feed_index(responses[VERSIONS[1]]).keys()
    record_property("compared_drama_ids", ",".join(str(value) for value in sorted(common)))
