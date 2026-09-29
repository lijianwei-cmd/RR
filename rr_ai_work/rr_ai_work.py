"""Contracts from the read-only TB task and API revision 33 / PRD revision 55."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

BASE_URL = "https://alpha-api.duoduoshipin.vip"
CLIENT_TYPE = "android_rrsp_xb_RRMJ_REPLACE"
VERSIONS = ("10.39.2", "10.40.0")
FEED_PATH = "/app/drama/playlet/feed"
DETAIL_PATH = "/app/drama/page"


class Blocked(AssertionError):
    """Missing evidence/preconditions, never a passing or silently skipped test."""


@dataclass
class ApiResponse:
    status: int | None
    body: Any = None
    error: str = ""


def request_api(path: str, version: str, *, params=None, ali_id="", session=None) -> ApiResponse:
    if path not in (FEED_PATH, DETAIL_PATH) or version not in VERSIONS:
        raise ValueError("Only the reviewed Alpha paths and client versions are supported.")
    if path == DETAIL_PATH and not ali_id:
        raise Blocked("BLOCKED: detail requires a currently valid RR_AI_ALI_ID; no historical value is replayed.")
    headers = {"ct": CLIENT_TYPE, "cv": version}
    if ali_id:
        headers["aliId"] = ali_id
    try:
        response = (session or requests).get(
            BASE_URL + path, headers=headers, params=params,
            timeout=(5, 20), allow_redirects=False,
        )
    except requests.RequestException as exc:
        return ApiResponse(None, error=type(exc).__name__)
    try:
        return ApiResponse(response.status_code, response.json())
    except ValueError:
        return ApiResponse(response.status_code, error="Response is not JSON")


def successful_data(response: ApiResponse) -> dict:
    assert not response.error, f"Request failed: {response.error}"
    assert response.status == 200, f"Expected HTTP 200, actual {response.status}"
    assert isinstance(response.body, dict), "Expected a JSON object"
    assert response.body.get("code") == "0000", "Business response is not successful (expected string code 0000)"
    data = response.body.get("data")
    assert isinstance(data, dict), "Expected data object"
    return data


def ai_state(drama: dict) -> str:
    if "isAiWork" not in drama:
        return "missing"
    value = drama["isAiWork"]
    if value is None:
        return "null"
    # bool is a subclass of int: never accept 0/1 or truthy strings.
    assert type(value) is bool, "isAiWork must be JSON boolean, null, or absent"
    return "true" if value else "false"


def feed_rows(response: ApiResponse) -> list[dict]:
    rows = successful_data(response).get("content")
    assert isinstance(rows, list), "Expected data.content array"
    if not rows:
        raise Blocked("BLOCKED: empty feed gives no isAiWork field evidence")
    for row in rows:
        assert isinstance(row, dict) and isinstance(row.get("drama"), dict), "Expected content[*].drama object"
        drama_id = row["drama"].get("dramaId")
        assert type(drama_id) is int and drama_id > 0, "Expected a positive integer dramaId"
    return rows


def feed_index(response: ApiResponse) -> dict[int, str]:
    result = {}
    for row in feed_rows(response):
        drama_id = row["drama"]["dramaId"]
        state = ai_state(row["drama"])
        if drama_id in result:
            assert result[drama_id] == state, "The same drama has conflicting AI states within one response"
        result[drama_id] = state
    return result


def require_positive_negative(response: ApiResponse) -> None:
    states = set(feed_index(response).values())
    if not {"true", "false"} <= states:
        raise Blocked("BLOCKED: this page does not contain both AI and non-AI samples")


def compare_versions(left: ApiResponse, right: ApiResponse) -> None:
    a, b = feed_index(left), feed_index(right)
    common = a.keys() & b.keys()
    if not common:
        raise Blocked("BLOCKED: versions have no shared drama; cannot compare field values")
    for drama_id in sorted(common):
        # null and absent remain distinct evidence, but both mean unknown.
        normalize = lambda x: "unknown" if x in {"null", "missing"} else x
        assert normalize(a[drama_id]) == normalize(b[drama_id]), (
            f"AI field differs between versions for dramaId={drama_id}"
        )


def detail_matches_feed(response: ApiResponse, drama_id: int, expected_state: str) -> None:
    drama = successful_data(response).get("dramaInfo")
    assert isinstance(drama, dict), "Expected data.dramaInfo object"
    assert type(drama.get("dramaId")) is int and drama["dramaId"] == drama_id, "Detail dramaId does not match request"
    state = ai_state(drama)
    normalize = lambda x: "unknown" if x in {"null", "missing"} else x
    assert normalize(state) == normalize(expected_state), "Detail and feed AI states differ"
