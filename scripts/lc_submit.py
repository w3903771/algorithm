"""把力扣那 100 题的题解提交到**力扣判题机**，拿真实判定。

用法:
  uv run python scripts/lc_submit.py --check      # 只检查登录状态
  uv run python scripts/lc_submit.py --dry LC1    # 只打印将要提交什么，不真提交
  uv run python scripts/lc_submit.py LC1          # 提交单题
  uv run python scripts/lc_submit.py LC           # 提交全部 LC 开头的题解
  uv run python scripts/lc_submit.py --retry LC   # 连同上轮失败的题一起重提（默认只跳过 AC）
  uv run python scripts/lc_submit.py --delay=20 LC
  uv run python scripts/lc_submit.py --keep-comments LC1   # 保留注释与文档字符串

注意:
  - 需要先登录一次: uv run python scripts/lc_login.py
  - 与登录**共用同一个持久化浏览器配置**（.auth/leetcode_profile）。
    力扣把会话跟浏览器指纹绑定，换指纹加载 storage_state 会导致提交 403
    并且会话被服务端作废，详见 lc_common.persistent_context 的注释。
  - 默认限速 15 秒/题。力扣对提交频率有风控，不建议调低。
  - 每题结果落盘各题的 meta.json（`langs.py`；与牛客各写各的题号），
    中断后重跑会跳过已 AC 的题；报告由 submit_report.render() 合并渲染。
  - 走页面内 fetch，复用浏览器的 cookie 与 csrftoken——
    力扣的提交接口要 `x-csrftoken` 头且与 cookie 对应，在页面上下文里发最省事。
  - 力扣不提供 PyPy，所以没有牛客那边的 --pypy 开关，一律 python3。
  - **默认剥掉注释与文档字符串再提交**（scripts/strip_code.py）：题解的文档字符串
    是给教程站点渲染用的教程正文，不该跟着代码进判题机。要原样提交加 --keep-comments。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import strip_code  # noqa: E402
from lc_common import PROFILE, REST_AUTH_JS, WHOAMI_JS, persistent_context  # noqa: E402
import sol_store as store  # noqa: E402
from submit_report import load_results, render, save_results, sort_key  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"        # 公开数据：站点构建与 check_prose 要读，随仓库发布

LANG = "python3"
DEFAULT_DELAY = 15.0
POLL_INTERVAL = 1.5
POLL_MAX = 40

# 页面内执行：力扣的提交接口要 x-csrftoken 头，值就是同名 cookie，
# 在页面上下文里取最直接，也免得自己维护 cookie jar。
JS_SUBMIT = """
async ([slug, body]) => {
  const csrf = (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
  const r = await fetch(`/problems/${slug}/submit/`, {
    method: 'POST', credentials: 'include',
    headers: {'Content-Type': 'application/json', 'x-csrftoken': decodeURIComponent(csrf),
              'x-requested-with': 'XMLHttpRequest'},
    body: JSON.stringify(body),
  });
  const t = await r.text();
  try { return {status: r.status, json: JSON.parse(t)}; }
  catch (e) { return {status: r.status, text: t.slice(0, 600)}; }
}
"""

JS_CHECK = """
async (sid) => {
  const r = await fetch(`/submissions/detail/${sid}/check/`, {credentials: 'include'});
  const t = await r.text();
  try { return {status: r.status, json: JSON.parse(t)}; }
  catch (e) { return {status: r.status, text: t.slice(0, 600)}; }
}
"""


def load_index() -> dict:
    """题号 -> 题目元信息。提交要的是 titleSlug 与**内部** questionId。"""
    d = json.loads((DATA / "_sources.json").read_text(encoding="utf-8"))
    idx = {}
    for s in d["sets"]:
        if s["site"] != "leetcode" or not (ROOT / s["list"]).exists():
            continue
        raw = ROOT / s["raw"]
        for it in json.loads((ROOT / s["list"]).read_text(encoding="utf-8")):
            meta = dict(it)
            f = raw / f"{it['no']}.json"
            if f.exists():
                # internalId 在抓题面时记下的，题单接口不给
                meta.update(json.loads(f.read_text(encoding="utf-8")).get("meta") or {})
            idx[it["no"]] = meta
    return idx


def judge_once(page, meta: dict, code: str) -> dict:
    slug = meta["uuid"]
    qid = meta.get("internalId") or meta.get("questionId")
    resp = page.evaluate(JS_SUBMIT, [slug, {"lang": LANG, "question_id": str(qid),
                                            "typed_code": code}])
    j = resp.get("json") or {}
    sid = j.get("submission_id")
    if not sid:
        return {"status": "SUBMIT_FAIL", "lang": LANG,
                "verdict": str(j or resp)[:300]}

    last = {}
    for _ in range(POLL_MAX):
        time.sleep(POLL_INTERVAL)
        s = page.evaluate(JS_CHECK, sid)
        d = (s.get("json") or {})
        if not d:
            continue
        last = d
        # PENDING / STARTED 是排队与判题中，SUCCESS 才是跑完（跑完不等于 AC）
        if d.get("state") == "SUCCESS":
            break

    msg = str(last.get("status_msg") or "")
    ac = last.get("status_code") == 10 and msg == "Accepted"
    out = {"status": "AC" if ac else "FAIL", "submissionId": sid, "lang": LANG,
           "verdict": msg or "轮询超时，未拿到终态"}
    if ac:
        # 力扣会给运行时与内存的百分位，写进结果方便日后回看性能。
        # status_runtime / status_memory 才是「0 ms」「20.8 MB」这种可读值，
        # runtime / memory 是原始数字，两个都留着
        for k in ("status_runtime", "status_memory", "runtime", "memory",
                  "runtime_percentile", "memory_percentile"):
            if last.get(k) is not None:
                out[k] = last[k]
    else:
        for k in ("total_correct", "total_testcases", "last_testcase",
                  "expected_output", "code_output", "full_runtime_error",
                  "runtime_error", "compile_error"):
            v = last.get(k)
            if v not in (None, ""):
                out[k] = str(v)[:600]
    return out


def main(argv) -> int:
    # Windows 控制台默认 GBK，报告里的 ✅/❌ 会直接抛 UnicodeEncodeError
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    dry = "--dry" in flags
    check_only = "--check" in flags
    headed = "--headed" in flags
    retry_failed = "--retry" in flags
    keep_comments = "--keep-comments" in flags
    delay = DEFAULT_DELAY
    for a in flags:
        if a.startswith("--delay="):
            delay = float(a.split("=", 1)[1])

    if not PROFILE.exists() and not dry:
        print("未找到登录会话。请先运行:  uv run python scripts/lc_login.py")
        return 2

    if check_only:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            ctx = persistent_context(pw, headless=not headed)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto("https://leetcode.cn/problemset/", wait_until="domcontentloaded")
            who = page.evaluate(WHOAMI_JS) or {}
            rest = page.evaluate(REST_AUTH_JS)
            ctx.close()
        if who.get("isSignedIn") and rest.get("ok"):
            print(f"已登录：{who.get('username')}（鉴权接口通过，可以提交）")
            return 0
        print(f"不可提交：isSignedIn={who.get('isSignedIn')} 鉴权接口={rest.get('status')}"
              "　请运行 scripts/lc_login.py")
        return 2

    index = load_index()
    sols = store.all_numbers()
    if args:
        sols = [s for s in sols if any(s == a or s.startswith(a) for a in args)]
    sols = [s for s in sols if s in index]
    sols.sort(key=sort_key)
    if not sols:
        print("没有匹配的题解（solutions/leetcode/ 下还没有对应目录）")
        return 0

    results = load_results()
    if dry:
        for i, no in enumerate(sols, 1):
            meta = index[no]
            src = store.sol_path(no).read_text(encoding="utf-8")
            code = src if keep_comments else strip_code.strip(src)
            print(f"[{i}/{len(sols)}] {no:<8} DRY slug={meta['uuid']:<28} "
                  f"qid={meta.get('internalId') or meta.get('questionId'):<6} "
                  f"lang={LANG} code={len(code)}B {strip_code.summary(src, code)}")
        return 0

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        ctx = persistent_context(pw, headless=not headed)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://leetcode.cn/problemset/", wait_until="domcontentloaded")
        who = page.evaluate(WHOAMI_JS) or {}
        rest = page.evaluate(REST_AUTH_JS)
        if not (who.get("isSignedIn") and rest.get("ok")):
            print(f"会话不可用（isSignedIn={who.get('isSignedIn')} "
                  f"鉴权接口={rest.get('status')}），请重新运行 scripts/lc_login.py")
            ctx.close()
            return 2
        print(f"已登录：{who.get('username') or ''}\n")

        for i, no in enumerate(sols, 1):
            meta = index[no]
            tag = f"[{i}/{len(sols)}] {no:<8}"
            prev = results.get(no, {}).get("status")
            if prev == "AC":
                print(f"{tag} 已 AC，跳过", flush=True)
                continue
            if prev and not retry_failed:
                print(f"{tag} 上轮 {prev}，加 --retry 才重提", flush=True)
                continue

            # 提交接口只认题目页的同源上下文，逐题切页面
            page.goto(f"https://leetcode.cn/problems/{meta['uuid']}/",
                      wait_until="domcontentloaded")
            src = store.sol_path(no).read_text(encoding="utf-8")
            code = src if keep_comments else strip_code.strip(src)
            r = judge_once(page, meta, code)
            results[no] = r
            save_results(results, no)
            icon = "✅ AC" if r["status"] == "AC" else "❌ " + str(r.get("verdict"))[:80]
            extra = ""
            if r["status"] == "AC" and r.get("runtime"):
                extra = f"   {r['runtime']} / {r.get('memory', '')}"
            elif r.get("total_correct") is not None:
                extra = f"   {r.get('total_correct')}/{r.get('total_testcases')} 用例"
            print(f"{tag} {icon}{extra}", flush=True)
            time.sleep(delay)

        ctx.close()

    print(f"\n报告 -> {render(results)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
