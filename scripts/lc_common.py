"""力扣（leetcode.cn）抓取公共工具：GraphQL 会话、限速、磁盘缓存、HTML->Markdown。

与 nc_common.py 对等，但力扣走 GraphQL POST，缓存键要带上变量，
所以不能直接复用 nc_common.get（那个只按 URL 做键）。

匿名即可读题面与题单，不需要登录。
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "sources" / "_tmp" / "lc_cache"
CACHE.mkdir(parents=True, exist_ok=True)

GRAPHQL = "https://leetcode.cn/graphql/"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": UA,
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://leetcode.cn",
    "Referer": "https://leetcode.cn/",
    "Accept-Language": "zh-CN,zh;q=0.9",
})

_last = [0.0]
DELAY = 1.0

# --------------------------------------------------------------------------- #
# 浏览器会话（提交时用；抓题面不需要登录，走上面的 requests 会话就够）
# --------------------------------------------------------------------------- #

PROFILE = ROOT / ".auth" / "leetcode_profile"
STATE = ROOT / ".auth" / "leetcode.json"


def persistent_context(pw, headless: bool = True):
    """打开**持久化**浏览器配置（.auth/leetcode_profile），登录与提交共用同一份。

    为什么不像牛客那样用 storage_state：力扣会把会话跟浏览器指纹绑在一起。
    实测「headed 登录存 storage_state -> headless 新上下文加载」时，
    GraphQL 读接口还能过（`userStatus.isSignedIn` 为真），但提交 POST 一律
    403 `User is not authenticated`，且那次失败之后**整个会话被服务端作废**，
    连读接口也变成未登录。牛客没有这套处置，所以 nc_submit 那边照旧。

    持久化配置让两边跑在同一个 profile、同一套指纹里，会话不会因此被判为异常。
    """
    return pw.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE),
        headless=headless,
        user_agent=UA,
        viewport={"width": 1600, "height": 1000},
        args=["--disable-blink-features=AutomationControlled"],
    )


# 只问 GraphQL 不够：实测存在「GraphQL 说已登录、提交 POST 却 401/403」的状态。
# 提交接口走 DRF 鉴权，所以拿同一套鉴权的 REST 接口探一下才算数。
REST_AUTH_JS = """
async () => {
  const r = await fetch('/api/progress/all/', {credentials: 'include'});
  return {status: r.status, ok: r.status === 200};
}
"""

WHOAMI_JS = """
async () => {
  const r = await fetch('/graphql/', {
    method: 'POST', credentials: 'include',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query: '{ userStatus { isSignedIn username realName } }'}),
  });
  try { return (await r.json()).data.userStatus; } catch (e) { return null; }
}
"""


def throttle() -> None:
    dt = time.time() - _last[0]
    if dt < DELAY:
        time.sleep(DELAY - dt)
    _last[0] = time.time()


def gql(query: str, variables: dict, tag: str = "q", use_cache: bool = True) -> dict:
    """发一次 GraphQL 查询，结果按 (query, variables) 的哈希缓存到磁盘。"""
    key = hashlib.md5((query + json.dumps(variables, sort_keys=True)).encode()).hexdigest()[:16]
    p = CACHE / f"{tag}_{key}.json"
    if use_cache and p.exists() and p.stat().st_size > 0:
        return json.loads(p.read_text(encoding="utf-8"))
    for attempt in range(3):
        throttle()
        try:
            r = SESSION.post(GRAPHQL, json={"query": query, "variables": variables}, timeout=40)
            if r.status_code == 200:
                j = r.json()
                if j.get("errors"):
                    print(f"    [gql err] {tag} {variables}: {j['errors'][0].get('message')}")
                    return {}
                p.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
                return j
            # 400 基本都是字段名写错（力扣不同节点类型的译名字段不同名），把原因打出来
            print(f"    [http {r.status_code}] {tag} {variables}: {r.text[:300]}")
        except Exception as exc:
            print(f"    [retry {attempt + 1}] {tag} {variables}: {exc}")
        time.sleep(2 + attempt * 3)
    return {}


# --------------------------------------------------------------------------- #
# HTML -> Markdown
# --------------------------------------------------------------------------- #

# 力扣题面里的行内代码常写成 <code>nums[i]</code>，markdownify 转出来就是 `nums[i]`，
# 但题面同样大量用 <sup>/<sub> 表示 10^5、a_i，markdownify 默认丢标签只留文本，
# 会把 10<sup>5</sup> 变成 105。这里先手工转成数学写法再交给 markdownify。
_SUP = re.compile(r"<sup>(.*?)</sup>", re.S)
_SUB = re.compile(r"<sub>(.*?)</sub>", re.S)


def html_to_md(html: str) -> str:
    if not html:
        return ""
    from markdownify import markdownify

    s = _SUP.sub(lambda m: "^" + m.group(1).strip(), html)
    s = _SUB.sub(lambda m: "_" + m.group(1).strip(), s)
    s = markdownify(s, heading_style="ATX", bullets="-", code_language="")
    s = re.sub(r"\n{3,}", "\n\n", s)
    # markdownify 会把 &nbsp; 留成 \xa0，落到 Markdown 里就是不可见的怪空格
    return s.replace("\xa0", " ").strip()
