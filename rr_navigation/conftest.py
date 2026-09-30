import json
import os
from pathlib import Path

import pytest
import requests


@pytest.fixture(scope="session")
def settings():
    config_path = os.getenv("RR_NAV_CONFIG")

    if not config_path:
        pytest.fail(
            "缺少 RR_NAV_CONFIG，请设置本机配置文件路径",
            pytrace=False,
        )

    path = Path(config_path)
    if not path.is_file():
        pytest.fail("测试配置文件不存在", pytrace=False)

    try:
        config = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        pytest.fail(
            "测试配置读取失败，请检查文件权限和 JSON 格式",
            pytrace=False,
        )

    if not isinstance(config, dict):
        pytest.fail("测试配置顶层必须是 JSON 对象", pytrace=False)

    required = [
        "base_url",
        "navigation_id",
        "expected_drama_id",
        "expected_drama_name",
    ]

    for key in required:
        raw_value = config.get(key)
        value = "" if raw_value is None else str(raw_value).strip()
        if not value or "替换" in value:
            pytest.fail(f"测试配置尚未填写：{key}", pytrace=False)

    if not isinstance(config["base_url"], str):
        pytest.fail("base_url 必须是字符串", pytrace=False)

    headers = config.get("headers", {})
    if not isinstance(headers, dict):
        pytest.fail("headers 必须是 JSON 对象", pytrace=False)

    for key, value in headers.items():
        if not isinstance(value, str):
            pytest.fail(
                f"请求头的值必须是字符串：{key}",
                pytrace=False,
            )
        if not value.strip() or "替换" in value:
            pytest.fail(
                f"请求头尚未填写真实值：{key}",
                pytrace=False,
            )

    return config


@pytest.fixture(scope="session")
def detail_data(settings):
    url = (
        settings["base_url"].rstrip("/")
        + "/app/native-navigation/detail"
    )

    try:
        response = requests.get(
            url,
            params={"id": settings["navigation_id"]},
            headers=settings.get("headers", {}),
            timeout=(5, 20),
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        pytest.fail(
            f"请求失败：{type(exc).__name__}",
            pytrace=False,
        )

    assert response.status_code == 200, (
        f"HTTP 状态异常：{response.status_code}"
    )

    try:
        body = response.json()
    except ValueError:
        pytest.fail("响应不是合法 JSON", pytrace=False)

    assert isinstance(body, dict), "响应顶层必须是对象"

    data = body.get("data")
    assert isinstance(data, dict), "响应缺少有效 data 对象"

    return data