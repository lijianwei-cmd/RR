import pytest
import requests

from rr_ai_work import (
    ApiResponse, Blocked, DETAIL_PATH, FEED_PATH, ai_state,
    compare_versions, detail_matches_feed, feed_index,
    request_api, require_positive_negative, successful_data,
)


def response(*dramas):
    return ApiResponse(200, {"code": "0000", "data": {"content": [{"drama": x} for x in dramas]}})


@pytest.mark.parametrize("drama,state", [({}, "missing"), ({"isAiWork": None}, "null"),
    ({"isAiWork": True}, "true"), ({"isAiWork": False}, "false")])
def test_preserves_all_four_states(drama, state):
    assert ai_state(drama) == state


@pytest.mark.parametrize("invalid", [0, 1, "true", "false", "", [], {}])
def test_rejects_truthy_and_numeric_coercion(invalid):
    with pytest.raises(AssertionError):
        ai_state({"isAiWork": invalid})


@pytest.mark.parametrize("value", [ApiResponse(403, {}), ApiResponse(200, {"code": "403", "data": {}}),
    ApiResponse(200, {"code": 0, "data": {}}), ApiResponse(200, {"code": "0000", "data": None})])
def test_rejects_http_and_business_failure(value):
    with pytest.raises(AssertionError):
        successful_data(value)


def test_empty_feed_is_blocked_not_a_pass():
    with pytest.raises(Blocked):
        feed_index(response())


def test_missing_positive_sample_blocks_coverage():
    with pytest.raises(Blocked):
        require_positive_negative(response({"dramaId": 1, "isAiWork": False}))


def test_versions_cannot_turn_true_into_missing():
    with pytest.raises(AssertionError):
        compare_versions(response({"dramaId": 1, "isAiWork": True}), response({"dramaId": 1}))


def test_null_and_missing_compare_as_unknown():
    compare_versions(response({"dramaId": 1, "isAiWork": None}), response({"dramaId": 1}))


def test_no_shared_drama_blocks_comparison():
    with pytest.raises(Blocked):
        compare_versions(response({"dramaId": 1}), response({"dramaId": 2}))


def test_detail_must_match_requested_drama_and_state():
    r = ApiResponse(200, {"code": "0000", "data": {"dramaInfo": {"dramaId": 1, "isAiWork": True}}})
    detail_matches_feed(r, 1, "true")
    with pytest.raises(AssertionError):
        detail_matches_feed(r, 2, "true")
    with pytest.raises(AssertionError):
        detail_matches_feed(r, 1, "false")


def test_detail_missing_identity_never_sends():
    with pytest.raises(Blocked):
        request_api(DETAIL_PATH, "10.40.0")


@pytest.mark.parametrize("path", ["https://api.qwdjapp.com/app/drama/page", "/unknown"])
def test_only_reviewed_test_paths_allowed(path):
    with pytest.raises(ValueError):
        request_api(path, "10.40.0")


def test_no_redirect_and_no_credentials_on_feed():
    class Fake:
        def get(self, url, **kwargs):
            assert url == "https://alpha-api.duoduoshipin.vip/app/drama/playlet/feed"
            assert kwargs["headers"] == {"ct": "android_rrsp_xb_RRMJ_REPLACE", "cv": "10.39.2"}
            assert kwargs["allow_redirects"] is False
            raise requests.ConnectionError("secret-must-not-be-reported")
    result = request_api(FEED_PATH, "10.39.2", session=Fake())
    assert result.error == "ConnectionError"
    assert "secret" not in result.error
