"""一次性登录力扣，会话留在**持久化浏览器配置**里，供 lc_submit.py 复用。

用法:
  uv run python scripts/lc_login.py             # 打开浏览器窗口手动登录
  uv run python scripts/lc_login.py --wait=600  # 加长等待（默认 300 秒）
  uv run python scripts/lc_login.py --check     # 只检查登录状态，不开窗口

会话存在 `.auth/leetcode_profile/`（整个 `.auth/` 已被 .gitignore 排除）。

**为什么是持久化配置而不是 storage_state**（牛客那边就是 storage_state）：
力扣把会话跟浏览器指纹绑在一起。实测「headed 登录导出 storage_state ->
headless 新上下文导入」时，GraphQL 读接口还能过，但提交 POST 一律
403 `User is not authenticated`，而且那次失败之后**整个会话被服务端作废**。
登录与提交跑在同一个 profile 里就没这问题。

抓题面不需要登录，只有**提交**需要。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lc_common import PROFILE, REST_AUTH_JS, WHOAMI_JS, persistent_context  # noqa: E402

LOGIN_URL = "https://leetcode.cn/accounts/login/"
CHECK_URL = "https://leetcode.cn/problemset/"


def whoami(headless: bool = True) -> dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        ctx = persistent_context(pw, headless=headless)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(CHECK_URL, wait_until="domcontentloaded")
        who = dict(page.evaluate(WHOAMI_JS) or {})
        who["restAuth"] = page.evaluate(REST_AUTH_JS)
        ctx.close()
    return who


def main(argv) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if "--check" in argv:
        who = whoami(headless=True)
        rest = who.get("restAuth") or {}
        if who.get("isSignedIn") and rest.get("ok"):
            print(f"已登录：{who.get('username') or who.get('realName') or ''}（鉴权接口通过）")
            return 0
        if who.get("isSignedIn"):
            print(f"GraphQL 说已登录，但鉴权 REST 接口返回 {rest.get('status')}，提交会失败。")
            return 1
        print("未登录。运行:  uv run python scripts/lc_login.py")
        return 1

    from playwright.sync_api import sync_playwright

    wait = 300
    for a in argv[1:]:
        if a.startswith("--wait="):
            wait = int(a.split("=", 1)[1])

    PROFILE.parent.mkdir(parents=True, exist_ok=True)
    who, rest = {}, {}
    with sync_playwright() as pw:
        ctx = persistent_context(pw, headless=False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(CHECK_URL, wait_until="domcontentloaded")

        who = page.evaluate(WHOAMI_JS) or {}
        if who.get("isSignedIn"):
            print(f"检测到已登录状态：{who.get('username') or ''}")
        else:
            page.goto(LOGIN_URL, wait_until="domcontentloaded")
            print("\n浏览器窗口已打开力扣登录页，请在窗口里完成登录。")
            print(f"脚本会自动检测，登录成功即返回（最多等 {wait} 秒）。\n")

        # 不用「登录完按回车」：这脚本常在非交互环境里跑（工具链、CI），
        # 那里 stdin 是空设备，input() 直接 EOFError。轮询等待更稳也更省事。
        deadline = time.time() + wait
        while time.time() < deadline:
            try:
                who = dict(page.evaluate(WHOAMI_JS) or {})
                rest = page.evaluate(REST_AUTH_JS) or {}
            except Exception:
                who, rest = {}, {}       # 用户正在页面间跳转，下一轮再问
            if who.get("isSignedIn") and rest.get("ok"):
                break
            time.sleep(2)
        # 持久化配置会自己把 cookie 落盘，不用再导出 storage_state
        ctx.close()

    if who.get("isSignedIn"):
        name = who.get("username") or who.get("realName") or ""
        print(f"\n登录成功{('：' + name) if name else ''}，会话已存到 {PROFILE}")
        if rest.get("ok"):
            print("鉴权接口也通过了（提交走同一套鉴权），可以提交。")
        else:
            print(f"[注意] GraphQL 说已登录，但鉴权 REST 接口返回 {rest.get('status')}——"
                  "提交多半会失败，建议重新登录一次。")
        print("接下来:  uv run python scripts/lc_submit.py --check")
        return 0 if rest.get("ok") else 1
    print("\n[警告] 仍未检测到登录状态。请重跑本脚本。")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
