"""Optional consistency check; credentials are injected, never committed."""
import os

import pytest

from rr_ai_work import (
    DETAIL_PATH, FEED_PATH, VERSIONS, Blocked, ai_state,
    detail_matches_feed, feed_rows, request_api,
)

pytestmark = [pytest.mark.live, pytest.mark.detail]


@pytest.fixture(scope="module")
def detail_samples():
    if os.getenv("RR_AI_LIVE") != "1":
        raise Blocked("BLOCKED: use run_ai_work.py --suite detail")
    identity = os.getenv("RR_AI_ALI_ID", "").strip()
    if not identity:
        raise Blocked("BLOCKED: RR_AI_ALI_ID is not configured; no detail request sent")
    samples = {}
    rows = feed_rows(request_api(FEED_PATH, VERSIONS[1]))
    for row in rows:
        state = ai_state(row["drama"])
        first = row.get("firstEpisode")
        if state in {"true", "false"} and state not in samples and isinstance(first, dict) and first.get("sid"):
            drama_id = row["drama"]["dramaId"]
            params = {"dramaId": drama_id, "episodeSid": first["sid"], "isAgeLimit": "false"}
            samples[state] = (drama_id, request_api(DETAIL_PATH, VERSIONS[1], params=params, ali_id=identity))
        if len(samples) == 2:
            break
    return samples


@pytest.mark.parametrize("state", ["true", "false"])
def test_detail_ai_state_matches_feed(detail_samples, state):
    if state not in detail_samples:
        raise Blocked("BLOCKED: missing a feed sample with a usable firstEpisode.sid")
    drama_id, response = detail_samples[state]
    detail_matches_feed(response, drama_id, state)
