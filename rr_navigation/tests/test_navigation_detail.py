import allure


@allure.feature("首页组件跳转热剧自定义导航二级页")
@allure.story("导航详情接口")
@allure.title("返回的原生导航 ID 与请求目标一致")
def test_navigation_id(detail_data, settings):
    with allure.step("核对返回的导航 ID"):
        assert str(detail_data.get("id")) == str(
            settings["navigation_id"]
        )


@allure.feature("首页组件跳转热剧自定义导航二级页")
@allure.story("导航详情接口")
@allure.title("导航关联的剧集与后台测试配置一致")
def test_navigation_drama(detail_data, settings):
    with allure.step("确认基础信息存在"):
        base = detail_data.get("base")
        assert isinstance(base, dict), "缺少 base 对象"

    with allure.step("核对关联剧集 ID"):
        assert str(base.get("dramaId")) == str(
            settings["expected_drama_id"]
        )


@allure.feature("首页组件跳转热剧自定义导航二级页")
@allure.story("导航详情接口")
@allure.title("返回完整剧名，包含预期季信息")
def test_navigation_drama_name(detail_data, settings):
    with allure.step("确认剧集信息存在"):
        drama = detail_data.get("drama")
        assert isinstance(drama, dict), "缺少 drama 对象"

    with allure.step("与已确认的完整剧名比较"):
        assert drama.get("name") == settings["expected_drama_name"]