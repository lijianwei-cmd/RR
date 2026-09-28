import pytest
import requests


API_URL = "https://postman-echo.com/get"


@pytest.mark.smoke
@pytest.mark.parametrize(
    "keyword",
    ["video", "中文", ""],
    ids=["english", "chinese", "empty"],
)
def test_keyword_echo(keyword):
    """验证普通字符串、中文和空字符串正确回显。"""

    response = requests.get(
        API_URL,
        params={"keyword": keyword},
        timeout=(5, 15),
    )

    assert response.status_code == 200, (
    f"预期 HTTP 200，实际为 {response.status_code}"
)

    body = response.json()

    assert "args" in body, "响应缺少 args 字段"
    assert "keyword" in body["args"], "响应缺少 keyword 字段"
    assert body["args"]["keyword"] == keyword, (
        f"预期 keyword={keyword!r}，"
        f"实际 keyword={body['args']['keyword']!r}"
    )


def test_keyword_not_provided():
    """未传 keyword 时，回显参数中不应出现 keyword。"""

    response = requests.get(
        API_URL,
        timeout=(5, 15),
    )

    assert response.status_code == 200, (
        f"预期 HTTP 200，实际为 {response.status_code}"
    )

    body = response.json()

    assert "args" in body, "响应缺少 args 字段"
    assert "keyword" not in body["args"], (
        "未传 keyword，但响应中出现了该参数"
    )