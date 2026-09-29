"""Right-click Run in PyCharm. Defaults to offline checks; --suite feed is live."""
from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
from uuid import uuid4
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent


def summarize(xml_path: Path, exit_code: int) -> tuple[str, list[dict]]:
    rows = []
    if xml_path.exists():
        for case in ET.parse(xml_path).getroot().iter("testcase"):
            problem = case.find("failure")
            if problem is None:
                problem = case.find("error")
            skipped = case.find("skipped")
            detail = "" if problem is None else (problem.get("message", "") + "\n" + (problem.text or ""))
            status = "PASS"
            if problem is not None:
                status = "BLOCKED" if "BLOCKED:" in detail else "FAIL"
            elif skipped is not None:
                status = "NOT_RUN"
            properties = {p.get("name"): p.get("value") for p in case.findall("properties/property")}
            rows.append({"name": case.get("name"), "status": status, "detail": detail, "properties": properties})
    states = {r["status"] for r in rows}
    if "FAIL" in states:
        return "FAIL", rows
    if states & {"BLOCKED", "NOT_RUN"}:
        return "BLOCKED", rows
    if exit_code or not rows:
        return "ERROR", rows
    return "PASS", rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("offline", "feed", "detail"), default="offline")
    args = parser.parse_args()
    import pytest

    output = ROOT / "reports" / (datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8])
    output.mkdir(parents=True)
    target = {"offline": "test_contract_unit.py", "feed": "test_feed.py", "detail": "test_detail.py"}[args.suite]
    previous = os.environ.get("RR_AI_LIVE")
    if args.suite != "offline":
        os.environ["RR_AI_LIVE"] = "1"
    try:
        code = int(pytest.main([
            "-c", str(ROOT / "pytest.ini"), str(ROOT / "tests" / target),
            "-v", "-o", "junit_family=legacy", "-o", f"cache_dir={output / '.pytest_cache'}",
            f"--junitxml={output / 'results.xml'}",
        ]))
    finally:
        if previous is None:
            os.environ.pop("RR_AI_LIVE", None)
        else:
            os.environ["RR_AI_LIVE"] = previous
    status, rows = summarize(output / "results.xml", code)
    evidence = {
        "suite": args.suite, "status": status, "timestamp": datetime.now(timezone.utc).isoformat(),
        "business_verified": args.suite != "offline" and status == "PASS",
        "ui_verified": False, "cms_source_verified": False,
        "cases": rows, "pytest_exit_code": code,
        "task": "https://www.teambition.com/task/6aa3744e7acea37fa18af223",
        "environment": "Alpha", "base_url": "https://alpha-api.duoduoshipin.vip",
    }
    (output / "summary.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    table = "".join(
        f"<tr><td>{html.escape(r['name'] or '')}</td><td>{r['status']}</td>"
        f"<td><pre>{html.escape(r['detail'])}</pre>{html.escape(json.dumps(r['properties'],ensure_ascii=False))}</td></tr>"
        for r in rows
    )
    page = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>人人视频 AI 标识自动化</title>
<style>body{{font:16px system-ui;max-width:1200px;margin:40px auto;padding:0 24px;color:#17283e}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccd5df;padding:12px;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}h1{{color:#12587a}}</style>
<h1>人人视频 · 短剧 AI 标识</h1><p>运行范围：{args.suite}　结果：<b>{status}</b>　用例数：{len(rows)}</p>
<p>offline 仅验证测试工具逻辑；feed/detail 仅验证当前 Alpha 接口。客户端显示、离线下载和 CMS 源值未验收。</p>
<table><tr><th>用例</th><th>状态</th><th>证据或原因</th></tr>{table}</table></html>'''
    (output / "report.html").write_text(page, encoding="utf-8")
    print(f"\nSuite: {args.suite}; Status: {status}; Cases: {len(rows)}")
    print(f"HTML report: {output / 'report.html'}")
    print(f"JUnit report: {output / 'results.xml'}")
    return 2 if status == "BLOCKED" else (code or (0 if status == "PASS" else 1))


if __name__ == "__main__":
    raise SystemExit(main())
