"""抓某题的**社区题解**全文，落到 sources/05-nowcoder/community/<题号>.md。

牛客的题解在题目页的「题解」标签页里，是客户端渲染的，正文默认折叠。
抓取流程：开题目页 -> 点「题解(N)」标签 -> 把所有「展开」点开 -> 取整页文本。

不做语言筛选：站上大部分题解**没有打语言标签**，
按 Python3 过滤会得到「现在还没有解题哦」，把真正有用的题解全滤掉。
一律全量抓下来，语言自己看。

用法:
  uv run python scripts/nc_solutions.py BISHI127
  uv run python scripts/nc_solutions.py BISHI127 BISHI128 BISHI130
  uv run python scripts/nc_solutions.py --pages 2 BISHI103    # 多翻几页题解
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sources" / "05-nowcoder" / "community"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nc_submit as S  # noqa: E402  复用会话、题目 URL 拼装、索引加载

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")

# 点「题解(N)」标签：它是个叶子节点，文本形如 "题解(5)"
JS_TAB = """
() => {
  const els = [...document.querySelectorAll('*')].filter(
    e => e.children.length === 0 && /^题解\\(/.test((e.textContent || '').trim()));
  if (!els.length) return 'no-tab';
  let t = els[0];
  for (let i = 0; i < 3 && t; i++) { t.click(); t = t.parentElement; }
  return 'ok';
}
"""

# 把所有「展开」点开。点开后按钮文字会变，所以要反复扫直到没有为止。
JS_EXPAND = """
() => {
  const els = [...document.querySelectorAll('*')].filter(
    e => e.children.length === 0 && (e.textContent || '').trim() === '展开');
  els.forEach(e => { let t = e; for (let i = 0; i < 3 && t; i++) { t.click(); t = t.parentElement; } });
  return els.length;
}
"""

JS_NEXT = """
() => {
  const els = [...document.querySelectorAll('*')].filter(
    e => e.children.length === 0 && (e.textContent || '').trim() === '下一页');
  if (!els.length) return 0;
  let t = els[0];
  for (let i = 0; i < 3 && t; i++) { t.click(); t = t.parentElement; }
  return 1;
}
"""


def grab(page, meta: dict, pages: int) -> str:
    page.goto(S.question_url(meta), wait_until="domcontentloaded", timeout=60000)
    time.sleep(8)
    if page.evaluate(JS_TAB) == "no-tab":
        return ""
    time.sleep(6)

    chunks = []
    for pg_i in range(pages):
        for _ in range(6):                       # 展开是分批渲染的，多点几轮
            if not page.evaluate(JS_EXPAND):
                break
            time.sleep(1.5)
        time.sleep(2)
        txt = page.evaluate("() => document.body.innerText")
        # 只保留题解区：从「代码语言：」那一行之后开始，到页尾的编辑器模板之前
        i = txt.find("代码语言：")
        if i >= 0:
            txt = txt[i:]
        j = txt.find("ACM 模式")
        if j > 0:
            txt = txt[:j]
        chunks.append(f"\n\n<!-- 第 {pg_i + 1} 页 -->\n\n" + txt.strip())
        if pg_i + 1 < pages and not page.evaluate(JS_NEXT):
            break
        time.sleep(5)
    return "\n".join(chunks)


def main(argv) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    from playwright.sync_api import sync_playwright

    args = [a for a in argv[1:] if not a.startswith("--")]
    pages = 1
    for a in argv[1:]:
        if a.startswith("--pages"):
            pages = int(a.split("=", 1)[1]) if "=" in a else 2
    if not args:
        print(__doc__)
        return 2

    index = S.load_index()
    todo = [a for a in args if a in index]
    if not todo:
        print("没有匹配的题号")
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"])
        ctx = b.new_context(storage_state=str(S.AUTH), user_agent=UA,
                            viewport={"width": 1600, "height": 1000})
        page = ctx.new_page()
        for no in todo:
            meta = index[no]
            text = grab(page, meta, pages)
            p = OUT / f"{no}.md"
            p.write_text(
                f"# {no} {meta['title']} —— 社区题解\n\n"
                f"> 抓自 {meta['url']}　由 `scripts/nc_solutions.py` 生成，未做语言筛选。\n"
                + text + "\n", encoding="utf-8")
            print(f"{no:<10} {len(text):>7} 字 -> {p}", flush=True)
        b.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
