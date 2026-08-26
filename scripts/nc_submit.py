"""带登录态提交题解到牛客判题机，并轮询真实判题结果。

前置: 先跑一次 uv run python scripts/nc_login.py 保存会话。

用法:
  uv run python scripts/nc_submit.py --langs PIO1      # 查该题支持哪些语言（要开页面，慢）
  uv run python scripts/nc_submit.py --dry PIO         # 只打印将要提交什么，不真提交
  uv run python scripts/nc_submit.py PIO               # 提交 PIO 整套
  uv run python scripts/nc_submit.py BISHI136 BISHI137
  uv run python scripts/nc_submit.py --pypy BISHI147   # 用 PyPy3 提交（语法兼容 py3，快一个数量级）
  uv run python scripts/nc_submit.py --retry BISHI     # 连同上轮失败的题一起重提（默认只跳过 AC）
  uv run python scripts/nc_submit.py --keep-comments BISHI1  # 保留注释与文档字符串

设计取舍：
  - 默认限速 15 秒/题，避免触发风控；可用 --delay 调整，但不建议调低。
  - 每题结果落盘各题的 meta.json（`langs.py`），中断后重跑会跳过已 AC 的题。
  - **默认剥掉注释与文档字符串再提交**（scripts/strip_code.py）：题解的文档字符串
    是给教程站点渲染用的教程正文，不该跟着代码进判题机。要原样提交加 --keep-comments。
  - 走的是页面内 fetch（复用浏览器的 cookie 与同源上下文），
    比在 DOM 里模拟点击稳定得多，也不依赖前端改版。
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
AUTH = ROOT / ".auth" / "nowcoder.json"
TOKEN_CACHE = ROOT / ".auth" / "judge_token.json"
SOL = ROOT / "solutions"
NC = ROOT / "sources" / "05-nowcoder"

# 判题机已搬到独立域名，接口形状也变了，见本目录 README「牛客站点的逆向结论」。
JUDGE = "https://victorinox.nowcoder.com"
SUBMIT_API = JUDGE + "/api/service/judge/submit"
STATUS_API = JUDGE + "/api/service/judge/submit-status"
TOKEN_API = "https://gw-c.nowcoder.com/api/sparta/base-oauth/access-token"
APP_ID = 5

# 语言现在用数字 id，不再是 "python3" 这类字符串。11 = Python 3，25 = PyPy3。
LANG_PY3 = 11
LANG_PYPY3 = 25
LANG_BY_NAME = {"python3": LANG_PY3, "pypy3": LANG_PYPY3}

DEFAULT_DELAY = 15.0
POLL_INTERVAL = 2.0
POLL_MAX = 60


def load_index() -> dict:
    """题号 -> 题单条目。题单从 data/_sources.json 读，加题单不用改这里。"""
    idx = {}
    reg = DATA / "_sources.json"
    if reg.exists():
        d = json.loads(reg.read_text(encoding="utf-8"))
        for st in d["sets"]:
            if st["site"] != "nowcoder":
                continue
            f = ROOT / st["list"]
            if f.exists():
                for it in json.loads(f.read_text(encoding="utf-8")):
                    idx[it["no"]] = it
        return idx
    for slug in ("bishi", "pio", "bm"):          # 注册表读不到时的退路
        f = NC / f"{slug}_list.json"
        if f.exists():
            for it in json.loads(f.read_text(encoding="utf-8")):
                idx[it["no"]] = it
    return idx


# 结果存取与报告渲染跟力扣那边共用：两个脚本各写各的题号（P-M③ 起写进
# 各题自己的 meta.json），报告由 submit_report.render() 合并渲染，谁后跑都不会冲掉对方。
import sol_store as store  # noqa: E402
import strip_code  # noqa: E402
from submit_report import load_results, render, save_results, sort_key  # noqa: E402


def load_langs() -> dict:
    """按题覆盖提交语言。少数题 CPython 物理上过不去，只能走 PyPy3。

    原 solutions/_lang.json，P-M③ 起并进各题 meta.json 的 `langs.py.submitLang`。
    """
    return store.submit_langs()


# 页面内执行的 fetch 助手：复用浏览器 cookie 与同源上下文。
# 判题机是跨域的，但它对 www.nowcoder.com 开了 CORS，带 credentials 直接打就行。
JS_GET = """
async ([url, params]) => {
  const u = new URL(url, location.origin);
  Object.entries(params || {}).forEach(([k, v]) => u.searchParams.set(k, v));
  const r = await fetch(u, {credentials: 'include',
                           headers: {'X-Requested-With': 'XMLHttpRequest'}});
  const t = await r.text();
  try { return {status: r.status, json: JSON.parse(t)}; }
  catch (e) { return {status: r.status, text: t.slice(0, 800)}; }
}
"""

JS_POST = """
async ([url, body]) => {
  const r = await fetch(url + '?_=' + Date.now(), {
    method: 'POST', credentials: 'include',
    headers: {'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
    body: JSON.stringify(body),
  });
  const t = await r.text();
  try { return {status: r.status, json: JSON.parse(t)}; }
  catch (e) { return {status: r.status, text: t.slice(0, 800)}; }
}
"""


def get_token(page) -> str:
    """取判题机的 accessToken。它按**用户**签发（有效期 7 天）、与题目无关，
    所以整轮提交共用一个，缓存到 .auth/judge_token.json。"""
    if TOKEN_CACHE.exists():
        c = json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))
        if c.get("token") and time.time() < c.get("expires_at", 0):
            return c["token"]
    r = page.evaluate(JS_GET, [TOKEN_API, {"token": "", "sceneType": 1}])
    data = (r.get("json") or {}).get("data") or {}
    tok = data.get("accessToken") or ""
    if tok:
        TOKEN_CACHE.write_text(json.dumps(
            # 留一天余量，别卡着过期边界用
            {"token": tok,
             "expires_at": time.time() + float(data.get("expires", 604800)) - 86400},
            ensure_ascii=False, indent=2), encoding="utf-8")
    return tok


def question_url(meta: dict) -> str:
    """题目页地址。**必须带 tpId/tqId 查询参数**，光给 uuid 现在会返回 405。"""
    src = urllib.parse.quote(
        f"/exam/oj?questionJobId=10&topicId={meta['tpId']}", safe="")
    return (f"https://www.nowcoder.com/practice/{meta['uuid']}"
            f"?tpId={meta['tpId']}&tqId={meta['questionId']}&sourceUrl={src}")


def probe_languages(page, meta: dict) -> dict:
    """开题目页读该题真实支持的语言表，返回 {langId: langName}。
    慢（要等 Monaco 初始化），只给 --langs 用。"""
    page.goto(question_url(meta), wait_until="domcontentloaded", timeout=60000)
    for _ in range(20):
        time.sleep(1)
        langs = page.evaluate(
            "() => {try {return window.__ncMonacoEditorApi.editorParams"
            ".questionInfo.supportLanguages} catch (e) {return null}}")
        if langs:
            return {int(x["langId"]): x["langName"] for x in langs}
    return {}


def judge_once(page, qid, code: str, lang: int, uid: int, token: str) -> dict:
    body = {"content": code, "questionId": str(qid), "language": str(lang),
            "tagId": 0, "appId": APP_ID, "userId": uid,
            "submitType": 1, "remark": "{}", "token": token}
    resp = page.evaluate(JS_POST, [SUBMIT_API, body])
    j = resp.get("json") or {}
    if j.get("code") != 0:
        return {"status": "SUBMIT_FAIL", "verdict": str(j or resp)[:300]}
    sid = (j.get("data") or {}).get("id")

    last = {}
    for _ in range(POLL_MAX):
        time.sleep(POLL_INTERVAL)
        s = page.evaluate(JS_GET, [STATUS_API, {
            "id": sid, "tagId": 0, "appId": APP_ID, "userId": uid,
            "submitType": 1, "remark": "{}", "token": token}])
        d = (s.get("json") or {}).get("data") or {}
        if not d:
            continue
        last = d
        # status 0/1 是排队与判题中，其余为终态；desc 是给人看的判定文案
        if d.get("status") not in (0, 1, None) and d.get("desc"):
            break

    desc = str(last.get("desc") or "")
    ac = last.get("status") == 5 or "通过了所有的测试用例" in desc
    out = {"status": "AC" if ac else "FAIL", "submissionId": sid,
           "verdict": desc[:300] or "轮询超时，未拿到终态",
           "lang": last.get("language") or lang}
    if not ac:
        # 失败时把定位用的信息一并留下：第几个用例、输入、期望 vs 实际
        for k in ("caseIndex", "input", "expectedOutput", "output", "memo"):
            v = last.get(k)
            if v:
                out[k] = str(v)[:600]
    return out


def main(argv) -> int:
    # Windows 控制台默认 GBK，报告里的 ✅/❌ 会直接抛 UnicodeEncodeError
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    from playwright.sync_api import sync_playwright

    if not AUTH.exists():
        print("未找到登录会话。请先运行:  uv run python scripts/nc_login.py")
        return 2

    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    only_langs = "--langs" in flags
    dry = "--dry" in flags
    allow_pypy = "--pypy" in flags
    retry_failed = "--retry" in flags
    keep_comments = "--keep-comments" in flags
    delay = DEFAULT_DELAY
    for a in flags:
        if a.startswith("--delay="):
            delay = float(a.split("=", 1)[1])

    lang_override = load_langs()

    index = load_index()
    sols = store.all_numbers()
    if args:
        sols = [s for s in sols if any(s == a or s.startswith(a) for a in args)]
    sols = [s for s in sols if s in index]
    sols.sort(key=sort_key)
    if not sols:
        print("没有匹配的题解")
        return 0

    results = load_results()
    UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(storage_state=str(AUTH), user_agent=UA,
                                  viewport={"width": 1600, "height": 1000})
        page = ctx.new_page()
        page.goto("https://www.nowcoder.com/exam/oj", wait_until="domcontentloaded")
        uid = page.evaluate("() => (window.envInfo && window.envInfo.user "
                            "&& window.envInfo.user.userId) || 0")
        if not uid:
            print("会话已失效，请重新运行 scripts/nc_login.py")
            browser.close()
            return 2

        token = "" if only_langs else get_token(page)
        if not only_langs and not token:
            print("取判题 token 失败，会话可能已失效")
            browser.close()
            return 2

        for i, no in enumerate(sols, 1):
            meta = index[no]
            qid = meta["questionId"]
            tag = f"[{i}/{len(sols)}] {no:<10}"

            # --pypy 全局强制；否则查覆盖表，默认 Python3
            lang_id = (LANG_PYPY3 if allow_pypy else
                       LANG_BY_NAME.get(lang_override.get(no, ""), LANG_PY3))

            if only_langs:
                names = probe_languages(page, meta)
                mark = f"✔ {names[lang_id]}" if lang_id in names else "✘ 不支持"
                print(f"{tag} qid={qid:<10} python={mark}   "
                      f"raw={','.join(sorted(names.values()))[:120]}", flush=True)
                continue

            prev = results.get(no, {}).get("status")
            if prev == "AC":
                print(f"{tag} 已 AC，跳过", flush=True)
                continue
            if prev and not retry_failed:
                print(f"{tag} 上轮 {prev}，加 --retry 才重提", flush=True)
                continue

            src = store.sol_path(no).read_text(encoding="utf-8")
            code = src if keep_comments else strip_code.strip(src)
            if dry:
                print(f"{tag} DRY qid={qid} lang={lang_id} code={len(code)}B "
                      f"{strip_code.summary(src, code)}")
                continue

            r = judge_once(page, qid, code, lang_id, uid, token)
            results[no] = r
            save_results(results, no)
            icon = "✅ AC" if r["status"] == "AC" else "❌ " + str(r.get("verdict"))[:80]
            print(f"{tag} {icon}", flush=True)
            time.sleep(delay)

        browser.close()

    # 报告一律走 submit_report.render()：这里自己渲染的话，会把力扣那边
    # 写进同一份 _submit_report.md 的题目整段冲掉（那正是 submit_report 存在的理由）。
    if not only_langs and not dry:
        print(f"\n报告 -> {render()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
