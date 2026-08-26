"""一次性登录牛客并保存会话状态，供 nc_submit.py 复用。

用法:
  uv run python scripts/nc_login.py             # 打开浏览器窗口手动登录
  uv run python scripts/nc_login.py --wait=600  # 加长等待（默认 300 秒）
  uv run python scripts/nc_login.py --check     # 只检查登录状态，不开窗口

会打开一个真实浏览器窗口，你手动登录（扫码或账号密码均可）。
脚本轮询检测登录状态，成功即把 cookie/localStorage 存到 .auth/nowcoder.json。
该文件含登录凭据，已通过 .gitignore 排除，不要外传。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUTH = ROOT / ".auth"
STATE = AUTH / "nowcoder.json"

LOGIN_URL = "https://www.nowcoder.com/login"
CHECK_URL = "https://www.nowcoder.com/exam/oj?questionJobId=10&subTabName=online_coding_page"


IS_LOGIN = "() => !!(window.envInfo && window.envInfo.isLogin)"
NICKNAME = ("() => (window.envInfo && window.envInfo.user "
            "&& window.envInfo.user.nickname) || ''")


def main(argv=()) -> int:
    from playwright.sync_api import sync_playwright

    check_only = "--check" in argv
    wait = 300
    for a in argv:
        if a.startswith("--wait="):
            wait = int(a.split("=", 1)[1])

    AUTH.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=check_only)
        ctx = browser.new_context(
            storage_state=str(STATE) if STATE.exists() else None,
            viewport={"width": 1400, "height": 900},
        )
        page = ctx.new_page()
        page.goto(CHECK_URL, wait_until="domcontentloaded")

        ok = bool(page.evaluate(IS_LOGIN))
        if check_only:
            nickname = page.evaluate(NICKNAME) if ok else ""
            browser.close()
            print(f"已登录：{nickname}" if ok
                  else "未登录。运行:  uv run python scripts/nc_login.py")
            return 0 if ok else 1

        if ok:
            print("检测到已登录状态。")
        else:
            page.goto(LOGIN_URL, wait_until="domcontentloaded")
            print("\n浏览器窗口已打开牛客登录页，请在窗口里完成登录（扫码或密码均可）。")
            print(f"脚本会自动检测，登录成功即返回（最多等 {wait} 秒）。\n")

        # 不用「登录完按回车」：这脚本常在非交互环境里跑，那里 stdin 是空设备，
        # input() 直接 EOFError。轮询等待更稳。
        deadline = time.time() + wait
        while not ok and time.time() < deadline:
            time.sleep(2)
            try:
                ok = bool(page.evaluate(IS_LOGIN))
            except Exception:
                ok = False          # 正在页面间跳转，下一轮再问
        nickname = page.evaluate(NICKNAME) if ok else ""
        ctx.storage_state(path=str(STATE))
        browser.close()

    if ok:
        print(f"\n登录成功{('：' + nickname) if nickname else ''}，会话已保存到 {STATE}")
        print("接下来可以运行:  uv run python scripts/nc_submit.py --langs   （查看题目支持的语言）")
        return 0
    print("\n[警告] 仍未检测到登录状态，会话文件已写但可能无效。请重跑本脚本。")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
