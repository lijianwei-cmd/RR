# 人人视频：短剧 AI 标识自动化（图形界面使用）

本包对应 TB 任务“短剧播放器 AI 生成标识”，不是之前的 Echo 示例，也不是 Windows 剧集简介。仅访问 Alpha 测试接口，不修改 TB、飞书、CMS 或业务数据。

## 放入已有练习项目

将本目录放在 `D:\codex\rr-api-demo\rr_ai_work`。保留原 `tests/test_echo.py`。打开原来的 PyCharm 项目，沿用已经安装 pytest 9.1.1、Requests 2.34.2 的解释器。

## 第一次：点击运行离线自检

1. 左侧展开 `rr_ai_work`，打开 `run_ai_work.py`。
2. 在编辑区域右键 → Run 'run_ai_work'。默认是 offline，不请求业务接口。
3. 看运行窗口最后的 Status、Cases 和 HTML report 路径。
4. 在 PyCharm 中打开生成的 `reports/本次目录/report.html`，选择浏览器预览，或在资源管理器双击。
5. 离线通过只证明断言程序工作正常，不代表业务通过。

## 第二次：点击运行真实信息流接口

1. Run → Edit Configurations → 添加 Python 配置。
2. 名称：`人人视频-AI标识-Alpha信息流`。
3. Script path：本项目 `rr_ai_work/run_ai_work.py`。
4. Parameters：`--suite feed`。
5. Working directory：本项目的 `rr_ai_work` 目录；解释器沿用当前项目。
6. 保存，选择该配置，点击绿色运行。
7. 脚本对 Alpha 的 `/app/drama/playlet/feed` 发出两次 GET，客户端版本分别为 10.39.2 和 10.40.0，不附带 Token、签名或设备身份。不重试，不自动分页。
8. 共 7 条检查：每个版本的 HTTP/业务成功、可空 Boolean 字段、AI/非AI样本覆盖，以及同一作品的跨版本值对照。

空列表、没有正反样本、没有共同剧集会标为 BLOCKED，不会当作通过。版本结果不同只能说明本轮观察到差异，不能直接断定是版本门控或缓存缺陷。

## 可选：播放详情一致性

复制上述运行配置，名称改为 `人人视频-AI标识-Alpha详情`，Parameters 改为 `--suite detail`。
在 Environment variables 中配置当前有效的 `RR_AI_ALI_ID`。这份配置含设备身份时不要共享或提交 `.idea`。Jenkins 应使用凭据绑定。

此模式先读取当轮信息流，取一部 AI、一部非 AI 作品及各自 firstEpisode.sid，再调用详情。最多一次 feed 和两次详情请求；比较 `data.dramaInfo.isAiWork` 与当轮信息流。缺少身份会在发请求前 BLOCKED。

这种比较证明两个接口一致，不证明 CMS 源数据正确。null/缺省的线上样本当前不保证出现；离线测试覆盖它们的断言语义。登录态和签名规则不在本批范围。

## Jenkins 界面接入

当前本机文件尚未提交或推送。先在 PyCharm 的 Commit 界面仅选中本包源码文件（排除 reports、缓存、凭据），审查后提交并 Push 到你的**练习仓库**，再配置 Jenkins。真实 `rr-auto-test` 仓库必须使用其专用发布流程。

复用练习的 Windows Jenkins 任务，源码管理仍指向练习仓库和对应分支，依赖继续使用已有根目录 requirements.txt。将原 pytest 执行那一行替换为：

```bat
".venv\Scripts\python.exe" rr_ai_work\run_ai_work.py --suite feed
exit /b %ERRORLEVEL%
```

保留前面的环境准备和失败检查。构建前增加一条文件清理步骤，只删除本任务工作空间中 `rr_ai_work/reports` 的旧报告，或使用 Jenkins Workspace Cleanup 的 include pattern `rr_ai_work/reports/**`。不要把旧轮次 XML 与新轮次一起发布。

构建后操作 → Publish JUnit test result report，文件匹配填 `rr_ai_work/reports/**/results.xml`，不勾选 Allow empty results。增加 Archive the artifacts，匹配 `rr_ai_work/reports/**/*`。每次运行都有独立报告目录；报告归档保留在对应 Jenkins 构建中。

首次先手动 Build Now，确认日志为 suite=feed、用例数为 7，不能拿原 Echo 的 4 条结果作为验收。本次没有更改 Jenkins 任务，也没有开启定时执行。

## 如何读结果

- PASS：本次选择的范围通过。
- FAIL：出现 HTTP/业务错误、类型错误或接口值不一致。
- BLOCKED：缺少前置或样本，未完成验证，退出码 2。
- ERROR：运行器/依赖或测试收集异常。
- JUnit 为兼容 Jenkins 将阻塞表现为非通过；准确区分见 HTML 和 summary.json。

运行记录只保存检查结论与字段计数，不保存完整响应、播放地址、请求头、Token、签名或设备身份。

## 后续端侧范围

PRD 包含标识文案、全屏/清屏/倍速、换作品清除旧标识、平板适配和离线下载。当前只实现接口批次。Figma 节点尚未通过插件读取，样式验证待办；不能据文档图片 alt 文本声称完成视觉验收。

特别关注任务中“首次下载未保存 AI 属性，立即离线播放缺少标识”的回归，需要真实 Android 测试包、设备和下载数据，不能用这批接口结果代替。

来源、版本和未覆盖范围见 sources.json。账户/身份缺失时不要粘贴历史 curl 中的 Token 或签名。
