"""牛客抓取公共工具：会话、SSR __INITIAL_STATE__ 解析、限速。"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "sources" / "_tmp"
TMP.mkdir(parents=True, exist_ok=True)
CACHE = TMP / "http_cache"
CACHE.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": UA,
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
})

_last = [0.0]
DELAY = 1.2


def throttle() -> None:
    dt = time.time() - _last[0]
    if dt < DELAY:
        time.sleep(DELAY - dt)
    _last[0] = time.time()


def _cache_key(url: str) -> Path:
    safe = re.sub(r"\W+", "_", url)[-150:]
    return CACHE / (safe + ".html")


def get(url: str, use_cache: bool = True, **kw) -> str:
    p = _cache_key(url)
    if use_cache and p.exists() and p.stat().st_size > 0:
        return p.read_text(encoding="utf-8")
    throttle()
    for attempt in range(3):
        try:
            r = SESSION.get(url, timeout=40, **kw)
            r.encoding = r.encoding or "utf-8"
            if r.status_code == 200:
                p.write_text(r.text, encoding="utf-8")
                return r.text
            print(f"    [http {r.status_code}] {url}")
        except Exception as exc:
            print(f"    [retry {attempt+1}] {url}: {exc}")
        time.sleep(2 + attempt * 3)
    return ""


def initial_state(html: str) -> dict:
    """从牛客 SSR 页面里抠出 window.__INITIAL_STATE__ 的 JSON。"""
    m = re.search(r"window\.__INITIAL_STATE__\s*=\s*", html)
    if not m:
        return {}
    start = m.end()
    # 从第一个 { 开始做括号配平（跳过字符串字面量）
    i = html.find("{", start)
    if i < 0:
        return {}
    depth, in_str, esc, quote = 0, False, False, ""
    for j in range(i, len(html)):
        ch = html[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
            continue
        if ch in "\"'":
            in_str, quote = True, ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                blob = html[i:j + 1]
                try:
                    return json.loads(blob)
                except Exception:
                    try:
                        return json.loads(blob.replace("undefined", "null"))
                    except Exception as exc:
                        print(f"    [warn] __INITIAL_STATE__ 解析失败: {exc}")
                        return {}
    return {}
