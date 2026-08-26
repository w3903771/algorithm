"""剔除菜鸟教程里与算法竞赛（ACM/OJ）明显无关的页面，并重建 INDEX.md。

删除的四类：环境/工具链、Web/网络/数据库、并发与工程化、绘图/AI/爬虫/GUI。
原始 HTML 仍在 sources/_tmp/http_cache/，重跑 runoob_fetch.py 即可复原。

用法: uv run python scripts/runoob_prune.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sources" / "04-runoob"

DROP = {
    # 环境 / 工具链
    "03": "安装配置", "04": "PyCharm", "05": "VSCode", "36": "venv", "55": "pip", "54": "uWSGI",
    # 文件系统（OJ 只用 stdin/stdout）
    "31": "文件方法", "32": "os 文件方法",
    # Web / 网络 / 数据库
    "42": "CGI", "43": "MySQL Connector", "44": "MySQL", "45": "Socket", "46": "SMTP",
    "52": "MongoDB", "53": "urllib", "58": "requests",
    # 并发 / 工程化
    "47": "多线程", "80": "threading", "81": "asyncio", "73": "subprocess", "76": "logging",
    # 数据交换格式
    "48": "XML", "49": "JSON", "79": "CSV", "72": "pickle", "75": "StringIO",
    # 绘图 / AI / 爬虫 / GUI / 其它
    "60": "OpenAI", "62": "AI 绘图", "63": "statistics", "64": "hashlib",
    "65": "Qt", "82": "PyQt", "66": "pyecharts",
    "67": "Selenium", "68": "BeautifulSoup", "69": "Scrapy", "70": "Markdown 转 HTML",
    "40": "在线测验（无正文）", "61": "资源列表（无正文）",
}


def main() -> int:
    dropped, kept = [], []
    for p in sorted(OUT.glob("*.md")):
        if p.name == "INDEX.md":
            continue
        num = p.name.split("-", 1)[0]
        if num in DROP:
            dropped.append((p.name, DROP[num]))
            p.unlink()
        else:
            kept.append(p)

    # 重建索引
    lines = ["# 菜鸟教程 Python3（算法竞赛相关部分）\n",
             "> 入口: https://www.runoob.com/python3/python3-list.html  ",
             f"> 抓取 84 页，剔除与 ACM 明显无关的 {len(dropped)} 页，保留 **{len(kept)}** 页\n",
             "## 保留页面\n",
             "| # | 章节 | 文件 | 字符数 |", "| --- | --- | --- | --- |"]
    for i, p in enumerate(kept, 1):
        first = p.read_text(encoding="utf-8").split("\n", 1)[0]
        title = first.lstrip("# ").strip()
        lines.append(f"| {i} | {title} | [{p.name}]({p.name}) | {p.stat().st_size} |")

    lines += ["\n## 已剔除页面（与算法竞赛无关）\n",
              "> 原始 HTML 保留在 `sources/_tmp/http_cache/`，重跑 `scripts/runoob_fetch.py` 可复原。\n",
              "| 文件 | 原因分类 |", "| --- | --- |"]
    for name, why in dropped:
        lines.append(f"| {name} | {why} |")

    (OUT / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"删除 {len(dropped)} 页，保留 {len(kept)} 页")
    for name, why in dropped:
        print(f"  - {name}  ({why})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
